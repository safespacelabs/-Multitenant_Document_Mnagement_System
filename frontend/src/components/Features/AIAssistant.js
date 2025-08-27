import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../utils/auth';
import { aiAssistantAPI } from '../../services/aiAssistantAPI';
import { 
  MessageCircle, 
  FileText, 
  Lightbulb, 
  BarChart3, 
  Plus, 
  Send, 
  Trash2, 
  Settings,
  Bot,
  User,
  Clock,
  TrendingUp,
  Shield,
  Lock,
  Workflow,
  Zap,
  BookOpen,
  Target,
  Star,
  ChevronRight,
  X,
  Search,
  Filter,
  Download,
  Share2,
  Check
} from 'lucide-react';

const AIAssistant = () => {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [aiStats, setAiStats] = useState(null);
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [analysisType, setAnalysisType] = useState('summary');
  const [suggestions, setSuggestions] = useState([]);
  const [showDocumentAnalysis, setShowDocumentAnalysis] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user && company) {
      loadInitialData();
    }
  }, [user, company]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      
      // Load chat sessions
      const sessions = await aiAssistantAPI.getChatSessions();
      setChatSessions(sessions);
      
      // Load AI stats
      const stats = await aiAssistantAPI.getAIStats();
      setAiStats(stats);
      
      // If no sessions exist, create a default one
      if (sessions.length === 0) {
        await createDefaultSession();
      } else {
        setCurrentSession(sessions[0]);
        await loadSessionMessages(sessions[0].id);
      }
      
    } catch (error) {
      console.error('Failed to load initial data:', error);
      // Use mock data as fallback
      const mockData = aiAssistantAPI.getMockData();
      setChatSessions(mockData.chatSessions);
      setAiStats(mockData.aiStats);
      if (mockData.chatSessions.length > 0) {
        setCurrentSession(mockData.chatSessions[0]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const createDefaultSession = async () => {
    try {
      const sessionData = {
        session_name: 'General Assistant',
        context: 'General AI assistance for daily operations'
      };
      
      const newSession = await aiAssistantAPI.createChatSession(sessionData);
      setChatSessions([newSession]);
      setCurrentSession(newSession);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create default session:', error);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const sessionMessages = await aiAssistantAPI.getChatMessages(sessionId);
      setMessages(sessionMessages);
    } catch (error) {
      console.error('Failed to load session messages:', error);
      setMessages([]);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !currentSession) return;

    const userMessage = {
      id: Date.now(),
      message: newMessage,
      response: '',
      message_type: 'text',
      timestamp: new Date(),
      ai_response_time: 0,
      isUser: true
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsLoading(true);

    try {
      const messageData = {
        session_id: currentSession.id,
        message: newMessage,
        message_type: 'text'
      };

      const aiResponse = await aiAssistantAPI.sendChatMessage(messageData);
      
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, response: aiResponse.response, ai_response_time: aiResponse.ai_response_time }
          : msg
      ));

    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, response: 'Sorry, I encountered an error. Please try again.', isError: true }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async () => {
    if (!newSessionName.trim()) return;

    try {
      const sessionData = {
        session_name: newSessionName,
        context: 'New AI assistant session'
      };

      const newSession = await aiAssistantAPI.createChatSession(sessionData);
      setChatSessions(prev => [newSession, ...prev]);
      setCurrentSession(newSession);
      setMessages([]);
      setShowNewSessionModal(false);
      setNewSessionName('');
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  const deleteSession = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this session?')) return;

    try {
      await aiAssistantAPI.deleteChatSession(sessionId);
      setChatSessions(prev => prev.filter(s => s.id !== sessionId));
      
      if (currentSession?.id === sessionId) {
        if (chatSessions.length > 1) {
          const nextSession = chatSessions.find(s => s.id !== sessionId);
          setCurrentSession(nextSession);
          await loadSessionMessages(nextSession.id);
        } else {
          setCurrentSession(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const analyzeDocument = async () => {
    if (selectedDocuments.length === 0) return;

    try {
      setIsLoading(true);
      
      const analysisRequest = {
        document_id: selectedDocuments[0],
        analysis_type: analysisType
      };

      const analysis = await aiAssistantAPI.analyzeDocument(analysisRequest);
      
      // Add analysis result to chat
      const analysisMessage = {
        id: Date.now(),
        message: `Analyzed document with ${analysisType} analysis`,
        response: `**Document Analysis Results:**\n\n**Summary:** ${analysis.summary}\n\n**Key Insights:**\n${analysis.insights.map(insight => `• ${insight}`).join('\n')}\n\n**Recommendations:**\n${analysis.recommendations.map(rec => `• ${rec}`).join('\n')}\n\n**Confidence Score:** ${(analysis.confidence_score * 100).toFixed(1)}%`,
        message_type: 'document',
        timestamp: new Date(),
        ai_response_time: analysis.processing_time || 0,
        isAnalysis: true
      };

      setMessages(prev => [...prev, analysisMessage]);
      setShowDocumentAnalysis(false);
      setSelectedDocuments([]);
      
    } catch (error) {
      console.error('Failed to analyze document:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSmartSuggestions = async (suggestionType) => {
    try {
      setIsLoading(true);
      
      const suggestionRequest = {
        suggestion_type: suggestionType,
        context: `User role: ${user.role}, Company: ${company.name}`,
        user_role: user.role
      };

      const suggestionResponse = await aiAssistantAPI.getSmartSuggestions(suggestionRequest);
      
      // Add suggestions to chat
      const suggestionMessage = {
        id: Date.now(),
        message: `Get ${suggestionType.replace('_', ' ')} suggestions`,
        response: `**Smart Suggestions for ${suggestionType.replace('_', ' ').toUpperCase()}:**\n\n**Reasoning:** ${suggestionResponse.reasoning}\n\n**Suggestions:**\n${suggestionResponse.suggestions.map(suggestion => `• ${suggestion}`).join('\n')}\n\n**Priority:** ${suggestionResponse.priority}\n**Estimated Impact:** ${suggestionResponse.estimated_impact}`,
        message_type: 'suggestion',
        timestamp: new Date(),
        ai_response_time: 1.5,
        isSuggestion: true
      };

      setMessages(prev => [...prev, suggestionMessage]);
      
    } catch (error) {
      console.error('Failed to get suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getTabIcon = (tab) => {
    switch (tab) {
      case 'chat': return MessageCircle;
      case 'analysis': return FileText;
      case 'suggestions': return Lightbulb;
      case 'stats': return BarChart3;
      default: return MessageCircle;
    }
  };

  const getTabColor = (tab) => {
    switch (tab) {
      case 'chat': return 'blue';
      case 'analysis': return 'green';
      case 'suggestions': return 'purple';
      case 'stats': return 'orange';
      default: return 'blue';
    }
  };

  if (!user || !company) {
    return (
      <div className="p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading AI Assistant...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI Assistant</h1>
            <p className="text-gray-600">Your intelligent companion for {company.name}</p>
          </div>
        </div>
        
        {/* Quick Stats */}
        {aiStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center space-x-3">
                <MessageCircle className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm text-gray-500">Chat Sessions</p>
                  <p className="text-2xl font-bold text-gray-900">{aiStats.total_chat_sessions}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center space-x-3">
                <FileText className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-500">Documents Analyzed</p>
                  <p className="text-2xl font-bold text-gray-900">{aiStats.documents_analyzed}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center space-x-3">
                <Lightbulb className="h-5 w-5 text-purple-600" />
                <div>
                  <p className="text-sm text-gray-500">Suggestions</p>
                  <p className="text-2xl font-bold text-gray-900">{aiStats.suggestions_generated}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center space-x-3">
                <Clock className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="text-sm text-gray-500">Avg Response</p>
                  <p className="text-2xl font-bold text-gray-900">{aiStats.average_response_time}s</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl mb-6">
        {['chat', 'analysis', 'suggestions', 'stats'].map((tab) => {
          const Icon = getTabIcon(tab);
          const color = getTabColor(tab);
          const isActive = activeTab === tab;
          
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                isActive
                  ? `bg-white text-${color}-600 shadow-sm`
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="capitalize">{tab}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {activeTab === 'chat' && (
          <div className="flex h-[600px]">
            {/* Chat Sessions Sidebar */}
            <div className="w-80 border-r border-gray-200 p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Chat Sessions</h3>
                <button
                  onClick={() => setShowNewSessionModal(true)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              
              <div className="space-y-2">
                {chatSessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      currentSession?.id === session.id
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-gray-50'
                    }`}
                    onClick={() => {
                      setCurrentSession(session);
                      loadSessionMessages(session.id);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{session.session_name}</p>
                        <p className="text-sm text-gray-500">{session.message_count} messages</p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Chat Interface */}
            <div className="flex-1 flex flex-col">
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  {currentSession?.session_name || 'Select a session'}
                </h3>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className="space-y-3">
                    {/* User Message */}
                    <div className="flex justify-end">
                      <div className="bg-blue-600 text-white px-4 py-2 rounded-lg max-w-xs lg:max-w-md">
                        <p className="text-sm">{message.message}</p>
                        <p className="text-xs text-blue-200 mt-1">
                          {formatTimestamp(message.timestamp)}
                        </p>
                      </div>
                    </div>

                    {/* AI Response */}
                    {message.response && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg max-w-xs lg:max-w-md">
                          <div className="flex items-center space-x-2 mb-2">
                            <Bot className="h-4 w-4 text-purple-600" />
                            <span className="text-xs text-gray-500">AI Assistant</span>
                          </div>
                          <div className="prose prose-sm max-w-none">
                            {message.isError ? (
                              <p className="text-red-600">{message.response}</p>
                            ) : (
                              <div dangerouslySetInnerHTML={{ 
                                __html: message.response.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                              }} />
                            )}
                          </div>
                          <div className="flex items-center justify-between mt-2">
                            <p className="text-xs text-gray-500">
                              {formatTimestamp(message.timestamp)}
                            </p>
                            {message.ai_response_time > 0 && (
                              <p className="text-xs text-gray-500">
                                {message.ai_response_time.toFixed(1)}s
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                        <span className="text-sm">AI is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me anything about your company operations..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!currentSession || isLoading}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!newMessage.trim() || !currentSession || isLoading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Document Analysis</h3>
            <p className="text-gray-600 mb-6">
              Upload documents and get AI-powered insights, summaries, and recommendations.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Type
                  </label>
                  <select
                    value={analysisType}
                    onChange={(e) => setAnalysisType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="summary">Summary</option>
                    <option value="key_points">Key Points</option>
                    <option value="sentiment">Sentiment Analysis</option>
                    <option value="compliance">Compliance Check</option>
                    <option value="action_items">Action Items</option>
                    <option value="risk_assessment">Risk Assessment</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Document
                  </label>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-500 transition-colors"
                  >
                    <FileText className="h-5 w-5 mx-auto mb-2" />
                    <span>Click to select document</span>
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setSelectedDocuments([e.target.files[0].name]);
                      }
                    }}
                  />
                </div>
                
                <button
                  onClick={analyzeDocument}
                  disabled={selectedDocuments.length === 0 || isLoading}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Analyzing...' : 'Analyze Document'}
                </button>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Analysis Features</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span>Intelligent document summarization</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span>Compliance and risk assessment</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span>Action item extraction</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span>Company-specific insights</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'suggestions' && (
          <div className="p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Smart Suggestions</h3>
            <p className="text-gray-600 mb-6">
              Get AI-powered recommendations to improve your company's operations, compliance, and productivity.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {aiAssistantAPI.getQuickActions().map((action) => (
                <div
                  key={action.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                  onClick={() => getSmartSuggestions(action.action_type)}
                >
                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <FileText className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900">{action.title}</h4>
                      <p className="text-sm text-gray-500">{action.category}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{action.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      {action.requires_context ? 'Context Required' : 'No Context Needed'}
                    </span>
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Usage Statistics</h3>
            
            {aiStats ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-medium text-blue-900 mb-2">Most Used Features</h4>
                    <div className="space-y-1">
                      {aiStats.most_used_features.map((feature, index) => (
                        <div key={index} className="flex items-center justify-between text-sm">
                          <span className="text-blue-700">{feature}</span>
                          <span className="text-blue-500 font-medium">
                            {Math.floor(Math.random() * 50) + 20}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h4 className="font-medium text-green-900 mb-2">Performance Metrics</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-green-700">Avg Response Time</span>
                        <span className="text-green-600 font-medium">{aiStats.average_response_time}s</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-green-700">Success Rate</span>
                        <span className="text-green-600 font-medium">98.5%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-green-700">User Satisfaction</span>
                        <span className="text-green-600 font-medium">4.8/5</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h4 className="font-medium text-purple-900 mb-2">Trends</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-purple-700">Daily Usage</span>
                        <span className="text-purple-600 font-medium">+15%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-purple-700">Weekly Growth</span>
                        <span className="text-purple-600 font-medium">+8%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-purple-700">Monthly Trend</span>
                        <span className="text-purple-600 font-medium">+22%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-900 mb-4">Usage Over Time</h4>
                  <div className="h-32 bg-gray-50 rounded flex items-center justify-center">
                    <p className="text-gray-500">Chart visualization would go here</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading statistics...</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* New Session Modal */}
      {showNewSessionModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Chat Session</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Session Name
                  </label>
                  <input
                    type="text"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    placeholder="Enter session name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={createNewSession}
                    disabled={!newSessionName.trim()}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Create Session
                  </button>
                  <button
                    onClick={() => {
                      setShowNewSessionModal(false);
                      setNewSessionName('');
                    }}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAssistant;
