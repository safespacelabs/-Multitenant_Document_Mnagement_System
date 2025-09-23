import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { 
  FolderPlus, 
  Upload, 
  Search, 
  Filter, 
  Download, 
  Share, 
  Edit, 
  Trash2, 
  Eye, 
  CheckCircle, 
  X, 
  Clock, 
  Calendar, 
  UserPlus, 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  FolderOpen, 
  Archive, 
  Lock, 
  Unlock, 
  Bell, 
  Settings, 
  Plus, 
  Grid, 
  List, 
  ChevronDown, 
  MoreVertical, 
  Star, 
  BookOpen, 
  Clipboard, 
  Target, 
  Award, 
  Clock1, 
  UserCheck, 
  FileSignature, 
  User, 
  Folder,
  FileText,
  Users,
  BarChart3,
  Bot,
  Brain,
  Zap
} from 'lucide-react';

const HRUserFolders = () => {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('folders');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // State for different sections
  const [folders, setFolders] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [documents, setDocuments] = useState([]);
  
  // Form states
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showUploadDocument, setShowUploadDocument] = useState(false);
  const [newFolder, setNewFolder] = useState({
    name: '',
    display_name: '',
    description: '',
    user_id: '',
    folder_type: 'hr_managed',
    sort_order: 0
  });
  
  // Confirmation states
  const [showDeleteFolderConfirm, setShowDeleteFolderConfirm] = useState(false);
  const [showDeleteDocumentConfirm, setShowDeleteDocumentConfirm] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  
  // AI processing states
  const [processingAI, setProcessingAI] = useState({});
  const [aiAnalysisResults, setAiAnalysisResults] = useState({});
  const [showAIAnalysis, setShowAIAnalysis] = useState({});
  
  // E-signature states
  const [showSigningModal, setShowSigningModal] = useState(false);
  const [selectedDocumentForSigning, setSelectedDocumentForSigning] = useState(null);
  const [signingDocument, setSigningDocument] = useState(false);
  
  // Search and filters
  const [searchTerm, setSearchTerm] = useState('');
  const [userFilter, setUserFilter] = useState('');
  const [folderTypeFilter, setFolderTypeFilter] = useState('');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load users list
      await loadUsers();
      
      // Load folders list
      await loadFolders();
      
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError('Failed to load data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await fetch('/api/hr-admin/company/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const usersData = await response.json();
        setUsers(usersData);
      } else {
        throw new Error('Failed to load users');
      }
    } catch (err) {
      console.error('Error loading users:', err);
      throw err;
    }
  };

  const loadFolders = async () => {
    try {
      let url = '/api/hr-user-folders/folders';
      const params = new URLSearchParams();
      
      if (userFilter) params.append('user_id', userFilter);
      if (folderTypeFilter) params.append('folder_type', folderTypeFilter);
      if (searchTerm) params.append('search', searchTerm);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const foldersData = await response.json();
        setFolders(foldersData);
      } else {
        throw new Error('Failed to load folders');
      }
    } catch (err) {
      console.error('Error loading folders:', err);
      throw err;
    }
  };

  const createFolder = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/hr-user-folders/folders', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newFolder)
      });
      
      if (response.ok) {
        const createdFolder = await response.json();
        setFolders(prev => [createdFolder, ...prev]);
        setShowCreateFolder(false);
        setNewFolder({
          name: '',
          display_name: '',
          description: '',
          user_id: '',
          folder_type: 'hr_managed',
          sort_order: 0
        });
        
        // Show success message
        alert('Folder created successfully!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create folder');
      }
    } catch (err) {
      console.error('Error creating folder:', err);
      alert(`Error creating folder: ${err.message}`);
    }
  };

  const uploadDocument = async (formData) => {
    try {
      const response = await fetch(`/api/hr-user-folders/folders/${selectedFolder.id}/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });
      
      if (response.ok) {
        const uploadedDoc = await response.json();
        setDocuments(prev => [uploadedDoc, ...prev]);
        setShowUploadDocument(false);
        
        // Show success message
        alert('Document uploaded successfully!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload document');
      }
    } catch (err) {
      console.error('Error uploading document:', err);
      alert(`Error uploading document: ${err.message}`);
    }
  };

  const deleteFolder = async (folderId) => {
    setItemToDelete({ type: 'folder', id: folderId });
    setShowDeleteFolderConfirm(true);
  };

  const confirmDeleteFolder = async () => {
    const folderId = itemToDelete.id;
    
    try {
      const response = await fetch(`/api/hr-user-folders/folders/${folderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setFolders(prev => prev.filter(f => f.id !== folderId));
        if (selectedFolder?.id === folderId) {
          setSelectedFolder(null);
          setDocuments([]);
        }
        alert('Folder deleted successfully!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete folder');
      }
    } catch (err) {
      console.error('Error deleting folder:', err);
      alert(`Error deleting folder: ${err.message}`);
    } finally {
      setShowDeleteFolderConfirm(false);
      setItemToDelete(null);
    }
  };

  const deleteDocument = async (documentId) => {
    setItemToDelete({ type: 'document', id: documentId });
    setShowDeleteDocumentConfirm(true);
  };

  const confirmDeleteDocument = async () => {
    const documentId = itemToDelete.id;
    
    try {
      const response = await fetch(`/api/hr-user-folders/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setDocuments(prev => prev.filter(d => d.id !== documentId));
        alert('Document deleted successfully!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete document');
      }
    } catch (err) {
      console.error('Error deleting document:', err);
      alert(`Error deleting document: ${err.message}`);
    } finally {
      setShowDeleteDocumentConfirm(false);
      setItemToDelete(null);
    }
  };

  const viewDocument = async (documentId) => {
    try {
      const response = await fetch(`/api/hr-user-folders/documents/${documentId}/view`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get document view URL');
      }
      
      const data = await response.json();
      
      // Open document in new tab
      window.open(data.download_url, '_blank');
      
    } catch (error) {
      console.error('Error viewing document:', error);
      alert(`Error viewing document: ${error.message}`);
    }
  };

  const downloadDocument = async (documentId) => {
    try {
      const response = await fetch(`/api/hr-user-folders/documents/${documentId}/download`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to download document');
      }
      
      // Get the filename from the response headers or use a default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'document';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('Error downloading document:', error);
      alert(`Error downloading document: ${error.message}`);
    }
  };

  const canSignDirectly = user?.role === 'system_admin' || user?.role === 'hr_admin' || user?.role === 'hr_manager';

  const handleDirectSign = (document) => {
    setSelectedDocumentForSigning(document);
    setShowSigningModal(true);
  };

  const handleSignDocument = async () => {
    if (!selectedDocumentForSigning) return;
    
    try {
      setSigningDocument(true);
      
      // Call the e-signature API to sign the document directly
      const response = await fetch(`/api/esignature/sign-document-directly/${selectedDocumentForSigning.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          signature_text: `${user.full_name} - ${user.role}`,
          ip_address: window.location.hostname || 'unknown',
          user_agent: navigator.userAgent
        })
      });

      if (response.ok) {
        alert('Document signed successfully!');
        setShowSigningModal(false);
        setSelectedDocumentForSigning(null);
        // Refresh the documents list
        if (selectedFolder) {
          openFolder(selectedFolder);
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign document');
      }
    } catch (error) {
      console.error('Error signing document:', error);
      alert(`Error signing document: ${error.message}`);
    } finally {
      setSigningDocument(false);
    }
  };

  const openFolder = async (folder) => {
    setSelectedFolder(folder);
    setActiveTab('documents');
    
    try {
      const response = await fetch(`/api/hr-user-folders/folders/${folder.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const folderData = await response.json();
        setDocuments(folderData.documents);
        
        // Check AI analysis status for all documents
        folderData.documents.forEach(doc => {
          checkAIAnalysis(doc.id);
        });
      } else {
        throw new Error('Failed to load folder contents');
      }
    } catch (err) {
      console.error('Error loading folder contents:', err);
      alert(`Error loading folder contents: ${err.message}`);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  // AI Processing Functions
  const processDocumentWithAI = async (documentId) => {
    setProcessingAI(prev => ({ ...prev, [documentId]: true }));
    
    try {
      const response = await fetch(`/api/hr-user-folders/documents/${documentId}/process-ai`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const result = await response.json();
      
      if (response.ok) {
        if (result.already_processed) {
          alert('Document already processed by AI!');
        } else {
          alert('Document processed successfully with AI!');
          console.log('AI Analysis Result:', result);
        }
        
        // Normalize state by fetching canonical analysis status from GET endpoint
        const refreshed = await checkAIAnalysis(documentId);
        if (refreshed && refreshed.ai_processed !== undefined) {
          setAiAnalysisResults(prev => ({ ...prev, [documentId]: refreshed }));
        } else {
          // Fallback: mark as processed locally to avoid UI saying "Not Processed"
          setAiAnalysisResults(prev => ({
            ...prev,
            [documentId]: {
              ai_processed: true,
              analysis: result.analysis,
              processed_at: new Date().toISOString()
            }
          }));
        }
        
        // Refresh documents to show updated status
        if (selectedFolder) {
          await openFolder(selectedFolder);
        }
      } else {
        alert(`Error: ${result.detail}`);
      }
    } catch (error) {
      console.error('Error processing document with AI:', error);
      alert('Failed to process document with AI');
    } finally {
      setProcessingAI(prev => ({ ...prev, [documentId]: false }));
    }
  };

  const checkAIAnalysis = async (documentId) => {
    try {
      const response = await fetch(`/api/hr-user-folders/documents/${documentId}/ai-analysis`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      const result = await response.json();
      setAiAnalysisResults(prev => ({ ...prev, [documentId]: result }));
      return result;
    } catch (error) {
      console.error('Error checking AI analysis:', error);
      return null;
    }
  };

  const toggleAIAnalysis = (documentId) => {
    setShowAIAnalysis(prev => ({ ...prev, [documentId]: !prev[documentId] }));
    
    // Load AI analysis if not already loaded
    if (!aiAnalysisResults[documentId]) {
      checkAIAnalysis(documentId);
    } else if (aiAnalysisResults[documentId] && aiAnalysisResults[documentId].ai_processed === undefined) {
      // If we only have a raw POST response (no ai_processed flag), refresh from GET
      checkAIAnalysis(documentId);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <button
                  onClick={loadInitialData}
                  className="mt-3 bg-red-100 text-red-800 px-3 py-1 rounded-md text-sm hover:bg-red-200"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">HR User Folders</h1>
              <p className="text-sm text-gray-600">Manage user folders and documents</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowCreateFolder(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <FolderPlus className="h-4 w-4 mr-2" />
                Create Folder
              </button>
              {selectedFolder && (
                <button
                  onClick={() => setShowUploadDocument(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Document
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('folders')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'folders'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Folder className="h-4 w-4 inline mr-2" />
              Folders
            </button>
            {selectedFolder && (
              <button
                onClick={() => setActiveTab('documents')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'documents'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <FileText className="h-4 w-4 inline mr-2" />
                Documents in {selectedFolder.display_name}
              </button>
            )}
          </nav>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search folders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by User</label>
            <select
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Users</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>{user.full_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Type</label>
            <select
              value={folderTypeFilter}
              onChange={(e) => setFolderTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="hr_managed">HR Managed</option>
              <option value="user_created">User Created</option>
              <option value="system">System</option>
            </select>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'folders' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">User Folders</h3>
              <p className="text-sm text-gray-600">Manage folders for different users</p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Folder</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Documents</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {folders.map((folder) => (
                    <tr key={folder.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Folder className="h-5 w-5 text-blue-500 mr-3" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">{folder.display_name}</div>
                            {folder.description && (
                              <div className="text-sm text-gray-500">{folder.description}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {users.find(u => u.id === folder.user_id)?.full_name || folder.user_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          folder.folder_type === 'hr_managed' ? 'bg-blue-100 text-blue-800' :
                          folder.folder_type === 'user_created' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {folder.folder_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {folder.documents_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatFileSize(folder.total_size)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(folder.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => openFolder(folder)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => deleteFolder(folder.id)}
                            className="text-red-600 hover:text-red-900"
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

        {activeTab === 'documents' && selectedFolder && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Documents in {selectedFolder.display_name}</h3>
                  <p className="text-sm text-gray-600">
                    User: {users.find(u => u.id === selectedFolder.user_id)?.full_name || selectedFolder.user_id}
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab('folders')}
                  className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                >
                  ← Back to Folders
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Document</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documents.map((document) => (
                    <React.Fragment key={document.id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <FileText className="h-5 w-5 text-gray-400 mr-3" />
                            <div>
                              <div className="text-sm font-medium text-gray-900">{document.original_filename}</div>
                              {document.description && (
                                <div className="text-sm text-gray-500">{document.description}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {document.document_category || 'N/A'}
                          </div>
                          {document.document_subcategory && (
                            <div className="text-sm text-gray-500">{document.document_subcategory}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatFileSize(document.file_size)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col space-y-1">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              document.status === 'active' ? 'bg-green-100 text-green-800' :
                              document.status === 'archived' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {document.status}
                            </span>
                            {aiAnalysisResults[document.id]?.ai_processed ? (
                              <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                                <Bot className="h-3 w-3 mr-1" />
                                AI Processed
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">
                                <Clock className="h-3 w-3 mr-1" />
                                Not Processed
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(document.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => downloadDocument(document.id)}
                              className="text-blue-600 hover:text-blue-900"
                              title="Download Document"
                            >
                              <Download className="h-4 w-4" />
                            </button>
                            <button 
                              onClick={() => viewDocument(document.id)}
                              className="text-green-600 hover:text-green-900"
                              title="View Document"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => processDocumentWithAI(document.id)}
                              disabled={processingAI[document.id]}
                              className={`${processingAI[document.id] ? 'text-gray-400' : 'text-purple-600 hover:text-purple-900'}`}
                              title="Process with AI"
                            >
                              {processingAI[document.id] ? (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                              ) : (
                                <Bot className="h-4 w-4" />
                              )}
                            </button>
                            <button
                              onClick={() => toggleAIAnalysis(document.id)}
                              className="text-indigo-600 hover:text-indigo-900"
                              title="View AI Analysis"
                            >
                              <Brain className="h-4 w-4" />
                            </button>
                            {canSignDirectly && (
                              <button
                                onClick={() => handleDirectSign(document)}
                                className="text-green-600 hover:text-green-900"
                                title="Sign Document"
                              >
                                <FileSignature className="h-4 w-4" />
                              </button>
                            )}
                            <button
                              onClick={() => deleteDocument(document.id)}
                              className="text-red-600 hover:text-red-900"
                              title="Delete Document"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                      {/* AI Analysis Section */}
                      {showAIAnalysis[document.id] && (
                        <tr>
                          <td colSpan="6" className="px-6 py-4 bg-gray-50">
                            <div className="bg-white border border-gray-200 rounded-lg p-4">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="text-sm font-medium text-gray-900 flex items-center">
                                  <Brain className="h-4 w-4 mr-2 text-indigo-600" />
                                  AI Analysis Results
                                </h4>
                                <button
                                  onClick={() => toggleAIAnalysis(document.id)}
                                  className="text-gray-400 hover:text-gray-600"
                                >
                                  <X className="h-4 w-4" />
                                </button>
                              </div>
                              
                              {aiAnalysisResults[document.id] ? (
                                aiAnalysisResults[document.id].ai_processed ? (
                                  <div className="space-y-3">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                      <div>
                                        <label className="text-xs font-medium text-gray-500">Title</label>
                                        <p className="text-sm text-gray-900">{aiAnalysisResults[document.id].analysis.title}</p>
                                      </div>
                                      <div>
                                        <label className="text-xs font-medium text-gray-500">Document Type</label>
                                        <p className="text-sm text-gray-900">{aiAnalysisResults[document.id].analysis.document_type}</p>
                                      </div>
                                      <div>
                                        <label className="text-xs font-medium text-gray-500">Language</label>
                                        <p className="text-sm text-gray-900">{aiAnalysisResults[document.id].analysis.language}</p>
                                      </div>
                                      <div>
                                        <label className="text-xs font-medium text-gray-500">Word Count</label>
                                        <p className="text-sm text-gray-900">{aiAnalysisResults[document.id].analysis.word_count}</p>
                                      </div>
                                    </div>
                                    
                                    <div>
                                      <label className="text-xs font-medium text-gray-500">Summary</label>
                                      <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                                        {aiAnalysisResults[document.id].analysis.summary}
                                      </p>
                                    </div>
                                    
                                    {aiAnalysisResults[document.id].analysis.expiry_detected && (
                                      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                                        <div className="flex items-center">
                                          <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2" />
                                          <span className="text-sm font-medium text-yellow-800">Expiry Detected</span>
                                        </div>
                                        <p className="text-sm text-yellow-700 mt-1">
                                          Expiry Date: {aiAnalysisResults[document.id].analysis.expiry_date}
                                        </p>
                                        <p className="text-sm text-yellow-700">
                                          Urgency Level: {aiAnalysisResults[document.id].analysis.urgency_level}
                                        </p>
                                      </div>
                                    )}
                                    
                                    <details className="mt-3">
                                      <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                                        View Full AI Analysis JSON
                                      </summary>
                                      <pre className="mt-2 text-xs bg-gray-100 p-3 rounded-md overflow-auto max-h-64">
                                        {JSON.stringify(aiAnalysisResults[document.id].analysis, null, 2)}
                                      </pre>
                                    </details>
                                  </div>
                                ) : (
                                  <div className="text-center py-4">
                                    <Bot className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                                    <p className="text-sm text-gray-600 mb-3">
                                      This document has not been processed by AI yet.
                                    </p>
                                    <button
                                      onClick={() => processDocumentWithAI(document.id)}
                                      disabled={processingAI[document.id]}
                                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                                    >
                                      {processingAI[document.id] ? (
                                        <>
                                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                          Processing...
                                        </>
                                      ) : (
                                        <>
                                          <Zap className="h-4 w-4 mr-2" />
                                          Process with AI
                                        </>
                                      )}
                                    </button>
                                  </div>
                                )
                              ) : (
                                <div className="text-center py-4">
                                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                                  <p className="text-sm text-gray-600 mt-2">Loading AI analysis...</p>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Create Folder Modal */}
      {showCreateFolder && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Folder</h3>
              <form onSubmit={createFolder}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Folder Name</label>
                  <input
                    type="text"
                    required
                    value={newFolder.name}
                    onChange={(e) => setNewFolder(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter folder name"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <input
                    type="text"
                    required
                    value={newFolder.display_name}
                    onChange={(e) => setNewFolder(prev => ({ ...prev, display_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter display name"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={newFolder.description}
                    onChange={(e) => setNewFolder(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter description"
                    rows="3"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">User</label>
                  <select
                    required
                    value={newFolder.user_id}
                    onChange={(e) => setNewFolder(prev => ({ ...prev, user_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select a user</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>{user.full_name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateFolder(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
                  >
                    Create Folder
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {showUploadDocument && selectedFolder && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Document</h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                uploadDocument(formData);
              }}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">File</label>
                  <input
                    type="file"
                    name="file"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    name="document_category"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select category</option>
                    <option value="Career Development">Career Development</option>
                    <option value="Compensation">Compensation</option>
                    <option value="Performance">Performance</option>
                    <option value="Training">Training</option>
                    <option value="Compliance">Compliance</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    name="description"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter document description"
                    rows="3"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowUploadDocument(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700"
                  >
                    Upload
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Folder Confirmation Modal */}
      {showDeleteFolderConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Confirm Delete</h3>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to delete this folder? This will also delete all documents inside.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteFolderConfirm(false);
                    setItemToDelete(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteFolder}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700"
                >
                  Delete Folder
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Document Confirmation Modal */}
      {showDeleteDocumentConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Confirm Delete</h3>
              <p className="text-sm text-gray-600 mb-6">
                Are you sure you want to delete this document?
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteDocumentConfirm(false);
                    setItemToDelete(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteDocument}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700"
                >
                  Delete Document
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* E-Signature Modal */}
      {showSigningModal && selectedDocumentForSigning && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Sign Document</h3>
              <p className="text-sm text-gray-600 mb-4">
                You are about to sign: <strong>{selectedDocumentForSigning.original_filename}</strong>
              </p>
              <p className="text-sm text-gray-600 mb-6">
                Signature will be: <strong>{user.full_name} - {user.role}</strong>
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowSigningModal(false);
                    setSelectedDocumentForSigning(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSignDocument}
                  disabled={signingDocument}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  {signingDocument ? 'Signing...' : 'Sign Document'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HRUserFolders;
