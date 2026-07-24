import React, { useState } from 'react';
import { Download, FileText, CheckCircle, XCircle, AlertTriangle, Send, Loader2 } from 'lucide-react';
import { Document, Packer, Paragraph, HeadingLevel } from 'docx';
import { queryProposal } from '../services/api';
import './ResultsView.css';

const ResultsView = ({ reportData, proposalId }) => {
  const [activeTab, setActiveTab] = useState('criteria');
  const [queryText, setQueryText] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);

  const handleQuery = async () => {
    if (!queryText.trim() || !proposalId) return;
    setQueryLoading(true);
    try {
      const response = await queryProposal(proposalId, queryText);
      if (response.status === 'success') {
        setQueryResult(response.data);
      }
    } catch (error) {
      console.error(error);
      alert('Failed to execute query.');
    }
    setQueryLoading(false);
  };

  if (!reportData) return null;

  const score = reportData.final_score || 0;
  const rating = reportData.rating || 'N/A';
  const finalReport = reportData.final_report || 'No report generated.';
  const classification = reportData.classification || {};
  const criteriaScores = reportData.criteria_scores || {};
  
  let criteriaEvaluations = [];
  if (criteriaScores.criteria_evaluations) {
    criteriaEvaluations = criteriaScores.criteria_evaluations;
  }

  const handleDownloadDocx = async () => {
    const summaryText = reportData.structured_data?.summary || 'No executive summary available.';
    
    try {
      const doc = new Document({
        sections: [{
          properties: {},
          children: [
            new Paragraph({
              text: "Executive Summary",
              heading: HeadingLevel.HEADING_1,
            }),
            new Paragraph({
              text: summaryText,
            }),
          ],
        }],
      });

      const blob = await Packer.toBlob(doc);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'summary_report.docx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to create DOCX', error);
      alert('Failed to generate DOCX file.');
    }
  };

  return (
    <div className="glass-panel results-view">
      <div className="results-header">
        <div className="score-card">
          <h4>Opportunity Score</h4>
          <div className="score-value">
            <span className="score-number">{Number(score).toFixed(2)}</span>
            <span className="score-max">/ 10</span>
          </div>
          <div className="score-rating">{rating}</div>
        </div>
        <div className="results-actions">
          <button className="btn btn-secondary" onClick={handleDownloadDocx}>
            <Download size={18} />
            Download Summary
          </button>
        </div>
      </div>

      <div className="custom-tabs">
        <div className="tab-list">
          <button 
            className={`tab-btn ${activeTab === 'criteria' ? 'active' : ''}`}
            onClick={() => setActiveTab('criteria')}
          >
            Criteria Evaluation
          </button>
          <button 
            className={`tab-btn ${activeTab === 'division' ? 'active' : ''}`}
            onClick={() => setActiveTab('division')}
          >
            Division
          </button>
          <button 
            className={`tab-btn ${activeTab === 'executive' ? 'active' : ''}`}
            onClick={() => setActiveTab('executive')}
          >
            Executive Report
          </button>
          <button 
            className={`tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
            onClick={() => setActiveTab('raw')}
          >
            Raw Data
          </button>
        </div>

        <div className="tab-content" style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {activeTab === 'criteria' && (
            <div className="criteria-tab fade-in">
              <h3>Criteria Evaluation Results</h3>
              {criteriaEvaluations.length > 0 ? (
                <div className="table-responsive">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Criteria</th>
                        <th>Result</th>
                        <th>Assessment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {criteriaEvaluations.map((evalItem, idx) => (
                        <tr key={idx}>
                          <td>{evalItem.criteria}</td>
                          <td className="status-cell">
                            {evalItem.status?.toLowerCase() === 'pass' || evalItem.status?.toLowerCase() === 'yes' ? (
                              <span className="status-badge success"><CheckCircle size={14}/> {evalItem.status}</span>
                            ) : evalItem.status?.toLowerCase() === 'fail' || evalItem.status?.toLowerCase() === 'no' ? (
                              <span className="status-badge error"><XCircle size={14}/> {evalItem.status}</span>
                            ) : (
                              <span className="status-badge warning"><AlertTriangle size={14}/> {evalItem.status}</span>
                            )}
                          </td>
                          <td>{evalItem.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p>No criteria evaluation data available.</p>
              )}
            </div>
          )}

          {activeTab === 'division' && (
            <div className="division-tab fade-in">
              <h3>Division Classification</h3>
              <div className="json-viewer">
                <pre>{JSON.stringify(classification, null, 2)}</pre>
              </div>
            </div>
          )}

          {activeTab === 'executive' && (
            <div className="executive-tab fade-in">
              <h3>Summary Report</h3>
              <div className="markdown-content">
                {finalReport.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="raw-tab fade-in">
              <h3>Raw Agent Outputs</h3>
              <div className="json-viewer">
                <pre>{JSON.stringify(reportData, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Persistent Ask & Evaluate Panel */}
      <div className="persistent-query-panel mt-4 glass-panel fade-in" style={{ marginTop: '20px', padding: '20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <h3 style={{ marginBottom: '15px' }}>Ask Questions or Evaluate Custom Criteria</h3>
        <div className="query-input-container" style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
          <input
            type="text"
            style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)', backgroundColor: 'rgba(255,255,255,0.05)', color: 'white' }}
            placeholder="Ask a question about the proposal or enter a new criteria..."
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          />
          <button 
            className="btn btn-primary" 
            onClick={handleQuery}
            disabled={queryLoading || !proposalId}
          >
            {queryLoading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
            Send
          </button>
        </div>
        
        {queryResult && (
          <div className="query-result-card fade-in" style={{ padding: '15px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
            <h4 style={{ marginBottom: '10px' }}>
              Type: <span style={{ textTransform: 'capitalize', color: 'var(--primary-light)' }}>{queryResult.type.replace('_', ' ')}</span>
            </h4>
            <p style={{ marginBottom: '15px' }}><strong>Enhanced Query:</strong> {queryResult.enhanced_query}</p>
            
            <div className="result-content" style={{ padding: '15px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
              {queryResult.type === 'document_query' ? (
                <p>{queryResult.result.answer}</p>
              ) : (
                <div>
                  <p><strong>Criteria:</strong> {queryResult.result.criteria}</p>
                  <p><strong>Status:</strong> {queryResult.result.status}</p>
                  <p><strong>Reason:</strong> {queryResult.result.reason}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultsView;
