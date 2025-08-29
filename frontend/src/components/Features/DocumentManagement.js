import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../utils/auth';
import { documentsAPI, systemDocumentsAPI } from '../../services/api';
import DocumentESignatureIntegration from '../ESignature/DocumentESignatureIntegration';
import { 
  Upload, 
  FileText, 
  Download, 
  Trash2, 
  Eye, 
  Search,
  Filter,
  FileIcon,
  Image,
  FileVideo,
  Archive,
  Grid,
  List,
  Clock,
  User,
  CheckCircle,
  AlertCircle,
  Folder,
  FolderPlus,
  Users,
  Plus,
  X
} from 'lucide-react';

const DocumentManagement = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState('all');
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadingFile, setUploadingFile] = useState(null);
  const [filterBy, setFilterBy] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  
  // Folder navigation state
  const [currentFolderPath, setCurrentFolderPath] = useState([]);
  const [showFolderNavigation, setShowFolderNavigation] = useState(false);
  
  // Admin signing state
  const [showSigningModal, setShowSigningModal] = useState(false);
  const [selectedDocumentForSigning, setSelectedDocumentForSigning] = useState(null);
  
  // HR User Folders state
  const [showUserSearch, setShowUserSearch] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userFolders, setUserFolders] = useState([]);
  const [userDocuments, setUserDocuments] = useState([]);
  const [showCreateUserFolder, setShowCreateUserFolder] = useState(false);
  const [newUserFolder, setNewUserFolder] = useState({
    name: '',
    display_name: '',
    description: '',
    user_id: '',
    folder_type: 'hr_managed',
    sort_order: 0
  });
  const [showUploadToUserFolder, setShowUploadToUserFolder] = useState(false);
  const [selectedUserFolder, setSelectedUserFolder] = useState(null);
     const [companyUsers, setCompanyUsers] = useState([]);
   const [userSearchTerm, setUserSearchTerm] = useState('');
   const [filteredUsers, setFilteredUsers] = useState([]);
   const [loadingUsers, setLoadingUsers] = useState(false);
   const [loadingFolders, setLoadingFolders] = useState(false);

  // Determine if user is system admin
  const isSystemAdmin = user?.role === 'system_admin';
  
  // Check if user can sign documents directly (admin roles)
  const canSignDirectly = user?.role === 'system_admin' || user?.role === 'hr_admin' || user?.role === 'hr_manager';
  
  // Use appropriate API based on user role
  const docsAPI = isSystemAdmin ? systemDocumentsAPI : documentsAPI;

  useEffect(() => {
    fetchDocuments();
    fetchFolders();
    if (user?.role === 'hr_admin' || user?.role === 'hr_manager' || user?.role === 'system_admin') {
      // Test backend connectivity first
      testBackendConnection().then(() => {
        fetchCompanyUsers();
      }).catch(err => {
        console.error('Backend connection test failed:', err);
        setError('Cannot connect to backend server. Please check if the server is running.');
      });
    }
  }, [selectedFolder, isSystemAdmin, user?.role]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const folderParam = selectedFolder === 'all' ? null : (selectedFolder === 'root' ? '' : selectedFolder);
      const response = await docsAPI.list(folderParam);
      
      // Ensure documents is always an array
      let documentsData;
      if (Array.isArray(response)) {
        documentsData = response;
      } else if (response && response.data && Array.isArray(response.data)) {
        documentsData = response.data;
      } else if (response && typeof response === 'object') {
        documentsData = response.documents || response.items || [];
      } else {
        console.warn('Unexpected documents response format:', response);
        documentsData = [];
      }
      
      console.log('📄 Documents response:', response);
      console.log('📄 Processed documents data:', documentsData);
      setDocuments(documentsData);
      setError('');
    } catch (err) {
      setError('Failed to fetch documents: ' + err.message);
      console.error('Error fetching documents:', err);
      setDocuments([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const fetchFolders = async () => {
    try {
      const response = isSystemAdmin ? 
        await systemDocumentsAPI.getFolders() : 
        await documentsAPI.folders();
      
      console.log('📁 Folders API response:', response);
      
      // Handle different response formats
      let foldersData;
      if (Array.isArray(response)) {
        // Direct array response
        foldersData = response;
      } else if (response && response.data && Array.isArray(response.data)) {
        // Response wrapped in data property
        foldersData = response.data;
      } else if (response && typeof response === 'object') {
        // Try to extract data from response object
        foldersData = response.data || response.folders || [];
      } else {
        console.warn('Unexpected folders response format:', response);
        foldersData = [];
      }
      
      console.log('📁 Processed folders data:', foldersData);
      setFolders(foldersData);
    } catch (err) {
      console.error('Error fetching folders:', err);
      setFolders([]); // Set empty array on error
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setUploadingFile(file.name);
      setError('');
      
      const folderName = selectedFolder === 'all' || selectedFolder === 'root' ? null : selectedFolder;
      await docsAPI.upload(file, folderName);
      
      // Refresh documents and folders
      await fetchDocuments();
      await fetchFolders();
      
      // Reset file input
      event.target.value = '';
    } catch (err) {
      setError('Failed to upload file: ' + err.message);
      console.error('Error uploading file:', err);
    } finally {
      setUploadingFile(null);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      // Upload a dummy file to create the folder (this will trigger folder creation)
      const dummyFile = new File([''], 'folder_placeholder.txt', { type: 'text/plain' });
      await docsAPI.upload(dummyFile, newFolderName.trim());
      
      // Refresh folders
      await fetchFolders();
      
      setNewFolderName('');
      setShowNewFolder(false);
      setError('');
    } catch (err) {
      setError('Failed to create folder: ' + err.message);
      console.error('Error creating folder:', err);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await docsAPI.delete(docId);
      await fetchDocuments();
      setError('');
    } catch (err) {
      setError('Failed to delete document: ' + err.message);
      console.error('Error deleting document:', err);
    }
  };

  // Folder navigation functions
  const navigateToFolder = (folderName) => {
    setCurrentFolderPath([...currentFolderPath, folderName]);
    setSelectedFolder(folderName);
    setShowFolderNavigation(true);
  };

  const navigateBack = () => {
    const newPath = [...currentFolderPath];
    newPath.pop();
    setCurrentFolderPath(newPath);
    
    if (newPath.length === 0) {
      setSelectedFolder('all');
      setShowFolderNavigation(false);
    } else {
      setSelectedFolder(newPath[newPath.length - 1]);
    }
  };

  const navigateToRoot = () => {
    setCurrentFolderPath([]);
    setSelectedFolder('all');
    setShowFolderNavigation(false);
  };

  // Admin signing functions
  const handleDirectSign = (document) => {
    setSelectedDocumentForSigning(document);
    setShowSigningModal(true);
  };

  const handleSignDocument = async () => {
    try {
      // Call the e-signature API to sign the document directly
             const response = await fetch(`https://multitenant-backend-mlap.onrender.com/api/esignature/sign-document-directly/${selectedDocumentForSigning.id}`, {
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

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign document');
      }

      setShowSigningModal(false);
      setSelectedDocumentForSigning(null);
      await fetchDocuments(); // Refresh documents
      setError('');
    } catch (err) {
      setError('Failed to sign document: ' + err.message);
      console.error('Error signing document:', err);
    }
  };

  const filteredDocuments = (Array.isArray(documents) ? documents : []).filter(doc => {
    if (searchTerm) {
      return doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase());
    }
    if (filterBy === 'all') return true;
    if (filterBy === 'recent') {
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      return new Date(doc.created_at) > oneWeekAgo;
    }
    if (filterBy === 'processed') return doc.processed;
    if (filterBy === 'unprocessed') return !doc.processed;
    return true;
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Test backend connectivity
  const testBackendConnection = async () => {
    try {
      // Try to access a simple endpoint to test connectivity
      const response = await fetch('https://multitenant-backend-mlap.onrender.com/api/hr-admin/company/users', { 
        method: 'HEAD',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      console.log('✅ Backend connection test successful');
    } catch (err) {
      console.error('❌ Backend connection test failed:', err);
      throw new Error('Backend server is not accessible');
    }
  };

  // HR User Folders functions
  const fetchCompanyUsers = async () => {
    try {
      setLoadingUsers(true);
      const token = localStorage.getItem('access_token');
      console.log('🔑 Token for API call:', token ? `${token.substring(0, 20)}...` : 'No token found');
      
      if (!token) {
        throw new Error('No access token found. Please log in again.');
      }
      
      const response = await fetch('https://multitenant-backend-mlap.onrender.com/api/hr-admin/company/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const usersData = await response.json();
        // Filter out system_admin users - only show company users
        const companyUsersOnly = usersData.filter(user => user.role !== 'system_admin');
        console.log('👥 Company users loaded:', companyUsersOnly.length, 'users');
        console.log('👥 Company users details:', companyUsersOnly.map(u => ({ 
          id: u.id, 
          name: u.full_name, 
          role: u.role, 
          company_id: u.company_id 
        })));
        setCompanyUsers(companyUsersOnly);
        setFilteredUsers(companyUsersOnly);
        setError(''); // Clear any previous errors
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('API Error Response:', response.status, errorData);
        throw new Error(`Failed to load users: ${response.status} ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error loading users:', err);
      setError(`Failed to load company users: ${err.message}`);
    } finally {
      setLoadingUsers(false);
    }
  };

  const searchUsers = (searchTerm) => {
    if (!searchTerm.trim()) {
      setFilteredUsers(companyUsers);
      return;
    }
    
    const filtered = companyUsers.filter(user => 
      user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.username?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredUsers(filtered);
  };

  const selectUser = async (user) => {
    console.log('👤 User selected:', user);
    console.log('👤 User ID:', user.id);
    console.log('👤 User name:', user.full_name);
    console.log('👤 User company_id:', user.company_id);
    
    setSelectedUser(user);
    setShowUserSearch(false);
    setUserSearchTerm(''); // Clear search term
    
    // Test the API endpoint before calling fetchUserFolders
    try {
      console.log('🧪 Testing API endpoint...');
      const testResponse = await fetch(`https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/users/${user.id}/folders`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      console.log('🧪 Test response status:', testResponse.status);
      console.log('🧪 Test response headers:', Object.fromEntries(testResponse.headers.entries()));
      
      if (!testResponse.ok) {
        const testError = await testResponse.json().catch(() => ({}));
        console.error('🧪 Test failed:', testResponse.status, testError);
      }
    } catch (testErr) {
      console.error('🧪 Test error:', testErr);
    }
    
    await fetchUserFolders(user.id);
  };

  const handleUserSearch = async (searchTerm) => {
    if (!searchTerm.trim()) {
      setFilteredUsers(companyUsers);
      return;
    }
    
    const filtered = companyUsers.filter(user => 
      user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.username?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredUsers(filtered);
  };

  const fetchUserFolders = async (userId) => {
    try {
      setLoadingFolders(true);
      console.log('📁 Fetching folders for user:', userId);
      console.log('🔐 Access token:', localStorage.getItem('access_token') ? 'Present' : 'Missing');
      console.log('🌐 Full URL:', `https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/users/${userId}/folders`);
      
      const response = await fetch(`https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/users/${userId}/folders`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('📥 Response status:', response.status);
      console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Folders loaded:', data);
        setUserFolders(data.folders || []);
        setError(''); // Clear any previous errors
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ Failed to load folders:', response.status, errorData);
        console.error('❌ Response text:', await response.text().catch(() => 'Could not read response'));
        throw new Error(`Failed to load user folders: ${response.status}`);
      }
    } catch (err) {
      console.error('Error loading user folders:', err);
      setError(`Failed to load folders: ${err.message}`);
      setUserFolders([]);
    } finally {
      setLoadingFolders(false);
    }
  };

  const openUserFolder = async (folder) => {
    setSelectedUserFolder(folder);
    try {
      console.log('📂 Opening folder:', folder.id, folder.display_name);
      const response = await fetch(`https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/folders/${folder.id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Folder contents loaded:', data);
        setUserDocuments(data.documents || []);
        setError(''); // Clear any previous errors
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ Failed to load folder contents:', response.status, errorData);
        throw new Error(`Failed to load folder contents: ${response.status}`);
      }
    } catch (err) {
      console.error('Error loading folder contents:', err);
      setError(`Failed to load folder contents: ${err.message}`);
      setUserDocuments([]);
    }
  };

  const createUserFolder = async (e) => {
    e.preventDefault();
    
    // Ensure user_id is set from selected user
    if (!newUserFolder.user_id) {
      setError('User ID is required. Please try again.');
      return;
    }
    
    try {
      console.log('📁 Creating folder with data:', newUserFolder);
      
      const response = await fetch('https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/folders', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newUserFolder)
      });
      
      if (response.ok) {
        const createdFolder = await response.json();
        console.log('✅ Folder created successfully:', createdFolder);
        setUserFolders(prev => [createdFolder, ...prev]);
        setShowCreateUserFolder(false);
        setNewUserFolder({
          name: '',
          display_name: '',
          description: '',
          user_id: '',
          folder_type: 'hr_managed',
          sort_order: 0
        });
        setError('');
        
        // Refresh folders to ensure data persistence
        await fetchUserFolders(selectedUser.id);
      } else {
        const errorData = await response.json();
        console.error('❌ Folder creation failed:', response.status, errorData);
        throw new Error(errorData.detail || 'Failed to create folder');
      }
    } catch (err) {
      setError('Failed to create folder: ' + err.message);
      console.error('Error creating folder:', err);
    }
  };

  const uploadToUserFolder = async (formData) => {
    try {
      // Create a new FormData with the correct structure
      const uploadFormData = new FormData();
      
      // Get the file from the original formData
      const file = formData.get('file');
      if (!file) {
        throw new Error('No file selected');
      }
      
      // Add the file
      uploadFormData.append('file', file);
      
      // Create metadata object and convert to JSON string
      const metadata = {
        document_category: formData.get('document_category') || '',
        document_subcategory: formData.get('document_subcategory') || '',
        description: formData.get('description') || '',
        tags: [],
        is_public: false,
        access_level: 'private',
        version: '1.0',
        status: 'active'
      };
      
      // Add the metadata as a JSON string
      uploadFormData.append('document_data', JSON.stringify(metadata));
      
      console.log('📤 Uploading file:', file.name, 'Size:', file.size, 'Type:', file.type);
      console.log('📤 Metadata:', metadata);
      
      const response = await fetch(`https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/folders/${selectedUserFolder.id}/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: uploadFormData
      });
      
      if (response.ok) {
        const uploadedDoc = await response.json();
        console.log('✅ Document uploaded successfully:', uploadedDoc);
        setUserDocuments(prev => [uploadedDoc, ...prev]);
        setShowUploadToUserFolder(false);
        setError('');
        
        // Refresh folder contents to ensure data persistence
        await openUserFolder(selectedUserFolder);
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Upload Error Response:', response.status, errorData);
        
        // Handle different error types
        if (response.status === 422) {
          // Validation error - show specific validation details
          if (errorData.detail && Array.isArray(errorData.detail)) {
            const validationErrors = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
            throw new Error(`Validation failed: ${validationErrors}`);
          } else if (errorData.detail) {
            throw new Error(`Validation failed: ${errorData.detail}`);
          } else {
            throw new Error('Document validation failed. Please check file type, size, and required fields.');
          }
        } else {
          throw new Error(errorData.detail || `Upload failed with status ${response.status}`);
        }
      }
    } catch (err) {
      setError('Failed to upload document: ' + err.message);
      console.error('Error uploading document:', err);
    }
  };

  const deleteUserFolder = async (folderId) => {
    if (!window.confirm('Are you sure you want to delete this folder? This will also delete all documents inside.')) {
      return;
    }
    
    try {
      const response = await fetch(`https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/folders/${folderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setUserFolders(prev => prev.filter(f => f.id !== folderId));
        if (selectedUserFolder?.id === folderId) {
          setSelectedUserFolder(null);
          setUserDocuments([]);
        }
        setError('');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete folder');
      }
    } catch (err) {
      setError('Failed to delete folder: ' + err.message);
      console.error('Error deleting folder:', err);
    }
  };

  const deleteUserDocument = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      const response = await fetch(`https://multitenant-backend-mlap.onrender.com/api/hr-user-folders/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setUserDocuments(prev => prev.filter(d => d.id !== documentId));
        setError('');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete document');
      }
    } catch (err) {
      setError('Failed to delete document: ' + err.message);
      console.error('Error deleting document:', err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {isSystemAdmin ? 'System Documents' : 'Document Management'}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {isSystemAdmin ? 
              'Manage system-level documents and files' : 
              'Upload, organize, and manage your documents'}
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {viewMode === 'grid' ? 'List View' : 'Grid View'}
          </button>
        </div>
      </div>

      {/* Folder Navigation Breadcrumb */}
      {showFolderNavigation && currentFolderPath.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-center space-x-2">
            <button
              onClick={navigateToRoot}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              📁 Root
            </button>
            {currentFolderPath.map((folder, index) => (
              <div key={index} className="flex items-center space-x-2">
                <span className="text-gray-400">/</span>
                {index === currentFolderPath.length - 1 ? (
                  <span className="text-blue-800 font-medium">{folder}</span>
                ) : (
                  <button
                    onClick={() => {
                      const newPath = currentFolderPath.slice(0, index + 1);
                      setCurrentFolderPath(newPath);
                      setSelectedFolder(newPath[newPath.length - 1]);
                    }}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {folder}
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={navigateBack}
              className="ml-4 px-2 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            >
              ← Back
            </button>
          </div>
        </div>
      )}

      {/* System Admin Badge */}
      {isSystemAdmin && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">
                <strong>System Administrator Mode:</strong> You are managing system-level documents with elevated privileges.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        {/* File Upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload {isSystemAdmin ? 'System' : ''} Document
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400">
            <div className="space-y-1 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="flex text-sm text-gray-600">
                <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                  <span>Upload a file</span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    onChange={handleFileUpload}
                    disabled={!!uploadingFile}
                  />
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500">PNG, JPG, PDF up to 100MB</p>
              {uploadingFile && (
                <p className="text-sm text-blue-600">Uploading {uploadingFile}...</p>
              )}
            </div>
          </div>
        </div>

        {/* Folder Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Folder</label>
            <select
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Folders</option>
              <option value="root">Root (No Folder)</option>
              {Array.isArray(folders) && folders.map(folder => (
                <option key={folder} value={folder}>{folder}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <span className="invisible">Hidden</span>
            </label>
            {!showNewFolder ? (
              <button
                onClick={() => setShowNewFolder(true)}
                className="w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                + New Folder
              </button>
            ) : (
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Folder name"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
                />
                <button
                  onClick={handleCreateFolder}
                  className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  ✓
                </button>
                <button
                  onClick={() => {
                    setShowNewFolder(false);
                    setNewFolderName('');
                  }}
                  className="px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  ✕
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Filters and Search */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter</label>
            <select
              value={filterBy}
              onChange={(e) => setFilterBy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Documents</option>
              <option value="recent">Recent (Last 7 days)</option>
              <option value="processed">Processed</option>
              <option value="unprocessed">Unprocessed</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* HR User Folders Section - Only visible for HR roles */}
        {(user?.role === 'hr_admin' || user?.role === 'hr_manager' || user?.role === 'system_admin') && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium text-blue-900">HR User Document Management</h3>
                <p className="text-sm text-blue-700">Create folders and manage documents for any user in your company</p>
              </div>
              <div className="flex space-x-2">
                                 {companyUsers.length === 0 && (
                   <button
                     onClick={() => fetchCompanyUsers()}
                     disabled={loadingUsers}
                     className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                   >
                     {loadingUsers ? '🔄 Loading...' : '🔄 Retry Load Users'}
                   </button>
                 )}
                                 <button
                   onClick={() => {
                     if (companyUsers.length === 0) {
                       // Retry loading users if none are loaded
                       fetchCompanyUsers();
                     }
                     setShowUserSearch(true);
                     setUserSearchTerm(''); // Clear any previous search
                     setFilteredUsers(companyUsers); // Show all users initially
                   }}
                   className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                 >
                   <Users className="h-4 w-4 mr-2" />
                   Search User
                 </button>
              </div>
            </div>

            {/* Selected User Display */}
            {selectedUser && (
              <div className="bg-white rounded-lg p-4 border border-blue-200">
                                 <div className="flex items-center justify-between mb-4">
                   <div className="flex items-center space-x-3">
                     <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                       <User className="h-5 w-5 text-blue-600" />
                     </div>
                     <div>
                       <h4 className="text-lg font-medium text-gray-900">{selectedUser.full_name}</h4>
                       <p className="text-sm text-gray-600">{selectedUser.email} • {selectedUser.role}</p>
                     </div>
                   </div>
                   <div className="flex items-center space-x-2">
                     <button
                       onClick={() => fetchUserFolders(selectedUser.id)}
                       className="text-blue-600 hover:text-blue-800 p-1"
                       title="Refresh user data"
                     >
                       🔄
                     </button>
                     <button
                       onClick={() => {
                         setSelectedUser(null);
                         setUserFolders([]);
                         setUserDocuments([]);
                         setSelectedUserFolder(null);
                       }}
                       className="text-gray-400 hover:text-gray-600"
                       title="Close user"
                     >
                       <X className="h-5 w-5" />
                     </button>
                   </div>
                 </div>

                {/* User Folders */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h5 className="text-md font-medium text-gray-900">User Folders ({userFolders.length})</h5>
                    <button
                      onClick={() => {
                        setNewUserFolder(prev => ({ ...prev, user_id: selectedUser.id }));
                        setShowCreateUserFolder(true);
                      }}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Create Folder
                    </button>
                  </div>

                                     {loadingFolders ? (
                     <div className="text-center py-4">
                       <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                       <p className="text-sm text-gray-500">Loading folders...</p>
                     </div>
                   ) : userFolders.length === 0 ? (
                     <p className="text-sm text-gray-500 text-center py-4">No folders created yet for this user.</p>
                   ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {userFolders.map((folder) => (
                        <div key={folder.id} className="bg-gray-50 rounded-lg p-3 border border-gray-200 hover:bg-gray-100">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <Folder className="h-4 w-4 text-blue-500" />
                              <div>
                                <h6 className="text-sm font-medium text-gray-900">{folder.display_name}</h6>
                                <p className="text-xs text-gray-500">{folder.documents_count || 0} documents</p>
                              </div>
                            </div>
                            <div className="flex space-x-1">
                              <button
                                onClick={() => openUserFolder(folder)}
                                className="text-blue-600 hover:text-blue-800 p-1"
                                title="View folder contents"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => deleteUserFolder(folder.id)}
                                className="text-red-600 hover:text-red-800 p-1"
                                title="Delete folder"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Selected Folder Documents */}
                {selectedUserFolder && (
                  <div className="mt-4 bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                      <h6 className="text-md font-medium text-gray-900">
                        Documents in {selectedUserFolder.display_name} ({userDocuments.length})
                      </h6>
                      <button
                        onClick={() => setShowUploadToUserFolder(true)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                      >
                        <Upload className="h-4 w-4 mr-1" />
                        Upload Document
                      </button>
                    </div>

                    {userDocuments.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-2">No documents in this folder.</p>
                    ) : (
                      <div className="space-y-2">
                        {userDocuments.map((doc) => (
                          <div key={doc.id} className="flex items-center justify-between bg-white rounded p-2 border border-gray-200">
                            <div className="flex items-center space-x-2">
                              <FileText className="h-4 w-4 text-gray-400" />
                              <div>
                                <p className="text-sm font-medium text-gray-900">{doc.original_filename}</p>
                                <p className="text-xs text-gray-500">{formatFileSize(doc.file_size)} • {formatDate(doc.created_at)}</p>
                              </div>
                            </div>
                            <button
                              onClick={() => deleteUserDocument(doc.id)}
                              className="text-red-600 hover:text-red-800 p-1"
                              title="Delete document"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Current Folder Indicator */}
      {selectedFolder !== 'all' && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <p className="text-sm text-blue-800">
            <strong>Current Folder:</strong> {selectedFolder === 'root' ? 'Root (No Folder)' : selectedFolder}
            {filteredDocuments.length > 0 && (
              <span className="ml-2">({filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''})</span>
            )}
          </p>
        </div>
      )}

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            {isSystemAdmin ? 'System Documents' : 'Documents'} 
            <span className="text-sm text-gray-500 ml-2">
              ({filteredDocuments.length} total)
            </span>
          </h3>
        </div>

        {loading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Loading documents...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-6 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">
              {selectedFolder === 'all' ? 
                'Get started by uploading your first document.' :
                `No documents in ${selectedFolder === 'root' ? 'root folder' : selectedFolder}.`
              }
            </p>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6' : 'divide-y divide-gray-200'}>
            {filteredDocuments.map((doc) => (
              viewMode === 'grid' ? (
                // Grid View
                <div key={doc.id} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate" title={doc.original_filename}>
                        {doc.original_filename}
                      </h4>
                      <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                        <span>{formatFileSize(doc.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                      {doc.folder_name && (
                        <div className="mt-1">
                          <button
                            onClick={() => navigateToFolder(doc.folder_name)}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer"
                          >
                            📁 {doc.folder_name}
                          </button>
                        </div>
                      )}
                      <div className="mt-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${doc.processed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                          {doc.processed ? '✓ Processed' : '⏳ Processing'}
                        </span>
                      </div>
                    </div>
                    <div className="ml-2 flex-shrink-0 flex items-center space-x-2">
                      {/* E-Signature Integration */}
                      {user && (
                        <DocumentESignatureIntegration
                          document={doc}
                          userRole={user.role}
                          userId={user.id}
                          onSignatureRequestCreated={(signatureRequest) => {
                            console.log('Signature request created:', signatureRequest);
                          }}
                        />
                      )}
                      
                      {/* Admin Direct Signing */}
                      {canSignDirectly && (
                        <button
                          onClick={() => handleDirectSign(doc)}
                          className="text-green-600 hover:text-green-800 text-sm"
                          title="Sign document directly"
                        >
                          ✍️
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                        title="Delete document"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                // List View
                <div key={doc.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <svg className="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {doc.original_filename}
                          </p>
                          <div className="flex items-center space-x-4 mt-1">
                            <span className="text-xs text-gray-500">{formatFileSize(doc.file_size)}</span>
                            <span className="text-xs text-gray-500">{formatDate(doc.created_at)}</span>
                            {doc.folder_name && (
                              <button
                                onClick={() => navigateToFolder(doc.folder_name)}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer"
                              >
                                📁 {doc.folder_name}
                              </button>
                            )}
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${doc.processed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                              {doc.processed ? '✓ Processed' : '⏳ Processing'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {/* E-Signature Integration */}
                      {user && (
                        <DocumentESignatureIntegration
                          document={doc}
                          userRole={user.role}
                          userId={user.id}
                          onSignatureRequestCreated={(signatureRequest) => {
                            console.log('Signature request created:', signatureRequest);
                          }}
                        />
                      )}
                      
                      {/* Admin Direct Signing */}
                      {canSignDirectly && (
                        <button
                          onClick={() => handleDirectSign(doc)}
                          className="text-green-600 hover:text-green-800 text-sm p-1"
                          title="Sign document directly"
                        >
                          ✍️
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="text-red-600 hover:text-red-800 text-sm p-1"
                        title="Delete document"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              )
            ))}
          </div>
        )}
      </div>

      {/* Admin Signing Modal */}
      {showSigningModal && selectedDocumentForSigning && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Sign Document: {selectedDocumentForSigning.original_filename}
              </h3>
              
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  You are about to sign this document directly as {user?.role}. 
                  This will create a signed version of the document.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowSigningModal(false);
                    setSelectedDocumentForSigning(null);
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleSignDocument()}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Sign Document
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* HR User Search Modal */}
      {showUserSearch && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Search for User</h3>
                <button
                  onClick={() => setShowUserSearch(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              
                             <div className="mb-4">
                 <form onSubmit={(e) => {
                   e.preventDefault();
                   handleUserSearch(userSearchTerm);
                 }}>
                   <div className="flex space-x-2">
                     <input
                       type="text"
                       placeholder="Search by name, email, or username..."
                       value={userSearchTerm}
                       onChange={(e) => setUserSearchTerm(e.target.value)}
                       className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                     />
                     <button
                       type="submit"
                       className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                     >
                       🔍 Search
                     </button>
                   </div>
                 </form>
                 
                 <div className="mt-2 flex justify-center">
                   <button
                     onClick={() => {
                       setUserSearchTerm('');
                       setFilteredUsers(companyUsers);
                     }}
                     className="text-sm text-blue-600 hover:text-blue-800 underline"
                   >
                     Show All Users
                   </button>
                 </div>
               </div>

                             <div className="mb-3 flex justify-between items-center">
                 <span className="text-sm text-gray-600">
                   {filteredUsers.length} user{filteredUsers.length !== 1 ? 's' : ''} found
                 </span>
                 {userSearchTerm && (
                   <button
                     onClick={() => {
                       setUserSearchTerm('');
                       setFilteredUsers(companyUsers);
                     }}
                     className="text-sm text-blue-600 hover:text-blue-800"
                   >
                     Clear Search
                   </button>
                 )}
               </div>
               
               <div className="max-h-96 overflow-y-auto">
                 {loadingUsers ? (
                   <div className="text-center py-4">
                     <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                     <p className="text-sm text-gray-500">Loading users...</p>
                   </div>
                 ) : filteredUsers.length === 0 ? (
                   <p className="text-center text-gray-500 py-4">
                     {userSearchTerm ? 'No users found matching your search.' : 'No users available.'}
                   </p>
                 ) : (
                   <div className="space-y-2">
                     {filteredUsers.map((user) => (
                       <div
                         key={user.id}
                         onClick={() => selectUser(user)}
                         className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                       >
                         <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                           <User className="h-4 w-4 text-blue-600" />
                         </div>
                         <div className="flex-1">
                           <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
                           <p className="text-xs text-gray-500">{user.email} • {user.role}</p>
                         </div>
                         <div className="text-xs text-gray-400">
                           Click to select
                         </div>
                       </div>
                     ))}
                   </div>
                 )}
               </div>
            </div>
          </div>
        </div>
      )}

      {/* Create User Folder Modal */}
      {showCreateUserFolder && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Folder</h3>
              <form onSubmit={createUserFolder}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Folder Name</label>
                  <input
                    type="text"
                    required
                    value={newUserFolder.name}
                    onChange={(e) => setNewUserFolder(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter folder name"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <input
                    type="text"
                    required
                    value={newUserFolder.display_name}
                    onChange={(e) => setNewUserFolder(prev => ({ ...prev, display_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter display name"
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={newUserFolder.description}
                    onChange={(e) => setNewUserFolder(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter description"
                    rows="3"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateUserFolder(false)}
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

      {/* Upload to User Folder Modal */}
      {showUploadToUserFolder && selectedUserFolder && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Document</h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                uploadToUserFolder(formData);
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
                    onClick={() => setShowUploadToUserFolder(false)}
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
    </div>
  );
};

export default DocumentManagement; 