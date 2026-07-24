import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Upload, FilePlus, Play, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadKnowledgeFiles, evaluateProposal, getReport } from '../services/api';
import ResultsView from '../components/ResultsView';
import './SubmitPage.css';

const SubmitPage = () => {
  const { id } = useParams(); // If we are viewing a historical report
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  
  const [proposalId, setProposalId] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (id) {
      fetchReport(id);
    } else {
      // Reset state for new submission
      setProposalId(null);
      setUploadSuccess(false);
      setReportData(null);
      setMessage(null);
    }
  }, [id]);

  const fetchReport = async (recordId) => {
    setLoading(true);
    try {
      const data = await getReport(recordId);
      setReportData(data.evaluation_result);
      if (data.proposal_data && data.proposal_data.proposal_id) {
        setProposalId(data.proposal_data.proposal_id);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load report' });
    }
    setLoading(false);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    const validFiles = selectedFiles.filter(file => 
      file.type === 'application/pdf' || 
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel'
    );

    if (validFiles.length === 0) {
      setMessage({ type: 'error', text: 'Please upload PDF or Excel files only.' });
      return;
    }

    setUploading(true);
    setMessage({ type: 'info', text: 'Uploading files in progress...' });
    setUploadSuccess(false);
    try {
      const response = await uploadKnowledgeFiles(validFiles);
      if (response.status === 'success') {
        setProposalId(response.proposal_id);
        setUploadSuccess(true);
        setMessage({ type: 'success', text: 'Files uploaded successfully! You can now Evaluate the Proposal.' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to upload proposal files.' });
    }
    setUploading(false);
  };

  const handleEvaluate = async () => {
    if (!proposalId) return;
    setLoading(true);
    setMessage(null);
    try {
      const response = await evaluateProposal(proposalId);
      if (response.status === 'success') {
        setReportData(response.result);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error during evaluation.' });
    }
    setLoading(false);
  };

  return (
    <div className="page-container fade-in">
      <div className="page-header">
        <h1>{id ? 'Historical Report' : 'Submit New Proposal'}</h1>
        {!id && <p className="page-subtitle">Upload your business proposals for AI evaluation.</p>}
      </div>

      {message && (
        <div className={`alert alert-${message.type} fade-in`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      {!id && (
        <div className="glass-panel upload-section mb-4">
          <div className="flex justify-between align-center mb-4">
            <h3>Step 1: Upload Documents</h3>
            <span className="step-badge">Required</span>
          </div>
          
          <div 
            className={`file-drop-area large-drop-area ${dragActive ? 'dragover' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              ref={fileInputRef}
              type="file" 
              multiple 
              accept=".pdf,.xlsx,.xls" 
              onChange={handleChange} 
              style={{ display: 'none' }} 
            />
            <FilePlus size={56} className="upload-icon mb-2" />
            <h2>Drag & Drop PDF or Excel files</h2>
            <p>or click to select files from your computer</p>
            {selectedFiles.length > 0 && (
              <div className="selected-files mt-2">
                <p><strong>{selectedFiles.length} file(s) selected</strong></p>
                <button 
                  className="btn btn-primary mt-2"
                  onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                  disabled={uploading}
                >
                  <Upload size={18} className="mr-2" />
                  {uploading ? 'Uploading...' : 'Upload to Knowledge Base'}
                </button>
              </div>
            )}
          </div>

          <div className="evaluation-action mt-4">
            <h3>Step 2: Evaluate</h3>
            <p className="text-light mb-2">Once documents are uploaded to the Knowledge Base, proceed to evaluation.</p>
            <button 
              className="btn btn-primary btn-large" 
              disabled={!uploadSuccess || loading}
              onClick={handleEvaluate}
            >
              <Play size={20} />
              {loading && uploadSuccess ? 'Evaluating...' : 'Evaluate Proposal'}
            </button>
          </div>
        </div>
      )}

      {(reportData || loading && id) && (
        <div className="results-container mt-4 fade-in">
          {loading ? (
            <div className="loading-state">Loading report data...</div>
          ) : (
            <ResultsView reportData={reportData} proposalId={proposalId} />
          )}
        </div>
      )}
    </div>
  );
};

export default SubmitPage;
