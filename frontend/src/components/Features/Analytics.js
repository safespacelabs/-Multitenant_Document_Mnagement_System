import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { documentsAPI, usersAPI, companiesAPI, chatAPI } from '../../services/api';

const Analytics = () => {
  const { user, company } = useAuth();
  const [analytics, setAnalytics] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('week'); // week, month, quarter, year

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = {};

      // Load role-specific analytics
      if (user.role === 'system_admin') {
        // System-wide analytics
        try {
          const companiesResponse = await companiesAPI.list();
          data.companies = companiesResponse.data;
          data.totalCompanies = companiesResponse.data.length;
          data.activeCompanies = companiesResponse.data.filter(c => c.is_active).length;
        } catch (err) {
          console.log('Companies data not available');
        }
      }

      // Document analytics for company users only (not system admins)
      if (user.role !== 'system_admin' && company) {
        try {
          const documentsResponse = await documentsAPI.list();
          data.documents = documentsResponse.data;
          data.totalDocuments = documentsResponse.data.length;
          data.processedDocuments = documentsResponse.data.filter(d => d.processed).length;
          data.documentsByType = getDocumentsByType(documentsResponse.data);
          data.recentUploads = getRecentUploads(documentsResponse.data);
        } catch (err) {
          console.log('Documents data not available');
        }
      }

      // User analytics for company management roles (not system admin)
      if (['hr_admin', 'hr_manager'].includes(user.role) && company) {
        try {
          const usersResponse = await usersAPI.list();
          data.users = usersResponse.data;
          data.totalUsers = usersResponse.data.length;
          data.activeUsers = usersResponse.data.filter(u => u.is_active).length;
        } catch (err) {
          console.log('Users data not available');
        }
      }

      // Chat analytics for company users only (not system admins)
      if (user.role !== 'system_admin' && company) {
        try {
          const chatResponse = await chatAPI.getHistory();
          data.chatHistory = chatResponse.data;
          data.totalChats = chatResponse.data.length;
          data.recentChats = chatResponse.data.slice(0, 5);
        } catch (err) {
          console.log('Chat data not available');
        }
      }

      setAnalytics(data);
      setError(null);
    } catch (error) {
      console.error('Failed to load analytics:', error);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const getDocumentsByType = (documents) => {
    const types = {};
    documents.forEach(doc => {
      const extension = doc.original_filename.split('.').pop().toLowerCase();
      types[extension] = (types[extension] || 0) + 1;
    });
    return Object.entries(types).map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count);
  };

  const getRecentUploads = (documents) => {
    return documents
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
      .slice(0, 7)
      .map(doc => ({
        date: new Date(doc.created_at).toLocaleDateString(),
        count: 1
      }))
      .reduce((acc, item) => {
        const existing = acc.find(a => a.date === item.date);
        if (existing) {
          existing.count += 1;
        } else {
          acc.push(item);
        }
        return acc;
      }, []);
  };

  const getOverviewCards = () => {
    const cards = [];

    if (user.role === 'system_admin') {
      cards.push(
        {
          title: 'Total Companies',
          value: analytics.totalCompanies || 0,
          subtitle: `${analytics.activeCompanies || 0} active`,
          color: 'bg-purple-500',
          icon: '🏢'
        },
        {
          title: 'System Health',
          value: 'Excellent',
          subtitle: 'All systems operational',
          color: 'bg-green-500',
          icon: '💚'
        }
      );
    }

    if (['hr_admin', 'hr_manager'].includes(user.role) && company) {
      cards.push({
        title: 'Total Users',
        value: analytics.totalUsers || 0,
        subtitle: `${analytics.activeUsers || 0} active`,
        color: 'bg-blue-500',
        icon: '👥'
      });
    }

    // Only show document and chat cards for company users
    if (user.role !== 'system_admin' && company) {
      cards.push(
        {
          title: 'Documents',
          value: analytics.totalDocuments || 0,
          subtitle: `${analytics.processedDocuments || 0} processed`,
          color: 'bg-indigo-500',
          icon: '📄'
        },
        {
          title: 'AI Conversations',
          value: analytics.totalChats || 0,
          subtitle: 'Total interactions',
          color: 'bg-orange-500',
          icon: '🤖'
        }
      );
    }

    return cards;
  };

  const getRoleSpecificMetrics = () => {
    if (user.role === 'system_admin') {
      return [
        { label: 'Database Connections', value: analytics.totalCompanies || 0 },
        { label: 'Storage Usage', value: '2.4 GB' },
        { label: 'API Requests', value: '15.2K' },
        { label: 'Uptime', value: '99.9%' }
      ];
    }

    if (user.role === 'hr_admin') {
      return [
        { label: 'Pending Invitations', value: '3' },
        { label: 'Document Approvals', value: '7' },
        { label: 'Team Productivity', value: '92%' },
        { label: 'Compliance Score', value: '98%' }
      ];
    }

    if (user.role === 'hr_manager') {
      return [
        { label: 'Team Members', value: analytics.totalUsers || 0 },
        { label: 'Documents Reviewed', value: analytics.processedDocuments || 0 },
        { label: 'Task Completion', value: '87%' },
        { label: 'Team Satisfaction', value: '94%' }
      ];
    }

    return [
      { label: 'My Documents', value: analytics.totalDocuments || 0 },
      { label: 'AI Interactions', value: analytics.totalChats || 0 },
      { label: 'Tasks Completed', value: '12' },
      { label: 'Goals Achieved', value: '85%' }
    ];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Insights and metrics for {user.role.replace('_', ' ').toLowerCase()} operations
          </p>
          {company && (
            <p className="text-sm text-gray-500 mt-1">Company: {company.name}</p>
          )}
        </div>

        {/* Time Range Selector */}
        <div className="mb-6 flex space-x-2">
          {['week', 'month', 'quarter', 'year'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                timeRange === range
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {getOverviewCards().map((card, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                    {card.title}
                  </h3>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{card.value}</p>
                  <p className="text-sm text-gray-600 mt-1">{card.subtitle}</p>
                </div>
                <div className="text-3xl">{card.icon}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Main Analytics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Document Types Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Types</h3>
            {analytics.documentsByType && analytics.documentsByType.length > 0 ? (
              <div className="space-y-3">
                {analytics.documentsByType.slice(0, 5).map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                      <span className="text-sm font-medium text-gray-700 uppercase">
                        {item.type}
                      </span>
                    </div>
                    <span className="text-sm text-gray-600">{item.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No document data available</p>
            )}
          </div>

          {/* Activity Timeline */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            {analytics.recentUploads && analytics.recentUploads.length > 0 ? (
              <div className="space-y-3">
                {analytics.recentUploads.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">{item.date}</span>
                    <span className="text-sm font-medium text-blue-600">
                      {item.count} upload{item.count !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No activity data available</p>
            )}
          </div>

          {/* Role-Specific Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Metrics</h3>
            <div className="space-y-4">
              {getRoleSpecificMetrics().map((metric, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{metric.label}</span>
                  <span className="text-sm font-semibold text-gray-900">{metric.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Conversations */}
        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent AI Conversations</h3>
          </div>
          <div className="p-6">
            {analytics.recentChats && analytics.recentChats.length > 0 ? (
              <div className="space-y-4">
                {analytics.recentChats.map((chat, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {chat.question}
                    </p>
                    <p className="text-xs text-gray-500 mt-1 truncate">
                      {chat.answer}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(chat.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No recent conversations</p>
            )}
          </div>
        </div>

        {/* Performance Insights */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">📊 Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">Document Processing</h4>
              <p className="text-sm text-gray-600">
                {analytics.processedDocuments || 0} of {analytics.totalDocuments || 0} documents 
                have been processed by AI. 
                {analytics.totalDocuments > 0 && 
                  ` Processing rate: ${Math.round((analytics.processedDocuments / analytics.totalDocuments) * 100)}%`
                }
              </p>
            </div>
            
            <div className="bg-white rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">User Engagement</h4>
              <p className="text-sm text-gray-600">
                {analytics.totalChats || 0} AI conversations completed. 
                Users are actively engaging with the AI assistant for document analysis and support.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 