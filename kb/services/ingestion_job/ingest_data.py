import os
import requests
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from qdrant_client import QdrantClient, models
from minio import Minio
from jira import JIRA
from atlassian import Confluence
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Configuration ---
# General
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8000/embed")
COLLECTION_NAME = "knowledge_base"
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", 64))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 10))

# MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = "raw-data"

# Qdrant
QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT")

# Jira
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_JQL = os.getenv("JIRA_JQL", "project = KB") # Example JQL

# Confluence
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACES = os.getenv("CONFLUENCE_SPACES", "KB,DOCS").split(',') # Comma-separated list of space keys

# --- Clients ---
qdrant_client = QdrantClient(host=QDRANT_ENDPOINT, port=6333)
minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
jira_client = JIRA(server=JIRA_URL, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))
confluence_client = Confluence(url=CONFLUENCE_URL, username=CONFLUENCE_USERNAME, password=CONFLUENCE_API_TOKEN)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len,
)

def get_embeddings(texts):
    """Calls the embedding service in batches."""
    try:
        response = requests.post(EMBEDDING_SERVICE_URL, json={"texts": texts})
        response.raise_for_status()
        return response.json()["embeddings"]
    except requests.RequestException as e:
        print(f"Error calling embedding service: {e}")
        return None

def upload_to_minio(doc_id, content):
    """Uploads raw content to MinIO."""
    try:
        content_json = json.dumps(content, indent=2, ensure_ascii=False)
        content_bytes = content_json.encode('utf-8')
        minio_client.put_object(
            MINIO_BUCKET,
            doc_id,
            data=io.BytesIO(content_bytes),
            length=len(content_bytes),
            content_type='application/json'
        )
    except Exception as e:
        print(f"Error uploading to MinIO for doc {doc_id}: {e}")


def process_and_upload_documents(documents):
    """
    Processes a list of document dictionaries, chunks text, gets embeddings,
    and uploads to Qdrant and MinIO in batches for efficiency.
    """
    points_to_upload = []
    
    for doc in documents:
        doc_id = doc['metadata']['doc_id']
        
        # Upload raw document to MinIO
        upload_to_minio(f"{doc_id}.json", doc)

        # Chunk the text
        chunks = text_splitter.split_text(doc['text'])
        
        if not chunks:
            continue

        # Get embeddings for all chunks of the document in one go
        embeddings = get_embeddings(chunks)
        if not embeddings:
            print(f"Skipping document {doc_id} due to embedding failure.")
            continue

        # Create Qdrant points
        for i, chunk in enumerate(chunks):
            point_id = str(uuid.uuid4())
            
            metadata = doc['metadata'].copy()
            metadata['chunk_index'] = i
            
            points_to_upload.append(
                models.PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload={
                        "text": chunk,
                        "metadata": metadata
                    }
                )
            )

    # Batch upload points to Qdrant
    if points_to_upload:
        print(f"Uploading {len(points_to_upload)} points to Qdrant...")
        try:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points_to_upload,
                wait=True
            )
        except Exception as e:
            print(f"Error uploading points to Qdrant: {e}")

def fetch_jira_issue(issue_key):
    """Fetches a single Jira issue and formats it."""
    try:
        issue = jira_client.issue(issue_key, expand="changelog")
        
        content = [issue.fields.summary, issue.fields.description or ""]
        for comment in issue.fields.comment.comments:
            content.append(comment.body)
        
        text_content = "\n\n".join(filter(None, content))
        
        return {
            "text": text_content,
            "metadata": {
                "doc_id": f"jira-{issue.key}",
                "source": "jira",
                "title": issue.fields.summary,
                "url": issue.permalink(),
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "project": issue.fields.project.key,
                "status": issue.fields.status.name,
            }
        }
    except Exception as e:
        print(f"Failed to fetch Jira issue {issue_key}: {e}")
        return None

def ingest_jira():
    """Ingests data from Jira using parallel fetching."""
    print("Starting Jira ingestion...")
    issues = jira_client.search_issues(JIRA_JQL, maxResults=False, fields="key")
    issue_keys = [issue.key for issue in issues]
    print(f"Found {len(issue_keys)} issues in Jira.")

    documents = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_issue = {executor.submit(fetch_jira_issue, key): key for key in issue_keys}
        for future in as_completed(future_to_issue):
            result = future.result()
            if result:
                documents.append(result)
    
    print(f"Successfully fetched {len(documents)} issues. Processing and uploading...")
    process_and_upload_documents(documents)
    print("Jira ingestion finished.")


def fetch_confluence_page(page_id):
    """Fetches a single Confluence page and formats it."""
    try:
        page = confluence_client.get_page_by_id(page_id, expand='body.storage,version')
        html_content = page['body']['storage']['value']
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator='\n', strip=True)
        
        return {
            "text": text_content,
            "metadata": {
                "doc_id": f"confluence-{page['id']}",
                "source": "confluence",
                "title": page['title'],
                "url": page['_links']['webui'],
                "created": page['history']['createdDate'],
                "updated": page['version']['when'],
                "space": page['space']['key'],
            }
        }
    except Exception as e:
        print(f"Failed to fetch Confluence page {page_id}: {e}")
        return None

def ingest_confluence():
    """Ingests data from Confluence using parallel fetching, supporting CQL."""
    print("Starting Confluence ingestion...")
    page_ids = []

    if CONFLUENCE_CQL:
        print(f"Fetching pages from Confluence using CQL: {CONFLUENCE_CQL}")
        try:
            # The atlassian-python-api cql method handles pagination automatically
            cql_results = confluence_client.cql(CONFLUENCE_CQL, limit=200)
            # The structure of the result is a dict with a 'results' key
            page_ids = [page['content']['id'] for page in cql_results.get('results', [])]
        except Exception as e:
            print(f"Error executing Confluence CQL query: {e}")
            # Exit gracefully if CQL fails
            page_ids = []
    else:
        print(f"CONFLUENCE_CQL not set. Fetching all pages from spaces: {CONFLUENCE_SPACES}")
        for space in CONFLUENCE_SPACES:
            try:
                pages_in_space = confluence_client.get_all_pages_from_space(space)
                page_ids.extend([page['id'] for page in pages_in_space])
            except Exception as e:
                print(f"Error fetching pages from space {space}: {e}")

    if not page_ids:
        print("No pages found in Confluence to ingest.")
        return

    print(f"Found {len(page_ids)} pages to process.")

    documents = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(fetch_confluence_page, page_id): page_id for page_id in page_ids}
        for future in as_completed(future_to_page):
            result = future.result()
            if result:
                documents.append(result)

    if not documents:
        print("Failed to fetch details for any of the found page IDs.")
        return
        
    print(f"Successfully fetched {len(documents)} pages. Processing and uploading...")
    process_and_upload_documents(documents)
    print("Confluence ingestion finished.")


def main():
    """Main function to run the ingestion job."""
    print("Starting ingestion job...")
    
    # 1. Ensure Qdrant collection exists
    try:
        qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        print(f"Qdrant collection '{COLLECTION_NAME}' already exists.")
    except Exception:
        print(f"Creating Qdrant collection '{COLLECTION_NAME}'...")
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE), # Adjust size based on embedding model
        )

    # 2. Ensure MinIO bucket exists
    if not minio_client.bucket_exists(MINIO_BUCKET):
        print(f"Creating MinIO bucket '{MINIO_BUCKET}'...")
        minio_client.make_bucket(MINIO_BUCKET)
    else:
        print(f"MinIO bucket '{MINIO_BUCKET}' already exists.")

    # 3. Run ingestion sources
    ingest_jira()
    ingest_confluence()

    print("Ingestion job finished.")

if __name__ == "__main__":
    main()