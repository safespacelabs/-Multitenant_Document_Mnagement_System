import React, { useState, useEffect, useRef } from 'react';
import { hrChatbotAPI } from '../../services/api';
import {
  Send,
  Bot,
  User,
  Loader,
  Plus,
  Trash2,
  MessageSquare,
  UserPlus,
  FileUp,
  FileCheck,
  AlertCircle,
  CheckCircle,
  Clock,
  Users,
  FileText
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../../utils/auth';

function HRChatbot() {
  const { user, company } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [pendingAction, setPendingAction] = useState(null);
  const messagesEndRef = useRef(null);

  // Example prompts for HR actions
  const examplePrompts = [
    { icon: UserPlus, text: "Create a new employee John Doe with email john@company.com as manager", label: "Create User" },
    { icon: FileUp, text: "Upload passport for employee John Doe", label: "Upload Document" },
    { icon: FileCheck, text: "Show me all I9 documents expiring soon", label: "I9 Compliance" },
    { icon: Users, text: "How many employees do we have?", label: "Employee Count" },
    { icon: FileText, text: "What documents are expired?", label: "Expired Docs" },
    { icon: Clock, text: "Show compliance status", label: "Compliance" }
  ];

  useEffect(() => {
    if (user && company) {
      loadSessions();
    }
  }, [user, company]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = async () => {
    if (!company) return;
    setLoadingSessions(true);
    try {
      const data = await hrChatbotAPI.listSessions();
      const sessionList = Array.isArray(data) ? data : (data.sessions || []);
      setSessions(sessionList);

      if (sessionList.length > 0) {
        const mostRecent = sessionList[0];
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
      const data = await hrChatbotAPI.getSessionMessages(sessionId);
      const messageList = Array.isArray(data) ? data : (data.messages || []);
      const formattedMessages = messageList.flatMap(msg => [
        { type: 'user', content: msg.question, timestamp: msg.created_at },
        {
          type: 'bot',
          content: msg.answer,
          timestamp: msg.created_at,
          hrAction: msg.hr_action || null
        }
      ]);
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await hrChatbotAPI.createSession('HR Chat');
      setSessions(prev => [response, ...prev]);
      setActiveSessionId(response.id);
      setMessages([]);
      setPendingAction(null);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();
    try {
      await hrChatbotAPI.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
        setPendingAction(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const selectSession = (sessionId) => {
    setActiveSessionId(sessionId);
    loadSessionMessages(sessionId);
    setPendingAction(null);
  };

  const sendMessage = async (messageText = null) => {
    const message = messageText || inputMessage.trim();
    if (!message || loading) return;

    // Create session if none exists
    let sessionId = activeSessionId;
    if (!sessionId) {
      try {
        const response = await hrChatbotAPI.createSession('HR Chat');
        setSessions(prev => [response, ...prev]);
        sessionId = response.id;
        setActiveSessionId(sessionId);
      } catch (error) {
        console.error('Failed to create session:', error);
        return;
      }
    }

    // Add user message to UI
    const userMessage = { type: 'user', content: message, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await hrChatbotAPI.sendMessage(message, sessionId);

      const botMessage = {
        type: 'bot',
        content: response.answer,
        timestamp: response.created_at,
        hrAction: response.hr_action || null
      };
      setMessages(prev => [...prev, botMessage]);

      // Track pending action for confirmation flow
      if (response.hr_action && response.hr_action.status === 'pending_confirmation') {
        setPendingAction(response.hr_action);
      } else {
        setPendingAction(null);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        type: 'bot',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAction = () => {
    sendMessage('yes');
  };

  const handleCancelAction = () => {
    sendMessage('no');
  };

  const handleExampleClick = (prompt) => {
    setInputMessage(prompt);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Check if user has HR permissions
  const hasHRPermissions = user && ['hr_admin', 'hr_manager'].includes(user.role);

  return (
    <div className="flex h-full bg-gray-50">
      {/* Sessions Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={createNewSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <Plus size={18} />
            New HR Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loadingSessions ? (
            <div className="flex items-center justify-center p-4">
              <Loader className="animate-spin text-gray-400" size={24} />
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No chat sessions yet
            </div>
          ) : (
            sessions.map(session => (
              <div
                key={session.id}
                onClick={() => selectSession(session.id)}
                className={`flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 border-b border-gray-100 ${
                  activeSessionId === session.id ? 'bg-purple-50 border-l-4 border-l-purple-600' : ''
                }`}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <MessageSquare size={16} className="text-gray-400 flex-shrink-0" />
                  <span className="text-sm text-gray-700 truncate">
                    {session.title || 'HR Chat'}
                  </span>
                </div>
                <button
                  onClick={(e) => deleteSession(session.id, e)}
                  className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 hover:opacity-100"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
              <Bot size={24} className="text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-800">HR Assistant</h2>
              <p className="text-sm text-gray-500">
                Create users, manage documents, check compliance
              </p>
            </div>
            {hasHRPermissions && (
              <span className="ml-auto px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full flex items-center gap-1">
                <CheckCircle size={12} />
                HR Actions Enabled
              </span>
            )}
            {!hasHRPermissions && (
              <span className="ml-auto px-3 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full flex items-center gap-1">
                <AlertCircle size={12} />
                View Only (HR role required for actions)
              </span>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <Bot size={32} className="text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">HR Assistant</h3>
              <p className="text-gray-500 text-center mb-8 max-w-md">
                I can help you create users, manage documents, check I9 compliance, and more.
                Try one of these examples:
              </p>

              <div className="grid grid-cols-2 gap-3 max-w-2xl">
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(prompt.text)}
                    className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors text-left"
                  >
                    <prompt.icon size={20} className="text-purple-600 flex-shrink-0" />
                    <div>
                      <div className="text-sm font-medium text-gray-700">{prompt.label}</div>
                      <div className="text-xs text-gray-500 truncate max-w-[200px]">{prompt.text}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex gap-3 ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.type === 'bot' && (
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot size={18} className="text-purple-600" />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] rounded-lg px-4 py-3 ${
                      msg.type === 'user'
                        ? 'bg-purple-600 text-white'
                        : msg.isError
                        ? 'bg-red-50 text-red-700 border border-red-200'
                        : 'bg-white border border-gray-200 text-gray-800'
                    }`}
                  >
                    {msg.type === 'bot' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p>{msg.content}</p>
                    )}

                    {/* HR Action Indicator */}
                    {msg.hrAction && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <div className="flex items-center gap-2 text-xs">
                          {msg.hrAction.status === 'pending_confirmation' && (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded flex items-center gap-1">
                              <Clock size={12} />
                              Awaiting Confirmation
                            </span>
                          )}
                          {msg.hrAction.action_type && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded">
                              {msg.hrAction.action_type.replace('_', ' ')}
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  {msg.type === 'user' && (
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                      <User size={18} className="text-gray-600" />
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot size={18} className="text-purple-600" />
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                    <Loader className="animate-spin text-purple-600" size={20} />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Pending Action Confirmation */}
        {pendingAction && pendingAction.status === 'pending_confirmation' && (
          <div className="px-6 py-3 bg-yellow-50 border-t border-yellow-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle size={18} className="text-yellow-600" />
                <span className="text-sm text-yellow-800">
                  Action pending confirmation: <strong>{pendingAction.action_type?.replace('_', ' ')}</strong>
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCancelAction}
                  className="px-3 py-1 text-sm bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmAction}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={hasHRPermissions ? "Ask me to create users, check compliance, manage documents..." : "Ask questions about employees, documents, compliance..."}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !inputMessage.trim()}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading ? <Loader className="animate-spin" size={20} /> : <Send size={20} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HRChatbot;
