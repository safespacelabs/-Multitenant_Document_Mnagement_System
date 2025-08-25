import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { documentsAPI, systemDocumentsAPI } from '../../services/api';
import { 
  Search,
  Filter,
  Download,
  List,
  Grid,
  FileText,
  File,
  Image,
  Video,
  Music,
  Archive,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  Share,
  Star,
  Calendar,
  User,
  Folder,
  Upload,
  Plus,
  X,
  ChevronDown,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';

const EnhancedDocumentManager = () => {
  const { user, company } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    category: '',
    fileType: '',
    employee: '',
    dateRange: ''
  });
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);

  useEffect(() => {
    loadDocuments();
    loadFolders();
  }, [selectedFolder]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use appropriate API based on user role
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      const response = await api.list(selectedFolder);
      
      const documentsData = response.data || response || [];
      setDocuments(documentsData);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadFolders = async () => {
    try {
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      const response = await api.folders();
      const foldersData = response.data || response || [];
      setFolders(foldersData);
    } catch (error) {
      console.error('Failed to load folders:', error);
    }
  };

  const handleUpload = async (files) => {
    if (!files || files.length === 0) return;
    
    try {
      setUploading(true);
      setUploadProgress(0);
      
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      const folderToUse = selectedFolder || 'General';
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const progress = ((i + 1) / files.length) * 100;
        setUploadProgress(progress);
        
        await api.upload(file, folderToUse);
      }
      
      // Reload documents after upload
      await loadDocuments();
      setShowUploadModal(false);
      setUploadProgress(0);
      
      // Show success message
      alert(`${files.length} file(s) uploaded successfully!`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDownload = async (document) => {
    try {
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      const response = await api.download(document.id);
      
      // Create download link
      const blob = new Blob([response]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = document.original_filename || document.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      await api.delete(documentId);
      
      // Remove from local state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      setSelectedDocuments(prev => prev.filter(id => id !== documentId));
      
      alert('Document deleted successfully!');
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Delete failed. Please try again.');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedDocuments.length === 0) {
      alert('Please select documents to delete.');
      return;
    }
    
    if (!window.confirm(`Are you sure you want to delete ${selectedDocuments.length} document(s)?`)) {
      return;
    }
    
    try {
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      
      for (const docId of selectedDocuments) {
        await api.delete(docId);
      }
      
      // Reload documents
      await loadDocuments();
      setSelectedDocuments([]);
      
      alert(`${selectedDocuments.length} document(s) deleted successfully!`);
    } catch (error) {
      console.error('Bulk delete failed:', error);
      alert('Some documents could not be deleted. Please try again.');
    }
  };

  const handleBulkDownload = async () => {
    if (selectedDocuments.length === 0) {
      alert('Please select documents to download.');
      return;
    }
    
    try {
      const api = user.role === 'system_admin' ? systemDocumentsAPI : documentsAPI;
      
      for (const docId of selectedDocuments) {
        const doc = documents.find(d => d.id === docId);
        if (doc) {
          await handleDownload(doc);
        }
      }
      
      alert(`${selectedDocuments.length} document(s) download started!`);
    } catch (error) {
      console.error('Bulk download failed:', error);
      alert('Some documents could not be downloaded. Please try again.');
    }
  };

  const getFileIcon = (fileType) => {
    if (!fileType) return <File className="h-8 w-8 text-gray-500" />;
    
    switch (fileType.toLowerCase()) {
      case 'pdf':
        return <FileText className="h-8 w-8 text-red-500" />;
      case 'docx':
      case 'doc':
        return <FileText className="h-8 w-8 text-blue-500" />;
      case 'xlsx':
      case 'xls':
        return <FileText className="h-8 w-8 text-green-500" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
        return <Image className="h-8 w-8 text-purple-500" />;
      case 'mp4':
      case 'avi':
        return <Video className="h-8 w-8 text-orange-500" />;
      case 'mp3':
      case 'wav':
        return <Music className="h-8 w-8 text-pink-500" />;
      case 'zip':
      case 'rar':
        return <Archive className="h-8 w-8 text-yellow-500" />;
      default:
        return <File className="h-8 w-8 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  const toggleStar = (documentId) => {
    // This would need to be implemented in the backend
    // For now, just update local state
    setDocuments(prev => 
      prev.map(doc => 
        doc.id === documentId ? { ...doc, starred: !doc.starred } : doc
      )
    );
  };

  const toggleSelection = (documentId) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const handleShare = (document) => {
    // This would need to be implemented in the backend
    alert(`Share functionality for ${document.original_filename || document.name} would be implemented here.`);
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = 
      (doc.original_filename || doc.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.category || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.user?.full_name || doc.uploadedBy || '').toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = !filters.category || doc.category === filters.category;
    const matchesFileType = !filters.fileType || (doc.file_type || doc.type) === filters.fileType;
    const matchesEmployee = !filters.employee || (doc.user?.full_name || doc.uploadedBy) === filters.employee;
    
    return matchesSearch && matchesCategory && matchesFileType && matchesEmployee;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">{error}</div>
        <button 
          onClick={loadDocuments}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Organisation Files</h2>
          <p className="text-gray-600">Manage and organize your company documents</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowUploadModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Upload className="h-4 w-4" />
            <span>Upload Files</span>
          </button>
          
          {selectedDocuments.length > 0 && (
            <>
              <button 
                onClick={handleBulkDownload}
                className="bg-green-600 text-white px-4 py-2 rounded-xl hover:bg-green-700 transition-colors flex items-center space-x-2"
              >
                <Download className="h-4 w-4" />
                <span>Download ({selectedDocuments.length})</span>
              </button>
              
              <button 
                onClick={handleBulkDelete}
                className="bg-red-600 text-white px-4 py-2 rounded-xl hover:bg-red-700 transition-colors flex items-center space-x-2"
              >
                <Trash2 className="h-4 w-4" />
                <span>Delete ({selectedDocuments.length})</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Folder Selection */}
      {folders.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Current Folder</h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedFolder(null)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                !selectedFolder 
                  ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All Documents
            </button>
            {folders.map((folder) => (
              <button
                key={folder.id || folder.name}
                onClick={() => setSelectedFolder(folder.name)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  selectedFolder === folder.name 
                    ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {folder.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-4 mb-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search documents..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-xl leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-xl border transition-colors ${
              showFilters 
                ? 'bg-blue-50 text-blue-700 border-blue-200' 
                : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
            }`}
          >
            <Filter className="h-4 w-4 inline mr-2" />
            Filters
          </button>

          {/* View Mode Toggle */}
          <div className="flex border border-gray-200 rounded-xl overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 transition-colors ${
                viewMode === 'grid' 
                  ? 'bg-blue-50 text-blue-700' 
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 transition-colors ${
                viewMode === 'list' 
                  ? 'bg-blue-50 text-blue-700' 
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="border-t border-gray-200 pt-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Document Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Categories</option>
                  <option value="HR">HR</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Data">Data</option>
                  <option value="Legal">Legal</option>
                  <option value="Finance">Finance</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">File Type</label>
                <select
                  value={filters.fileType}
                  onChange={(e) => setFilters(prev => ({ ...prev, fileType: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Types</option>
                  <option value="pdf">PDF</option>
                  <option value="docx">DOCX</option>
                  <option value="xlsx">XLSX</option>
                  <option value="png">PNG</option>
                  <option value="jpg">JPG</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Employees</label>
                <select
                  value={filters.employee}
                  onChange={(e) => setFilters(prev => ({ ...prev, employee: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Employees</option>
                  {Array.from(new Set(documents.map(doc => doc.user?.full_name || doc.uploadedBy).filter(Boolean))).map(name => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="quarter">This Quarter</option>
                  <option value="year">This Year</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={() => setFilters({ category: '', fileType: '', employee: '', dateRange: '' })}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Clear All Filters
              </button>
              
              <div className="text-sm text-gray-500">
                {filteredDocuments.length} of {documents.length} documents
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Documents Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredDocuments.map((document) => (
            <div
              key={document.id}
              className={`bg-white rounded-xl shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer ${
                selectedDocuments.includes(document.id) ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => toggleSelection(document.id)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.includes(document.id)}
                    onChange={(e) => {
                      e.stopPropagation();
                      toggleSelection(document.id);
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  {getFileIcon(document.file_type || document.type)}
                </div>
                
                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleStar(document.id);
                    }}
                    className={`p-1 rounded hover:bg-gray-100 ${
                      document.starred ? 'text-yellow-500' : 'text-gray-400'
                    }`}
                  >
                    <Star className={`h-4 w-4 ${document.starred ? 'fill-current' : ''}`} />
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Show more options
                    }}
                    className="p-1 rounded hover:bg-gray-100 text-gray-400"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-medium text-gray-900 truncate" title={document.original_filename || document.name}>
                  {document.original_filename || document.name}
                </h3>
                
                <div className="text-sm text-gray-500 space-y-1">
                  <div className="flex items-center space-x-2">
                    <span>{formatFileSize(document.file_size || document.size)}</span>
                    <span>•</span>
                    <span>{formatDate(document.created_at || document.uploadDate)}</span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <User className="h-3 w-3" />
                    <span>{document.user?.full_name || document.uploadedBy || 'Unknown'}</span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Folder className="h-3 w-3" />
                    <span>{document.category || document.folder || 'General'}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 pt-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(document);
                    }}
                    className="p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
                    title="Download"
                  >
                    <Download className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleShare(document);
                    }}
                    className="p-2 rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
                    title="Share"
                  >
                    <Share className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(document.id);
                    }}
                    className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.length === filteredDocuments.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedDocuments(filteredDocuments.map(doc => doc.id));
                        } else {
                          setSelectedDocuments([]);
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredDocuments.map((document) => (
                  <tr key={document.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedDocuments.includes(document.id)}
                        onChange={() => toggleSelection(document.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          {getFileIcon(document.file_type || document.type)}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{document.original_filename || document.name}</div>
                          <div className="text-sm text-gray-500">{document.file_type || document.type}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {document.category || document.folder || 'General'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatFileSize(document.file_size || document.size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {document.user?.full_name || document.uploadedBy || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(document.created_at || document.uploadDate)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDownload(document)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleShare(document)}
                          className="text-green-600 hover:text-green-900"
                          title="Share"
                        >
                          <Share className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(document.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {filteredDocuments.length === 0 && (
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No documents found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery || Object.values(filters).some(f => f) 
              ? 'Try adjusting your search or filters.' 
              : 'Get started by uploading your first document.'}
          </p>
          {!searchQuery && !Object.values(filters).some(f => f) && (
            <div className="mt-6">
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="-ml-1 mr-2 h-5 w-5" />
                Upload Document
              </button>
            </div>
          )}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-xl bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Upload Documents</h3>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-4">
                  <p className="text-sm text-gray-600">
                    Drag and drop files here, or{' '}
                    <label className="text-blue-600 hover:text-blue-500 font-medium cursor-pointer">
                      browse
                      <input
                        type="file"
                        multiple
                        className="hidden"
                        onChange={(e) => handleUpload(Array.from(e.target.files))}
                        accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg,.txt,.csv"
                      />
                    </label>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    PDF, DOCX, XLSX, PNG, JPG up to 10MB
                  </p>
                </div>
                
                {uploading && (
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">Uploading... {Math.round(uploadProgress)}%</p>
                  </div>
                )}
              </div>
              
              <div className="mt-4 flex justify-end space-x-3">
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedDocumentManager;
