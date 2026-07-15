from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    proposal_text: str
    timeline_text: str
    financials: str
    financials_file_base64: str
    market: str
    risks: str
    roi_model: str
    
    financial_extracted_data: str
    structured_data: Dict[str, Any]
    classification: Dict[str, Any]
    criteria_scores: Dict[str, Any]
    roi_calculations: Dict[str, Any]
    final_score: float
    rating: str
    final_report: str

def get_llm():
    if "AZURE_OPENAI_API_KEY" in os.environ:
        try:
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
                openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
                temperature=0.2
            )
        except ImportError:
            pass
    return None

def mock_llm_call(prompt: str, json_format=True) -> Any:
    # Fallback mock for POC
    if "structuring" in prompt.lower():
        return {"summary": "A mock proposal", "missing_info": []}
    if "classification" in prompt.lower():
        return {"division": "Technology", "subdivision": "AI SaaS"}
    if "criteria" in prompt.lower():
        return {"market": 8, "feasibility": 6, "financial": 7, "strategic_fit": 9, "risk": 4}
    if "roi" in prompt.lower():
        return {"roi": "34%", "payback_period_months": 18, "irr": "6%", "breakeven_revenue": 450000}
    if "report" in prompt.lower():
        return "# Executive Summary\n\nThis is a mock report generated because no LLM key was provided."
    return {}

def call_llm(prompt: str, json_format=True) -> Any:
    llm = get_llm()
    print(f"llm: {llm}")
    print(f"prompt: {prompt}")
    
    if not llm:
        return mock_llm_call(prompt, json_format)
        
    try:
        from langchain.schema import HumanMessage
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

def agent_1_structuring(state: AgentState):
    prompt = f"""
    You are a Proposal Structuring Agent. Normalize the following input into a structured summary and identify any missing info.
    Proposal: {state.get('proposal_text', '')}
    Timeline: {state.get('timeline_text', '')}
    Respond ONLY in JSON with keys "summary" and "missing_info" (list of strings).
    """
    res = call_llm(prompt, json_format=True)
    return {"structured_data": res}

def agent_2_classification(state: AgentState):
    summary = state.get('structured_data', {}).get('summary', state.get('proposal_text', ''))
    prompt = f"""
    You are an Opportunity Classification Agent. Classify the proposal into a division (Technology, Retail, Manufacturing, Services, Logistics, Healthcare, Energy, Finance) and a subdivision.
    Proposal Summary: {summary}
    Respond ONLY in JSON with keys "division" and "subdivision".
    """
    res = call_llm(prompt, json_format=True)
    return {"classification": res}

def agent_3_criteria(state: AgentState):
    prompt = f"""
    You are a Criteria Evaluation Agent. Evaluate the proposal across 5 criteria (0-10 scale):
    market, feasibility, financial, strategic_fit, risk.
    Proposal: {state.get('proposal_text', '')}
    Financials: {state.get('financials', '')}
    Market: {state.get('market', '')}
    Risks: {state.get('risks', '')}
    Respond ONLY in JSON with these 5 keys inside a root object.
    """
    res = call_llm(prompt, json_format=True)
    return {"criteria_scores": res}

def extract_with_pandasai(base64_data: str) -> str:
    if not base64_data:
        return ""
        
    if "AZURE_OPENAI_API_KEY" not in os.environ:
        print("No AZURE_OPENAI_API_KEY found, using mock PandasAI data")
        return "MOCK EXCEL EXTRACT: Total Proposal Value=$5,000,000, IRR=20%, Payback Period=18 months"
        
    try:
        import base64
        import io
        import pandas as pd
        from pandasai import SmartDataframe
        from pandasai.llm.azure_openai import AzureOpenAI
        
        excel_data = base64.b64decode(base64_data)
        df = pd.read_excel(io.BytesIO(excel_data))
        
        print(f"Loaded Excel with {len(df)} rows. Analyzing with PandasAI...")
        llm = AzureOpenAI(
            api_token=os.environ["AZURE_OPENAI_API_KEY"],
            api_base=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
        sdf = SmartDataframe(df, config={"llm": llm})
        
        query = "Extract Total Proposal Value, IRR, and payback period from this data. Respond with a clear text summary."
        response = sdf.chat(query)
        return str(response)
            
    except Exception as e:
        print(f"Failed to process with PandasAI: {e}")
        return "MOCK EXCEL EXTRACT: Total Proposal Value=$5,000,000, IRR=20%, Payback Period=18 months"

def agent_excel_parser(state: AgentState):
    base64_data = state.get('financials_file_base64', '')
    if base64_data:
        print("Parsing uploaded Excel financials with PandasAI...")
        extracted = extract_with_pandasai(base64_data)
        return {"financial_extracted_data": extracted}
    return {"financial_extracted_data": ""}

def agent_4_roi(state: AgentState):
    extracted_fin = state.get('financial_extracted_data', '')
    fin_text = state.get('financials', '')
    combined_financials = f"Raw Text: {fin_text}\nExtracted from Excel: {extracted_fin}"
    
    prompt = f"""
    You are an ROI & Return Calculation Agent.
    Calculate ROI, payback period, IRR, and breakeven revenue based on:
    Financials: {combined_financials}
    ROI Model: {state.get('roi_model', '')}
    Respond ONLY in JSON with keys "roi", "payback_period_months", "irr", "breakeven_revenue".
    """
    res = call_llm(prompt, json_format=True)
    return {"roi_calculations": res}

def agent_5_scoring(state: AgentState):
    scores = state.get("criteria_scores", {})
    m = float(scores.get("market", 5))
    f = float(scores.get("feasibility", 5))
    fin = float(scores.get("financial", 5))
    s = float(scores.get("strategic_fit", 5))
    r = float(scores.get("risk", 5))
    
    final_score = (0.25 * m) + (0.20 * f) + (0.25 * fin) + (0.15 * s) - (0.15 * r)
    
    if final_score >= 8.0:
        rating = "Exceptional"
    elif final_score >= 6.5:
        rating = "High Potential"
    elif final_score >= 5.0:
        rating = "Moderate"
    else:
        rating = "Low Potential"
        
    return {"final_score": final_score, "rating": rating}

def agent_6_report(state: AgentState):
    prompt = f"""
    You are a Summary Report Agent. Generate a human-readable markdown report.
    Use the following data:
    Classification: {state.get('classification')}
    Criteria: {state.get('criteria_scores')}
    ROI: {state.get('roi_calculations')}
    Final Score: {state.get('final_score')} / Rating: {state.get('rating')}
    
    Sections:
    1. Executive Summary
    2. Opportunity Classification
    3. Criteria Evaluation Table
    4. Financial & ROI Analysis
    """
    res = call_llm(prompt, json_format=False)
    return {"final_report": res}

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("structuring", agent_1_structuring)
    workflow.add_node("classification", agent_2_classification)
    workflow.add_node("criteria", agent_3_criteria)
    workflow.add_node("excel_parser", agent_excel_parser)
    workflow.add_node("roi", agent_4_roi)
    workflow.add_node("scoring", agent_5_scoring)
    workflow.add_node("report", agent_6_report)
    
    workflow.set_entry_point("structuring")
    workflow.add_edge("structuring", "classification")
    workflow.add_edge("classification", "criteria")
    workflow.add_edge("criteria", "excel_parser")
    workflow.add_edge("excel_parser", "roi")
    workflow.add_edge("roi", "scoring")
    workflow.add_edge("scoring", "report")
    workflow.add_edge("report", END)
    
    return workflow.compile()

evaluator_app = build_graph()
