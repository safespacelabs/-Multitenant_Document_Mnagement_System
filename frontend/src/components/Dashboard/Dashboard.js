import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { authAPI, documentsAPI, usersAPI, companiesAPI } from '../../services/api';
import { EnhancedDocumentManager } from '../Documents';
import ChatInterface from '../Features/ChatInterface';
import Analytics from '../Features/Analytics';
import Settings from '../Features/Settings';
import SystemOverview from '../Features/SystemOverview';
import TestingInterface from '../Testing/TestingInterface';
import ESignatureManager from '../ESignature/ESignatureManager';
import { 
  Search,
  Bell,
  MessageCircle,
  Headphones,
  Star,
  ChevronDown,
  Menu,
  X,
  Home,
  FileText,
  Users,
  BarChart3,
  Settings as SettingsIcon,
  FileSignature,
  Building2,
  Crown,
  LogOut,
  User,
  Calendar,
  Clock,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Plus
} from 'lucide-react';

const Dashboard = () => {
  const { user, company, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchResults, setSearchResults] = useState({ employees: [], documents: [] });

  console.log('🏠 Dashboard component rendering...');
  console.log('👤 User:', user);
  console.log('🏢 Company:', company);
  console.log('📍 Location:', location.pathname);

  useEffect(() => {
    if (user && user.username) {
      console.log('👤 User loaded, loading stats...');
      loadQuickStats();
      loadNotifications();
    } else {
      console.log('⏳ Waiting for user to load...');
    }
  }, [user, company]);

  const loadQuickStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('❌ No authentication token found, skipping stats load');
        setLoading(false);
        return;
      }
      
      console.log('🔍 Loading quick stats for user:', user.username, 'role:', user.role);
      
      const statsData = {};
      
      if (user.role !== 'system_admin' && company) {
        try {
          console.log('📄 Loading documents...');
          const documentsResponse = await documentsAPI.list(null);
          const documentsData = documentsResponse.data || documentsResponse;
          statsData.documentsCount = Array.isArray(documentsData) ? documentsData.length : 0;
          console.log('✅ Documents loaded:', statsData.documentsCount);
        } catch (err) {
          console.error('❌ Failed to load documents:', err);
          statsData.documentsCount = 0;
        }
      }

      if (['hr_admin', 'hr_manager'].includes(user.role) && company) {
        try {
          console.log('👥 Loading users...');
          const usersResponse = await usersAPI.list(company.id);
          const usersData = usersResponse.data || usersResponse;
          statsData.usersCount = Array.isArray(usersData) ? usersData.length : 0;
          console.log('✅ Users loaded:', statsData.usersCount);
        } catch (err) {
          console.error('❌ Failed to load users:', err);
          statsData.usersCount = 0;
        }
      }

      if (user.role === 'system_admin') {
        try {
          console.log('🏢 Loading companies...');
          const companiesResponse = await companiesAPI.list();
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

  const loadNotifications = () => {
    // Mock notifications - in real app, fetch from API
    const mockNotifications = [
      { id: 1, type: 'info', message: 'New document uploaded', time: '2 min ago' },
      { id: 2, type: 'warning', message: 'Pending signature request', time: '1 hour ago' },
      { id: 3, type: 'success', message: 'Document signed successfully', time: '3 hours ago' }
    ];
    setNotifications(mockNotifications);
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setShowSearchResults(false);
      return;
    }

    try {
      // Mock search results - in real app, implement actual search API calls
      const results = {
        employees: [
          { id: 1, name: 'John Doe', role: 'HR Manager', department: 'HR' },
          { id: 2, name: 'Jane Smith', role: 'Employee', department: 'Engineering' }
        ],
        documents: [
          { id: 1, name: 'Employee Handbook.pdf', type: 'PDF', size: '2.3 MB' },
          { id: 2, name: 'Company Policy.docx', type: 'DOCX', size: '1.1 MB' }
        ]
      };
      
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search failed:', error);
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
    const basePath = user.role === 'system_admin' ? '/system-dashboard' : '/dashboard';
    
    const baseItems = [
      { id: 'overview', name: 'Overview', icon: Home, path: basePath, color: 'blue' },
      { id: 'documents', name: 'Documents', icon: FileText, path: `${basePath}/documents`, color: 'green' },
      { id: 'esignature', name: 'E-Signature', icon: FileSignature, path: `${basePath}/esignature`, color: 'purple' },
      { id: 'chat', name: 'AI Assistant', icon: MessageCircle, path: `${basePath}/chat`, color: 'indigo' },
      { id: 'analytics', name: 'Analytics', icon: BarChart3, path: `${basePath}/analytics`, color: 'orange' },
      { id: 'settings', name: 'Settings', icon: SettingsIcon, path: `${basePath}/settings`, color: 'gray' }
    ];

    if (user.role === 'system_admin') {
      baseItems.splice(1, 0, { id: 'system-admins', name: 'System Admins', icon: Crown, path: `${basePath}/system-admins`, color: 'red' });
      baseItems.splice(2, 0, { id: 'companies', name: 'Companies', icon: Building2, path: `${basePath}/companies`, color: 'teal' });
    }

    if (['hr_admin', 'hr_manager'].includes(user.role)) {
      baseItems.splice(2, 0, { id: 'users', name: 'User Management', icon: Users, path: `${basePath}/users`, color: 'pink' });
    }

    baseItems.push({ id: 'testing', name: 'Testing', icon: SettingsIcon, path: `${basePath}/testing`, color: 'yellow' });

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

    return `${greeting}!`;
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

    if (currentPath === basePath) {
      return (
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            {/* Hero Banner */}
            <div className="relative bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 rounded-xl p-8 text-white mb-8 overflow-hidden">
              <div className="absolute inset-0 bg-black opacity-10"></div>
              <div className="relative z-10">
                <h2 className="text-4xl font-bold mb-2">{getWelcomeMessage()}</h2>
                <p className="text-xl text-blue-100 mb-4">
                  Welcome back, {user.full_name || user.username}!
                </p>
                <p className="text-blue-100 text-lg">
                  Manage your documents, collaborate with team members, and stay organized.
                </p>
                {company && (
                  <p className="text-blue-100 mt-2 text-lg">
                    Managing documents for <span className="font-semibold">{company.name}</span>
                  </p>
                )}
              </div>
              <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-white/10 to-transparent"></div>
            </div>

            {/* Quick Actions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {user.role === 'system_admin' ? (
                <>
                  <div
                    onClick={() => navigate('/system-dashboard/companies')}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-blue-100 rounded-xl">
                        <Building2 className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">Manage Companies</h3>
                        <p className="text-gray-600">Create and configure companies</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/system-dashboard/chat')}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-green-100 rounded-xl">
                        <MessageCircle className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">System Assistant</h3>
                        <p className="text-gray-600">AI assistant for system management</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/system-dashboard/testing')}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-purple-100 rounded-xl">
                        <SettingsIcon className="h-8 w-8 text-purple-600" />
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
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-blue-100 rounded-xl">
                        <FileText className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">Upload Documents</h3>
                        <p className="text-gray-600">Add and process your files</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/dashboard/chat')}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-green-100 rounded-xl">
                        <MessageCircle className="h-8 w-8 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">AI Assistant</h3>
                        <p className="text-gray-600">Chat with AI about your documents</p>
                      </div>
                    </div>
                  </div>

                  <div
                    onClick={() => navigate('/dashboard/testing')}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-105"
                  >
                    <div className="flex items-center">
                      <div className="p-3 bg-purple-100 rounded-xl">
                        <SettingsIcon className="h-8 w-8 text-purple-600" />
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

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-100 rounded-xl">
                    <FileText className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Documents</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.documentsCount || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-green-100 rounded-xl">
                    <Users className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Team Members</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.usersCount || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="p-3 bg-purple-100 rounded-xl">
                    <Building2 className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Companies</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.companiesCount || 0}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">Document uploaded: Employee Handbook.pdf</span>
                  <span className="text-xs text-gray-400">2 minutes ago</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">New user registered: John Doe</span>
                  <span className="text-xs text-gray-400">1 hour ago</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                  <span className="text-sm text-gray-600">Document signed: Company Policy.docx</span>
                  <span className="text-xs text-gray-400">3 hours ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    console.log('🔍 Current path:', currentPath);
    console.log('🔍 Base path:', basePath);
    
    if (currentPath.includes('/system-admins')) {
      console.log('📋 Rendering SystemAdminManagement');
      return <SystemOverview />;
    }
    if (currentPath.includes('/companies')) {
      console.log('🏢 Rendering CompanyManagement');
      return <SystemOverview />;
    }
    if (currentPath.includes('/users')) {
      console.log('👥 Rendering UserManagement');
      return <SystemOverview />;
    }
    if (currentPath.includes('/documents')) {
      console.log('📄 Rendering EnhancedDocumentManager');
      return <EnhancedDocumentManager />;
    }
    if (currentPath.includes('/esignature')) {
      return (
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
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
            
            <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-6">
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
      {/* Modern Sidebar */}
      <div className={`${sidebarOpen ? 'block' : 'hidden'} lg:block fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg lg:static lg:inset-0`}>
        <div className="flex flex-col h-full">
          {/* Logo/Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">DM</span>
              </div>
              <div>
                <span className="font-bold text-xl text-gray-900">Document Manager</span>
                <p className="text-xs text-gray-500">Enterprise Solution</p>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* User Info */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">
                  {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {user.full_name || user.username}
                </p>
                <p className="text-xs text-gray-500">{user.email}</p>
              </div>
            </div>
            <div className="mt-3">
              <span className={`inline-flex px-3 py-1 text-xs font-medium rounded-full ${getRoleColor(user.role)}`}>
                {user.role.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            {company && (
              <div className="mt-3">
                <p className="text-xs text-gray-500 font-medium">Company: {company.name}</p>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          {!loading && (
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Quick Stats</h3>
              <div className="space-y-3">
                {stats.documentsCount !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Documents</span>
                    <span className="font-semibold text-gray-900">{stats.documentsCount || 0}</span>
                  </div>
                )}
                {stats.usersCount !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Users</span>
                    <span className="font-semibold text-gray-900">{stats.usersCount}</span>
                  </div>
                )}
                {stats.companiesCount !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Companies</span>
                    <span className="font-semibold text-gray-900">{stats.companiesCount}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-6 py-4 space-y-2">
            {getMenuItems().map((item) => {
              const Icon = item.icon;
              const isActive = isActivePage(item.path);
              
              return (
                <button
                  key={item.id}
                  onClick={() => navigate(item.path)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${
                    isActive
                      ? `bg-${item.color}-50 text-${item.color}-700 border border-${item.color}-200 shadow-sm`
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${isActive ? `text-${item.color}-600` : 'text-gray-400'}`} />
                  <span className="font-medium">{item.name}</span>
                </button>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-6 border-t border-gray-200">
            <button
              onClick={handleLogout}
              className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOut className="h-5 w-5" />
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
        {/* Modern Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
              >
                <Menu className="h-6 w-6" />
              </button>
              
              {/* Search Bar */}
              <div className="relative w-96">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search for employees, documents, or actions..."
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-xl leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    handleSearch(e.target.value);
                  }}
                  onFocus={() => setShowSearchResults(true)}
                />
                
                {/* Search Results Dropdown */}
                {showSearchResults && searchQuery && (
                  <div className="absolute z-50 w-full mt-1 bg-white rounded-xl shadow-lg border border-gray-200 max-h-96 overflow-y-auto">
                    <div className="p-4">
                      <h3 className="text-sm font-semibold text-gray-900 mb-3">Search Results</h3>
                      
                      {/* Employees */}
                      {searchResults.employees.length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Employees</h4>
                          <div className="space-y-2">
                            {searchResults.employees.map((employee) => (
                              <div key={employee.id} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                  <User className="h-4 w-4 text-blue-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{employee.name}</p>
                                  <p className="text-xs text-gray-500">{employee.role} • {employee.department}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Documents */}
                      {searchResults.documents.length > 0 && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Documents</h4>
                          <div className="space-y-2">
                            {searchResults.documents.map((doc) => (
                              <div key={doc.id} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer">
                                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                                  <FileText className="h-4 w-4 text-green-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                                  <p className="text-xs text-gray-500">{doc.type} • {doc.size}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {searchResults.employees.length === 0 && searchResults.documents.length === 0 && (
                        <p className="text-sm text-gray-500 text-center py-4">No results found</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <div className="relative">
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 relative">
                  <Bell className="h-6 w-6" />
                  {notifications.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {notifications.length}
                    </span>
                  )}
                </button>
              </div>
              
              {/* Messages */}
              <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                <MessageCircle className="h-6 w-6" />
              </button>
              
              {/* Support */}
              <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                <Headphones className="h-6 w-6" />
              </button>
              
              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{user.full_name || user.username}</p>
                  <p className="text-xs text-gray-500 capitalize">{user.role.replace('_', ' ')}</p>
                </div>
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium text-sm">
                    {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                  </span>
                </div>
                <button className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                  <ChevronDown className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {renderMainContent()}
        </main>
      </div>
    </div>
  );
};

export default Dashboard; 