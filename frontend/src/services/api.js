import axios from 'axios';

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests (except for public endpoints)
api.interceptors.request.use((config) => {
  // Skip authorization for public endpoints
  if (!config.url.includes('/public') && !config.url.includes('/system-admin/login')) {
    const token = localStorage.getItem('access_token');
    console.log('🔍 API Request:', config.url);
    console.log('🔑 Token from localStorage:', token ? token.substring(0, 50) + '...' : 'None');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Authorization header set');
    } else {
      console.log('❌ No token found, request will fail');
    }
  } else {
    console.log('🌐 Public API Request:', config.url);
    console.log('🔗 Full URL:', config.baseURL + config.url);
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.config.url, response.status);
    console.log('📦 Response data:', response.data);
    return response;
  },
  (error) => {
    console.log('❌ API Error:', error.config?.url, error.response?.status, error.response?.data);
    console.log('🔍 Error details:', {
      message: error.message,
      code: error.code,
      config: error.config,
      response: error.response
    });
    
    if (error.response?.status === 401) {
      console.log('🔐 401 Unauthorized - clearing auth data');
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('company');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData, companyId = null) => {
    if (companyId) {
      return api.post(`/api/auth/register?company_id=${companyId}`, userData);
    }
    return api.post('/api/auth/register', userData);
  },
  systemAdminLogin: (credentials) => api.post('/api/auth/system-admin/login', credentials),
  getMe: () => api.get('/api/auth/me'),
};

const companiesAPI = {
  list: () => api.get('/api/companies'),
  listPublic: () => api.get('/api/companies/public'), // Public endpoint for main landing
  create: (companyData) => api.post('/api/companies', companyData),
  get: (id) => api.get(`/api/companies/${id}`),
  getPublic: (id) => api.get(`/api/companies/${id}/public`), // Public endpoint for company access
  getStats: (id) => api.get(`/api/companies/${id}/stats`),
  delete: (id) => api.delete(`/api/companies/${id}`),
  requestAccess: (id, requestData) => api.post(`/api/companies/${id}/request-access`, requestData),
};

const documentsAPI = {
  upload: (file, folderName = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (folderName) {
      formData.append('folder_name', folderName);
    }
    return api.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: (folderName = null) => {
    const params = folderName !== null ? { folder_name: folderName } : {};
    return api.get('/api/documents/', { params });
  },
  folders: () => api.get('/api/documents/folders'),
  get: (id) => api.get(`/api/documents/${id}`),
  delete: (id) => api.delete(`/api/documents/${id}`),
};

const usersAPI = {
  list: () => api.get('/api/users/'),
  get: (id) => api.get(`/api/users/${id}`),
  update: (id, userData) => api.put(`/api/users/${id}`, userData),
  delete: (id) => api.delete(`/api/users/${id}`),
  activate: (id) => api.post(`/api/users/${id}/activate`),
  getStats: () => api.get('/api/users/stats/company'),
};

const userManagementAPI = {
  inviteUser: (inviteData) => api.post('/api/user-management/invite', inviteData),
  setupPassword: (setupData) => api.post('/api/user-management/setup-password', setupData),
  listInvitations: () => api.get('/api/user-management/invitations'),
  listUsers: () => api.get('/api/user-management/users'),
  cancelInvitation: (id) => api.delete(`/api/user-management/invitations/${id}`),
  getPermissions: () => api.get('/api/user-management/permissions'),
  getInvitationDetails: (uniqueId) => api.get(`/api/user-management/invitation/${uniqueId}`),
};

const chatAPI = {
  sendMessage: (question) => api.post('/api/chat', { question }),
  getHistory: () => api.get('/api/chat/history'),
};

const systemChatAPI = {
  sendMessage: (question) => api.post('/api/chat/system', { question }),
  getHistory: () => api.get('/api/chat/system/history'),
};

// System Admin Document API
const systemDocumentsAPI = {
  list: async (folderName = null) => {
    const params = new URLSearchParams();
    if (folderName !== null) {
      params.append('folder_name', folderName);
    }
    
    const response = await fetch(`/api/documents/system/?${params}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch system documents');
    }
    
    return response.json();
  },

  upload: async (file, folderName = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (folderName) {
      formData.append('folder_name', folderName);
    }
    
    const response = await fetch('/api/documents/system/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload system document');
    }
    
    return response.json();
  },

  get: async (documentId) => {
    const response = await fetch(`/api/documents/system/${documentId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch system document');
    }
    
    return response.json();
  },

  delete: async (documentId) => {
    const response = await fetch(`/api/documents/system/${documentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete system document');
    }
    
    return response.json();
  },

  download: async (documentId) => {
    const response = await fetch(`/api/documents/system/${documentId}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get download URL');
    }
    
    return response.json();
  },

  getFolders: async () => {
    const response = await fetch('/api/documents/system/folders', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch system folders');
    }
    
    return response.json();
  }
};

// System Admin Management API
const systemAdminAPI = {
  create: async (adminData) => {
    const response = await fetch('/api/auth/system/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(adminData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create system admin');
    }
    
    return response.json();
  },

  list: async () => {
    const response = await fetch('/api/auth/system/admins', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch system admins');
    }
    
    return response.json();
  },

  delete: async (adminId) => {
    const response = await fetch(`/api/auth/system/admins/${adminId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete system admin');
    }
    
    return response.json();
  }
};

export { 
  authAPI, 
  documentsAPI, 
  companiesAPI, 
  usersAPI, 
  userManagementAPI,
  chatAPI, 
  systemChatAPI, 
  systemDocumentsAPI,
  systemAdminAPI 
};

export default api;
