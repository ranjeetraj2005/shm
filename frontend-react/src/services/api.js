import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const saveCriteria = async (text) => {
  const response = await axios.post(`${API_URL}/criteria`, { criteria_text: text });
  return response.data;
};

export const getCriteria = async () => {
  const response = await axios.get(`${API_URL}/criteria`);
  return response.data;
};

export const uploadPastOpportunities = async (files) => {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  const response = await axios.post(`${API_URL}/upload_past_opportunities`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const uploadKnowledgeFiles = async (files) => {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  const response = await axios.post(`${API_URL}/upload_knowledge`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const evaluateProposal = async (proposalId) => {
  const response = await axios.post(`${API_URL}/evaluate`, { proposal_id: proposalId });
  return response.data;
};

export const getHistory = async () => {
  const response = await axios.get(`${API_URL}/history`);
  return response.data;
};

export const getReport = async (recordId) => {
  const response = await axios.get(`${API_URL}/report/${recordId}`);
  return response.data;
};

export const queryProposal = async (proposalId, query) => {
  const response = await axios.post(`${API_URL}/query`, { proposal_id: proposalId, query });
  return response.data;
};
