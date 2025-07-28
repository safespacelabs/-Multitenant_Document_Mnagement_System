import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { systemAdminAPI } from '../../services/api';
import { 
  Shield, 
  UserPlus, 
  Eye, 
  EyeOff,
  Crown,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader,
  Trash2
} from 'lucide-react';

const SystemAdminManagement = () => {
  const { user } = useAuth();
  const [systemAdmins, setSystemAdmins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);
  
  const [createForm, setCreateForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: ''
  });

  useEffect(() => {
    loadSystemAdmins();
  }, []);

  const loadSystemAdmins = async () => {
    try {
      setLoading(true);
      const response = await systemAdminAPI.list();
      setSystemAdmins(response);
      setError('');
    } catch (err) {
      console.error('Failed to load system admins:', err);
      setError('Failed to load system administrators: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setError('');
    setSuccess('');

    try {
      const adminData = {
        ...createForm,
        role: 'system_admin'
      };
      
      await systemAdminAPI.create(adminData);
      
      // Reset form
      setCreateForm({
        username: '',
        email: '',
        password: '',
        full_name: ''
      });
      setShowCreateForm(false);
      setShowPassword(false);
      
      // Show success message
      setSuccess(`System administrator "${createForm.username}" created successfully! S3 storage has been automatically configured.`);
      
      // Reload list
      await loadSystemAdmins();
      
    } catch (err) {
      setError('Failed to create system admin: ' + err.message);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleFormChange = (e) => {
    setCreateForm({
      ...createForm,
      [e.target.name]: e.target.value
    });
  };

  const confirmDeleteAdmin = (admin) => {
    if (admin.id === user.id) {
      setError('You cannot delete your own admin account.');
      return;
    }
    setConfirmDelete(admin);
  };

  const handleDelete = async (adminId) => {
    setDeleteLoading(adminId);
    setError('');
    setSuccess('');

    try {
      const result = await systemAdminAPI.delete(adminId);
      
      setSuccess(`System administrator deleted successfully! ${result.s3_cleanup ? 'S3 bucket cleaned up. ' : ''}${result.documents_deleted} documents and ${result.chat_history_deleted} chat records removed.`);
      
      // Close confirmation dialog
      setConfirmDelete(null);
      
      // Reload list
      await loadSystemAdmins();
      
    } catch (err) {
      setError('Failed to delete system admin: ' + err.message);
    } finally {
      setDeleteLoading('');
    }
  };

  // Only accessible to system admins
  if (user?.role !== 'system_admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600 mb-4">This page is restricted to system administrators only.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Crown className="h-8 w-8 text-red-500 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">System Administrator Management</h1>
          </div>
          <p className="text-gray-600">
            Manage system administrators and their privileges. New admins will have automatic S3 storage setup.
          </p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <XCircle className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
              <p className="text-sm text-green-800">{success}</p>
            </div>
          </div>
        )}

        {/* Create New Admin Section */}
        <div className="bg-white rounded-lg shadow-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <UserPlus className="h-5 w-5 text-blue-500 mr-2" />
                <h2 className="text-lg font-semibold text-gray-900">Create New System Administrator</h2>
              </div>
              <button
                onClick={() => {
                  setShowCreateForm(!showCreateForm);
                  setError('');
                  setSuccess('');
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {showCreateForm ? 'Cancel' : '+ New Admin'}
              </button>
            </div>
          </div>

          {showCreateForm && (
            <div className="p-6">
              {/* Security Warning */}
              <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start">
                  <AlertTriangle className="h-5 w-5 text-yellow-400 mr-2 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-yellow-800 mb-1">Security Notice</h3>
                    <p className="text-sm text-yellow-700">
                      The new system administrator will have full access to all companies, databases, and system operations.
                      S3 storage will be automatically configured with secure, compliant bucket names.
                    </p>
                  </div>
                </div>
              </div>

              <form onSubmit={handleCreateSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Username *
                    </label>
                    <input
                      type="text"
                      name="username"
                      required
                      value={createForm.username}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter unique username"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      name="full_name"
                      required
                      value={createForm.full_name}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter full name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      name="email"
                      required
                      value={createForm.email}
                      onChange={handleFormChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter email address"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Password *
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        required
                        minLength="8"
                        value={createForm.password}
                        onChange={handleFormChange}
                        className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Enter secure password (min 8 chars)"
                      />
                      <button
                        type="button"
                        className="absolute inset-y-0 right-0 pr-3 flex items-center"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-gray-400" />
                        ) : (
                          <Eye className="h-4 w-4 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Auto-setup Info */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-900 mb-2">
                    Automatic Setup Included:
                  </h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• S3 storage bucket with compliant naming</li>
                    <li>• Secure folder structure creation</li>
                    <li>• Database record with proper configuration</li>
                    <li>• Full system administration privileges</li>
                  </ul>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createLoading}
                    className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {createLoading ? (
                      <>
                        <Loader className="h-4 w-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-2" />
                        Create System Admin
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* Current System Admins */}
        <div className="bg-white rounded-lg shadow-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Users className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Current System Administrators</h2>
              {systemAdmins.length > 0 && (
                <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-sm">
                  {systemAdmins.length}
                </span>
              )}
            </div>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader className="h-6 w-6 animate-spin text-blue-500 mr-2" />
                <span className="text-gray-600">Loading system administrators...</span>
              </div>
            ) : systemAdmins.length === 0 ? (
              <div className="text-center py-8">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No system administrators found.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {systemAdmins.map((admin) => (
                  <div key={admin.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center">
                          <Crown className="h-5 w-5 text-red-500 mr-2" />
                          <h3 className="text-lg font-medium text-gray-900">{admin.full_name}</h3>
                          {admin.id === user.id && (
                            <span className="ml-2 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                              You
                            </span>
                          )}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">
                          <p><strong>Username:</strong> {admin.username}</p>
                          <p><strong>Email:</strong> {admin.email}</p>
                          <p><strong>Created:</strong> {new Date(admin.created_at).toLocaleDateString()}</p>
                          <p><strong>S3 Bucket:</strong> {admin.s3_bucket_name || 'Not configured'}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          admin.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {admin.is_active ? 'Active' : 'Inactive'}
                        </div>
                        
                        {/* Delete button - only show for other admins */}
                        {admin.id !== user.id && (
                          <button
                            onClick={() => confirmDeleteAdmin(admin)}
                            disabled={deleteLoading === admin.id}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Delete Administrator"
                          >
                            {deleteLoading === admin.id ? (
                              <Loader className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Delete Confirmation Dialog */}
        {confirmDelete && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <Trash2 className="h-6 w-6 text-red-600" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-gray-900">
                    Delete System Administrator
                  </h3>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-500 mb-3">
                  Are you sure you want to delete the system administrator:
                </p>
                <div className="bg-gray-50 rounded-md p-3">
                  <div className="flex items-center">
                    <Crown className="h-4 w-4 text-red-500 mr-2" />
                    <div>
                      <p className="font-medium text-gray-900">{confirmDelete.full_name}</p>
                      <p className="text-sm text-gray-600">{confirmDelete.username} • {confirmDelete.email}</p>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <div className="flex items-start">
                    <AlertTriangle className="h-4 w-4 text-yellow-400 mt-0.5 mr-2 flex-shrink-0" />
                    <div className="text-sm text-yellow-800">
                      <p className="font-medium">This action cannot be undone!</p>
                      <ul className="mt-1 list-disc list-inside space-y-1">
                        <li>S3 bucket and all files will be permanently deleted</li>
                        <li>All system documents will be removed</li>
                        <li>Chat history will be deleted</li>
                        <li>Database records will be permanently removed</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setConfirmDelete(null)}
                  disabled={deleteLoading}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(confirmDelete.id)}
                  disabled={deleteLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {deleteLoading === confirmDelete.id ? (
                    <>
                      <Loader className="h-4 w-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Administrator
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemAdminManagement; 