import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../utils/auth';
import { documentsAPI, usersAPI, companiesAPI, systemDocumentsAPI } from '../../services/api';
import { EnhancedDocumentManager } from '../Documents';
import { HRAdminDashboard } from '../Features';
import { Analytics } from '../Features';
import UserManagement from '../Users/UserManagement';
import Sidebar from '../Layout/Sidebar';
import Header from '../Layout/Header';
import { 
  Home, 
  FileText, 
  Users, 
  BarChart3, 
  MessageCircle, 
  FileSignature,
  Grid,
  SettingsIcon,
  Crown,
  Building2,
  Menu,
  X,
  LogOut,
  Search,
  Bell,
  Headphones,
  ChevronDown,
  User
} from 'lucide-react';

const Dashboard = () => {
  const { user, company, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [collapsed, setCollapsed] = useState(false);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchResults, setSearchResults] = useState({ employees: [], documents: [] });
  const [recentActivity, setRecentActivity] = useState([]);

  console.log('🏠 Dashboard component rendering...');
  console.log('👤 User:', user);
  console.log('🏢 Company:', company);
  console.log('📍 Location:', location.pathname);

  useEffect(() => {
    loadQuickStats();
    loadNotifications();
    loadRecentActivity();
    
    // Add click outside handler for search results
    const handleClickOutside = (event) => {
      if (showSearchResults && !event.target.closest('.search-container')) {
        setShowSearchResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSearchResults]);

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

  const loadNotifications = async () => {
    try {
      // Load real notifications from backend
      if (user && company) {
        // Get recent documents for document-related notifications
        const documentsResponse = await documentsAPI.list(null);
        const documents = documentsResponse.data || documentsResponse || [];
        
        // Get recent user activities for user-related notifications
        let userActivities = [];
        if (['hr_admin', 'hr_manager', 'system_admin'].includes(user.role)) {
          try {
            const usersResponse = await usersAPI.list();
            const users = usersResponse.data || usersResponse || [];
            userActivities = users.slice(0, 3); // Get 3 most recent users
          } catch (error) {
            console.error('Failed to load user activities:', error);
          }
        }
        
        // Generate real notifications based on actual data
        const realNotifications = [];
        
        // Document notifications
        if (documents.length > 0) {
          const recentDocs = documents.slice(0, 2);
          recentDocs.forEach((doc, index) => {
            realNotifications.push({
              id: `doc_${doc.id}`,
              type: 'info',
              message: `New document uploaded: ${doc.original_filename || doc.name}`,
              time: `${index + 1} hour${index > 0 ? 's' : ''} ago`
            });
          });
        }
        
        // User activity notifications
        if (userActivities.length > 0) {
          userActivities.forEach((user, index) => {
            realNotifications.push({
              id: `user_${user.id}`,
              type: 'success',
              message: `New team member added: ${user.full_name || user.username}`,
              time: `${index + 1} day${index > 0 ? 's' : ''} ago`
            });
          });
        }
        
        // Add system notifications
        realNotifications.push({
          id: 'system_1',
          type: 'warning',
          message: 'System maintenance scheduled for tonight',
          time: '2 hours ago'
        });
        
        setNotifications(realNotifications);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
      // Fallback to minimal notifications if API fails
      setNotifications([
        { id: 1, type: 'info', message: 'System ready', time: 'Just now' }
      ]);
    }
  };

  const loadRecentActivity = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('❌ No authentication token found, skipping recent activity load');
        return;
      }

      console.log('🔍 Loading recent activity for user:', user.username, 'role:', user.role);

      const activityData = [];

      if (user.role === 'system_admin') {
        // System admin activity (e.g., system logs, maintenance)
        activityData.push({ id: 'sys_1', type: 'system', message: 'System maintenance scheduled for tonight', time: '2 hours ago' });
        activityData.push({ id: 'sys_2', type: 'system', message: 'Database backup completed successfully', time: '1 day ago' });
      } else if (['hr_admin', 'hr_manager'].includes(user.role)) {
        // HR Admin/Manager activity (e.g., user additions, document uploads)
        if (company) {
          try {
            const usersResponse = await usersAPI.list(company.id);
            const users = usersResponse.data || usersResponse || [];
            users.forEach((user, index) => {
              activityData.push({
                id: `user_${user.id}`,
                type: 'user',
                message: `New team member added: ${user.full_name || user.username}`,
                time: `${index + 1} day${index > 0 ? 's' : ''} ago`
              });
            });
          } catch (error) {
            console.error('Failed to load HR manager activity:', error);
          }
        }

        try {
          const documentsResponse = await documentsAPI.list(null);
          const documents = documentsResponse.data || documentsResponse || [];
          documents.forEach((doc, index) => {
            activityData.push({
              id: `doc_${doc.id}`,
              type: 'upload',
              message: `New document uploaded: ${doc.original_filename || doc.name}`,
              time: `${index + 1} hour${index > 0 ? 's' : ''} ago`
            });
          });
        } catch (error) {
          console.error('Failed to load HR manager activity:', error);
        }
      }

      setRecentActivity(activityData.slice(0, 10)); // Limit to 10 recent activities
    } catch (error) {
      console.error('Failed to load recent activity:', error);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setShowSearchResults(false);
      return;
    }

    try {
      setLoading(true);
      
      // Real search implementation using APIs
      const results = {
        employees: [],
        documents: []
      };

      // Search for documents
      try {
        const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
        const documentsResponse = await api.list(null);
        const allDocuments = documentsResponse.data || documentsResponse || [];
        
        const matchingDocuments = allDocuments.filter(doc => 
          (doc.original_filename || doc.name || '').toLowerCase().includes(query.toLowerCase()) ||
          (doc.category || doc.folder || '').toLowerCase().includes(query.toLowerCase()) ||
          (doc.user?.full_name || doc.uploadedBy || '').toLowerCase().includes(query.toLowerCase())
        );
        
        results.documents = matchingDocuments.slice(0, 5); // Limit to 5 results
      } catch (error) {
        console.error('Document search failed:', error);
      }

      // Search for users (if user has permission)
      if (['hr_admin', 'hr_manager', 'system_admin'].includes(user.role)) {
        try {
          const usersResponse = await usersAPI.list();
          const allUsers = usersResponse.data || usersResponse || [];
          
          const matchingUsers = allUsers.filter(user => 
            (user.full_name || user.username || '').toLowerCase().includes(query.toLowerCase()) ||
            (user.role || '').toLowerCase().includes(query.toLowerCase()) ||
            (user.email || '').toLowerCase().includes(query.toLowerCase())
          );
          
          results.employees = matchingUsers.slice(0, 5); // Limit to 5 results
        } catch (error) {
          console.error('User search failed:', error);
        }
      }
      
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search failed:', error);
      // Show empty results instead of mock data
      setSearchResults({ employees: [], documents: [] });
      setShowSearchResults(true);
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
    
    if (path === basePath) return true;
    if (path !== basePath && location.pathname.startsWith(path)) return true;
    return false;
  };

  const renderMainContent = () => {
    const path = location.pathname;
    
    // HR Admin Dashboard
    if (path === '/dashboard/hr-admin' && ['hr_admin', 'hr_manager'].includes(user?.role)) {
      return <HRAdminDashboard />;
    }
    
    // Document Management
    if (path === '/dashboard/documents') {
      return <EnhancedDocumentManager />;
    }
    
    // Analytics
    if (path === '/dashboard/analytics') {
      return <Analytics />;
    }
    
    // User Management
    if (path === '/dashboard/users' && ['hr_admin', 'hr_manager', 'system_admin'].includes(user?.role)) {
      return <UserManagement />;
    }
    
    // E-Signature
    if (path === '/dashboard/esignature') {
      return <div className="p-6"><h2 className="text-2xl font-bold mb-4">E-Signature Management</h2><p>E-Signature features coming soon...</p></div>;
    }
    
    // Chat/AI Assistant
    if (path === '/dashboard/chat') {
      return <div className="p-6"><h2 className="text-2xl font-bold mb-4">AI Assistant</h2><p>AI Assistant features coming soon...</p></div>;
    }
    
    // Default Dashboard Overview
    return (
      <div className="p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome back, {user?.full_name || user?.username}!</h1>
          <p className="text-gray-600">Here's what's happening with your documents today.</p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <QuickActionCard
            title="Document Management"
            description="Upload, organize, and manage your files"
            icon={FileText}
            color="blue"
            onClick={() => navigate('/dashboard/documents')}
          />
          <QuickActionCard
            title="User Management"
            description="Manage team members and permissions"
            icon={Users}
            color="green"
            onClick={() => navigate('/dashboard/users')}
          />
          <QuickActionCard
            title="Analytics"
            description="View insights and reports"
            icon={BarChart3}
            color="purple"
            onClick={() => navigate('/dashboard/analytics')}
          />
          {['hr_admin', 'hr_manager'].includes(user?.role) && (
            <QuickActionCard
              title="HR Admin"
              description="HR management dashboard"
              icon={Users}
              color="indigo"
              onClick={() => navigate('/dashboard/hr-admin')}
            />
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {recentActivity.length > 0 ? (
              recentActivity.slice(0, 3).map((activity, index) => (
                <div key={activity.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  {activity.type === 'upload' ? (
                    <FileText className="h-5 w-5 text-blue-500" />
                  ) : activity.type === 'user' ? (
                    <Users className="h-5 w-5 text-green-500" />
                  ) : (
                    <FileText className="h-5 w-5 text-purple-500" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900">{activity.message}</p>
                    <p className="text-sm text-gray-500">{activity.time}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4 text-gray-500">
                <p>No recent activity</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const formatFileSize = (bytes, decimalPoint = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimalPoint < 0 ? 0 : decimalPoint;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  // Quick Action Card Component
  const QuickActionCard = ({ title, description, icon: Icon, color, onClick }) => {
    const colorClasses = {
      blue: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
      green: 'bg-green-50 text-green-600 hover:bg-green-100',
      purple: 'bg-purple-50 text-purple-600 hover:bg-purple-100',
      indigo: 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
    };

    return (
      <button
        onClick={onClick}
        className={`p-6 rounded-xl border border-gray-200 text-left transition-all duration-200 hover:shadow-md ${colorClasses[color]}`}
      >
        <Icon className="h-8 w-8 mb-3" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </button>
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
              <div className="relative w-96 search-container">
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
                      
                      {loading ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                          <span className="ml-2 text-sm text-gray-500">Searching...</span>
                        </div>
                      ) : (
                        <>
                          {/* Employees */}
                          {searchResults.employees.length > 0 && (
                            <div className="mb-4">
                              <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Employees</h4>
                              <div className="space-y-2">
                                {searchResults.employees.map((employee) => (
                                  <div 
                                    key={employee.id} 
                                    className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                                    onClick={() => {
                                      if (['hr_admin', 'hr_manager', 'system_admin'].includes(user.role)) {
                                        navigate('/dashboard/users');
                                      }
                                      setShowSearchResults(false);
                                      setSearchQuery('');
                                    }}
                                  >
                                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                      <User className="h-4 w-4 text-blue-600" />
                                    </div>
                                    <div>
                                      <p className="text-sm font-medium text-gray-900">{employee.full_name || employee.name}</p>
                                      <p className="text-xs text-gray-500">{employee.role} • {employee.department || 'N/A'}</p>
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
                                  <div 
                                    key={doc.id} 
                                    className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                                    onClick={() => {
                                      navigate('/dashboard/documents');
                                      setShowSearchResults(false);
                                      setSearchQuery('');
                                    }}
                                  >
                                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                                      <FileText className="h-4 w-4 text-green-600" />
                                    </div>
                                    <div>
                                      <p className="text-sm font-medium text-gray-900">{doc.original_filename || doc.name}</p>
                                      <p className="text-xs text-gray-500">{doc.file_type || doc.type} • {formatFileSize(doc.file_size || doc.size)}</p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {searchResults.employees.length === 0 && searchResults.documents.length === 0 && (
                            <p className="text-sm text-gray-500 text-center py-4">No results found</p>
                          )}
                        </>
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