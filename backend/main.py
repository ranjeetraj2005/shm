from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from database import save_evaluation, get_all_evaluations, get_evaluation, get_client as get_qdrant
from agent_pipeline import evaluator_app, process_user_query
import os
import uuid
import PyPDF2
from io import BytesIO
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agentic Proposal Evaluator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Qdrant setup using database.py get_client

def get_embeddings(text: str) -> list[float]:
    if "AZURE_OPENAI_API_KEY" in os.environ:
        try:
            from langchain_openai import AzureOpenAIEmbeddings
            embedder = AzureOpenAIEmbeddings(
                azure_deployment=os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
                api_key=os.environ.get("AZURE_OPENAI_API_KEY")
            )
            return embedder.embed_query(text)
        except Exception:
            pass
    return [0.0] * 1536

def process_file_content(file: UploadFile) -> str:
    content = file.file.read()
    if file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    elif file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
        df = pd.read_excel(BytesIO(content))
        return df.to_string()
    return content.decode("utf-8", errors="ignore")

def store_in_qdrant(collection_name: str, text: str, extra_payload: dict = None):
    client = get_qdrant()
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    points = []
    
    # Generate unique point IDs using uuid
    for chunk in chunks:
        if not chunk.strip(): continue
        vector = get_embeddings(chunk)
        payload = {"text": chunk}
        if extra_payload:
            payload.update(extra_payload)
        points.append(
            PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
        )
    if points:
        client.upsert(collection_name=collection_name, points=points)

class ProposalInput(BaseModel):
    proposal_id: str

class CriteriaInput(BaseModel):
    criteria_text: str

CRITERIA_FILE = "criteria.txt"

@app.post("/criteria")
def save_criteria(data: CriteriaInput):
    client = get_qdrant()
    if client.collection_exists("evaluation_criteria"):
        client.delete_collection("evaluation_criteria")
    store_in_qdrant("evaluation_criteria", data.criteria_text)
    return {"status": "success"}

@app.get("/criteria")
def get_criteria():
    criteria_text = ""
    client = get_qdrant()
    if client.collection_exists("evaluation_criteria"):
        scroll_res, _ = client.scroll(
            collection_name="evaluation_criteria", 
            limit=1000, 
            with_payload=True
        )
        for point in scroll_res:
            criteria_text += point.payload.get("text", "") + "\n"
    return {"criteria_text": criteria_text}

@app.post("/upload_criteria")
def upload_criteria(files: List[UploadFile] = File(...)):
    collection_name = "evaluation_criteria"
    combined_text = ""
    for f in files:
        combined_text += f"\n--- {f.filename} ---\n" + process_file_content(f)
    
    store_in_qdrant(collection_name, combined_text)
    return {"status": "success"}

@app.post("/upload_knowledge")
def upload_knowledge(files: List[UploadFile] = File(...)):
    proposal_id = str(uuid.uuid4())
    collection_name = "business_proposals"
    combined_text = ""
    for f in files:
        combined_text += f"\n--- {f.filename} ---\n" + process_file_content(f)
    
    store_in_qdrant(collection_name, combined_text, extra_payload={"proposal_id": proposal_id})
    return {"status": "success", "proposal_id": proposal_id}

@app.post("/upload_past_opportunities")
def upload_past_opportunities(files: List[UploadFile] = File(...)):
    collection_name = "past_opportunities"
    combined_text = ""
    for f in files:
        combined_text += f"\n--- {f.filename} ---\n" + process_file_content(f)
    
    store_in_qdrant(collection_name, combined_text)
    return {"status": "success"}

@app.post("/evaluate")
def evaluate_proposal(data: ProposalInput):
    collection_name = "business_proposals"
    proposal_text = ""
    client = get_qdrant()
    
    if client.collection_exists(collection_name):
        scroll_res, _ = client.scroll(
            collection_name=collection_name, 
            limit=1000, 
            with_payload=True
        )
        for point in scroll_res:
            if point.payload.get("proposal_id") == data.proposal_id:
                proposal_text += point.payload.get("text", "") + "\n"

    criteria_text = ""
    if client.collection_exists("evaluation_criteria"):
        scroll_res, _ = client.scroll(
            collection_name="evaluation_criteria", 
            limit=1000, 
            with_payload=True
        )
        for point in scroll_res:
            criteria_text += point.payload.get("text", "") + "\n"

    past_opportunities_text = ""
    if client.collection_exists("past_opportunities"):
        scroll_res, _ = client.scroll(
            collection_name="past_opportunities", 
            limit=1000, 
            with_payload=True
        )
        for point in scroll_res:
            past_opportunities_text += point.payload.get("text", "") + "\n"

    initial_state = {
        "proposal_text": proposal_text,
        "financials_base64": "",
        "criteria_text": criteria_text,
        "past_opportunities_text": past_opportunities_text,
        "structured_data": {},
        "classification": {},
        "criteria_scores": {},
        "final_score": 0.0,
        "rating": "",
        "final_report": ""
    }
    
    try:
        final_state = evaluator_app.invoke(initial_state)
        
        # Save evaluation
        record_id = save_evaluation(
            proposal_data={"proposal_id": data.proposal_id},
            evaluation_result=final_state
        )
        
        return {
            "status": "success",
            "id": record_id,
            "result": final_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    return get_all_evaluations()

@app.get("/report/{record_id}")
def get_report(record_id: str):
    eval_data = get_evaluation(record_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Not found")
    return eval_data

class UserQueryInput(BaseModel):
    proposal_id: str
    query: str

@app.post("/query")
def handle_user_query(data: UserQueryInput):
    collection_name = "business_proposals"
    proposal_text = ""
    client = get_qdrant()
    
    if client.collection_exists(collection_name):
        scroll_res, _ = client.scroll(
            collection_name=collection_name, 
            limit=1000, 
            with_payload=True
        )
        for point in scroll_res:
            if point.payload.get("proposal_id") == data.proposal_id:
                proposal_text += point.payload.get("text", "") + "\n"

    past_opportunities_text = ""
    if client.collection_exists("past_opportunities"):
        scroll_res, _ = client.scroll(
            collection_name="past_opportunities", 
            limit=1000, 
            with_payload=True
        )
        for point in scroll_res:
            past_opportunities_text += point.payload.get("text", "") + "\n"

    try:
        res = process_user_query(data.query, proposal_text, past_opportunities_text)
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
