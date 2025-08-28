# PDF Unstructured Search Backend (ETL + API)

A reference backend to index and search **Paragraphs, Images, and Tables** extracted from PDFs.

## Tech
- **Python 3.10+**
- **FastAPI** for the Search API
- **OpenSearch** (or Elasticsearch 8.x) for hybrid search (BM25 + vector)
- **sentence-transformers** for text & image embeddings (CLIP for images)
- **Redis** for rate limiting & seatbelt caching
- **JWT or API Key** auth for the API

## Run locally
```bash
# 1) Start infra (OpenSearch + Redis)
docker compose up -d

# 2) Create virtualenv and install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3) Export env (or use .env file)
export OPENSEARCH_URL=http://localhost:9200
export OPENSEARCH_USER=admin
export OPENSEARCH_PASS=admin
export OPENSEARCH_INDEX=pdf_search
export API_KEYS=devkey123,anotherkey456
export JWT_SECRET=supersecret
export REDIS_URL=redis://localhost:6379/0

# 4) Create index
python -m src.search_index --create

# 5) Ingest sample (expects your parser output JSONL at data/parsed.jsonl)
python -m src.etl_pipeline --input data/parsed.jsonl

# 6) Run API
uvicorn src.api.main:app --reload --port 8080
```

## Parser Input Format (JSONL)
Each line is one **document fragment** (paragraph, table, image) from a PDF:
```json
{
  "pdf_id": "invoice-42",
  "page": 3,
  "type": "paragraph",              // "paragraph" | "table" | "image"
  "text": "This is a paragraph...", // for paragraph/table (table text can be linearized)
  "table": { "rows": [[...]] },     // optional for tables
  "image_b64": "..."                // optional for images (base64-encoded)
  "bbox": [x0,y0,x1,y1],            // optional
  "metadata": { "title": "Report Q1" }
}
```

## Security
- **API Key** via `x-api-key` header or **JWT** via `Authorization: Bearer ...`
- **Rate limiting** via Redis token bucket (configurable)
- **CORS** locked down by default

## AWS Deployment (brief)
- **Amazon OpenSearch Service** for the index
- **Amazon ElastiCache (Redis)** for rate limiting
- **API** on **AWS Fargate (ECS)** or **Lambda (via API Gateway)**
- **Secrets** in **AWS Secrets Manager / SSM Parameter Store**
- **Artifacts** in **ECR** (Docker) and **S3** for parser outputs
- **Private networking** via **VPC**, **Security Groups**, **NACLs**
- **Observability**: CloudWatch logs/metrics, X-Ray tracing
