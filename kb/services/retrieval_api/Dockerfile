FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn python-multipart requests qdrant-client minio

# Copy the application code
COPY ./retrieval_api.py /app/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "retrieval_api:app", "--host", "0.0.0.0", "--port", "8000"]
