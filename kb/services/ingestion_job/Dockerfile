FROM python:3.9-slim

WORKDIR /app

# Install dependencies
# - requests: For HTTP requests to embedding service
# - qdrant-client: Qdrant database client
# - minio: MinIO object storage client
# - jira: Python client for Jira API
# - atlassian-python-api: Python client for Confluence API
# - beautifulsoup4: For parsing and cleaning HTML from Confluence
# - langchain-text-splitters: For robust text chunking
RUN pip install requests qdrant-client minio jira atlassian-python-api beautifulsoup4 langchain-text-splitters

# Copy the application code
COPY ./ingest_data.py /app/

# Command to run the script
CMD ["python", "ingest_data.py"]