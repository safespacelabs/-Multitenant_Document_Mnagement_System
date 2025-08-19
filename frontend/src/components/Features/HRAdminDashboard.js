import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { hrAdminAPI } from '../../services/api';

const HRAdminDashboard = () => {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [users, setUsers] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userFiles, setUserFiles] = useState(null);
  const [userCredentials, setUserCredentials] = useState(null);
  const [userActivity, setUserActivity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    includeInactive: false,
    roleFilter: '',
    search: ''
  });

  useEffect(() => {
    if (user.role === 'hr_admin' && company) {
      loadCompanyData();
    }
  }, [user.role, company]);

  const loadCompanyData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load users and analytics in parallel
      const [usersResponse, analyticsResponse] = await Promise.all([
        hrAdminAPI.getCompanyUsers(filters),
        hrAdminAPI.getCompanyAnalytics()
      ]);
      
      setUsers(usersResponse.data || []);
      setAnalytics(analyticsResponse.data || {});
    } catch (error) {
      console.error('Failed to load company data:', error);
      setError('Failed to load company data: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = async (userId) => {
    try {
      setLoading(true);
      const [filesResponse, credentialsResponse, activityResponse] = await Promise.all([
        hrAdminAPI.getUserFiles(userId),
        hrAdminAPI.getUserCredentials(userId),
        hrAdminAPI.getUserActivity(userId)
      ]);
      
      setUserFiles(filesResponse.data || {});
      setUserCredentials(credentialsResponse.data || {});
      setUserActivity(activityResponse.data || {});
      setSelectedUser(users.find(u => u.id === userId));
    } catch (error) {
      console.error('Failed to load user details:', error);
      setError('Failed to load user details: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async (userId) => {
    if (!window.confirm('Are you sure you want to reset this user\'s password?')) return;
    
    try {
      setLoading(true);
      await hrAdminAPI.resetUserPassword(userId);
      alert('Password reset successfully. User will need to set a new password.');
      // Refresh user data
      loadCompanyData();
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('Failed to reset password: ' + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleAccountLock = async (userId, lock) => {
    const action = lock ? 'lock' : 'unlock';
    if (!window.confirm(`Are you sure you want to ${action} this user's account?`)) return;
    
    try {
      setLoading(true);
      await hrAdminAPI.lockUserAccount(userId, { lock, reason: `Account ${action}ed by HR admin` });
      alert(`Account ${action}ed successfully.`);
      // Refresh user data
      loadCompanyData();
    } catch (error) {
      console.error(`Failed to ${action} account:`, error);
      alert(`Failed to ${action} account: ` + (error.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (user.role !== 'hr_admin') {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h2 className="text-xl font-semibold text-red-800 mb-2">Access Denied</h2>
            <p className="text-red-600">This dashboard is only accessible to HR administrators.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">HR Admin Dashboard</h1>
              <p className="text-gray-600">Manage company members, files, and access</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Company</p>
              <p className="font-semibold text-gray-900">{company?.name}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Company Overview', icon: '📊' },
              { id: 'users', name: 'All Members', icon: '👥' },
              { id: 'analytics', name: 'Analytics', icon: '📈' },
              { id: 'files', name: 'File Management', icon: '📁' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Content Tabs */}
        {!loading && (
          <>
            {/* Company Overview Tab */}
            {activeTab === 'overview' && analytics && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Users</p>
                      <p className="text-2xl font-semibold text-gray-900">{analytics.total_users}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-green-100 text-green-600">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Active Users</p>
                      <p className="text-2xl font-semibold text-gray-900">{analytics.active_users}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Documents</p>
                      <p className="text-2xl font-semibold text-gray-900">{analytics.total_documents}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                      </svg>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Storage Used</p>
                      <p className="text-2xl font-semibold text-gray-900">{formatFileSize(analytics.total_storage_used)}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* All Members Tab */}
            {activeTab === 'users' && (
              <div className="bg-white rounded-lg shadow">
                {/* Filters */}
                <div className="p-6 border-b border-gray-200">
                  <div className="flex flex-wrap gap-4">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="includeInactive"
                        checked={filters.includeInactive}
                        onChange={(e) => setFilters({...filters, includeInactive: e.target.checked})}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="includeInactive" className="ml-2 text-sm text-gray-700">
                        Include Inactive Users
                      </label>
                    </div>
                    
                    <select
                      value={filters.roleFilter}
                      onChange={(e) => setFilters({...filters, roleFilter: e.target.value})}
                      className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                      <option value="">All Roles</option>
                      <option value="hr_admin">HR Admin</option>
                      <option value="hr_manager">HR Manager</option>
                      <option value="employee">Employee</option>
                      <option value="customer">Customer</option>
                    </select>
                    
                    <input
                      type="text"
                      placeholder="Search by name or email..."
                      value={filters.search}
                      onChange={(e) => setFilters({...filters, search: e.target.value})}
                      className="border border-gray-300 rounded-md px-3 py-2 text-sm w-64"
                    />
                    
                    <button
                      onClick={loadCompanyData}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700"
                    >
                      Apply Filters
                    </button>
                  </div>
                </div>

                {/* Users Table */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          User
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Role
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Documents
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Last Login
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="flex-shrink-0 h-10 w-10">
                                <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                  <span className="text-sm font-medium text-gray-700">
                                    {user.full_name.split(' ').map(n => n[0]).join('')}
                                  </span>
                                </div>
                              </div>
                              <div className="ml-4">
                                <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                                <div className="text-sm text-gray-500">{user.email}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.role === 'hr_admin' ? 'bg-purple-100 text-purple-800' :
                              user.role === 'hr_manager' ? 'bg-blue-100 text-blue-800' :
                              user.role === 'employee' ? 'bg-green-100 text-green-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {user.role.replace('_', ' ').toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {user.documents_count} ({formatFileSize(user.total_documents_size)})
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.last_login ? formatDate(user.last_login) : 'Never'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleUserSelect(user.id)}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                View Details
                              </button>
                              <button
                                onClick={() => handlePasswordReset(user.id)}
                                className="text-yellow-600 hover:text-yellow-900"
                              >
                                Reset Password
                              </button>
                              <button
                                onClick={() => handleAccountLock(user.id, !user.is_active)}
                                className={user.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}
                              >
                                {user.is_active ? 'Lock' : 'Unlock'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && analytics && (
              <div className="space-y-6">
                {/* User Growth Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">User Growth Over Time</h3>
                  <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
                    <p className="text-gray-500">Chart visualization would go here</p>
                  </div>
                </div>

                {/* Document Categories */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Documents by Category</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analytics.document_categories?.map((category, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <h4 className="font-medium text-gray-900">{category.category}</h4>
                        <p className="text-sm text-gray-500">
                          {category.document_count} documents • {formatFileSize(category.total_size)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    {analytics.recent_activity?.slice(0, 10).map((activity, index) => (
                      <div key={index} className="flex items-center space-x-3 text-sm">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-gray-900">{activity.activity_type}</span>
                        <span className="text-gray-500">•</span>
                        <span className="text-gray-500">{formatDate(activity.timestamp)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* File Management Tab */}
            {activeTab === 'files' && selectedUser && userFiles && (
              <div className="space-y-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Files for {selectedUser.full_name}
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-sm text-blue-600">Total Documents</p>
                      <p className="text-2xl font-semibold text-blue-900">{userFiles.total_documents}</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-sm text-green-600">Total Size</p>
                      <p className="text-2xl font-semibold text-green-900">{formatFileSize(userFiles.total_size)}</p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <p className="text-sm text-purple-600">Categories</p>
                      <p className="text-2xl font-semibold text-purple-900">{userFiles.categories.length}</p>
                    </div>
                  </div>

                  {/* Documents Table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            File
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Category
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Size
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Created
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {userFiles.documents.map((doc) => (
                          <tr key={doc.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="flex-shrink-0 h-8 w-8">
                                  <div className="h-8 w-8 rounded bg-gray-100 flex items-center justify-center">
                                    <span className="text-xs text-gray-600">📄</span>
                                  </div>
                                </div>
                                <div className="ml-3">
                                  <div className="text-sm font-medium text-gray-900">{doc.original_filename}</div>
                                  <div className="text-sm text-gray-500">{doc.filename}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {doc.document_category || 'Uncategorized'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {formatFileSize(doc.file_size)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(doc.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                doc.status === 'active' ? 'bg-green-100 text-green-800' :
                                doc.status === 'archived' ? 'bg-gray-100 text-gray-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {doc.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* User Credentials */}
                {userCredentials && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">User Credentials</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">Password Set</p>
                        <p className="font-medium text-gray-900">
                          {userCredentials.password_set ? 'Yes' : 'No'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Account Locked</p>
                        <p className="font-medium text-gray-900">
                          {userCredentials.account_locked ? 'Yes' : 'No'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Login Attempts</p>
                        <p className="font-medium text-gray-900">{userCredentials.login_attempts}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Last Password Change</p>
                        <p className="font-medium text-gray-900">
                          {userCredentials.last_password_change ? formatDate(userCredentials.last_password_change) : 'Never'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* User Activity */}
                {userActivity && (
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                      {userActivity.activities?.slice(0, 10).map((activity, index) => (
                        <div key={index} className="flex items-center space-x-3 text-sm">
                          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          <span className="text-gray-900">{activity.activity_type}</span>
                          <span className="text-gray-500">•</span>
                          <span className="text-gray-500">{formatDate(activity.timestamp)}</span>
                          {activity.ip_address && (
                            <>
                              <span className="text-gray-500">•</span>
                              <span className="text-gray-500">IP: {activity.ip_address}</span>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default HRAdminDashboard;
