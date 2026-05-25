// Centralised axios client for talking to the FastAPI backend.
import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ===== Phase 1 — feedback CRUD + search =====
export const feedbackApi = {
  list: (params = {}) => api.get('/feedback', { params }).then((r) => r.data),
  get: (id) => api.get(`/feedback/${id}`).then((r) => r.data),
  create: (payload) => api.post('/feedback', payload).then((r) => r.data),
  update: (id, payload) => api.put(`/feedback/${id}`, payload).then((r) => r.data),
  remove: (id) => api.delete(`/feedback/${id}`).then((r) => r.data),
  search: (params) => api.get('/search', { params }).then((r) => r.data),
  stats: () => api.get('/feedback/stats').then((r) => r.data),
};

// ===== Phase 2 — ETL =====
export const etlApi = {
  /** Upload a CSV/Excel file and trigger the ETL pipeline. */
  run: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api
      .post('/etl/run', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data);
  },
  runs: (limit = 50) => api.get('/etl/runs', { params: { limit } }).then((r) => r.data),
};

// ===== Phase 2 — analytics =====
export const analyticsApi = {
  overview: () => api.get('/analytics/overview').then((r) => r.data),
  programs: () => api.get('/analytics/programs').then((r) => r.data),
  ratings: () => api.get('/analytics/ratings').then((r) => r.data),
  refresh: () => api.post('/analytics/refresh').then((r) => r.data),
  /** Absolute URLs the browser can use for downloads. */
  downloads: {
    cleanedCsv: `${API_BASE_URL}/analytics/download/cleaned.csv`,
    programsCsv: `${API_BASE_URL}/analytics/download/programs.csv`,
  },
};

export default api;
