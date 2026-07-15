import streamlit as st
import requests
import PyPDF2
from io import BytesIO

st.set_page_config(layout="wide", page_title="Agentic Proposal Evaluator")

API_URL = "http://localhost:8000"

def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(BytesIO(file.read()))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {e}"

st.title("Business Opportunity 360")

with st.sidebar:
    st.header("Navigation")
    if st.button("➕ New Submission"):
        st.session_state["view"] = "new"
        st.session_state["show_report_below"] = False
        
    st.markdown("---")
    st.header("Submission History")
    
    try:
        res = requests.get(f"{API_URL}/history")
        if res.status_code == 200:
            history = res.json()
            if not history:
                st.write("No history yet.")
            for item in history:
                # Safely extract title
                try:
                    title = item.get("payload", {}).get("evaluation_result", {}).get("structured_data", {}).get("summary", "Proposal")[:30] + "..."
                except:
                    title = f"Report {item['id'][:8]}"
                    
                if st.button(f"📄 {title}", key=item["id"]):
                    st.session_state["view"] = "report"
                    st.session_state["current_report"] = item["payload"]["evaluation_result"]
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")

def render_report(report_data):
    tab1, tab2, tab3 = st.tabs(["Evaluation Report", "Division Report", "Summary Report"])
    
    with tab1:
        st.header("Evaluation Results")
        score = report_data.get("final_score", 0)
        rating = report_data.get("rating", "N/A")
        st.metric(label="Opportunity Score", value=f"{score:.2f} / 10", delta=rating)
        st.markdown("---")
        st.markdown(report_data.get("final_report", "No report generated."))
        
    with tab2:
        st.subheader("Classification")
        classification = report_data.get("classification", {})
        if classification:
            for k, v in classification.items():
                st.write(f"**{k.title()}**: {v}")
        else:
            st.write("No classification data available.")
            
    with tab3:
        st.subheader("Structured Summary")
        structured = report_data.get("structured_data", {})
        if structured:
            st.write(f"**Summary:** {structured.get('summary', 'N/A')}")
            missing = structured.get('missing_info', [])
            if missing:
                st.write("**Missing Info:**")
                for m in missing:
                    st.write(f"- {m}")
        else:
            st.write("No summary data available.")
            
    with st.expander("View Raw Agent Outputs"):
        st.json(report_data)

if "view" not in st.session_state:
    st.session_state["view"] = "new"
    st.session_state["show_report_below"] = False

if st.session_state["view"] == "new":
    st.header("Submit New Proposal")
    st.markdown("Fill out the details below. You can upload PDFs or paste text.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        proposal_file = st.file_uploader("Upload Proposal (PDF)", type=["pdf"])
        proposal_text = st.text_area("Or paste Proposal Description", height=150)
        
        timeline_file = st.file_uploader("Upload Timeline & Milestones (PDF)", type=["pdf"])
        timeline_text = st.text_area("Or paste Timeline", height=100)
        
    with col2:
        financials_file = st.file_uploader("Upload Financials (Excel)", type=["xlsx", "xls"])
        financials = st.text_area("Or paste Financial Projections", height=100)
        market = st.text_area("Market Details", height=100)
        risks = st.text_area("Risks & Constraints", height=100)
        roi_model = st.text_area("Expected ROI or Revenue Model", height=100)

    if st.button("Evaluate Proposal", type="primary"):
        with st.spinner("Agentic pipeline is processing..."):
            p_text = extract_text_from_pdf(proposal_file) if proposal_file else proposal_text
            t_text = extract_text_from_pdf(timeline_file) if timeline_file else timeline_text
            
            import base64
            financials_base64 = base64.b64encode(financials_file.read()).decode("utf-8") if financials_file else ""
            
            payload = {
                "proposal_text": p_text,
                "timeline_text": t_text,
                "financials": financials,
                "financials_file_base64": financials_base64,
                "market": market,
                "risks": risks,
                "roi_model": roi_model
            }
            
            import json
            try:
                status_placeholder = st.status("Initializing Agentic Evaluation...", expanded=True)
                
                resp = requests.post(f"{API_URL}/evaluate_stream", json=payload, stream=True)
                
                if resp.status_code == 200:
                    for line in resp.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                data_str = decoded_line[6:]
                                try:
                                    event_data = json.loads(data_str)
                                    if "node" in event_data:
                                        node_name = event_data["node"]
                                        status_placeholder.write(f"✅ Agent `{node_name}` completed its task.")
                                    elif "status" in event_data and event_data["status"] == "success":
                                        status_placeholder.update(label="Evaluation Complete!", state="complete", expanded=False)
                                        st.session_state["current_report"] = event_data["result"]
                                        st.session_state["show_report_below"] = True
                                    elif "error" in event_data:
                                        status_placeholder.update(label="Evaluation Failed!", state="error")
                                        st.error(event_data["error"])
                                except Exception:
                                    pass
                else:
                    status_placeholder.update(label="Request Failed", state="error")
                    st.error(f"Error from backend: {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

    if st.session_state.get("show_report_below") and "current_report" in st.session_state:
        st.markdown("---")
        render_report(st.session_state["current_report"])

elif st.session_state["view"] == "report":
    report_data = st.session_state.get("current_report", {})
    render_report(report_data)
