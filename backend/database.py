import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

class QdrantDB:
    def __init__(self, path: str = "local_qdrant", collection_name: str = "proposals"):
        self.path = path
        self.collection_name = collection_name
        self._client = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(path=self.path)
            try:
                self._client.get_collection(self.collection_name)
            except Exception:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
        return self._client

    def save_evaluation(self, proposal_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> str:
        record_id = str(uuid.uuid4())
        # Dummy vector for POC payload storage
        dummy_vector = [0.0] * 384 
        
        payload = {
            "proposal_data": proposal_data,
            "evaluation_result": evaluation_result
        }
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=record_id,
                    vector=dummy_vector,
                    payload=payload
                )
            ]
        )
        return record_id

    def get_all_evaluations(self) -> List[Dict[str, Any]]:
        try:
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
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

    def get_evaluation(self, record_id: str) -> Dict[str, Any]:
        try:
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[record_id]
            )
            if records:
                return records[0].payload
        except Exception:
            pass
        return None

# Singleton instance for the module
db = QdrantDB()

# Export functions to maintain backward compatibility with main.py
def get_client() -> QdrantClient:
    return db.client

save_evaluation = db.save_evaluation
get_all_evaluations = db.get_all_evaluations
get_evaluation = db.get_evaluation
