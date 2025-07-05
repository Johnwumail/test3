from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os

app = FastAPI()

class EmbedRequest(BaseModel):
    texts: list[str]
    normalize_embeddings: bool = True

# Load the model from the environment variable
model_name = os.getenv("MODEL_NAME", "BAAI/bge-large-zh-v1.5")
model = SentenceTransformer(model_name)

@app.post("/embed")
def embed(request: EmbedRequest):
    try:
        embeddings = model.encode(request.texts, normalize_embeddings=request.normalize_embeddings)
        return {"embeddings": embeddings.tolist(), "model_used": model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
