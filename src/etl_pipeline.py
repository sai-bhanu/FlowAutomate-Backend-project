from __future__ import annotations
import argparse, json, base64
from typing import Iterable, Dict, Any
from opensearchpy import helpers
from .search_index import get_client, index_name
from .embedder import Embedder

def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    t = rec.get("type")
    text = rec.get("text") or ""
    table_text = ""
    if t == "table" and not text:
        table = rec.get("table")
        if table and "rows" in table:
            # simple linearization of table rows, customize as needed
            rows = table["rows"]
            table_text = "\n".join([", ".join(map(str, r)) for r in rows])
        text = table_text
    return {
        "pdf_id": rec.get("pdf_id"),
        "page": rec.get("page"),
        "type": t,
        "text": text,
        "table_text": table_text or None,
        "bbox": rec.get("bbox"),
        "metadata": rec.get("metadata") or {},
        "image_b64": rec.get("image_b64")  # kept transiently for embedding then dropped
    }

def to_actions(records: Iterable[Dict[str, Any]], embedder: Embedder):
    for rec in records:
        norm = normalize_record(rec)
        content_for_embedding = norm.get("text") or ""
        if not content_for_embedding and norm.get("image_b64"):
            vector = embedder.embed_image_b64(norm["image_b64"])
        else:
            vector = embedder.embed_text(content_for_embedding)
        # remove ephemeral
        norm.pop("image_b64", None)
        doc = {**norm, "vector": vector}
        yield {
            "_op_type": "index",
            "_index": index_name(),
            "_id": f"{doc['pdf_id']}:{doc.get('page',0)}:{hash((doc.get('text') or '')[:64])}",
            "_source": doc
        }

def load_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to JSONL exported from PDF parser")
    args = parser.parse_args()

    client = get_client()
    embedder = Embedder()
    records = load_jsonl(args.input)
    helpers.bulk(client, to_actions(records, embedder), chunk_size=256, request_timeout=120)
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
