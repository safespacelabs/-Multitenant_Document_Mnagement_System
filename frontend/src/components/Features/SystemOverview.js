import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { companiesAPI, usersAPI, documentsAPI } from '../../services/api';
import { Link } from 'react-router-dom';

const SystemOverview = () => {
  const { user, company } = useAuth();
  const [stats, setStats] = useState({});
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refreshData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const statsData = {};
      const activitiesData = [];

      // Load different data based on role
      if (user.role === 'system_admin') {
        // System admin sees all companies and global stats
        const companiesResponse = await companiesAPI.list();
        statsData.totalCompanies = companiesResponse.data.length;
        statsData.activeCompanies = companiesResponse.data.filter(c => c.is_active).length;
        
        // Add company activities
        companiesResponse.data.forEach(comp => {
          activitiesData.push({
            id: comp.id,
            type: 'company',
            title: `Company: ${comp.name}`,
            description: `Database: ${comp.database_name}`,
            time: comp.created_at,
            status: comp.is_active ? 'active' : 'inactive'
          });
        });
      }

      if (user.role !== 'customer') {
        // Load user stats for management roles
        try {
          const userStatsResponse = await usersAPI.getStats();
          Object.assign(statsData, userStatsResponse.data);
        } catch (err) {
          console.log('User stats not available');
        }
      }

      // Company users can see their document stats (not system admins)
      if (user.role !== 'system_admin' && company) {
        try {
          const documentsResponse = await documentsAPI.list();
          statsData.totalDocuments = documentsResponse.data.length;
          statsData.processedDocuments = documentsResponse.data.filter(d => d.processed).length;
          
          // Add recent document activities
          documentsResponse.data.slice(0, 5).forEach(doc => {
            activitiesData.push({
              id: doc.id,
              type: 'document',
              title: `Document: ${doc.original_filename}`,
              description: `Size: ${(doc.file_size / 1024).toFixed(1)} KB`,
              time: doc.created_at,
              status: doc.processed ? 'processed' : 'pending'
            });
          });
        } catch (err) {
          console.log('Document stats not available');
        }
      }

      setStats(statsData);
      setActivities(activitiesData.sort((a, b) => new Date(b.time) - new Date(a.time)).slice(0, 10));
      
    } catch (error) {
      console.error('Failed to load overview data:', error);
      setError('Failed to load overview data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [user.role, company]);

  const getRoleSpecificCards = () => {
    const baseCards = [];
    
    // Only company users can see document stats
    if (user.role !== 'system_admin' && company) {
      baseCards.push({
        title: 'Documents',
        value: stats.totalDocuments || 0,
        subtitle: `${stats.processedDocuments || 0} processed`,
        color: 'bg-blue-500',
        link: '/documents'
      });
    }

    if (user.role === 'system_admin') {
      return [
        {
          title: 'Companies',
          value: stats.totalCompanies || 0,
          subtitle: `${stats.activeCompanies || 0} active`,
          color: 'bg-purple-500',
          link: '/companies'
        },
        {
          title: 'System Health',
          value: 'Operational',
          subtitle: 'All systems running',
          color: 'bg-green-500',
          link: '/testing'
        }
      ];
    }

    if (user.role === 'hr_admin' || user.role === 'hr_manager') {
      return [
        {
          title: 'Users',
          value: stats.totalUsers || 0,
          subtitle: `${stats.activeUsers || 0} active`,
          color: 'bg-indigo-500',
          link: '/users'
        },
        ...baseCards,
        {
          title: 'Invitations',
          value: stats.pendingInvitations || 0,
          subtitle: 'Pending responses',
          color: 'bg-yellow-500',
          link: '/users'
        }
      ];
    }

    return [
      ...baseCards,
      {
        title: 'Chat Sessions',
        value: stats.chatSessions || 0,
        subtitle: 'This month',
        color: 'bg-green-500',
        link: '/chat'
      }
    ];
  };

  const getRoleWelcomeMessage = () => {
    const messages = {
      system_admin: {
        title: 'System Administrator Dashboard',
        description: 'Manage companies, monitor system health, and oversee the entire platform.'
      },
      hr_admin: {
        title: 'HR Administrator Dashboard',
        description: 'Manage users, oversee document processing, and maintain company operations.'
      },
      hr_manager: {
        title: 'HR Manager Dashboard',
        description: 'Supervise employees and customers, manage documents and user activities.'
      },
      employee: {
        title: 'Employee Dashboard',
        description: 'Upload documents, use AI chat assistance, and manage your profile.'
      },
      customer: {
        title: 'Customer Portal',
        description: 'Access your documents and get AI-powered assistance.'
      }
    };

    return messages[user.role] || messages.customer;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading overview...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center text-red-600">
          <p className="text-xl font-semibold">Error</p>
          <p>{error}</p>
          <button 
            onClick={refreshData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const welcomeMessage = getRoleWelcomeMessage();
  const cards = getRoleSpecificCards();

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">{welcomeMessage.title}</h1>
          <p className="text-gray-600 mt-2">{welcomeMessage.description}</p>
          {company && (
            <p className="text-sm text-gray-500 mt-1">Company: {company.name}</p>
          )}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {cards.map((card, index) => (
            <Link
              key={index}
              to={card.link}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6 border-l-4 border-opacity-75"
              style={{ borderLeftColor: card.color.replace('bg-', '').replace('-500', '') }}
            >
              <div className="flex items-center">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                    {card.title}
                  </h3>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{card.value}</p>
                  <p className="text-sm text-gray-600 mt-1">{card.subtitle}</p>
                </div>
                <div className={`p-3 rounded-full ${card.color} bg-opacity-10`}>
                  <div className={`w-6 h-6 ${card.color} rounded-full`}></div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          </div>
          <div className="p-6">
            {activities.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No recent activity</p>
            ) : (
              <div className="space-y-4">
                {activities.map((activity) => (
                  <div key={activity.id} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
                    <div className={`w-3 h-3 rounded-full ${
                      activity.status === 'active' || activity.status === 'processed' 
                        ? 'bg-green-500' 
                        : activity.status === 'pending' 
                        ? 'bg-yellow-500' 
                        : 'bg-gray-400'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                      <p className="text-xs text-gray-500">{activity.description}</p>
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(activity.time).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {user.role === 'system_admin' && (
              <>
                <Link
                  to="/system-admins"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
                >
                  <div className="text-red-500 font-semibold">Manage System Admins</div>
                  <div className="text-sm text-gray-600 mt-1">Create and manage administrators</div>
                </Link>
                <Link
                  to="/companies"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
                >
                  <div className="text-purple-500 font-semibold">Manage Companies</div>
                  <div className="text-sm text-gray-600 mt-1">Create and oversee companies</div>
                </Link>
              </>
            )}
            
            {(user.role === 'hr_admin' || user.role === 'hr_manager') && (
              <Link
                to="/users"
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
              >
                <div className="text-indigo-500 font-semibold">Invite Users</div>
                <div className="text-sm text-gray-600 mt-1">Send user invitations</div>
              </Link>
            )}
            
            <Link
              to="/documents"
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
            >
              <div className="text-blue-500 font-semibold">Upload Document</div>
              <div className="text-sm text-gray-600 mt-1">Add and process files</div>
            </Link>
            
            <Link
              to="/testing"
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center"
            >
              <div className="text-green-500 font-semibold">Test Features</div>
              <div className="text-sm text-gray-600 mt-1">Comprehensive testing interface</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview; 