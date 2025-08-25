import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { EnhancedDocumentManager } from '../Documents';
import { documentsAPI, usersAPI, companiesAPI } from '../../services/api';
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
  Plus,
  BookOpen,
  UserCheck,
  CalendarX,
  UserCircle,
  Network,
  Clock1,
  Target,
  Star as StarIcon,
  Users as UsersIcon,
  ArrowUpRight,
  Eye,
  Download,
  Filter,
  List,
  Grid
} from 'lucide-react';

const CompanyDashboard = () => {
  const [userData, setUserData] = useState(null);
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchResults, setSearchResults] = useState({ employees: [], documents: [] });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const userDataStr = localStorage.getItem('user_data');
    const companyId = localStorage.getItem('company_id');
    
    if (userDataStr && companyId) {
      try {
        const user = JSON.parse(userDataStr);
        setUserData(user);
        
        setCompanyData({
          id: companyId,
          name: user.company_name || 'Your Company'
        });
        
        loadNotifications();
      } catch (error) {
        console.error('Error parsing user data:', error);
        navigate('/company-login');
      }
    } else {
      navigate('/company-login');
    }
    
    setLoading(false);
  }, [navigate]);

  useEffect(() => {
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

  const loadNotifications = async () => {
    try {
      // Load real notifications from backend
      if (companyData) {
        // Get recent documents for document-related notifications
        const documentsResponse = await documentsAPI.list(null);
        const documents = documentsResponse.data || documentsResponse || [];
        
        // Get recent user activities for user-related notifications
        let userActivities = [];
        try {
          const usersResponse = await usersAPI.list();
          const users = usersResponse.data || usersResponse || [];
          userActivities = users.slice(0, 3); // Get 3 most recent users
        } catch (error) {
          console.error('Failed to load user activities:', error);
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

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setShowSearchResults(false);
      return;
    }

    try {
      const results = {
        employees: [],
        documents: []
      };

      // Search for documents using real API
      try {
        const documentsResponse = await documentsAPI.list(null);
        const allDocuments = documentsResponse.data || documentsResponse || [];
        
        const matchingDocuments = allDocuments.filter(doc => 
          (doc.original_filename || doc.name || '').toLowerCase().includes(query.toLowerCase()) ||
          (doc.category || doc.folder || '').toLowerCase().includes(query.toLowerCase()) ||
          (doc.user?.full_name || doc.uploadedBy || '').toLowerCase().includes(query.toLowerCase())
        );
        
        results.documents = matchingDocuments.slice(0, 5); // Limit to 5 results
      } catch (error) {
        console.error('Document search failed:', error);
        // Fallback to empty results
        results.documents = [];
      }

      // Search for employees using real API
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
        console.error('Employee search failed:', error);
        // Fallback to empty results
        results.employees = [];
      }
      
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search failed:', error);
      // Fallback to empty results
      setSearchResults({ employees: [], documents: [] });
      setShowSearchResults(true);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('company_id');
    localStorage.removeItem('user_data');
    navigate('/company-login');
  };

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning!';
    else if (hour < 17) return 'Good afternoon!';
    else return 'Good evening!';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!userData || !companyData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
          <p className="text-gray-600 mb-6">Please log in to access your company dashboard.</p>
          <button
            onClick={() => navigate('/company-login')}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Modern Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="h-12 w-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Building2 className="h-7 w-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{companyData.name}</h1>
                <p className="text-sm text-gray-600">Document Management System</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Search Bar */}
              <div className="relative w-96 search-container">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  placeholder="Search for actions or people..."
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-xl leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
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
                      
                      {searchResults.employees.length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Employees</h4>
                          <div className="space-y-2">
                            {searchResults.employees.map((employee) => (
                              <div 
                                key={employee.id} 
                                className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                                onClick={() => {
                                  // Navigate to employee management or profile
                                  setShowSearchResults(false);
                                  setSearchQuery('');
                                  // Navigate to user management if user has permission
                                  if (userData.role === 'hr_admin' || userData.role === 'system_admin') {
                                    navigate('/users');
                                  }
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
                      
                      {searchResults.documents.length > 0 && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Documents</h4>
                          <div className="space-y-2">
                            {searchResults.documents.map((doc) => (
                              <div 
                                key={doc.id} 
                                className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                                onClick={() => {
                                  // Navigate to document management
                                  setShowSearchResults(false);
                                  setSearchQuery('');
                                  navigate('/dashboard/documents');
                                }}
                              >
                                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                                  <FileText className="h-4 w-4 text-green-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{doc.original_filename || doc.name}</p>
                                  <p className="text-xs text-gray-500">{doc.file_type || doc.type} • {doc.file_size || doc.size}</p>
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

              {/* Header Icons */}
              <div className="flex items-center space-x-2">
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                  <Search className="h-5 w-5" />
                </button>
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                  <Star className="h-5 w-5" />
                </button>
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 relative">
                  <Bell className="h-5 w-5" />
                  {notifications.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {notifications.length}
                    </span>
                  )}
                </button>
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                  <MessageCircle className="h-5 w-5" />
                </button>
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                  <Headphones className="h-5 w-5" />
                </button>
              </div>

              {/* User Info */}
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{userData.full_name || userData.username}</p>
                  <p className="text-xs text-gray-500 capitalize">{userData.role || 'User'}</p>
                </div>
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium text-sm">
                    {(userData.full_name || userData.username || 'U').charAt(0).toUpperCase()}
                  </span>
                </div>
                <button className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                  <ChevronDown className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center text-white">
            <h2 className="text-4xl font-bold mb-4">{getWelcomeMessage()}</h2>
            <p className="text-xl text-blue-100">
              Welcome back, {userData.full_name || userData.username}!
            </p>
            <p className="text-lg text-blue-100 mt-2">
              Manage your company's documents, collaborate with team members, and stay organized.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Quick Actions */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <button 
              onClick={() => navigate('/dashboard/documents')}
              className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <BookOpen className="h-6 w-6" />
                <div>
                  <div className="font-medium">View Documents</div>
                </div>
              </div>
            </button>
            
            <button 
              onClick={() => navigate('/users')}
              className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <UsersIcon className="h-6 w-6" />
                <div>
                  <div className="font-medium">Manage Team</div>
                </div>
              </div>
            </button>
            
            <button 
              onClick={() => navigate('/dashboard/documents')}
              className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <CalendarX className="h-6 w-6" />
                <div>
                  <div className="font-medium">Upload Files</div>
                </div>
              </div>
            </button>
            
            <button 
              onClick={() => navigate('/analytics')}
              className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <UserCircle className="h-6 w-6" />
                <div>
                  <div className="font-medium">View Analytics</div>
                </div>
              </div>
            </button>
            
            <button 
              onClick={() => navigate('/dashboard/documents')}
              className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <Network className="h-6 w-6" />
                <div>
                  <div className="font-medium">Browse Files</div>
                </div>
              </div>
            </button>
          </div>
          
          <div className="mt-4">
            <button 
              onClick={() => navigate('/dashboard/documents')}
              className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <Clock1 className="h-6 w-6" />
                <div>
                  <div className="font-medium">Recent Files</div>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* HR Admin Tools Section */}
        {(userData.role === 'hr_admin' || userData.role === 'system_admin') && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">HR Admin Tools</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => navigate('/hr-admin-dashboard')}
                className="bg-indigo-600 text-white px-4 py-3 rounded-xl hover:bg-indigo-700 transition-colors text-left"
              >
                <div className="flex items-center space-x-3">
                  <Users className="h-6 w-6" />
                  <div>
                    <div className="font-medium">HR Admin Dashboard</div>
                    <div className="text-sm text-indigo-200">Manage company members, files & analytics</div>
                  </div>
                </div>
              </button>
              
              <button
                onClick={() => navigate('/users')}
                className="bg-green-600 text-white px-4 py-3 rounded-xl hover:bg-green-700 transition-colors text-left"
              >
                <div className="flex items-center space-x-3">
                  <UserCheck className="h-6 w-6" />
                  <div>
                    <div className="font-medium">User Management</div>
                    <div className="text-sm text-green-200">Manage user accounts & permissions</div>
                  </div>
                </div>
              </button>
              
              <button
                onClick={() => navigate('/analytics')}
                className="bg-purple-600 text-white px-4 py-3 rounded-xl hover:bg-purple-700 transition-colors text-left"
              >
                <div className="flex items-center space-x-3">
                  <BarChart3 className="h-6 w-6" />
                  <div>
                    <div className="font-medium">Analytics</div>
                    <div className="text-sm text-purple-200">View company performance metrics</div>
                  </div>
                </div>
              </button>
            </div>
          </div>
        )}

        {/* Approvals Section */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Approvals</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="h-5 w-5 text-blue-600" />
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <span className="text-lg">⋯</span>
                </button>
              </div>
              <div className="space-y-2 text-sm">
                <p className="font-medium">Document Approval</p>
                <p className="text-gray-500">Pending Review</p>
                <p className="text-gray-500">Type: Policy</p>
                <p className="text-gray-500">Submitted: Today</p>
                <p className="font-semibold">Status: Pending</p>
              </div>
              <div className="flex space-x-2 mt-4">
                <button 
                  onClick={() => navigate('/dashboard/documents')}
                  className="flex-1 bg-green-500 text-white p-2 rounded-lg hover:bg-green-600"
                >
                  <CheckCircle className="h-4 w-4 mx-auto" />
                </button>
                <button 
                  onClick={() => navigate('/dashboard/documents')}
                  className="flex-1 bg-red-500 text-white p-2 rounded-lg hover:bg-red-600"
                >
                  <X className="h-4 w-4 mx-auto" />
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <FileText className="h-5 w-5 text-green-600" />
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <span className="text-lg">⋯</span>
                </button>
              </div>
              <div className="space-y-2 text-sm">
                <p className="font-medium">File Upload</p>
                <p className="text-gray-500">New Document</p>
                <p className="text-gray-500">Submitted today</p>
                <p className="font-semibold">Ready for Review</p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '100%' }}></div>
                </div>
                <p className="text-gray-500">Status: Complete</p>
              </div>
              <div className="mt-4">
                <button 
                  onClick={() => navigate('/dashboard/documents')}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View Document
                </button>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <Star className="h-5 w-5 text-purple-600" />
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <span className="text-lg">⋯</span>
                </button>
              </div>
              <div className="space-y-2 text-sm">
                <p className="font-medium">Access Request</p>
                <p className="text-gray-500">New User</p>
                <p className="text-gray-500">Submitted Today</p>
                <p className="text-gray-500">Role: Employee</p>
              </div>
              <div className="mt-4">
                <button 
                  onClick={() => navigate('/users')}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  Review Request
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Document Management Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Document Management</h3>
            <p className="text-sm text-gray-600">Organize, search, and manage your company documents</p>
          </div>
          <div className="p-6">
            <EnhancedDocumentManager />
          </div>
        </div>
      </main>
    </div>
  );
};

export default CompanyDashboard;