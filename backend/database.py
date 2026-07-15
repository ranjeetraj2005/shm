import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Use local persistent storage
_client = None
COLLECTION_NAME = "proposals"

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(path="qdrant_data")
        try:
            _client.get_collection(COLLECTION_NAME)
        except Exception:
            _client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
    return _client

def save_evaluation(proposal_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> str:
    record_id = str(uuid.uuid4())
    # Dummy vector for POC payload storage
    dummy_vector = [0.0] * 384 
    
    payload = {
        "proposal_data": proposal_data,
        "evaluation_result": evaluation_result
    }
    
    get_client().upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=record_id,
                vector=dummy_vector,
                payload=payload
            )
        ]
    )
    return record_id

def get_all_evaluations() -> List[Dict[str, Any]]:
    try:
        records, _ = get_client().scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for record in records:
            results.append({
                "id": record.id,
                "payload": record.payload
            })
        return results
    except Exception:
        return []

def get_evaluation(record_id: str) -> Dict[str, Any]:
    try:
        records = get_client().retrieve(
            collection_name=COLLECTION_NAME,
            ids=[record_id]
        )
        if records:
            return records[0].payload
    except Exception:
        pass
    return None
