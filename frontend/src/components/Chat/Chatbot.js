import React, { useState, useEffect, useRef } from 'react';
import { chatAPI, documentsAPI } from '../../services/api';
import { Send, Bot, User, Loader, Plus, Trash2, MessageSquare, Paperclip, X, FileText, Upload } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../../utils/auth';
import SystemChatbot from './SystemChatbot';

function Chatbot() {
  const { user, company } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user.role !== 'system_admin' && company) {
      loadSessions();
      loadActiveSessionFromStorage();
    }
  }, [user.role, company]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Persist active session ID to localStorage
  useEffect(() => {
    if (activeSessionId && company) {
      localStorage.setItem(`active_chat_session_${company.id}_${user.id}`, activeSessionId);
    }
  }, [activeSessionId, company, user.id]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadActiveSessionFromStorage = () => {
    if (!company) return;

    const storedSessionId = localStorage.getItem(`active_chat_session_${company.id}_${user.id}`);
    if (storedSessionId) {
      setActiveSessionId(storedSessionId);
      loadSessionMessages(storedSessionId);
    }
  };

  const loadSessions = async () => {
    if (user.role === 'system_admin' || !company) return;

    setLoadingSessions(true);
    try {
      const response = await chatAPI.listSessions();
      setSessions(response.sessions || []);

      // If no active session and sessions exist, select the most recent
      if (!activeSessionId && response.sessions && response.sessions.length > 0) {
        const mostRecent = response.sessions[0];
        setActiveSessionId(mostRecent.id);
        loadSessionMessages(mostRecent.id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await chatAPI.getSessionMessages(sessionId);
      const formattedMessages = response.messages.flatMap(msg => [
        {type: 'user', content: msg.question, timestamp: msg.created_at},
        {type: 'bot', content: msg.answer, contextDocuments: msg.context_documents, timestamp: msg.created_at}
      ]);
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await chatAPI.createSession('New Chat');
      setSessions(prev => [response, ...prev]);
      setActiveSessionId(response.id);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();

    if (!window.confirm('Delete this chat? This cannot be undone.')) return;

    try {
      await chatAPI.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));

      if (activeSessionId === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId);
        if (remaining.length > 0) {
          setActiveSessionId(remaining[0].id);
          loadSessionMessages(remaining[0].id);
        } else {
          setActiveSessionId(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const switchSession = (sessionId) => {
    setActiveSessionId(sessionId);
    loadSessionMessages(sessionId);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }
      setSelectedFile(file);
      setShowUploadModal(true);
    }
  };

  const handleUploadAndAsk = async () => {
    if (!selectedFile || !inputMessage.trim()) {
      alert('Please select a file and enter a question');
      return;
    }

    setUploading(true);
    setShowUploadModal(false);

    const userMessage = {
      type: 'user',
      content: `📎 ${selectedFile.name}\n\nQ: ${inputMessage}`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Upload document to the documents system
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('folder_name', 'Chat Uploads');

      const uploadResponse = await documentsAPI.upload(formData);

      // Send message with reference to the uploaded document
      const question = `I just uploaded "${selectedFile.name}". ${inputMessage}`;
      const response = await chatAPI.sendMessage(question, company.id, activeSessionId);

      const botMessage = {
        type: 'bot',
        content: `📄 Document uploaded successfully!\n\n${response.answer}`,
        timestamp: response.created_at,
        contextDocuments: response.context_documents
      };
      setMessages(prev => [...prev, botMessage]);

      // Handle session creation/update
      if (!activeSessionId && response.session_id) {
        setActiveSessionId(response.session_id);
        await loadSessions();
      } else if (activeSessionId) {
        await loadSessions();
      }

      // Clear form
      setInputMessage('');
      setSelectedFile(null);
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = {
        type: 'bot',
        content: `Sorry, failed to upload document: ${error.message}. Please try again.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setUploading(false);
    }
  };

  const cancelUpload = () => {
    setSelectedFile(null);
    setShowUploadModal(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    if (user.role === 'system_admin' || !company) {
      const errorMessage = {
        type: 'bot',
        content: 'System administrators cannot access company chat.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setInputMessage('');
      return;
    }

    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(inputMessage, company.id, activeSessionId);

      const botMessage = {
        type: 'bot',
        content: response.answer,
        timestamp: response.created_at,
        contextDocuments: response.context_documents
      };
      setMessages(prev => [...prev, botMessage]);

      // If this was the first message (new session created)
      if (!activeSessionId && response.session_id) {
        setActiveSessionId(response.session_id);
        await loadSessions(); // Refresh session list
      } else if (activeSessionId) {
        // Update session list to reflect new message count
        await loadSessions();
      }
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (user.role === 'system_admin') {
    return <SystemChatbot />;
  }

  if (!company) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <Bot className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h2 className="text-xl font-bold text-gray-900">Company context required</h2>
          <p className="text-gray-600 mt-2">Please log in to a company to use chat.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] bg-gray-50">
      {/* Sidebar - Session List */}
      <div className="w-64 bg-gray-900 text-white flex flex-col">
        {/* New Chat Button */}
        <div className="p-3 border-b border-gray-700">
          <button
            onClick={createNewSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span className="font-medium">New Chat</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          {loadingSessions ? (
            <div className="flex items-center justify-center h-32">
              <Loader className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-gray-400 text-sm">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No chats yet</p>
              <p className="text-xs mt-1">Start a conversation!</p>
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => switchSession(session.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors group relative ${
                    activeSessionId === session.id
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{session.title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <button
                      onClick={(e) => deleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 ml-2 p-1 hover:bg-red-600 rounded transition-opacity"
                      title="Delete chat"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="p-3 border-t border-gray-700 text-xs text-gray-400">
          <p className="truncate">{user.username}</p>
          <p className="truncate text-gray-500">{company.name}</p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <h2 className="text-xl font-bold flex items-center">
            <Bot className="h-5 w-5 mr-2 text-blue-500" />
            AI Document Assistant
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Ask me anything - I'll automatically search documents, I9 forms, or answer general questions
          </p>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Bot className="h-16 w-16 mb-4 text-gray-300" />
              <p className="text-lg font-medium mb-2">Start a new conversation</p>
              <div className="max-w-md text-sm text-center space-y-2">
                <p className="text-gray-600">I can help with:</p>
                <div className="grid grid-cols-1 gap-2 mt-3">
                  <div className="p-3 bg-blue-50 rounded-lg text-left">
                    <p className="font-medium text-blue-900">📄 Documents</p>
                    <p className="text-xs text-blue-800 mt-1">"Summarize my contract" or "What's in report.pdf?"</p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg text-left">
                    <p className="font-medium text-green-900">🏢 I9 Compliance</p>
                    <p className="text-xs text-green-800 mt-1">"Show expiring I9 forms" or "I9 summary"</p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg text-left">
                    <p className="font-medium text-purple-900">💬 General Help</p>
                    <p className="text-xs text-purple-800 mt-1">"How many documents do I have?"</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-start gap-3">
                  {message.type === 'bot' && (
                    <Bot className="h-5 w-5 mt-0.5 text-blue-600 flex-shrink-0" />
                  )}
                  {message.type === 'user' && (
                    <User className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    {message.type === 'bot' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}

                    {message.contextDocuments && message.contextDocuments.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-300 text-xs text-gray-600">
                        📎 Sources: {message.contextDocuments.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-lg flex items-center gap-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <Loader className="h-4 w-4 animate-spin text-blue-600" />
                <span className="text-gray-700 text-sm">Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <form onSubmit={sendMessage} className="flex gap-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-3 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
              title="Upload document"
              disabled={loading || uploading}
            >
              <Paperclip className="h-5 w-5" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt"
            />
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask me anything about your documents..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading || uploading}
            />
            <button
              type="submit"
              disabled={loading || uploading || !inputMessage.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading || uploading ? <Loader className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </form>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Upload className="h-5 w-5 text-blue-600" />
                Upload and Ask
              </h3>
              <button
                onClick={cancelUpload}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {selectedFile && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What would you like to know about this document?
              </label>
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="E.g., Summarize this document, What are the key points?, etc."
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={cancelUpload}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleUploadAndAsk}
                disabled={!inputMessage.trim() || uploading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader className="h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Upload & Ask
                  </>
                )}
              </button>
            </div>

            <p className="mt-3 text-xs text-gray-500">
              Supported formats: PDF, DOC, DOCX, TXT (max 10MB)
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Chatbot;
