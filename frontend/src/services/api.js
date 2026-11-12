import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_BACKEND_URL || '',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
// Token is sent via httpOnly cookie automatically (withCredentials: true)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Dispatch a custom event so components can react to auth loss
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default api;

// API functions
export const authApi = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  session: (sessionId) => api.post('/api/auth/session', { session_id: sessionId }),
  me: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
};

export const uploadApi = {
  upload: (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });
  },
  getFile: (documentId) => api.get(`/api/upload/${documentId}/file`, { responseType: 'blob' }),
};

export const analyzeApi = {
  analyze: (documentId, forceReanalyze = false) =>
    api.post('/api/analyze', { document_id: documentId, force_reanalyze: forceReanalyze }),
  getAnalysis: (documentId) => api.get(`/api/analyze/${documentId}`),
  listDocuments: () => api.get('/api/analyze/documents/list'),
  deleteDocument: (documentId) => api.delete(`/api/analyze/${documentId}`),
};

export const chatApi = {
  send: (documentId, message, history = []) =>
    api.post('/api/chat', { document_id: documentId, message, history }),
  search: (documentId, query) =>
    api.post('/api/chat/search', null, { params: { document_id: documentId, query } }),
};

export const mlApi = {
  train: () => api.post('/api/ml/train'),
  getMetrics: () => api.get('/api/ml/metrics'),
  classifyClause: (text) => api.post('/api/ml/classify/clause', { text }),
  riskScore: (text) => api.post('/api/ml/risk-score', { text }),
  classifyDocType: (text) => api.post('/api/ml/classify/document-type', { text }),
};
