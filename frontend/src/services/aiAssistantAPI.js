// Align with production backend base like api.js
const API_BASE_URL = 'https://multitenant-backend-mlap.onrender.com';
const buildApiUrl = (endpoint) => `${API_BASE_URL}${endpoint}`;

// Helper function to make HTTP requests
const makeRequest = async (url, options = {}) => {
  const fullUrl = url.startsWith('http') ? url : buildApiUrl(url);
  const response = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      ...options.headers
    },
    ...options
  });
  
  if (!response.ok) {
    let errorBody;
    try {
      errorBody = await response.json();
    } catch (_) {
      errorBody = { detail: response.statusText };
    }
    const err = new Error(errorBody.detail || 'Request failed');
    err.status = response.status;
    err.body = errorBody;
    throw err;
  }
  
  return response.json();
};

const AI_ASSISTANT_BASE_URL = '/api/ai-assistant';

export const aiAssistantAPI = {
  // Chat Sessions
  createChatSession: async (sessionData) => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/chat/sessions`, { method: 'POST', body: JSON.stringify(sessionData) });
      return response;
    } catch (error) {
      console.error('Failed to create chat session:', error);
      // Fallback: create a local pseudo-session if the assistant router is unavailable
      if (error.status === 404) {
        return {
          id: 'default-session',
          session_name: sessionData.session_name || 'General Assistant',
          created_at: new Date().toISOString(),
          last_activity: new Date().toISOString(),
          message_count: 0
        };
      }
      throw error;
    }
  },

  getChatSessions: async () => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/chat/sessions`);
      return response;
    } catch (error) {
      console.error('Failed to get chat sessions:', error);
      // Fallback: use a single default session
      if (error.status === 404) {
        return [
          {
            id: 'default-session',
            session_name: 'Document Review Session',
            created_at: new Date().toISOString(),
            last_activity: new Date().toISOString(),
            message_count: 0
          }
        ];
      }
      throw error;
    }
  },

  deleteChatSession: async (sessionId) => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/chat/sessions/${sessionId}`, { method: 'DELETE' });
      return response;
    } catch (error) {
      console.error('Failed to delete chat session:', error);
      throw error;
    }
  },

  // Chat Messages
  sendChatMessage: async (messageData) => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/chat/messages`, { method: 'POST', body: JSON.stringify(messageData) });
      return response;
    } catch (error) {
      console.error('Failed to send chat message:', error);
      // Fallback: use existing chatbot endpoint /api/chat/
      if (error.status === 404) {
        const chatResp = await makeRequest('/api/chat/', {
          method: 'POST',
          body: JSON.stringify({ question: messageData.message })
        });
        return {
          id: `${Date.now()}`,
          session_id: messageData.session_id || 'default-session',
          message: messageData.message,
          response: chatResp.answer,
          message_type: messageData.message_type || 'text',
          timestamp: chatResp.created_at,
          ai_response_time: 1.0
        };
      }
      throw error;
    }
  },

  getChatMessages: async (sessionId) => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/chat/sessions/${sessionId}/messages`);
      return response;
    } catch (error) {
      console.error('Failed to get chat messages:', error);
      // Fallback: map /api/chat/history to assistant message format
      if (error.status === 404) {
        const history = await makeRequest('/api/chat/history');
        return history.map((h, idx) => ({
          id: `${idx}`,
          session_id: sessionId,
          message: h.question,
          response: h.answer,
          message_type: 'text',
          timestamp: h.created_at,
          ai_response_time: 1.0
        }));
      }
      throw error;
    }
  },

  // Ask about a document (uploads a file and a question)
  askAboutDocument: async (file, question, { readContent = true } = {}) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('question', question);
      formData.append('read_content', readContent ? 'true' : 'false');

      // Try dedicated assistant endpoint first
      const uploadUrl = `${AI_ASSISTANT_BASE_URL}/chat/ask-about-document`;
      const response = await fetch(buildApiUrl(uploadUrl), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });

      if (!response.ok) {
        throw Object.assign(new Error('Upload QA failed'), { status: response.status });
      }
      return await response.json();
    } catch (error) {
      // Fallback: embed extracted text into existing chat endpoint
      try {
        let docText = '';
        // Best-effort text extraction for plain text and markdown; otherwise use filename only
        if (file && /\.(txt|md|csv|json)$/i.test(file.name)) {
          docText = await file.text();
        }

        const prompt = docText
          ? `You are given the following document content between <document> tags. Answer the user question strictly using that content.\n\n<document>\n${docText.slice(0, 15000)}\n</document>\n\nQuestion: ${question}`
          : `The user attached a file named "${file?.name}". If possible, answer the question using general knowledge. Question: ${question}`;

        const chatResp = await makeRequest('/api/chat/', {
          method: 'POST',
          body: JSON.stringify({ question: prompt })
        });

        return {
          answer: chatResp.answer,
          created_at: chatResp.created_at,
        };
      } catch (fallbackErr) {
        console.error('askAboutDocument fallback failed:', fallbackErr);
        throw error;
      }
    }
  },

  // Document Analysis
  analyzeDocument: async (analysisRequest) => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/documents/analyze`, { method: 'POST', body: JSON.stringify(analysisRequest) });
      return response;
    } catch (error) {
      console.error('Failed to analyze document:', error);
      throw error;
    }
  },

  // Smart Suggestions
  getSmartSuggestions: async (suggestionRequest) => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/suggestions`, { method: 'POST', body: JSON.stringify(suggestionRequest) });
      return response;
    } catch (error) {
      console.error('Failed to get smart suggestions:', error);
      throw error;
    }
  },

  // AI Assistant Statistics
  getAIStats: async () => {
    try {
      const response = await makeRequest(`${AI_ASSISTANT_BASE_URL}/stats`);
      return response;
    } catch (error) {
      console.error('Failed to get AI stats:', error);
      throw error;
    }
  },

  // Quick Actions
  getQuickActions: () => {
    return [
      {
        id: 'document-analysis',
        title: 'Analyze Document',
        description: 'Get AI-powered insights from your documents',
        action_type: 'document_analysis',
        icon: 'FileText',
        category: 'Documents',
        requires_context: true
      },
      {
        id: 'workflow-optimization',
        title: 'Optimize Workflow',
        description: 'Get suggestions to improve your processes',
        action_type: 'workflow_optimization',
        icon: 'Workflow',
        category: 'Processes',
        requires_context: false
      },
      {
        id: 'compliance-check',
        title: 'Compliance Check',
        description: 'Verify compliance with industry standards',
        action_type: 'compliance_check',
        icon: 'Shield',
        category: 'Compliance',
        requires_context: true
      },
      {
        id: 'security-audit',
        title: 'Security Audit',
        description: 'Review and improve security measures',
        action_type: 'security_audit',
        icon: 'Lock',
        category: 'Security',
        requires_context: false
      },
      {
        id: 'productivity-tips',
        title: 'Productivity Tips',
        description: 'Get personalized productivity recommendations',
        action_type: 'productivity_tips',
        icon: 'TrendingUp',
        category: 'Productivity',
        requires_context: false
      }
    ];
  },

  // Mock data for development/testing
  getMockData: () => {
    return {
      chatSessions: [
        {
          id: '1',
          session_name: 'Document Review Session',
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000),
          last_activity: new Date(Date.now() - 30 * 60 * 1000),
          message_count: 15
        },
        {
          id: '2',
          session_name: 'Compliance Questions',
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000),
          last_activity: new Date(Date.now() - 6 * 60 * 60 * 1000),
          message_count: 8
        }
      ],
      aiStats: {
        total_chat_sessions: 24,
        total_messages: 156,
        documents_analyzed: 12,
        suggestions_generated: 8,
        average_response_time: 1.8,
        most_used_features: ['Document Analysis', 'Chat Assistant', 'Smart Suggestions'],
        company_usage_trend: {
          daily: [5, 8, 12, 15, 18, 22, 25],
          weekly: [45, 52, 48, 61, 58, 67, 72],
          monthly: [180, 195, 210, 225]
        }
      }
    };
  }
};
