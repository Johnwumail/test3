# Use a base image with CUDA support for GPU acceleration
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn python-multipart sentence-transformers

# Copy the application code
COPY ./reranker_app.py /app/

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "reranker_app:app", "--host", "0.0.0.0", "--port", "8000"]
