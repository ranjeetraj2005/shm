from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from typing import Optional
from database import save_evaluation, get_all_evaluations, get_evaluation
from agent_pipeline import evaluator_app

app = FastAPI(title="Agentic Proposal Evaluator")

class ProposalInput(BaseModel):
    proposal_text: str
    timeline_text: Optional[str] = ""
    financials: Optional[str] = ""
    market: Optional[str] = ""
    risks: Optional[str] = ""
    roi_model: Optional[str] = ""
    financials_file_base64: Optional[str] = ""

@app.post("/evaluate")
def evaluate_proposal(data: ProposalInput):
    initial_state = {
        "proposal_text": data.proposal_text,
        "timeline_text": data.timeline_text,
        "financials": data.financials,
        "financials_file_base64": data.financials_file_base64,
        "market": data.market,
        "risks": data.risks,
        "roi_model": data.roi_model,
        "structured_data": {},
        "classification": {},
        "criteria_scores": {},
        "roi_calculations": {},
        "final_score": 0.0,
        "rating": "",
        "final_report": ""
    }
    
    try:
        final_state = evaluator_app.invoke(initial_state)
        
        record_id = save_evaluation(
            proposal_data=data.dict(),
            evaluation_result=final_state
        )
        
        return {
            "status": "success",
            "id": record_id,
            "result": final_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate_stream")
def evaluate_stream(data: ProposalInput):
    initial_state = {
        "proposal_text": data.proposal_text,
        "timeline_text": data.timeline_text,
        "financials": data.financials,
        "financials_file_base64": data.financials_file_base64,
        "market": data.market,
        "risks": data.risks,
        "roi_model": data.roi_model,
        "structured_data": {},
        "classification": {},
        "criteria_scores": {},
        "roi_calculations": {},
        "final_score": 0.0,
        "rating": "",
        "final_report": ""
    }

    def event_generator():
        try:
            final_state = initial_state.copy()
            for step in evaluator_app.stream(initial_state):
                node_name = list(step.keys())[0]
                update = step[node_name]
                final_state.update(update)
                yield f"event: progress\ndata: {json.dumps({'node': node_name})}\n\n"
                
            record_id = save_evaluation(
                proposal_data=data.dict(),
                evaluation_result=final_state
            )
            
            yield f"event: complete\ndata: {json.dumps({'status': 'success', 'id': record_id, 'result': final_state})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/history")
def get_history():
    return get_all_evaluations()

@app.get("/report/{record_id}")
def get_report(record_id: str):
    eval_data = get_evaluation(record_id)
    if not eval_data:
        raise HTTPException(status_code=404, detail="Not found")
    return eval_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
