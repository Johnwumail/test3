import os
import requests
import json
from qdrant_client import QdrantClient, models
from minio import Minio

# --- Configuration ---
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT")
EMBEDDING_SERVICE_URL = "http://embedding-service:8000/embed"

# --- Clients ---
qdrant_client = QdrantClient(host=QDRANT_ENDPOINT, port=6333)
minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)

COLLECTION_NAME = "knowledge_base"

def get_embeddings(texts):
    response = requests.post(EMBEDDING_SERVICE_URL, json={"texts": texts})
    response.raise_for_status()
    return response.json()["embeddings"]

def ingest_jira():
    # Placeholder for Jira ingestion logic
    print("Ingesting from Jira...")
    # 1. Fetch data from Jira API
    # 2. Process and chunk the data
    # 3. Get embeddings
    # 4. Store in Qdrant and MinIO
    pass

def ingest_confluence():
    # Placeholder for Confluence ingestion logic
    print("Ingesting from Confluence...")
    pass

def main():
    # Ensure collection exists
    try:
        qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    except Exception:
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE), # Adjust size based on embedding model
        )

    # Ensure bucket exists
    if not minio_client.bucket_exists("raw-data"):
        minio_client.make_bucket("raw-data")

    ingest_jira()
    ingest_confluence()

    print("Ingestion job finished.")

if __name__ == "__main__":
    main()
