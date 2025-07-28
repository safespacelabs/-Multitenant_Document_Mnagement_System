import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { authAPI, userManagementAPI } from '../../services/api';
import { 
  Settings as SettingsIcon, 
  User, 
  Shield, 
  Bell, 
  Database,
  Key,
  Eye,
  EyeOff,
  Save,
  RefreshCw
} from 'lucide-react';

function Settings() {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [permissions, setPermissions] = useState([]);
  
  // Profile settings
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || '',
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  
  // Security settings
  const [securityForm, setSecurityForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  
  // System settings (for admins)
  const [systemSettings, setSystemSettings] = useState({
    company_name: company?.name || '',
    company_email: company?.email || '',
    max_file_size: '50',
    allowed_file_types: 'pdf,doc,docx,txt,jpg,png,gif,csv,xlsx,xls',
    auto_process_documents: true,
    enable_ai_chat: true,
    session_timeout: '30'
  });

  useEffect(() => {
    // Only load permissions for company users, not system admins
    if (user.role !== 'system_admin' && company) {
      loadPermissions();
    }
  }, [user.role, company]);

  const loadPermissions = async () => {
    if (user.role === 'system_admin' || !company) {
      // Don't load company permissions for system admins
      return;
    }
    
    try {
      const response = await userManagementAPI.getPermissions();
      setPermissions(response.data);
    } catch (error) {
      console.error('Failed to load permissions:', error);
    }
  };

  const showMessage = (msg, type = 'success') => {
    setMessage({ text: msg, type });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      // Note: This would need an actual update profile endpoint
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      showMessage('Profile updated successfully!');
    } catch (error) {
      console.error('Failed to update profile:', error);
      showMessage('Failed to update profile', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (securityForm.new_password !== securityForm.confirm_password) {
      showMessage('New passwords do not match', 'error');
      return;
    }
    
    if (securityForm.new_password.length < 8) {
      showMessage('Password must be at least 8 characters long', 'error');
      return;
    }

    try {
      setLoading(true);
      // Note: This would need an actual change password endpoint
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      setSecurityForm({ current_password: '', new_password: '', confirm_password: '' });
      showMessage('Password changed successfully!');
    } catch (error) {
      console.error('Failed to change password:', error);
      showMessage('Failed to change password', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSystemUpdate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      // Note: This would need actual system settings endpoints
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      showMessage('System settings updated successfully!');
    } catch (error) {
      console.error('Failed to update system settings:', error);
      showMessage('Failed to update system settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getAvailableTabs = () => {
    const tabs = [
      { id: 'profile', name: 'Profile', icon: '👤' },
      { id: 'notifications', name: 'Notifications', icon: '📧' },
      { id: 'security', name: 'Security', icon: '🔒' },
      { id: 'permissions', name: 'Permissions', icon: '🛡️' }
    ];

    // Add system tab for admins
    if (['system_admin', 'hr_admin'].includes(user.role)) {
      tabs.push({ id: 'system', name: 'System', icon: '⚙️' });
    }

    return tabs;
  };

  const renderProfile = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              value={profileForm.full_name}
              onChange={(e) => setProfileForm(prev => ({ ...prev, full_name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={profileForm.username}
              onChange={(e) => setProfileForm(prev => ({ ...prev, username: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
            <input
              type="text"
              value={user?.role?.replace('_', ' ').toUpperCase()}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
            />
          </div>

          {company && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Company</label>
              <input
                type="text"
                value={company.name}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={profileForm.current_password}
                onChange={(e) => setProfileForm(prev => ({ ...prev, current_password: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              value={profileForm.new_password}
              onChange={(e) => setProfileForm(prev => ({ ...prev, new_password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              value={profileForm.confirm_password}
              onChange={(e) => setProfileForm(prev => ({ ...prev, confirm_password: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={handleProfileUpdate}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <Save className="h-4 w-4 mr-2" />
          {loading ? 'Updating...' : 'Update Profile'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-2">
            Manage your account, security, and system preferences
          </p>
          {company && (
            <p className="text-sm text-gray-500 mt-1">Company: {company.name}</p>
          )}
        </div>

        {/* Message Display */}
        {message && (
          <div className={`mb-6 p-4 rounded border ${
            message.type === 'error' 
              ? 'bg-red-100 border-red-400 text-red-700' 
              : 'bg-green-100 border-green-400 text-green-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Settings Container */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {getAvailableTabs().map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="max-w-2xl">
                <h3 className="text-lg font-medium text-gray-900 mb-6">Profile Information</h3>
                <form onSubmit={handleProfileUpdate} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, full_name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        value={profileForm.username}
                        onChange={(e) => setProfileForm(prev => ({ ...prev, username: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Account Information</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Role:</span>
                        <span className="ml-2 font-medium">{user.role.replace('_', ' ').toUpperCase()}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Member Since:</span>
                        <span className="ml-2 font-medium">
                          {new Date(user.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">User ID:</span>
                        <span className="ml-2 font-medium text-xs">{user.id}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Status:</span>
                        <span className="ml-2">
                          <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                            Active
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading ? 'Updating...' : 'Update Profile'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="max-w-2xl">
                <h3 className="text-lg font-medium text-gray-900 mb-6">Security Settings</h3>
                
                {/* Change Password */}
                <div className="mb-8">
                  <h4 className="font-medium text-gray-900 mb-4">Change Password</h4>
                  <form onSubmit={handlePasswordChange} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Current Password
                      </label>
                      <input
                        type="password"
                        value={securityForm.current_password}
                        onChange={(e) => setSecurityForm(prev => ({ ...prev, current_password: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={securityForm.new_password}
                        onChange={(e) => setSecurityForm(prev => ({ ...prev, new_password: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={securityForm.confirm_password}
                        onChange={(e) => setSecurityForm(prev => ({ ...prev, confirm_password: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50"
                      >
                        {loading ? 'Changing...' : 'Change Password'}
                      </button>
                    </div>
                  </form>
                </div>

                {/* Security Options */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-4">Security Options</h4>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <h5 className="font-medium text-gray-900">Two-Factor Authentication</h5>
                        <p className="text-sm text-gray-600">Add an extra layer of security to your account</p>
                      </div>
                      <button className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 text-sm">
                        Enable
                      </button>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <h5 className="font-medium text-gray-900">Login Notifications</h5>
                        <p className="text-sm text-gray-600">Get notified of new login attempts</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" defaultChecked />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Permissions Tab */}
            {activeTab === 'permissions' && (
              <div className="max-w-4xl">
                <h3 className="text-lg font-medium text-gray-900 mb-6">Your Permissions</h3>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center">
                    <div className="text-blue-400 mr-3">ℹ️</div>
                    <div>
                      <h4 className="font-medium text-blue-900">Role: {user.role.replace('_', ' ').toUpperCase()}</h4>
                      <p className="text-sm text-blue-800">
                        Your permissions are determined by your role and cannot be changed by yourself.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {permissions.length > 0 ? permissions.map((permission, index) => (
                    <div key={index} className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="text-green-500 mr-3">✓</div>
                      <span className="text-sm font-medium text-green-800">
                        {permission.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  )) : (
                    <div className="col-span-2 text-center py-8 text-gray-500">
                      <p>No permissions data available</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* System Tab (Admin only) */}
            {activeTab === 'system' && ['system_admin', 'hr_admin'].includes(user.role) && (
              <div className="max-w-4xl">
                <h3 className="text-lg font-medium text-gray-900 mb-6">System Configuration</h3>
                
                <form onSubmit={handleSystemUpdate} className="space-y-8">
                  {/* Company Settings */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-4">Company Settings</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Name
                        </label>
                        <input
                          type="text"
                          value={systemSettings.company_name}
                          onChange={(e) => setSystemSettings(prev => ({ ...prev, company_name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Company Email
                        </label>
                        <input
                          type="email"
                          value={systemSettings.company_email}
                          onChange={(e) => setSystemSettings(prev => ({ ...prev, company_email: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Document Settings */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-4">Document Settings</h4>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Maximum File Size (MB)
                        </label>
                        <input
                          type="number"
                          value={systemSettings.max_file_size}
                          onChange={(e) => setSystemSettings(prev => ({ ...prev, max_file_size: e.target.value }))}
                          className="w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Allowed File Types
                        </label>
                        <input
                          type="text"
                          value={systemSettings.allowed_file_types}
                          onChange={(e) => setSystemSettings(prev => ({ ...prev, allowed_file_types: e.target.value }))}
                          placeholder="pdf,doc,docx,txt,jpg,png"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Comma-separated list of file extensions</p>
                      </div>
                    </div>
                  </div>

                  {/* System Features */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-4">System Features</h4>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <h5 className="font-medium text-gray-900">Auto-Process Documents</h5>
                          <p className="text-sm text-gray-600">Automatically process uploaded documents with AI</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input 
                            type="checkbox" 
                            className="sr-only peer"
                            checked={systemSettings.auto_process_documents}
                            onChange={(e) => setSystemSettings(prev => ({ ...prev, auto_process_documents: e.target.checked }))}
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div>
                          <h5 className="font-medium text-gray-900">Enable AI Chat</h5>
                          <p className="text-sm text-gray-600">Allow users to chat with AI assistant</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input 
                            type="checkbox" 
                            className="sr-only peer"
                            checked={systemSettings.enable_ai_chat}
                            onChange={(e) => setSystemSettings(prev => ({ ...prev, enable_ai_chat: e.target.checked }))}
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={loading}
                      className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading ? 'Updating...' : 'Update System Settings'}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings; 