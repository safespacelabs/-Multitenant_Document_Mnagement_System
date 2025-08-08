import React, { useState, useEffect } from 'react';
import { userManagementAPI, usersAPI } from '../../services/api';
import { useAuth } from '../../utils/auth';
import { 
  Users, 
  UserPlus, 
  Mail, 
  Shield, 
  Calendar, 
  Settings,
  Eye,
  EyeOff,
  Trash2,
  Edit3,
  CheckCircle,
  Clock,
  AlertTriangle,
  Search,
  Filter,
  MoreVertical,
  Crown,
  UserCog,
  Briefcase,
  User as UserIcon
} from 'lucide-react';

function UserManagement({ companyId, onClose }) {
  const [users, setUsers] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [permissions, setPermissions] = useState([]);
  const { user: currentUser } = useAuth();

  // Invite form state
  const [inviteForm, setInviteForm] = useState({
    email: '',
    full_name: '',
    role: 'customer'
  });

  // Edit form state
  const [editForm, setEditForm] = useState({
    role: '',
    is_active: true
  });

  const roleConfig = {
    hr_admin: {
      label: 'HR Admin',
      icon: Crown,
      color: 'text-purple-600 bg-purple-100',
      description: 'Full admin access, can manage all users'
    },
    hr_manager: {
      label: 'HR Manager', 
      icon: UserCog,
      color: 'text-blue-600 bg-blue-100',
      description: 'Can manage employees and customers'
    },
    employee: {
      label: 'Employee',
      icon: Briefcase,
      color: 'text-green-600 bg-green-100', 
      description: 'Can manage customers'
    },
    customer: {
      label: 'Customer',
      icon: UserIcon,
      color: 'text-gray-600 bg-gray-100',
      description: 'Basic access only'
    }
  };

  useEffect(() => {
    if (companyId) {
      fetchData();
    }
  }, [companyId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Use different endpoints for system admins
      const isSystemAdmin = currentUser?.role === 'system_admin';
      
      let usersResponse, invitationsResponse, permissionsResponse;
      
      if (isSystemAdmin && companyId) {
        // System admin endpoints with company ID in path
        [usersResponse, invitationsResponse, permissionsResponse] = await Promise.all([
          usersAPI.list(companyId),
          userManagementAPI.listInvitations(companyId),
          userManagementAPI.getPermissions()
        ]);
      } else {
        // Regular company user endpoints
        [usersResponse, invitationsResponse, permissionsResponse] = await Promise.all([
          usersAPI.list(companyId),
          userManagementAPI.listInvitations(companyId),
          userManagementAPI.getPermissions()
        ]);
      }

      setUsers(usersResponse);
      setInvitations(invitationsResponse);
      setPermissions(permissionsResponse);
    } catch (err) {
      setError('Failed to fetch user data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async (e) => {
    e.preventDefault();
    try {
      await userManagementAPI.inviteUser(inviteForm, companyId);
      setShowInviteModal(false);
      setInviteForm({ email: '', full_name: '', role: 'customer' });
      await fetchData();
    } catch (err) {
      setError(err.message || 'Failed to invite user');
    }
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    try {
      await userManagementAPI.updateUser(selectedUser.id, editForm, companyId);
      setShowEditModal(false);
      setSelectedUser(null);
      await fetchData();
    } catch (err) {
      setError(err.message || 'Failed to update user');
    }
  };

  const handleCancelInvitation = async (invitationId) => {
    if (!window.confirm('Are you sure you want to cancel this invitation?')) return;
    
    try {
      await userManagementAPI.cancelInvitation(invitationId, companyId);
      await fetchData();
    } catch (err) {
      setError(err.message || 'Failed to cancel invitation');
    }
  };

  const handleDeactivateUser = async (userId) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;
    
    try {
      await userManagementAPI.updateUser(userId, { is_active: false }, companyId);
      await fetchData();
    } catch (err) {
      setError(err.message || 'Failed to deactivate user');
    }
  };

  const canInviteRole = (targetRole) => {
    const currentRole = currentUser?.role;
    
    // System admins can invite any company role
    if (currentRole === 'system_admin') {
      const companyRoles = ['hr_admin', 'hr_manager', 'employee', 'customer'];
      return companyRoles.includes(targetRole);
    }
    
    const hierarchy = {
      hr_admin: ['hr_manager', 'employee', 'customer'],
      hr_manager: ['employee', 'customer'],
      employee: ['customer'],
      customer: []
    };
    return hierarchy[currentRole]?.includes(targetRole) || false;
  };

  const canManageUser = (targetUser) => {
    if (targetUser.id === currentUser?.id) return false; // Can't manage self
    return canInviteRole(targetUser.role);
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.username.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'all' || user.role === filterRole;
    return matchesSearch && matchesRole;
  });

  const availableRoles = Object.keys(roleConfig).filter(role => canInviteRole(role));

  if (loading) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-8 border w-full max-w-6xl shadow-lg rounded-lg bg-white min-h-96">
          <div className="flex items-center justify-center min-h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading user data...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-8 border w-full max-w-7xl shadow-lg rounded-lg bg-white min-h-screen">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
              <p className="text-sm text-gray-600">Company ID: {companyId}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {availableRoles.length > 0 && (
              <button
                onClick={() => setShowInviteModal(true)}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Invite User
              </button>
            )}
            <button
              onClick={onClose}
              className="inline-flex items-center px-4 py-2 bg-gray-200 text-gray-800 text-sm font-medium rounded-lg hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Search and Filter */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search users by name, email, or username..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Roles</option>
              {Object.entries(roleConfig).map(([role, config]) => (
                <option key={role} value={role}>{config.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="w-8 h-8 text-blue-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Users</p>
                <p className="text-2xl font-semibold text-gray-900">{users.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="w-8 h-8 text-yellow-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Pending Invites</p>
                <p className="text-2xl font-semibold text-gray-900">{invitations.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Active Users</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {users.filter(u => u.is_active).length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Crown className="w-8 h-8 text-purple-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Admins</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {users.filter(u => u.role === 'hr_admin').length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Company Users</h3>
          </div>
          
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
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((user) => {
                  const RoleIcon = roleConfig[user.role]?.icon || UserIcon;
                  return (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <span className="text-sm font-medium text-gray-700">
                                {user.full_name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{user.full_name}</div>
                            <div className="text-sm text-gray-500">{user.email}</div>
                            <div className="text-xs text-gray-400">@{user.username}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <RoleIcon className={`w-4 h-4 mr-2 ${roleConfig[user.role]?.color.split(' ')[0]}`} />
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleConfig[user.role]?.color}`}>
                            {roleConfig[user.role]?.label}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? (
                            <>
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Active
                            </>
                          ) : (
                            <>
                              <EyeOff className="w-3 h-3 mr-1" />
                              Inactive
                            </>
                          )}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1 text-gray-400" />
                          {new Date(user.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          {canManageUser(user) && (
                            <>
                              <button
                                onClick={() => {
                                  setSelectedUser(user);
                                  setEditForm({ role: user.role, is_active: user.is_active });
                                  setShowEditModal(true);
                                }}
                                className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded hover:bg-blue-100 transition-colors"
                              >
                                <Edit3 className="w-3 h-3 mr-1" />
                                Edit
                              </button>
                              {user.is_active && (
                                <button
                                  onClick={() => handleDeactivateUser(user.id)}
                                  className="inline-flex items-center px-3 py-1 bg-red-50 text-red-700 text-xs font-medium rounded hover:bg-red-100 transition-colors"
                                >
                                  <EyeOff className="w-3 h-3 mr-1" />
                                  Deactivate
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Invitations */}
        {invitations.length > 0 && (
          <div className="mt-8 bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-6 py-3 bg-yellow-50 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <Clock className="w-5 h-5 mr-2 text-yellow-600" />
                Pending Invitations
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invited User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invited Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expires
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {invitations.map((invitation) => {
                    const RoleIcon = roleConfig[invitation.role]?.icon || UserIcon;
                    const isExpired = new Date(invitation.expires_at) < new Date();
                    
                    return (
                      <tr key={invitation.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
                                <Mail className="w-5 h-5 text-yellow-600" />
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">{invitation.full_name}</div>
                              <div className="text-sm text-gray-500">{invitation.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <RoleIcon className={`w-4 h-4 mr-2 ${roleConfig[invitation.role]?.color.split(' ')[0]}`} />
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleConfig[invitation.role]?.color}`}>
                              {roleConfig[invitation.role]?.label}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(invitation.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            isExpired ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {isExpired ? 'Expired' : new Date(invitation.expires_at).toLocaleDateString()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => handleCancelInvitation(invitation.id)}
                            className="inline-flex items-center px-3 py-1 bg-red-50 text-red-700 text-xs font-medium rounded hover:bg-red-100 transition-colors"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Cancel
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Invite User Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-60">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-lg bg-white">
              <div className="mt-3">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                  <UserPlus className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mt-4 text-center">Invite New User</h3>
                
                <form onSubmit={handleInviteUser} className="mt-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={inviteForm.full_name}
                      onChange={(e) => setInviteForm({...inviteForm, full_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter full name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      value={inviteForm.email}
                      onChange={(e) => setInviteForm({...inviteForm, email: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="user@example.com"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role *
                    </label>
                    <select
                      required
                      value={inviteForm.role}
                      onChange={(e) => setInviteForm({...inviteForm, role: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {availableRoles.map(role => (
                        <option key={role} value={role}>
                          {roleConfig[role].label} - {roleConfig[role].description}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowInviteModal(false);
                        setInviteForm({ email: '', full_name: '', role: 'customer' });
                      }}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Send Invitation
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Edit User Modal */}
        {showEditModal && selectedUser && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-60">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-lg bg-white">
              <div className="mt-3">
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                  <Edit3 className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mt-4 text-center">
                  Edit User: {selectedUser.full_name}
                </h3>
                
                <form onSubmit={handleEditUser} className="mt-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role *
                    </label>
                    <select
                      required
                      value={editForm.role}
                      onChange={(e) => setEditForm({...editForm, role: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {availableRoles.concat([selectedUser.role]).filter((role, index, self) => self.indexOf(role) === index).map(role => (
                        <option key={role} value={role}>
                          {roleConfig[role].label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={editForm.is_active}
                      onChange={(e) => setEditForm({...editForm, is_active: e.target.checked})}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                      Active User
                    </label>
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowEditModal(false);
                        setSelectedUser(null);
                      }}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Update User
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserManagement; 