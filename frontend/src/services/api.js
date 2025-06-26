import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('company');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData) => api.post('/api/auth/register', userData),
  getMe: () => api.get('/api/auth/me'),
};

export const companiesAPI = {
  list: () => api.get('/api/companies'),
  create: (companyData) => api.post('/api/companies', companyData),
  get: (id) => api.get(`/api/companies/${id}`),
};

export const documentsAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: () => api.get('/api/documents'),
  get: (id) => api.get(`/api/documents/${id}`),
  delete: (id) => api.delete(`/api/documents/${id}`),
};

export const chatAPI = {
  sendMessage: (question) => api.post('/api/chat', { question }),
  getHistory: () => api.get('/api/chat/history'),
};

export default api;