import React, { useState, useEffect, useRef } from 'react';
import { Upload, Save, CheckCircle, AlertCircle } from 'lucide-react';
import { getCriteria, saveCriteria, uploadPastOpportunities } from '../services/api';
import './AdminPage.css';

const AdminPage = () => {
  const [criteriaText, setCriteriaText] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchCriteria();
  }, []);

  const fetchCriteria = async () => {
    try {
      const data = await getCriteria();
      setCriteriaText(data.criteria_text || '');
    } catch (error) {
      console.error('Failed to fetch criteria', error);
    }
  };

  const handleSaveText = async () => {
    setLoading(true);
    setMessage(null);
    try {
      await saveCriteria(criteriaText);
      setMessage({ type: 'success', text: 'Criteria text saved successfully! Old criteria deleted.' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save criteria text.' });
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
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    const validFiles = Array.from(files).filter(file => 
      file.type === 'application/pdf' || 
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel'
    );

    if (validFiles.length === 0) {
      setMessage({ type: 'error', text: 'Please upload PDF or Excel files only.' });
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      await uploadPastOpportunities(validFiles);
      setMessage({ type: 'success', text: 'Past opportunities uploaded to Knowledge Base successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to upload past opportunities.' });
    }
    setLoading(false);
  };

  return (
    <div className="page-container fade-in">
      <div className="page-header">
        <h1>Admin Setup</h1>
        <p className="page-subtitle">Configure Evaluation Criteria & Upload Past Opportunities.</p>
      </div>

      {message && (
        <div className={`alert alert-${message.type} fade-in`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {/* Criteria Edit Box */}
        <div className="glass-panel flex flex-col">
          <div className="flex justify-between align-center mb-2">
            <h3>Criteria Details</h3>
            <button 
              className="btn btn-primary" 
              onClick={handleSaveText}
              disabled={loading}
            >
              <Save size={18} />
              {loading ? 'Saving...' : 'Save Text'}
            </button>
          </div>
          <p className="text-light mb-4 text-sm">Enter the rules for the AI evaluator. Saving will overwrite existing criteria.</p>
          <textarea 
            className="criteria-textarea"
            value={criteriaText}
            onChange={(e) => setCriteriaText(e.target.value)}
            placeholder="Enter evaluation criteria here..."
          ></textarea>
        </div>

        {/* Previous Opportunities Upload */}
        <div className="glass-panel">
          <h3>Upload Previous Opportunities</h3>
          <p className="text-light mb-4 text-sm">Upload past proposals (PDF/Excel) to detect duplicates.</p>
          
          <div 
            className={`file-drop-area ${dragActive ? 'dragover' : ''}`}
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
            <Upload size={48} className="upload-icon mb-2" />
            <h4>Drag & Drop files here</h4>
            <p>or click to browse</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
