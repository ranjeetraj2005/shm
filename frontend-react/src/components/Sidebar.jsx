import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { PlusCircle, Settings, History, FileText, ChevronRight } from 'lucide-react';
import { getHistory } from '../services/api';
import './Sidebar.css';

const Sidebar = () => {
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await getHistory();
      setHistory(data || []);
    } catch (error) {
      console.error('Failed to fetch history', error);
    }
    setLoadingHistory(false);
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="logo-icon">🤖</div>
        <h2>Agentic Evaluator</h2>
      </div>

      <div className="sidebar-section">
        <h3>Navigation</h3>
        <nav className="nav-menu">
          <NavLink to="/" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            <PlusCircle size={20} />
            <span>New Submission</span>
          </NavLink>
          <NavLink to="/admin" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            <Settings size={20} />
            <span>Admin - Criteria Setup</span>
          </NavLink>
        </nav>
      </div>

      <div className="sidebar-divider"></div>

      <div className="sidebar-section">
        <div className="history-header">
          <h3>Submission History</h3>
          <button onClick={fetchHistory} className="refresh-btn" title="Refresh History">
            <History size={16} />
          </button>
        </div>
        
        <div className="history-list">
          {loadingHistory ? (
            <div className="history-loading">Loading...</div>
          ) : history.length === 0 ? (
            <div className="history-empty">No history yet.</div>
          ) : (
            history.map((item) => {
              let title = `Report ${item.id.substring(0, 8)}`;
              try {
                if (item.payload?.evaluation_result?.structured_data?.summary) {
                  title = item.payload.evaluation_result.structured_data.summary.substring(0, 30) + '...';
                }
              } catch (e) {}

              return (
                <NavLink 
                  key={item.id} 
                  to={`/report/${item.id}`} 
                  className={({ isActive }) => (isActive ? 'history-item active' : 'history-item')}
                >
                  <FileText size={16} className="history-icon" />
                  <span className="history-title" title={title}>{title}</span>
                  <ChevronRight size={14} className="history-chevron" />
                </NavLink>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
