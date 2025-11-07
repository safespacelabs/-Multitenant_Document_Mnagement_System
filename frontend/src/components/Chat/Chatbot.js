import React, { useState, useEffect, useRef } from 'react';
import { chatAPI, documentsAPI } from '../../services/api';
import { Send, Bot, User, Loader, FileText, X, CheckCircle, Search, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../../utils/auth';
import SystemChatbot from './SystemChatbot';

function Chatbot() {
  const { user, company } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Only load chat history for company users, not system admins
    if (user.role !== 'system_admin' && company) {
      loadChatHistory();
      loadDocuments();
      loadSelectedDocumentsFromStorage();
    }
  }, [user.role, company]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Persist selected documents to localStorage
  useEffect(() => {
    if (company && selectedDocuments.length > 0) {
      localStorage.setItem(
        `chatbot_selected_docs_${company.id}`,
        JSON.stringify(selectedDocuments)
      );
    }
  }, [selectedDocuments, company]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    if (user.role === 'system_admin' || !company) {
      return;
    }

    try {
      const response = await chatAPI.getHistory();
      const history = response.data.slice(0, 10).reverse();
      const formattedHistory = history.flatMap(chat => [
        { type: 'user', content: chat.question, timestamp: chat.created_at },
        { type: 'bot', content: chat.answer, timestamp: chat.created_at }
      ]);
      setMessages(formattedHistory);
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const loadDocuments = async () => {
    if (user.role === 'system_admin' || !company) {
      return;
    }

    setLoadingDocuments(true);
    try {
      const response = await documentsAPI.list();
      const docs = response.data || response || [];
      setDocuments(Array.isArray(docs) ? docs : []);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    } finally {
      setLoadingDocuments(false);
    }
  };

  const loadSelectedDocumentsFromStorage = () => {
    if (!company) return;

    try {
      const stored = localStorage.getItem(`chatbot_selected_docs_${company.id}`);
      if (stored) {
        const parsedDocs = JSON.parse(stored);
        setSelectedDocuments(parsedDocs);
      }
    } catch (error) {
      console.error('Failed to load selected documents from storage:', error);
    }
  };

  const toggleDocumentSelection = (doc) => {
    setSelectedDocuments(prev => {
      const isSelected = prev.some(d => d.id === doc.id);
      if (isSelected) {
        return prev.filter(d => d.id !== doc.id);
      } else {
        return [...prev, { id: doc.id, filename: doc.original_filename }];
      }
    });
  };

  const clearSelectedDocuments = () => {
    setSelectedDocuments([]);
    if (company) {
      localStorage.removeItem(`chatbot_selected_docs_${company.id}`);
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.original_filename?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    // Prevent system admins from sending messages
    if (user.role === 'system_admin' || !company) {
      const errorMessage = {
        type: 'bot',
        content: 'System administrators cannot access company chat. Please use system-level features.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setInputMessage('');
      return;
    }

    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
      selectedDocs: selectedDocuments.length > 0 ? selectedDocuments.map(d => d.filename) : null
    };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // Pass selected document IDs to backend for context-aware responses
      const documentIds = selectedDocuments.length > 0
        ? selectedDocuments.map(d => d.id)
        : null;

      const response = await chatAPI.sendMessage(inputMessage, company.id, documentIds);
      const botMessage = {
        type: 'bot',
        content: response.data.answer,
        timestamp: response.data.created_at,
        contextDocuments: response.data.context_documents
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Show system chatbot for system admins
  if (user.role === 'system_admin') {
    return <SystemChatbot />;
  }

  // Require company context
  if (!company) {
    return (
      <div className="bg-white rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold flex items-center">
            <Bot className="h-6 w-6 mr-2 text-blue-500" />
            Document Assistant
          </h2>
          <p className="text-gray-600 text-sm">
            Company context required for chat
          </p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Chat requires a company context.</p>
            <p className="text-sm mt-2">Please ensure you're properly logged in to a company.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold flex items-center">
            <Bot className="h-6 w-6 mr-2 text-blue-500" />
            Document Assistant
          </h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowDocumentSelector(!showDocumentSelector)}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 flex items-center"
            >
              <FileText className="h-4 w-4 mr-1" />
              Select Documents ({selectedDocuments.length})
            </button>
            <button
              onClick={loadDocuments}
              className="p-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              title="Refresh documents"
            >
              <RefreshCw className={`h-4 w-4 ${loadingDocuments ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
        <p className="text-gray-600 text-sm">
          Ask questions about your documents and get intelligent answers
        </p>

        {/* Selected Documents Bar */}
        {selectedDocuments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-xs text-gray-500 flex items-center">
              <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
              Active context:
            </span>
            {selectedDocuments.map((doc) => (
              <span
                key={doc.id}
                className="inline-flex items-center px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
              >
                <FileText className="h-3 w-3 mr-1" />
                {doc.filename}
                <button
                  onClick={() => toggleDocumentSelection(doc)}
                  className="ml-1 hover:text-green-900"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            <button
              onClick={clearSelectedDocuments}
              className="text-xs text-red-600 hover:text-red-800 underline"
            >
              Clear all
            </button>
          </div>
        )}

        {/* Document Selector Panel */}
        {showDocumentSelector && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-700">Select Documents</h3>
              <button
                onClick={() => setShowDocumentSelector(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="mb-2">
              <div className="relative">
                <Search className="absolute left-2 top-2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search documents..."
                  className="w-full pl-8 pr-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Documents List */}
            <div className="max-h-60 overflow-y-auto space-y-1">
              {loadingDocuments ? (
                <div className="text-center py-4 text-gray-500 text-sm">
                  <Loader className="h-5 w-5 animate-spin mx-auto mb-2" />
                  Loading documents...
                </div>
              ) : filteredDocuments.length === 0 ? (
                <div className="text-center py-4 text-gray-500 text-sm">
                  {searchQuery ? 'No documents match your search' : 'No documents available'}
                </div>
              ) : (
                filteredDocuments.map((doc) => {
                  const isSelected = selectedDocuments.some(d => d.id === doc.id);
                  return (
                    <button
                      key={doc.id}
                      onClick={() => toggleDocumentSelection(doc)}
                      className={`w-full text-left px-3 py-2 text-sm rounded border transition-colors ${
                        isSelected
                          ? 'bg-blue-100 border-blue-300 text-blue-900'
                          : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center flex-1 min-w-0">
                          <FileText className={`h-4 w-4 mr-2 flex-shrink-0 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`} />
                          <span className="truncate">{doc.original_filename}</span>
                        </div>
                        {isSelected && (
                          <CheckCircle className="h-4 w-4 ml-2 text-blue-600 flex-shrink-0" />
                        )}
                      </div>
                      {doc.folder_name && (
                        <div className="text-xs text-gray-500 ml-6 mt-1">
                          Folder: {doc.folder_name}
                        </div>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p className="font-medium text-lg mb-2">Start a conversation with Document Assistant!</p>
            <div className="max-w-md mx-auto text-sm space-y-2">
              <p className="text-gray-600">
                {selectedDocuments.length > 0 ? (
                  <>
                    <CheckCircle className="inline h-4 w-4 text-green-500 mr-1" />
                    {selectedDocuments.length} document(s) selected. Ask me anything about them!
                  </>
                ) : (
                  <>
                    <FileText className="inline h-4 w-4 mr-1" />
                    Select documents above to ask specific questions, or ask general queries.
                  </>
                )}
              </p>
              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-left">
                <p className="font-medium text-blue-900 mb-2">Try asking:</p>
                <ul className="text-blue-800 space-y-1">
                  <li>• "What documents do I have?"</li>
                  <li>• "Summarize the content of [document name]"</li>
                  <li>• "What are the key points in the selected documents?"</li>
                  <li>• "Show me expiring documents"</li>
                </ul>
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
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'bot' && (
                  <Bot className="h-4 w-4 mt-1 text-blue-500" />
                )}
                {message.type === 'user' && (
                  <User className="h-4 w-4 mt-1 text-white" />
                )}
                <div className="flex-1">
                  {message.type === 'bot' ? (
                    <ReactMarkdown className="prose prose-sm max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}

                  {/* Show selected documents for user messages */}
                  {message.type === 'user' && message.selectedDocs && (
                    <div className="mt-2 pt-2 border-t border-blue-400">
                      <p className="text-xs opacity-90 flex items-center">
                        <FileText className="h-3 w-3 mr-1" />
                        Context: {message.selectedDocs.join(', ')}
                      </p>
                    </div>
                  )}

                  {/* Show context documents for bot responses */}
                  {message.type === 'bot' && message.contextDocuments && message.contextDocuments.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-300">
                      <p className="text-xs text-gray-600">
                        Referenced documents: {message.contextDocuments.join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Bot className="h-4 w-4 text-blue-500" />
                <Loader className="h-4 w-4 animate-spin text-blue-500" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about your documents..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !inputMessage.trim()}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

export default Chatbot;