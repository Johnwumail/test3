from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from qdrant_client import QdrantClient
import os

app = FastAPI()

class QueryRequest(BaseModel):
    text: str

# --- Configuration ---
QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT")
EMBEDDING_SERVICE_URL = "http://embedding-service:8000/embed"
RERANKER_SERVICE_URL = "http://reranker-service:8000/rerank"
COLLECTION_NAME = "knowledge_base"

# --- Clients ---
qdrant_client = QdrantClient(host=QDRANT_ENDPOINT, port=6333)

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

@app.get("/health")
def health():
    return {"status": "ok"}
