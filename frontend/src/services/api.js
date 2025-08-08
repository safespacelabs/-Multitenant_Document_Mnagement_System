// API base URL - use full URL in production, relative in development
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://multitenant-backend-mlap.onrender.com'
  : '';

// Helper function to build API URLs
const buildApiUrl = (endpoint) => {
  return `${API_BASE_URL}${endpoint}`;
};

// Authentication API
const authAPI = {
  login: async (credentials) => {
    const response = await fetch(buildApiUrl('/api/auth/login'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }
    
    return response.json();
  },

  systemAdminLogin: async (credentials) => {
    const response = await fetch(buildApiUrl('/api/auth/system-admin/login'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'System admin login failed');
    }
    
    return response.json();
  },

  register: async (userData, companyId) => {
    const response = await fetch(buildApiUrl(`/api/auth/register?company_id=${companyId}`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }
    
    return response.json();
  },

  getMe: async () => {
    const response = await fetch(buildApiUrl('/api/auth/me'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get user info');
    }
    
    return response.json();
  }
};

// Companies API
const companiesAPI = {
  list: async () => {
    const response = await fetch(buildApiUrl('/api/companies/'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch companies');
    }
    
    return response.json();
  },

  create: async (companyData) => {
    const response = await fetch(buildApiUrl('/api/companies/'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(companyData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create company');
    }
    
    return response.json();
  },

  delete: async (companyId) => {
    const response = await fetch(buildApiUrl(`/api/companies/${companyId}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete company');
    }
    
    return response.json();
  }
};

// Users API
const usersAPI = {
  list: async (companyId) => {
    const response = await fetch(buildApiUrl(`/api/users/${companyId}`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch users');
    }
    
    return response.json();
  },

  create: async (userData, companyId) => {
    const response = await fetch(buildApiUrl(`/api/users/${companyId}`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(userData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create user');
    }
    
    return response.json();
  },

  delete: async (userId, companyId) => {
    const response = await fetch(buildApiUrl(`/api/users/${companyId}/${userId}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete user');
    }
    
    return response.json();
  }
};

// User Management API
const userManagementAPI = {
  getRoles: async () => {
    const response = await fetch(buildApiUrl('/api/user-management/roles'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch roles');
    }
    
    return response.json();
  },

  createCustomRole: async (roleData) => {
    const response = await fetch(buildApiUrl('/api/user-management/roles/create-custom-role'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(roleData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create custom role');
    }
    
    return response.json();
  },

  deleteCustomRole: async (roleName) => {
    const response = await fetch(buildApiUrl(`/api/user-management/roles/delete-custom-role/${roleName}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete custom role');
    }
    
    return response.json();
  },

  getPermissionActions: async () => {
    const response = await fetch(buildApiUrl('/api/user-management/roles/permission-actions'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch permission actions');
    }
    
    return response.json();
  },

  inviteUser: async (inviteData, companyId) => {
    const response = await fetch(buildApiUrl('/api/user-management/invite'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ ...inviteData, company_id: companyId })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to invite user');
    }
    
    return response.json();
  },

  listInvitations: async (companyId) => {
    const response = await fetch(buildApiUrl('/api/user-management/invitations'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch invitations');
    }
    
    return response.json();
  },

  cancelInvitation: async (invitationId, companyId) => {
    const response = await fetch(buildApiUrl(`/api/user-management/invitations/${invitationId}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to cancel invitation');
    }
    
    return response.json();
  },

  updateUser: async (userId, userData, companyId) => {
    const response = await fetch(buildApiUrl(`/api/user-management/users/${userId}`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ ...userData, company_id: companyId })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update user');
    }
    
    return response.json();
  },

  getPermissions: async () => {
    const response = await fetch(buildApiUrl('/api/user-management/permissions'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch permissions');
    }
    
    return response.json();
  }
};

// Documents API
const documentsAPI = {
  list: async (companyId) => {
    const response = await fetch(buildApiUrl(`/api/documents/${companyId}`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch documents');
    }
    
    return response.json();
  },

  upload: async (file, companyId) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(buildApiUrl(`/api/documents/${companyId}/upload`), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload document');
    }
    
    return response.json();
  },

  delete: async (documentId, companyId) => {
    const response = await fetch(buildApiUrl(`/api/documents/${companyId}/${documentId}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete document');
    }
    
    return response.json();
  },

  download: async (documentId, companyId) => {
    const response = await fetch(buildApiUrl(`/api/documents/${companyId}/${documentId}/download`), {
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
  }
};

// Chat API
const chatAPI = {
  sendMessage: async (message, companyId) => {
    const response = await fetch(buildApiUrl(`/api/chat/${companyId}`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send message');
    }
    
    return response.json();
  },

  getHistory: async (companyId) => {
    const response = await fetch(buildApiUrl(`/api/chat/${companyId}/history`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch chat history');
    }
    
    return response.json();
  }
};

// System Chat API
const systemChatAPI = {
  sendMessage: async (message) => {
    const response = await fetch(buildApiUrl('/api/chat/system'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send system message');
    }
    
    return response.json();
  },

  getHistory: async () => {
    const response = await fetch(buildApiUrl('/api/chat/system/history'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch system chat history');
    }
    
    return response.json();
  }
};

// System Documents API
const systemDocumentsAPI = {
  list: async () => {
    const response = await fetch(buildApiUrl('/api/documents/system'), {
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

  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(buildApiUrl('/api/documents/system/upload'), {
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

  delete: async (documentId) => {
    const response = await fetch(buildApiUrl(`/api/documents/system/${documentId}`), {
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
    const response = await fetch(buildApiUrl(`/api/documents/system/${documentId}/download`), {
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
    const response = await fetch(buildApiUrl('/api/documents/system/folders'), {
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
    const response = await fetch(buildApiUrl('/api/auth/system/register'), {
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
    const response = await fetch(buildApiUrl('/api/auth/system/admins'), {
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
    const response = await fetch(buildApiUrl(`/api/auth/system/admins/${adminId}`), {
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

// E-Signature API
const esignatureAPI = {
  list: async (filter = 'all') => {
    const response = await fetch(buildApiUrl(`/api/esignature/list${filter !== 'all' ? `?status=${filter}` : ''}`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch e-signature requests');
    }
    
    return response.json();
  },

  createRequest: async (requestData) => {
    const response = await fetch(buildApiUrl('/api/esignature/create-request'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create e-signature request');
    }
    
    return response.json();
  },

  sendRequest: async (requestId) => {
    const response = await fetch(buildApiUrl(`/api/esignature/${requestId}/send`), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send e-signature request');
    }
    
    return response.json();
  },

  cancelRequest: async (requestId) => {
    const response = await fetch(buildApiUrl(`/api/esignature/${requestId}/cancel`), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to cancel e-signature request');
    }
    
    return response.json();
  },

  getStatus: async (requestId) => {
    const response = await fetch(buildApiUrl(`/api/esignature/${requestId}/status`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get e-signature status');
    }
    
    return response.json();
  },

  getPublicStatus: async (documentId, recipientEmail) => {
    const response = await fetch(buildApiUrl(`/api/esignature/${documentId}/status-public?recipient_email=${encodeURIComponent(recipientEmail)}`), {
      method: 'GET'
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get e-signature status');
    }
    
    return response.json();
  },

  signDocument: async (documentId, signRequest) => {
    const response = await fetch(buildApiUrl(`/api/esignature/${documentId}/sign`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(signRequest)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to sign document');
    }
    
    return response.json();
  },

  signDocumentDirectly: async (documentId, signData) => {
    const response = await fetch(buildApiUrl(`/api/esignature/sign-document-directly/${documentId}`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(signData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to sign document directly');
    }
    
    return response.json();
  },

  downloadSigned: async (requestId) => {
    const response = await fetch(buildApiUrl(`/api/esignature/${requestId}/download-signed`), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to download signed document');
    }
    
    return response.blob();
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
  systemAdminAPI,
  esignatureAPI
};
