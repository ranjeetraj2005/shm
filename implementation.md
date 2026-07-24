# Goal Description

Enhance the Agentic Business Proposal Evaluator POC by moving file processing to the backend, integrating Qdrant vector database for document storage and retrieval, and improving the frontend user experience for multiple file uploads.

## Key Architectural Updates

> [!IMPORTANT]
> - **File Parsing on Backend**: PDF and Excel extraction have been moved from the Streamlit frontend to the FastAPI backend. Files are now uploaded via `multipart/form-data`.
> - **Qdrant Vector Database Integration**: 
>   - **Business Proposals**: Proposals uploaded by the user are sent to the `upload_knowledge` endpoint and stored in a shared Qdrant collection (e.g., `business_proposals`).
>   - **Evaluation Criteria**: Criteria uploaded by the admin are parsed and stored in a separate, dedicated Qdrant collection (e.g., `evaluation_criteria`).
> - **Two-Step Submission & Tabbed Results**: The frontend now utilizes a decoupled upload/evaluate flow. Results are rendered natively inside a 5-tab UI containing downloadable DOCX and PDF reports generated on the fly.

## Current State & Endpoints

### Frontend (`frontend/app.py`)
- **Navigation**: "Admin - Criteria Setup" and "Submit New Proposal" available in the sidebar.
- **Admin View**: 
  - Allows uploading criteria files (TXT/PDF) which are sent to a new `/upload_criteria` endpoint to be embedded into the `evaluation_criteria` Qdrant collection.
- **Submit View**: 
  - Unified multiple file upload component (`accept_multiple_files=True`) for Business Proposals.
  - A manual "Upload to Knowledge Base" button is provided to initiate the upload. Upload progress is displayed to the user.
  - Files are securely pushed to the `business_proposals` collection via `/upload_knowledge`.
  - The "Evaluate Proposal" button remains disabled until a successful upload. Once clicked, it fetches the report from `/evaluate`. The upload section and evaluate button remain visible and scrollable along with the results.
- **Results View (5 Tabs)**:
  - **Tab 1 - Criteria Evaluation**: Data table visualizing match/fail status (`Criteria`, `Result`, `Assessment`, `Implication`).
  - **Tab 2 - Classification**: Division classification JSON output.
  - **Tab 3 - Evaluation Report**: Full markdown report.
  - **Tab 4 - Executive Summary**: Downloadable DOCX summary using `python-docx`.
  - **Tab 5 - Detailed Summary**: Downloadable PDF report using `fpdf2`.
  - **Persistent Query Panel**: A fixed "Ask & Evaluate" panel at the bottom of the results view allows users to ask ad-hoc questions or evaluate new custom criteria at any time, independently of the active tab.

### Backend (`backend/main.py`)
- **Endpoints**: 
  - `POST /upload_criteria` & `GET /criteria`: Replaces the old text-file approach. Uploaded criteria files are parsed, chunked, and stored in the `evaluation_criteria` Qdrant collection.
  - `POST /upload_knowledge`: Receives raw business proposal files, extracts text (via PyPDF2/pandas), chunks it, embeds it via Azure OpenAI Embeddings, and stores it in the `business_proposals` Qdrant collection.
  - `POST /evaluate`: Accepts `proposal_id`. Queries both the `business_proposals` collection (for the specific proposal's chunks) and the `evaluation_criteria` collection to retrieve the necessary context, reassembles it, and invokes the LangGraph pipeline.

### Backend Agents (`backend/agent_pipeline.py`)
- **Agent 1 (Structuring)**: Analyzes the context and identifies missing info.
- **Agent 2 (Classification)**: Identifies division based on the structured summary.
- **Agent 3 (Criteria)**: Reads `proposal_text` (from the knowledge Qdrant collection) and `criteria_text` (from the criteria Qdrant collection). Outputs match/fail for each criteria.
- **Agent 4 (Scoring)**: Calculates a score based on the match/fail ratio from Agent 3.
- **Agent 5 (Report)**: Generates final report summarizing the criteria matches, division, and final score.

### Requirements
- Added `qdrant-client`, `langchain-openai`, `pypdf2`, `pandas`, `openpyxl`, `python-multipart`, `python-docx`, and `fpdf2` to `backend/requirements.txt`.

## Verification Plan
1. Start FastAPI and Streamlit.
2. Ensure Qdrant can run locally and Azure OpenAI credentials are set in the `.env` file.
3. Go to the Admin page and upload criteria files to populate the criteria collection.
4. Go to New Submission, upload sample PDF and Excel business proposals.
5. Verify the files are successfully parsed and stored in the respective Qdrant collections, and the resulting evaluation retrieves context from both collections to generate the report.
