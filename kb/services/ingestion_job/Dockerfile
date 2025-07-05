FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install requests qdrant-client minio

# Copy the application code
COPY ./ingest_data.py /app/

# Command to run the script
CMD ["python", "ingest_data.py"]
