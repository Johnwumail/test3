from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from qdrant_client import QdrantClient, models
from minio import Minio
import os

app = FastAPI()

class QueryRequest(BaseModel):
    text: str

# --- Configuration ---
QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT")
EMBEDDING_SERVICE_URL = "http://embedding-service:8000/embed"
RERANKER_SERVICE_URL = "http://reranker-service:8000/rerank"
COLLECTION_NAME = "knowledge_base"

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = "raw-data"

# --- Clients ---
qdrant_client = QdrantClient(host=QDRANT_ENDPOINT, port=6333)
minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

def get_embeddings(texts):
    response = requests.post(EMBEDDING_SERVICE_URL, json={"texts": texts})
    response.raise_for_status()
    return response.json()["embeddings"]

def rerank(query, docs):
    response = requests.post(RERANKER_SERVICE_URL, json={"query": query, "docs": docs})
    response.raise_for_status()
    return response.json()["scores"]

@app.post("/query")
def query(request: QueryRequest):
    try:
        query_embedding = get_embeddings([request.text])[0]

        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=10 # Number of results to retrieve
        )

        # Rerank the results
        docs_to_rerank = [result.payload["text"] for result in search_results]
        scores = rerank(request.text, docs_to_rerank)

        reranked_results = sorted(zip(scores, search_results), key=lambda x: x[0], reverse=True)

        return {"results": [result.payload for score, result in reranked_results]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/document/{doc_id}")
def delete_document(doc_id: str):
    """Deletes a document from MinIO and Qdrant based on its doc_id."""
    try:
        # 1. Delete from Qdrant
        # Qdrant allows deleting points by filter. We filter by the 'doc_id' in the payload metadata.
        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.doc_id",
                            match=models.MatchValue(value=doc_id)
                        )
                    ]
                )
            )
        )
        print(f"Successfully deleted document {doc_id} from Qdrant.")

        # 2. Delete from MinIO
        # The MinIO object name is the doc_id with a .json extension
        minio_client.remove_object(MINIO_BUCKET, f"{doc_id}.json")
        print(f"Successfully deleted document {doc_id}.json from MinIO bucket {MINIO_BUCKET}.")

        return {"status": "success", "message": f"Document {doc_id} deleted successfully."}

    except Exception as e:
        print(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document {doc_id}: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}
