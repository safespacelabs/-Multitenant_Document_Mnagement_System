import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { EnhancedDocumentManager } from '../Documents';
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

  const loadNotifications = () => {
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
      // Enhanced search with real data integration
      const results = {
        employees: [],
        documents: []
      };

      // Search for documents (if available)
      try {
        // This would integrate with the company's document API
        // For now, using enhanced mock data
        const mockDocuments = [
          { id: 1, name: 'Employee Handbook.pdf', type: 'PDF', size: '2.3 MB', category: 'HR' },
          { id: 2, name: 'Company Policy.docx', type: 'DOCX', size: '1.1 MB', category: 'Legal' },
          { id: 3, name: 'Budget Report.xlsx', type: 'XLSX', size: '856 KB', category: 'Finance' },
          { id: 4, name: 'Marketing Plan.pdf', type: 'PDF', size: '1.5 MB', category: 'Marketing' }
        ];
        
        const matchingDocuments = mockDocuments.filter(doc => 
          doc.name.toLowerCase().includes(query.toLowerCase()) ||
          doc.category.toLowerCase().includes(query.toLowerCase())
        );
        
        results.documents = matchingDocuments;
      } catch (error) {
        console.error('Document search failed:', error);
      }

      // Search for employees (if available)
      try {
        // This would integrate with the company's user API
        // For now, using enhanced mock data
        const mockEmployees = [
          { id: 1, name: 'John Doe', role: 'HR Manager', department: 'HR' },
          { id: 2, name: 'Jane Smith', role: 'Employee', department: 'Engineering' },
          { id: 3, name: 'Mike Johnson', role: 'Team Lead', department: 'Engineering' },
          { id: 4, name: 'Sarah Wilson', role: 'Accountant', department: 'Finance' }
        ];
        
        const matchingEmployees = mockEmployees.filter(emp => 
          emp.name.toLowerCase().includes(query.toLowerCase()) ||
          emp.role.toLowerCase().includes(query.toLowerCase()) ||
          emp.department.toLowerCase().includes(query.toLowerCase())
        );
        
        results.employees = matchingEmployees;
      } catch (error) {
        console.error('Employee search failed:', error);
      }
      
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search failed:', error);
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
                                  // This could navigate to employee details or management
                                }}
                              >
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
                                  // This could navigate to document details or management
                                }}
                              >
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
                <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 relative">
                  <Bell className="h-5 w-5" />
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    10
                  </span>
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
            <button className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left">
              <div className="flex items-center space-x-3">
                <BookOpen className="h-6 w-6" />
                <div>
                  <div className="font-medium">View My Learning</div>
                </div>
              </div>
            </button>
            
            <button className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left">
              <div className="flex items-center space-x-3">
                <UsersIcon className="h-6 w-6" />
                <div>
                  <div className="font-medium">Manage My Team</div>
                </div>
              </div>
            </button>
            
            <button className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left">
              <div className="flex items-center space-x-3">
                <CalendarX className="h-6 w-6" />
                <div>
                  <div className="font-medium">Request Time Off</div>
                </div>
              </div>
            </button>
            
            <button className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left">
              <div className="flex items-center space-x-3">
                <UserCircle className="h-6 w-6" />
                <div>
                  <div className="font-medium">View My Profile</div>
                </div>
              </div>
            </button>
            
            <button className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left">
              <div className="flex items-center space-x-3">
                <Network className="h-6 w-6" />
                <div>
                  <div className="font-medium">View Org Chart</div>
                </div>
              </div>
            </button>
          </div>
          
          <div className="mt-4">
            <button className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left">
              <div className="flex items-center space-x-3">
                <Clock1 className="h-6 w-6" />
                <div>
                  <div className="font-medium">View My Time Sheet</div>
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
                <p className="font-medium">Internal Training</p>
                <p className="text-gray-500">Course Title</p>
                <p className="text-gray-500">Type</p>
                <p className="text-gray-500">Price</p>
                <p className="text-gray-500">Diversity</p>
                <p className="text-gray-500">Online Item</p>
                <p className="font-semibold">0.0 USD</p>
              </div>
              <div className="flex space-x-2 mt-4">
                <button className="flex-1 bg-green-500 text-white p-2 rounded-lg hover:bg-green-600">
                  <CheckCircle className="h-4 w-4 mx-auto" />
                </button>
                <button className="flex-1 bg-red-500 text-white p-2 rounded-lg hover:bg-red-600">
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
                <p className="font-medium">Job Requisition</p>
                <p className="text-gray-500">Project Manager</p>
                <p className="text-gray-500">Submitted on Oct 22, 2023</p>
                <p className="font-semibold">Req Id 2755</p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '60%' }}></div>
                </div>
                <p className="text-gray-500">Hiring Manager</p>
                <p className="text-gray-500">Recruiter</p>
                <p className="text-gray-500">Pending For 2 days</p>
              </div>
              <div className="mt-4">
                <a href="#" className="text-blue-600 hover:text-blue-700 text-sm font-medium">View All (8)</a>
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
                <p className="font-medium">Create Spot Award</p>
                <p className="text-gray-500">Retail Sales Associate</p>
                <p className="text-gray-500">Submitted On Sep 17, 2023</p>
                <p className="text-gray-500">Submitted By Mya Cooper</p>
              </div>
              <div className="mt-4">
                <a href="#" className="text-blue-600 hover:text-blue-700 text-sm font-medium">View All (6)</a>
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