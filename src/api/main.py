from __future__ import annotations
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opensearchpy import OpenSearch
from typing import List, Optional, Any
import redis
from ..config import settings
from ..search_index import get_client, index_name
from ..security import require_api_key
from ..embedder import Embedder

app = FastAPI(title="PDF Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

rds = redis.from_url(settings.REDIS_URL)
embedder = Embedder()

class SearchRequest(BaseModel):
    query: str
    pdf_id: Optional[str] = None
    k: int = 10
    use_vector: bool = True

class SearchHit(BaseModel):
    score: float
    pdf_id: str
    page: Optional[int]
    type: str
    text: Optional[str]
    table_text: Optional[str]
    metadata: dict | None = None

class SearchResponse(BaseModel):
    took_ms: int
    hits: List[SearchHit]

def token_bucket(key: str, refill_rate: int = 10, capacity: int = 20) -> bool:
    # Allows ~10 req/sec with burst 20 per API key
    with rds.pipeline() as p:
        p.hgetall(key)
        data = p.execute()[0]
    import time
    now = int(time.time())
    tokens = int(data.get(b"tokens", b"0")) if data else capacity
    last = int(data.get(b"last", b"%d" % now)) if data else now
    elapsed = max(0, now - last)
    tokens = min(capacity, tokens + elapsed * refill_rate)
    if tokens <= 0:
        with rds.pipeline() as p:
            p.hset(key, mapping={"tokens": tokens, "last": now})
            p.expire(key, 60)
            p.execute()
        return False
    tokens -= 1
    with rds.pipeline() as p:
        p.hset(key, mapping={"tokens": tokens, "last": now})
        p.expire(key, 60)
        p.execute()
    return True

@app.post("/v1/search", response_model=SearchResponse, dependencies=[Depends(require_api_key)])
def search(req: SearchRequest):
    api_key = "default"  # already validated; for per-key limits, pass real header value
    if not token_bucket(f"rl:{api_key}"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    client: OpenSearch = get_client()
    must: list[dict[str, Any]] = []
    if req.pdf_id:
        must.append({"term": {"pdf_id": req.pdf_id}})

    # Keyword query (BM25)
    keyword_q = {
        "multi_match": {
            "query": req.query,
            "fields": ["text^3", "table_text^2"],
            "type": "best_fields"
        }
    }
    should: list[dict[str, Any]] = [keyword_q]

    # Vector query (semantic)
    if req.use_vector:
        qvec = embedder.embed_text(req.query)
        should.append({
            "knn": {
                "vector": {
                    "vector": qvec,
                    "k": max(50, req.k)  # retrieve more for re-ranking
                }
            }
        })

    body = {
        "size": req.k,
        "query": {
            "bool": {
                "must": must,
                "should": should,
                "minimum_should_match": 1
            }
        },
        "_source": ["pdf_id", "page", "type", "text", "table_text", "metadata"]
    }

    res = client.search(index=index_name(), body=body)
    hits = [
        SearchHit(
            score=h.get("_score", 0.0),
            pdf_id=h["_source"].get("pdf_id"),
            page=h["_source"].get("page"),
            type=h["_source"].get("type"),
            text=h["_source"].get("text"),
            table_text=h["_source"].get("table_text"),
            metadata=h["_source"].get("metadata"),
        )
        for h in res["hits"]["hits"]
    ]
    return SearchResponse(took_ms=res["took"], hits=hits)

class IndexRequest(BaseModel):
    # For small docs, you can ingest directly via API; otherwise use ETL script
    records: list[dict]

@app.post("/v1/index", dependencies=[Depends(require_api_key)])
def index_docs(req: IndexRequest):
    from opensearchpy import helpers
    client = get_client()
    actions = []
    for rec in req.records:
        from ..etl_pipeline import normalize_record
        norm = normalize_record(rec)
        vec = embedder.embed_text(norm.get("text") or "")
        norm["vector"] = vec
        _id = f"{norm['pdf_id']}:{norm.get('page',0)}:{hash((norm.get('text') or '')[:64])}"
        actions.append({"_op_type":"index","_index": index_name(), "_id": _id, "_source": norm})
    helpers.bulk(client, actions)
    return {"indexed": len(actions)}
