import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { authAPI, documentsAPI, usersAPI, companiesAPI } from '../../services/api';
import Header from '../Layout/Header';
import Sidebar from '../Layout/Sidebar';
import CompanyManagement from '../Features/CompanyManagement';
import SystemAdminManagement from '../Features/SystemAdminManagement';
import UserManagement from '../Features/UserManagement';
import DocumentManagement from '../Features/DocumentManagement';
import ChatInterface from '../Features/ChatInterface';
import Analytics from '../Features/Analytics';
import Settings from '../Features/Settings';
import SystemOverview from '../Features/SystemOverview';
import TestingInterface from '../Testing/TestingInterface';
import ESignatureManager from '../ESignature/ESignatureManager';
import { 
  Building2, 
  Users, 
  FileText
} from 'lucide-react';

const Dashboard = () => {
  const { user, company, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  console.log('🏠 Dashboard component rendering...');
  console.log('👤 User:', user);
  console.log('🏢 Company:', company);
  console.log('📍 Location:', location.pathname);

  useEffect(() => {
    // Only load stats if user is authenticated
    if (user && user.username) {
      console.log('👤 User loaded, loading stats...');
      loadQuickStats();
    } else {
      console.log('⏳ Waiting for user to load...');
    }
  }, [user, company]);

  const loadQuickStats = async () => {
    try {
      // Check if user is authenticated
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('❌ No authentication token found, skipping stats load');
        setLoading(false);
        return;
      }
      
      console.log('🔍 Loading quick stats for user:', user.username, 'role:', user.role);
      
      const statsData = {};
      
      // Load documents count (only for company users, not system admins)
      if (user.role !== 'system_admin' && company) {
        try {
          console.log('📄 Loading documents...');
          const documentsResponse = await documentsAPI.list(null);
          // Check if response has data property, otherwise use the response directly
          const documentsData = documentsResponse.data || documentsResponse;
          statsData.documentsCount = Array.isArray(documentsData) ? documentsData.length : 0;
          console.log('✅ Documents loaded:', statsData.documentsCount);
        } catch (err) {
          console.error('❌ Failed to load documents:', err);
          statsData.documentsCount = 0;
        }
      }

      // Load users count for management roles (company-specific, not system admin)
      if (['hr_admin', 'hr_manager'].includes(user.role) && company) {
        try {
          console.log('👥 Loading users...');
          const usersResponse = await usersAPI.list(company.id);
          // Check if response has data property, otherwise use the response directly
          const usersData = usersResponse.data || usersResponse;
          statsData.usersCount = Array.isArray(usersData) ? usersData.length : 0;
          console.log('✅ Users loaded:', statsData.usersCount);
        } catch (err) {
          console.error('❌ Failed to load users:', err);
          statsData.usersCount = 0;
        }
      }

      // Load companies count for system admin
      if (user.role === 'system_admin') {
        try {
          console.log('🏢 Loading companies...');
          const companiesResponse = await companiesAPI.list();
          // Check if response has data property, otherwise use the response directly
          const companiesData = companiesResponse.data || companiesResponse;
          statsData.companiesCount = Array.isArray(companiesData) ? companiesData.length : 0;
          console.log('✅ Companies loaded:', statsData.companiesCount);
        } catch (err) {
          console.error('❌ Failed to load companies:', err);
          statsData.companiesCount = 0;
        }
      }

      setStats(statsData);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const getMenuItems = () => {
    // Determine base path based on user role
    const basePath = user.role === 'system_admin' ? '/system-dashboard' : '/dashboard';
    
    const baseItems = [
      { id: 'overview', name: 'Overview', icon: '📊', path: basePath },
      { id: 'documents', name: 'Documents', icon: '📄', path: `${basePath}/documents` },
      { id: 'esignature', name: 'E-Signature', icon: '✍️', path: `${basePath}/esignature` },
      { id: 'chat', name: 'AI Assistant', icon: '🤖', path: `${basePath}/chat` },
      { id: 'analytics', name: 'Analytics', icon: '📈', path: `${basePath}/analytics` },
      { id: 'settings', name: 'Settings', icon: '⚙️', path: `${basePath}/settings` }
    ];

    // Add role-specific items
    if (user.role === 'system_admin') {
      baseItems.splice(1, 0, { id: 'system-admins', name: 'System Admins', icon: '👑', path: `${basePath}/system-admins` });
      baseItems.splice(2, 0, { id: 'companies', name: 'Companies', icon: '🏢', path: `${basePath}/companies` });
    }

    if (['hr_admin', 'hr_manager'].includes(user.role)) {
      baseItems.splice(2, 0, { id: 'users', name: 'User Management', icon: '👥', path: `${basePath}/users` });
    }

    // Add testing interface
    baseItems.push({ id: 'testing', name: 'Testing', icon: '🧪', path: `${basePath}/testing` });

    return baseItems;
  };

  const getRoleColor = (role) => {
    const colors = {
      system_admin: 'bg-red-100 text-red-800',
      hr_admin: 'bg-purple-100 text-purple-800',
      hr_manager: 'bg-blue-100 text-blue-800',
      employee: 'bg-green-100 text-green-800',
      customer: 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    let greeting;
    
    if (hour < 12) greeting = 'Good morning';
    else if (hour < 17) greeting = 'Good afternoon';
    else greeting = 'Good evening';

    return `${greeting}, ${user.full_name || user.username}!`;
  };

  const isActivePage = (path) => {
    const basePath = user.role === 'system_admin' ? '/system-dashboard' : '/dashboard';
    
    if (path === basePath && location.pathname === basePath) return true;
    if (path !== basePath && location.pathname.startsWith(path)) return true;
    return false;
  };

  const renderMainContent = () => {
    const basePath = user.role === 'system_admin' ? '/system-dashboard' : '/dashboard';
    const currentPath = location.pathname;

    // Overview/Dashboard home
    if (currentPath === basePath) {
      return (
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            {/* Welcome Section */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white mb-8">
              <h2 className="text-2xl font-bold mb-2">{getWelcomeMessage()}</h2>
              <p className="text-blue-100">
                Welcome to your document management dashboard. You have {user.role.replace('_', ' ')} access.
              </p>
              {company && (
                <p className="text-blue-100 mt-1">
                  Managing documents for {company.name}
                </p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {user.role === 'system_admin' ? (
                <>
                  <div
                    onClick={() => navigate('/system-dashboard/companies')}
                    className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <span className="text-2xl">🏢</span>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">Manage Companies</h3>
                        <p className="text-gray-600">Create and configure companies</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/system-dashboard/chat')}
                    className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-green-100 rounded-lg">
                        <span className="text-2xl">🤖</span>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">System Assistant</h3>
                        <p className="text-gray-600">AI assistant for system management</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/system-dashboard/testing')}
                    className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-purple-100 rounded-lg">
                        <span className="text-2xl">🧪</span>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">System Testing</h3>
                        <p className="text-gray-600">Comprehensive system testing</p>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div
                    onClick={() => navigate('/dashboard/documents')}
                    className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <span className="text-2xl">📄</span>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">Upload Documents</h3>
                        <p className="text-gray-600">Add and process your files</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/dashboard/chat')}
                    className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-green-100 rounded-lg">
                        <span className="text-2xl">🤖</span>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">AI Assistant</h3>
                        <p className="text-gray-600">Chat with AI about your documents</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/dashboard/testing')}
                    className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-purple-100 rounded-lg">
                        <span className="text-2xl">🧪</span>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">Test Features</h3>
                        <p className="text-gray-600">Comprehensive system testing</p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* System Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">API Services</span>
                  <span className="text-sm font-medium text-green-600">Operational</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">Database</span>
                  <span className="text-sm font-medium text-green-600">Connected</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">AI Services</span>
                  <span className="text-sm font-medium text-green-600">Available</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // Individual sections
    console.log('🔍 Current path:', currentPath);
    console.log('🔍 Base path:', basePath);
    
    if (currentPath.includes('/system-admins')) {
      console.log('📋 Rendering SystemAdminManagement');
      return <SystemAdminManagement />;
    }
    if (currentPath.includes('/companies')) {
      console.log('🏢 Rendering CompanyManagement');
      return <CompanyManagement />;
    }
    if (currentPath.includes('/users')) {
      console.log('👥 Rendering UserManagement');
      return <UserManagement />;
    }
    if (currentPath.includes('/documents')) {
      console.log('📄 Rendering DocumentManagement');
      return <DocumentManagement />;
    }
    if (currentPath.includes('/esignature')) {
      return (
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            {/* Role-specific E-Signature Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">
                📝 E-Signature Features for {user.role.replace('_', ' ').toUpperCase()}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {user.role === 'system_admin' && (
                  <>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">🔧 System-Wide Management</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• View all company signature requests</li>
                        <li>• Create system-wide policy acknowledgments</li>
                        <li>• Cancel any signature request</li>
                        <li>• Download signed documents from all companies</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">📊 Monitoring & Analytics</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Monitor platform-wide e-signature activity</li>
                        <li>• Track completion rates across companies</li>
                        <li>• Generate system reports</li>
                        <li>• Manage cross-company agreements</li>
                      </ul>
                    </div>
                  </>
                )}
                {user.role === 'hr_admin' && (
                  <>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">👥 HR Administration</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Create policy acknowledgment requests</li>
                        <li>• Send contract approval requests</li>
                        <li>• Manage employee onboarding signatures</li>
                        <li>• Create customer agreement templates</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">🔐 Administrative Controls</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Cancel pending signature requests</li>
                        <li>• Download completed signed documents</li>
                        <li>• View all company signature activity</li>
                        <li>• Set signature request templates</li>
                      </ul>
                    </div>
                  </>
                )}
                {user.role === 'hr_manager' && (
                  <>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">📋 Management Functions</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Create contract approval requests</li>
                        <li>• Send budget approval requests</li>
                        <li>• Create customer agreement requests</li>
                        <li>• Manage team signature workflows</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">👀 Monitoring & Tracking</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• View signature request status</li>
                        <li>• Track team signature completion</li>
                        <li>• Download signed documents</li>
                        <li>• Monitor workflow progress</li>
                      </ul>
                    </div>
                  </>
                )}
                {user.role === 'employee' && (
                  <>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">💼 Employee Functions</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Create budget approval requests</li>
                        <li>• Send customer agreement requests</li>
                        <li>• Request document signatures</li>
                        <li>• View your signature requests</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">📄 Document Management</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Sign received documents</li>
                        <li>• Download signed copies</li>
                        <li>• Track signature status</li>
                        <li>• Manage personal signature requests</li>
                      </ul>
                    </div>
                  </>
                )}
                {user.role === 'customer' && (
                  <>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">🤝 Customer Functions</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Create customer agreement requests</li>
                        <li>• Request document signatures</li>
                        <li>• View your signature requests</li>
                        <li>• Sign received documents</li>
                      </ul>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-200">
                      <h4 className="font-medium text-blue-800 mb-2">📱 Self-Service</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• Download signed documents</li>
                        <li>• Track signature status</li>
                        <li>• Manage personal requests</li>
                        <li>• View signature history</li>
                      </ul>
                    </div>
                  </>
                )}
              </div>
            </div>
            
            {/* How to Use Instructions */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-green-900 mb-3">🚀 How to Use E-Signature</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <div className="text-2xl mb-2">1️⃣</div>
                  <h4 className="font-medium text-green-800 mb-2">Create Request</h4>
                  <p className="text-sm text-green-700">Click "Create Request" or choose from role-specific templates to start a new signature request.</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <div className="text-2xl mb-2">2️⃣</div>
                  <h4 className="font-medium text-green-800 mb-2">Add Recipients</h4>
                  <p className="text-sm text-green-700">Enter recipient details, upload documents, and set signature requirements.</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <div className="text-2xl mb-2">3️⃣</div>
                  <h4 className="font-medium text-green-800 mb-2">Track & Download</h4>
                  <p className="text-sm text-green-700">Monitor signature status and download completed documents when ready.</p>
                </div>
              </div>
            </div>
            
            {/* E-Signature Manager Component */}
            <ESignatureManager userRole={user.role} userId={user.id} />
          </div>
        </div>
      );
    }
    if (currentPath.includes('/chat')) {
      return <ChatInterface />;
    }
    if (currentPath.includes('/analytics')) {
      return <Analytics />;
    }
    if (currentPath.includes('/settings')) {
      return <Settings />;
    }
    if (currentPath.includes('/testing')) {
      return <TestingInterface />;
    }

    // Default fallback
    console.log('⚠️ No matching route found, showing fallback');
    return (
      <div className="p-6">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Page Not Found</h2>
          <p className="text-gray-600">The requested page could not be found.</p>
          <p className="text-sm text-gray-500 mt-2">Current path: {currentPath}</p>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'block' : 'hidden'} lg:block fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg lg:static lg:inset-0`}>
        <div className="flex flex-col h-full">
          {/* Logo/Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">DM</span>
              </div>
              <span className="font-semibold text-gray-900">Document Manager</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* User Info */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium">
                  {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
            </div>
            <div className="mt-2">
              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getRoleColor(user.role)}`}>
                {user.role.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            {company && (
              <div className="mt-2">
                <p className="text-xs text-gray-500">Company: {company.name}</p>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          {!loading && (
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Quick Stats</h3>
              <div className="space-y-2">
                {stats.documentsCount !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Documents</span>
                    <span className="font-medium">{stats.documentsCount || 0}</span>
                  </div>
                )}
                {stats.usersCount !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Users</span>
                    <span className="font-medium">{stats.usersCount}</span>
                  </div>
                )}
                {stats.companiesCount !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Companies</span>
                    <span className="font-medium">{stats.companiesCount}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {getMenuItems().map((item) => (
              <button
                key={item.id}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActivePage(item.path)
                    ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.name}</span>
              </button>
            ))}
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={handleLogout}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              <span>🚪</span>
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600"
              >
                ☰
              </button>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {getWelcomeMessage()}
                </h1>
                <p className="text-sm text-gray-500">
                  {company ? `Managing ${company.name}` : 'Document Management System'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500">
                <span>Last login:</span>
                <span>{new Date().toLocaleDateString()}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-sm text-gray-600">Online</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1">
          {renderMainContent()}
        </main>
      </div>
    </div>
  );
};

export default Dashboard; 