from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import CrossEncoder
import os

app = FastAPI()

class RerankRequest(BaseModel):
    query: str
    docs: list[str]

# Load the model from the environment variable
model_name = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-base")
model = CrossEncoder(model_name)

@app.post("/rerank")
def rerank(request: RerankRequest):
    try:
        scores = model.predict([(request.query, doc) for doc in request.docs])
        return {"scores": scores.tolist(), "model_used": model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
