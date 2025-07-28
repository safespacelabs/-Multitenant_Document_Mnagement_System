import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { userManagementAPI } from '../../services/api';

const UserManagement = () => {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    email: '',
    full_name: '',
    role: 'employee'
  });


  const loadUsers = async () => {
    if (user.role === 'system_admin' || !company) {
      setError('System admins cannot access company user management');
      return;
    }
    
    try {
      setLoading(true);
      const response = await userManagementAPI.listUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadInvitations = async () => {
    if (user.role === 'system_admin' || !company) {
      return;
    }
    
    try {
      const response = await userManagementAPI.listInvitations();
      setInvitations(response.data);
    } catch (error) {
      console.error('Failed to load invitations:', error);
    }
  };

  useEffect(() => {
    // Only load user management data for company users, not system admins
    if (user.role !== 'system_admin' && company) {
      loadUsers();
      loadInvitations();
    }
  }, [user.role, company]);

  const handleInviteUser = async (e) => {
    e.preventDefault();
    
    if (user.role === 'system_admin' || !company) {
      alert('System admins cannot invite company users');
      return;
    }
    
    try {
      setLoading(true);
      await userManagementAPI.inviteUser(inviteForm);
      setShowInviteModal(false);
      setInviteForm({ email: '', full_name: '', role: 'employee' });
      loadInvitations();
      alert('Invitation sent successfully!');
    } catch (error) {
      console.error('Failed to send invitation:', error);
      alert('Failed to send invitation: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCancelInvitation = async (invitationId) => {
    if (user.role === 'system_admin' || !company) {
      alert('System admins cannot manage company invitations');
      return;
    }
    
    if (!window.confirm('Are you sure you want to cancel this invitation?')) return;
    
    try {
      await userManagementAPI.cancelInvitation(invitationId);
      loadInvitations();
      alert('Invitation cancelled successfully!');
    } catch (error) {
      console.error('Failed to cancel invitation:', error);
      alert('Failed to cancel invitation');
    }
  };

  const getRoleColor = (role) => {
    const colors = {
      hr_admin: 'bg-purple-100 text-purple-800',
      hr_manager: 'bg-blue-100 text-blue-800',
      employee: 'bg-green-100 text-green-800',
      customer: 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const getAvailableRoles = () => {
    // Based on user role, determine what roles they can assign
    if (user.role === 'hr_admin') {
      return ['hr_manager', 'employee', 'customer'];
    } else if (user.role === 'hr_manager') {
      return ['employee', 'customer'];
    }
    return ['employee'];
  };

  const canManageRole = (targetRole) => {
    const manageable = getAvailableRoles();
    return manageable.includes(targetRole);
  };



  // Redirect system admins to their dedicated management interface
  if (user.role === 'system_admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🔄</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Redirecting...</h1>
          <p className="text-gray-600 mb-4">System administrators should use the dedicated admin management interface.</p>
          <div className="mt-6">
            <a
              href="/system-admins"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Go to System Admin Management
            </a>
          </div>
        </div>
      </div>
    );
  }

  // Require company context for user management
  if (!company) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🏢</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">No Company Context</h1>
          <p className="text-gray-600 mb-4">User management requires a company context.</p>
          <p className="text-sm text-gray-500">Please ensure you're properly logged in to a company.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600 mt-2">Manage user invitations and company users</p>
        </div>

        {/* Action Buttons */}
        <div className="mb-6 flex space-x-4">
          <button
            onClick={() => setShowInviteModal(true)}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Invite New User
          </button>
          <button
            onClick={() => { loadUsers(); loadInvitations(); }}
            className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('users')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Active Users ({users.length})
              </button>
              <button
                onClick={() => setActiveTab('invitations')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'invitations'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Pending Invitations ({invitations.length})
              </button>
            </nav>
          </div>

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="p-6">
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-4 text-gray-600">Loading users...</p>
                </div>
              ) : users.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No users found</p>
                </div>
              ) : (
                <div className="grid gap-4">
                  {users.map((user) => (
                    <div key={user.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-medium text-gray-900">{user.full_name}</h3>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                              {user.role.replace('_', ' ').toUpperCase()}
                            </span>
                            {user.is_active ? (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                Inactive
                              </span>
                            )}
                          </div>
                          <div className="mt-1 text-sm text-gray-600">
                            <p>Username: {user.username}</p>
                            <p>Email: {user.email}</p>
                            <p>S3 Folder: {user.s3_folder}</p>
                            <p>Created: {new Date(user.created_at).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          {canManageRole(user.role) && (
                            <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                              Edit
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Invitations Tab */}
          {activeTab === 'invitations' && (
            <div className="p-6">
              {invitations.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No pending invitations</p>
                </div>
              ) : (
                <div className="grid gap-4">
                  {invitations.map((invitation) => (
                    <div key={invitation.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-medium text-gray-900">{invitation.full_name}</h3>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(invitation.role)}`}>
                              {invitation.role.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                              Pending
                            </span>
                          </div>
                          <div className="mt-1 text-sm text-gray-600">
                            <p>Email: {invitation.email}</p>
                            <p>Invited: {new Date(invitation.created_at).toLocaleString()}</p>
                            <p>Expires: {new Date(invitation.expires_at).toLocaleString()}</p>
                            <p>Unique ID: {invitation.unique_id}</p>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleCancelInvitation(invitation.id)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Invite User Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Invite New User</h3>
                <form onSubmit={handleInviteUser} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={inviteForm.full_name}
                      onChange={(e) => setInviteForm(prev => ({ ...prev, full_name: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={inviteForm.email}
                      onChange={(e) => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role
                    </label>
                    <select
                      value={inviteForm.role}
                      onChange={(e) => setInviteForm(prev => ({ ...prev, role: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {getAvailableRoles().map(role => (
                        <option key={role} value={role}>
                          {role.replace('_', ' ').toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex space-x-3 pt-4">
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading ? 'Sending...' : 'Send Invitation'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowInviteModal(false)}
                      className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}



        {error && (
          <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserManagement; 