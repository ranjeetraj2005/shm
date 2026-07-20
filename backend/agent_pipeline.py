from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
import json
import os
import base64
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    proposal_text: str
    financials_base64: str
    criteria_text: str
    
    structured_data: Dict[str, Any]
    classification: Dict[str, Any]
    criteria_scores: Dict[str, Any]
    final_score: float
    rating: str
    final_report: str

def get_llm():
    if "AZURE_OPENAI_API_KEY" in os.environ:
        try:
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
                api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
                temperature=0.2
            )
        except ImportError as e:
            print(f"Error importing AzureChatOpenAI: {e}")
            pass
    return None

def mock_llm_call(prompt: str, json_format=True) -> Any:
    if "structuring" in prompt.lower():
        return {"summary": "A mocked structured proposal summary.", "missing_info": ["Detailed timelines"]}
    if "classification" in prompt.lower():
        return {"division": "Technology", "subdivision": "SaaS"}
    if "criteria" in prompt.lower():
        return {"criteria_evaluations": [{"criteria": "Is scalable", "status": "match", "reason": "Software based"}], "overall_match_percentage": 85}
    if "report" in prompt.lower():
        return "# Executive Summary\n\nThis is a mocked report."
    return {}

def call_llm(prompt: str, json_format=True) -> Any:
    llm = get_llm()
    if not llm:
        print("llm not found, providing mock result")
        return mock_llm_call(prompt, json_format)
        
    try:
        from langchain_core.messages import HumanMessage
        msg = llm.invoke([HumanMessage(content=prompt)])
        content = msg.content
        if json_format:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        return content
    except Exception as e:
        print(f"LLM Error: {e}")
        return mock_llm_call(prompt, json_format)

def extract_with_pandasai(base64_str: str, llm) -> str:
    if not base64_str:
        return "No financial data provided."
    try:
        excel_bytes = base64.b64decode(base64_str)
        df = pd.read_excel(BytesIO(excel_bytes))
        
        if llm:
            try:
                from pandasai import SmartDataframe
                sdf = SmartDataframe(df, config={"llm": llm})
                res = sdf.chat("Summarize the key financial highlights and metrics.")
                if res:
                    return str(res)
            except ImportError:
                pass
                
        return df.head(20).to_markdown()
    except Exception as e:
        return f"Error extracting excel data: {e}"

def agent_1_structuring(state: AgentState):
    prompt = f"""
    You are a Proposal Structuring Agent. Normalize the following input into a structured summary and identify any missing info.
    Proposal Text: {state.get('proposal_text', '')}
    Respond ONLY in JSON with keys "summary" and "missing_info" (list of strings).
    """
    res = call_llm(prompt, json_format=True)
    return {"structured_data": res}

def agent_2_classification(state: AgentState):
    summary = state.get('structured_data', {}).get('summary', state.get('proposal_text', ''))
    prompt = f"""
    You are an Opportunity Classification Agent. Classify the proposal into a division.
    Proposal Summary: {summary}
    Respond ONLY in JSON with keys "division" and "Summary" where summary will deail out top 2-3 reason to identify this division by submitted business opportunity proposal.
    """
    res = call_llm(prompt, json_format=True)
    return {"classification": res}

def agent_3_criteria(state: AgentState):
    llm = get_llm()
    financials_text = extract_with_pandasai(state.get("financials_base64", ""), llm)
    
    prompt = f"""
    You are a Criteria Evaluation Agent. 
    Evaluate the proposal against the provided Admin Criteria. 
    For each criteria, state whether it is a "match" or "fail", and a brief reason.
    
    Admin Criteria:
    {state.get('criteria_text', 'No criteria defined.')}
    
    Proposal Data:
    {state.get('proposal_text', '')}
    
    Financial Data:
    {financials_text}
    
    Respond ONLY in JSON with keys "criteria_evaluations" (list of objects with "criteria", "status" as "match" or "fail", and "reason") and "overall_match_percentage" (0-100 integer).
    """
    res = call_llm(prompt, json_format=True)
    return {"criteria_scores": res}

def agent_5_scoring(state: AgentState):
    scores = state.get("criteria_scores", {})
    match_percentage = scores.get("overall_match_percentage", 50)
    
    final_score = match_percentage / 10.0
    
    if final_score >= 8.0:
        rating = "Exceptional Fit"
    elif final_score >= 6.5:
        rating = "Good Fit"
    elif final_score >= 5.0:
        rating = "Moderate Fit"
    else:
        rating = "Poor Fit"
        
    return {"final_score": final_score, "rating": rating}

def agent_6_report(state: AgentState):
    prompt = f"""
    You are a Summary Report Agent. Generate a human-readable markdown report summarizing the fit of the proposal against the admin criteria.
    
    Data:
    Classification: {state.get('classification')}
    Criteria Evaluations: {state.get('criteria_scores')}
    Final Score: {state.get('final_score')} / Rating: {state.get('rating')}
    
    Sections:
    1. Executive Summary
    2. Classification
    3. Criteria Evaluation Results
    """
    res = call_llm(prompt, json_format=False)
    return {"final_report": res}

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("structuring", agent_1_structuring)
    workflow.add_node("classification", agent_2_classification)
    workflow.add_node("criteria", agent_3_criteria)
    workflow.add_node("scoring", agent_5_scoring)
    workflow.add_node("report", agent_6_report)
    
    workflow.set_entry_point("structuring")
    workflow.add_edge("structuring", "classification")
    workflow.add_edge("classification", "criteria")
    workflow.add_edge("criteria", "scoring")
    workflow.add_edge("scoring", "report")
    workflow.add_edge("report", END)
    
    return workflow.compile()

evaluator_app = build_graph()
