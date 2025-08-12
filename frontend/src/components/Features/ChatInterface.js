import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../utils/auth';
import { chatAPI } from '../../services/api';
import { 
  MessageCircle, 
  Send, 
  Bot, 
  User, 
  FileText, 
  Loader,
  Trash2,
  RefreshCw,
  Settings,
  Brain,
  Zap
} from 'lucide-react';
import SystemChatbot from '../Chat/SystemChatbot';

const ChatInterface = () => {
  const { user, company } = useAuth();
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
    // Add welcome message
    setMessages([
      {
        id: 'welcome',
        type: 'system',
        content: `Welcome to AI Assistant! I'm here to help you with document analysis, company information, and answer your questions. How can I assist you today?`,
        timestamp: new Date()
      }
    ]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    // Only load chat history for company users, not system admins
    if (user.role === 'system_admin' || !company) {
      return;
    }
    
    try {
      const response = await chatAPI.getHistory(company.id);
      setChatHistory(response.data);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!currentMessage.trim() || loading) return;

    // Prevent system admins from sending messages to company chat
    if (user.role === 'system_admin' || !company) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'System administrators cannot access company chat. Please use system-level features.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setCurrentMessage('');
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: currentMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setLoading(true);

    try {
      const response = await chatAPI.sendMessage(currentMessage, company.id);
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.answer,
        context_documents: response.data.context_documents,
        timestamp: new Date(response.data.created_at)
      };

      setMessages(prev => [...prev, aiMessage]);
      await loadChatHistory(); // Refresh history
      
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (question) => {
    setCurrentMessage(question);
  };

  const getSuggestedQuestions = () => {
    const baseQuestions = [
      "What documents have been uploaded recently?",
      "Can you help me analyze my documents?",
      "How can I organize my files better?",
      "What are the system capabilities?"
    ];

    const roleSpecificQuestions = {
      system_admin: [
        "Show me system-wide statistics",
        "What companies are most active?",
        "How is the database performance?",
        "What are the recent system activities?"
      ],
      hr_admin: [
        "How many users are in our company?",
        "What documents need processing?",
        "Show me employee activity summary",
        "What are pending invitations?"
      ],
      hr_manager: [
        "Show me team document uploads",
        "What tasks need my attention?",
        "How can I help team members?",
        "What are recent employee activities?"
      ],
      employee: [
        "How do I upload documents?",
        "What are my recent uploads?",
        "Can you help me with document formatting?",
        "How do I share files with my team?"
      ],
      customer: [
        "How do I get started?",
        "What services are available?",
        "Can you help me with my documents?",
        "How do I contact support?"
      ]
    };

    return [...baseQuestions, ...(roleSpecificQuestions[user.role] || [])];
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Show system chatbot for system admins
  if (user.role === 'system_admin') {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">System Administrator AI Assistant</h1>
            <p className="text-gray-600 mt-2">
              Get AI-powered help with system monitoring, company management, and administrative tasks
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* System Chat Interface */}
            <div className="lg:col-span-4">
              <SystemChatbot />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Require company context for chat
  if (!company) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🏢</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">No Company Context</h1>
          <p className="text-gray-600 mb-4">Chat requires a company context.</p>
          <p className="text-sm text-gray-500">Please ensure you're properly logged in to a company.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">AI Assistant</h1>
          <p className="text-gray-600 mt-2">
            Get AI-powered help with documents, analysis, and company information
          </p>
          {company && (
            <p className="text-sm text-gray-500 mt-1">Company: {company.name}</p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-medium">🤖</span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">AI Assistant</h3>
                      <p className="text-sm text-gray-500">
                        Ready to help • Role: {user.role.replace('_', ' ').toUpperCase()}
                      </p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setShowHistory(!showHistory)}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
                    >
                      {showHistory ? 'Hide' : 'Show'} History
                    </button>
                    <button
                      onClick={() => setMessages([{
                        id: 'welcome',
                        type: 'system',
                        content: 'Chat cleared. How can I help you?',
                        timestamp: new Date()
                      }])}
                      className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              </div>

              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] px-4 py-2 rounded-lg ${
                        message.type === 'user'
                          ? 'bg-blue-500 text-white'
                          : message.type === 'error'
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : message.type === 'system'
                          ? 'bg-gray-100 text-gray-800 border border-gray-200'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      
                      {message.context_documents && message.context_documents.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-300">
                          <p className="text-xs opacity-75">Referenced documents:</p>
                          <ul className="text-xs mt-1 space-y-1">
                            {message.context_documents.map((doc, index) => (
                              <li key={index} className="opacity-75">📄 {doc}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      <p className="text-xs mt-1 opacity-75">
                        {formatTimestamp(message.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
                
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-200 px-4 py-2 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                        <span className="text-sm text-gray-600">AI is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-200">
                <form onSubmit={handleSendMessage} className="flex space-x-2">
                  <input
                    type="text"
                    value={currentMessage}
                    onChange={(e) => setCurrentMessage(e.target.value)}
                    placeholder="Ask me anything about your documents, company, or system..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={loading}
                  />
                  <button
                    type="submit"
                    disabled={loading || !currentMessage.trim()}
                    className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Send
                  </button>
                </form>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Suggested Questions */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-medium text-gray-900 mb-3">Suggested Questions</h3>
              <div className="space-y-2">
                {getSuggestedQuestions().slice(0, 6).map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="w-full text-left p-2 text-sm bg-gray-50 hover:bg-gray-100 rounded border text-gray-700 transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-medium text-gray-900 mb-3">Chat Statistics</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Conversations:</span>
                  <span className="font-medium">{chatHistory.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Messages Today:</span>
                  <span className="font-medium">{messages.filter(m => m.type !== 'system').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">AI Responses:</span>
                  <span className="font-medium">{messages.filter(m => m.type === 'ai').length}</span>
                </div>
              </div>
            </div>

            {/* Recent History */}
            {showHistory && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-gray-900 mb-3">Recent History</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {chatHistory.slice(0, 10).map((chat, index) => (
                    <div key={index} className="p-2 bg-gray-50 rounded text-xs">
                      <p className="font-medium text-gray-700 truncate">{chat.question}</p>
                      <p className="text-gray-500 mt-1 truncate">{chat.answer}</p>
                      <p className="text-gray-400 mt-1">
                        {new Date(chat.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                  {chatHistory.length === 0 && (
                    <p className="text-gray-500 text-sm">No chat history yet</p>
                  )}
                </div>
              </div>
            )}

            {/* Help Tips */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">💡 Tips</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Ask about specific documents</li>
                <li>• Request data analysis</li>
                <li>• Get help with workflows</li>
                <li>• Ask role-specific questions</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 