import React, { useState, useEffect } from 'react';
import { 
  Search, X, Filter, Download, List, Calendar, 
  Briefcase, DollarSign, User, FileText, TrendingUp, Monitor, MoreHorizontal,
  ChevronLeft, Folder, File, Image, FileText as FileTextIcon, BarChart3
} from 'lucide-react';
import { useAuth } from '../../utils/auth';
import { documentsAPI } from '../../services/api';

const EnhancedDocumentManager = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [folders, setFolders] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [documentCategory, setDocumentCategory] = useState('All Files');
  const [fileType, setFileType] = useState('All Files');
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [sortBy, setSortBy] = useState('date');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [selectedCategory, selectedFolder, currentPage, searchQuery, documentCategory, fileType]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Loading initial data...');
      
      // Check authentication status first
      const { token, user } = checkAuthStatus();
      console.log('🔐 Auth check result:', { hasToken: !!token, hasUser: !!user });
      
      if (!token) {
        console.log('❌ No token found, setting error');
        setError('No authentication token found. Please log in.');
        setLoading(false);
        return;
      }
      
      // Load categories
      console.log('📂 Loading categories...');
      const categoriesData = await documentsAPI.getCategories();
      console.log('✅ Categories loaded:', categoriesData);
      setCategories(categoriesData.data || []);
      
      // Load enhanced documents
      console.log('📄 Loading enhanced documents...');
      const documentsData = await documentsAPI.getEnhanced({ page: currentPage, page_size: 20 });
      console.log('✅ Enhanced documents loaded:', documentsData);
      
      setDocuments(documentsData.documents || []);
      setFolders(documentsData.folders || []);
      setTotalCount(documentsData.total_count || 0);
      setTotalPages(documentsData.total_pages || 1);
      
    } catch (error) {
      console.error('❌ Failed to load initial data:', error);
      
      // Provide more specific error messages
      if (error.message.includes('Failed to fetch')) {
        setError('Network error: Unable to connect to the server. Please check your internet connection.');
      } else if (error.message.includes('401') || error.message.includes('403')) {
        setError('Authentication error: Please log in again.');
        // Clear invalid tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      } else {
        setError(`Failed to load data: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    try {
      setLoading(true);
      
      const params = {
        category_id: selectedCategory?.id,
        folder_id: selectedFolder?.id,
        file_type: fileType !== 'All Files' ? fileType : undefined,
        search_query: searchQuery || undefined,
        page: currentPage,
        page_size: 20
      };
      
      const response = await documentsAPI.getEnhanced(params);
      setDocuments(response.documents || []);
      setTotalPages(response.total_pages || 1);
      setTotalCount(response.total_count || 0);
      
    } catch (error) {
      console.error('Failed to load documents:', error);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    loadDocuments();
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setSelectedFolder(null);
    setCurrentPage(1);
  };

  const handleFolderSelect = (folder) => {
    setSelectedFolder(folder);
    setCurrentPage(1);
  };

  const handleBulkDownload = async () => {
    // Implementation for bulk download
    console.log('Bulk download selected documents');
  };

  const handleViewModeToggle = () => {
    setViewMode(viewMode === 'grid' ? 'list' : 'grid');
  };

  const handleSortChange = () => {
    // Implementation for sorting
    console.log('Sorting changed');
  };

  const getFileIcon = (fileType) => {
    if (fileType.includes('image') || fileType.includes('jpg') || fileType.includes('png')) {
      return <Image className="w-8 h-8 text-blue-500" />;
    }
    if (fileType.includes('pdf')) {
      return <FileTextIcon className="w-8 h-8 text-red-500" />;
    }
    if (fileType.includes('word') || fileType.includes('doc')) {
      return <FileText className="w-8 h-8 text-blue-600" />;
    }
    if (fileType.includes('excel') || fileType.includes('xls')) {
      return <BarChart3 className="w-8 h-8 text-green-600" />;
    }
    return <File className="w-8 h-8 text-gray-500" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  const getCategoryIcon = (iconName) => {
    const iconMap = {
      'briefcase': <Briefcase className="w-5 h-5" />,
      'dollar-sign': <DollarSign className="w-5 h-5" />,
      'user': <User className="w-5 h-5" />,
      'file-text': <FileText className="w-5 h-5" />,
      'trending-up': <TrendingUp className="w-5 h-5" />,
      'monitor': <Monitor className="w-5 h-5" />,
      'more-horizontal': <MoreHorizontal className="w-5 h-5" />
    };
    return iconMap[iconName] || <Folder className="w-5 h-5" />;
  };

  // Test login function for debugging
  const handleTestLogin = async () => {
    try {
      console.log('🔐 Attempting test login...');
      const response = await fetch('https://multitenant-backend-mlap.onrender.com/test-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Test login successful:', data);
        
        // Store the test token
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Reload the page to refresh authentication state
        window.location.reload();
      } else {
        console.error('❌ Test login failed:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error details:', errorText);
      }
    } catch (error) {
      console.error('❌ Test login error:', error);
    }
  };

  // Check authentication status
  const checkAuthStatus = () => {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    
    console.log('🔐 Auth status check:');
    console.log('Token:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN');
    console.log('User:', user ? JSON.parse(user) : 'NO USER');
    
    return { token, user: user ? JSON.parse(user) : null };
  };

  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Document Management</h1>
              <p className="text-gray-600">Manage and organize your documents efficiently</p>
            </div>
            
            {/* Test Login Button for Debugging */}
            <div className="flex items-center space-x-4">
              <button
                onClick={checkAuthStatus}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Check Auth Status
              </button>
              <button
                onClick={handleTestLogin}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Test Login
              </button>
            </div>
          </div>
          
          {/* Authentication Status Display */}
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="font-semibold text-gray-900 mb-2">Authentication Status</h3>
            <div className="text-sm text-gray-600">
              {(() => {
                const { token, user } = checkAuthStatus();
                return (
                  <div>
                    <p>Token: {token ? '✅ Present' : '❌ Missing'}</p>
                    <p>User: {user ? `✅ ${user.username} (${user.role})` : '❌ Not logged in'}</p>
                  </div>
                );
              })()}
            </div>
          </div>
        </div>

        {/* Left Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
          {/* Logo */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <span className="text-xl font-bold text-gray-900">PFile</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            <div className="space-y-1">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Navigation
              </div>
              <a href="#" className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
                <Folder className="w-5 h-5" />
                <span>My Files</span>
              </a>
              <a href="#" className="flex items-center space-x-3 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg">
                <User className="w-5 h-5" />
                <span>Org Files</span>
              </a>
              <a href="#" className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
                <Calendar className="w-5 h-5" />
                <span>Recent</span>
              </a>
              <a href="#" className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
                <span className="w-5 h-5">⭐</span>
                <span>Starred</span>
              </a>
              <a href="#" className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
                <FileText className="w-5 h-5" />
                <span>Logs</span>
              </a>
              <a href="#" className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
                <span className="w-5 h-5">⬆️</span>
                <span>Uploads</span>
              </a>
            </div>

            {/* Categories */}
            <div className="space-y-1 mt-6">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Organisation Files
              </div>
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => handleCategorySelect(category)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 text-left rounded-lg transition-colors ${
                    selectedCategory?.id === category.id
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="w-5 h-5 text-gray-600">
                    {getCategoryIcon(category.icon)}
                  </div>
                  <span className="text-sm">{category.display_name}</span>
                </button>
              ))}
            </div>
          </nav>

          {/* Collapse Button */}
          <div className="p-4 border-t border-gray-200">
            <button className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg">
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              {/* Search Bar */}
              <div className="flex-1 max-w-2xl">
                <form onSubmit={handleSearch} className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    placeholder="Search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-8 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <Filter className="w-5 h-5" />
                  </button>
                </form>
              </div>

              {/* User Info */}
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-700">{user?.full_name || 'User'}</span>
                <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-gray-700">
                    {user?.full_name?.charAt(0) || 'U'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6 overflow-auto">
            {/* Breadcrumbs */}
            <div className="mb-6">
              <nav className="flex" aria-label="Breadcrumb">
                <ol className="flex items-center space-x-2">
                  <li>
                    <a href="#" className="text-gray-500 hover:text-gray-700">
                      Organisation Files
                    </a>
                  </li>
                  {selectedCategory && (
                    <>
                      <li>
                        <span className="text-gray-400 mx-2">/</span>
                      </li>
                      <li>
                        <span className="text-gray-900 font-medium">
                          {selectedCategory.display_name}
                        </span>
                      </li>
                    </>
                  )}
                </ol>
              </nav>
            </div>

            {/* Filters and Actions */}
            <div className="mb-6 flex flex-wrap items-center gap-4">
              <div className="flex items-center space-x-4">
                <select
                  value={documentCategory}
                  onChange={(e) => setDocumentCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="All Files">Document Category</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.display_name}>
                      {category.display_name}
                    </option>
                  ))}
                </select>

                <select
                  value={fileType}
                  onChange={(e) => setFileType(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="All Files">File Type</option>
                  <option value="pdf">PDF</option>
                  <option value="doc">Word</option>
                  <option value="xls">Excel</option>
                  <option value="image">Images</option>
                </select>

                <select className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option>Select Employees</option>
                  <option>All Employees</option>
                  <option>HR Team</option>
                  <option>Managers</option>
                </select>
              </div>

              <div className="flex items-center space-x-2 ml-auto">
                <button
                  onClick={handleBulkDownload}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Files</span>
                </button>

                <button
                  onClick={handleViewModeToggle}
                  className={`p-2 rounded-lg transition-colors ${
                    viewMode === 'list' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  <List className="w-4 h-4" />
                </button>

                <button
                  onClick={handleSortChange}
                  className="p-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Calendar className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Documents Grid */}
            {error ? (
              <div className="text-center py-8">
                <p className="text-red-600">{error}</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {documents.map((document) => (
                  <div
                    key={document.id}
                    className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
                  >
                    <div className="flex flex-col items-center text-center space-y-3">
                      <div className="w-16 h-16 flex items-center justify-center">
                        {getFileIcon(document.file_type)}
                      </div>
                      
                      <div className="w-full">
                        <h3 className="text-sm font-medium text-gray-900 truncate" title={document.original_filename}>
                          {document.original_filename}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatFileSize(document.file_size)} • {formatDate(document.created_at)}
                        </p>
                        {document.user?.full_name && (
                          <p className="text-xs text-gray-400 mt-1 truncate">
                            {document.user.full_name}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                
                <span className="px-3 py-2 text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </span>
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            )}

            {/* Empty State */}
            {documents.length === 0 && !loading && (
              <div className="text-center py-12">
                <Folder className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
                <p className="text-gray-500">
                  {searchQuery ? `No documents match "${searchQuery}"` : 'Upload your first document to get started'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedDocumentManager;
