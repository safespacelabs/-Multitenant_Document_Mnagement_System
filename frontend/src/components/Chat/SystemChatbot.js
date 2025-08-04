import React, { useState, useEffect, useRef } from 'react';
import { systemChatAPI, systemDocumentsAPI } from '../../services/api';
import { Send, Bot, User, Loader, Shield, Database, Activity, Upload, Paperclip, FolderPlus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../../utils/auth';

function SystemChatbot() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [showFolderInput, setShowFolderInput] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [folders, setFolders] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Only load for system admins
    if (user.role === 'system_admin') {
      loadChatHistory();
      loadFolders();
      // Add welcome message
      setMessages([{
        type: 'system',
        content: `Welcome, System Administrator! I'm your AI assistant for system-level tasks and monitoring. I can help you with:

• Company management and statistics
• System health monitoring  
• User oversight across all companies
• Administrative guidance and troubleshooting
• Document management and file uploads

How can I assist you today?`,
        timestamp: new Date()
      }]);
    }
  }, [user.role]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const response = await systemChatAPI.getHistory();
      const history = response.data.slice(0, 10).reverse();
      const formattedHistory = history.flatMap(chat => [
        { type: 'user', content: chat.question, timestamp: chat.created_at },
        { type: 'bot', content: chat.answer, timestamp: chat.created_at }
      ]);
      setMessages(prev => [...formattedHistory, ...prev]);
    } catch (error) {
      console.error('Failed to load system chat history:', error);
    }
  };

  const loadFolders = async () => {
    try {
      const response = await systemDocumentsAPI.getFolders();
      setFolders(response);
    } catch (error) {
      console.error('Failed to load folders:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingFile(true);
    try {
      const folderName = selectedFolder || 'ChatUploads';
      
      // Add upload start message
      const uploadMessage = {
        type: 'user',
        content: `Uploading file: ${file.name} to folder: ${folderName}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, uploadMessage]);

      await systemDocumentsAPI.upload(file, folderName);
      
      // Add success message
      const successMessage = {
        type: 'bot',
        content: `✅ **File Uploaded Successfully**\n\n**File:** ${file.name}\n**Folder:** ${folderName}\n**Size:** ${(file.size / 1024).toFixed(1)} KB\n\nThe file is now available in Document Management!`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, successMessage]);

      // Refresh folders in case a new one was created
      loadFolders();
      
      // Reset
      setSelectedFolder('');
      setShowFolderInput(false);
      event.target.value = '';
      
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: `❌ **Upload Failed**\n\nError: ${error.message}\n\nPlease try again or use a different file.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setUploadingFile(false);
    }
  };

  const handleUploadClick = () => {
    if (folders.length === 0) {
      setShowFolderInput(true);
    } else {
      fileInputRef.current?.click();
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = { type: 'user', content: inputMessage, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await systemChatAPI.sendMessage(inputMessage);
      const botMessage = {
        type: 'bot',
        content: response.data.answer,
        timestamp: response.data.created_at
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

  const getSuggestedQuestions = () => {
    return [
      "Show me system status",
      "How many companies are active?", 
      "Create folder name ProjectFiles",
      "Upload file to folder",
      "Give me system statistics",
      "Help me with document management"
    ];
  };

  const handleSuggestedQuestion = (question) => {
    setInputMessage(question);
  };

  // Only show for system admins
  if (user.role !== 'system_admin') {
    return (
      <div className="bg-white rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold flex items-center">
            <Shield className="h-6 w-6 mr-2 text-red-500" />
            System Administrator Assistant
          </h2>
          <p className="text-gray-600 text-sm">
            Access restricted to system administrators
          </p>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <Shield className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>System administrator access required.</p>
            <p className="text-sm mt-2">Please log in with system administrator credentials.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow h-[calc(100vh-12rem)] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold flex items-center">
          <Shield className="h-6 w-6 mr-2 text-blue-500" />
          System Administrator Assistant
        </h2>
        <p className="text-gray-600 text-sm">
          System-level monitoring, management, and administrative assistance
        </p>
        <div className="flex items-center space-x-4 mt-2">
          <div className="flex items-center space-x-1 text-xs text-green-600">
            <Activity className="h-3 w-3" />
            <span>System Online</span>
          </div>
          <div className="flex items-center space-x-1 text-xs text-blue-600">
            <Database className="h-3 w-3" />
            <span>Database Connected</span>
          </div>
          <div className="flex items-center space-x-1 text-xs text-purple-600">
            <Shield className="h-3 w-3" />
            <span>Admin Mode</span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 1 && (
          <div className="mb-6">
            <div className="text-center text-gray-500 mb-4">
              <Shield className="h-8 w-8 mx-auto mb-2 text-blue-500" />
              <p className="text-sm font-medium">Quick System Commands</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {getSuggestedQuestions().map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="text-left p-3 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg text-sm text-blue-800 transition-colors"
                >
                  {question}
                </button>
              ))}
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
                  : message.type === 'system'
                  ? 'bg-gradient-to-r from-blue-50 to-purple-50 text-gray-800 border border-blue-200'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <div className="flex items-start space-x-2">
                {message.type === 'bot' && (
                  <Shield className="h-4 w-4 mt-1 text-blue-500" />
                )}
                {message.type === 'system' && (
                  <Bot className="h-4 w-4 mt-1 text-blue-500" />
                )}
                {message.type === 'user' && (
                  <User className="h-4 w-4 mt-1 text-white" />
                )}
                <div className="flex-1">
                  {message.type === 'bot' || message.type === 'system' ? (
                    <ReactMarkdown className="prose prose-sm max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  <p className="text-xs mt-1 opacity-75">
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Shield className="h-4 w-4 text-blue-500" />
                <Loader className="h-4 w-4 animate-spin text-blue-500" />
                <span>Processing system query...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200">
        {/* Folder Selection */}
        {showFolderInput && (
          <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <FolderPlus className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">Select Upload Folder</span>
            </div>
            <div className="flex space-x-2">
              <select
                value={selectedFolder}
                onChange={(e) => setSelectedFolder(e.target.value)}
                className="flex-1 border border-blue-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">ChatUploads (default)</option>
                {Array.isArray(folders) && folders.map((folder) => (
                  <option key={folder} value={folder}>
                    {folder}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => {
                  fileInputRef.current?.click();
                  setShowFolderInput(false);
                }}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Upload
              </button>
              <button
                type="button"
                onClick={() => setShowFolderInput(false)}
                className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <form onSubmit={sendMessage}>
          <div className="flex space-x-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about system status, companies, or administrative tasks..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading || uploadingFile}
            />
            
            {/* File Upload Button */}
            <button
              type="button"
              onClick={handleUploadClick}
              disabled={uploadingFile || loading}
              className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              title="Upload File"
            >
              {uploadingFile ? (
                <Loader className="h-4 w-4 animate-spin" />
              ) : (
                <Paperclip className="h-4 w-4" />
              )}
            </button>

            {/* Send Button */}
            <button
              type="submit"
              disabled={loading || !inputMessage.trim() || uploadingFile}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          
          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            className="hidden"
            accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.png,.jpg,.jpeg,.gif"
          />
          
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>System Administrator Chat • Secure Connection</span>
            <div className="flex items-center space-x-4">
              <span>📁 Upload files • 💬 Chat commands</span>
              <span>Press Enter to send</span>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SystemChatbot; 