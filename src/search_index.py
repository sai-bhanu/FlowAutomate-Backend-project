from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
from .config import settings
import argparse, json

def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[settings.OPENSEARCH_URL],
        http_auth=HTTPBasicAuth(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASS),
        use_ssl=settings.OPENSEARCH_URL.startswith("https"),
        verify_certs=False,
        connection_class=RequestsHttpConnection,
        timeout=30
    )

def index_name() -> str:
    return settings.OPENSEARCH_INDEX

def mapping():
    return {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "knn": True
            },
            "analysis": {
                "analyzer": {
                    "default": {
                        "type": "standard"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "pdf_id": {"type": "keyword"},
                "page": {"type": "integer"},
                "type": {"type": "keyword"},
                "text": {"type": "text"},
                "table_text": {"type": "text"},
                "bbox": {"type": "integer"},
                "metadata": {"type": "object", "enabled": True},
                "vector": {
                    "type": "knn_vector",
                    "dimension": settings.EMBEDDING_DIM,
                    "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "nmslib"}
                }
            }
        }
    }

def create_index():
    client = get_client()
    idx = index_name()
    if client.indices.exists(idx):
        print(f"Index '{idx}' already exists")
        return
    client.indices.create(idx, body=mapping())
    print(f"Created index '{idx}'")

def delete_index():
    client = get_client()
    idx = index_name()
    if client.indices.exists(idx):
        client.indices.delete(idx)
        print(f"Deleted index '{idx}'")
    else:
        print(f"Index '{idx}' not found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()
    if args.delete:
        delete_index()
    if args.create:
        create_index()
