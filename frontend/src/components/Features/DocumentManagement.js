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
  FolderPlus
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

  // Determine if user is system admin
  const isSystemAdmin = user?.role === 'system_admin';
  
  // Use appropriate API based on user role
  const docsAPI = isSystemAdmin ? systemDocumentsAPI : documentsAPI;

  useEffect(() => {
    fetchDocuments();
    fetchFolders();
  }, [selectedFolder, isSystemAdmin]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const folderParam = selectedFolder === 'all' ? null : (selectedFolder === 'root' ? '' : selectedFolder);
      const response = await docsAPI.list(folderParam);
      setDocuments(response);
      setError('');
    } catch (err) {
      setError('Failed to fetch documents: ' + err.message);
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFolders = async () => {
    try {
      const response = isSystemAdmin ? 
        await systemDocumentsAPI.getFolders() : 
        await documentsAPI.folders();
      setFolders(response);
    } catch (err) {
      console.error('Error fetching folders:', err);
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

  const filteredDocuments = documents.filter(doc => {
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
              {folders.map(folder => (
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
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            📁 {doc.folder_name}
                          </span>
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
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                📁 {doc.folder_name}
                              </span>
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
    </div>
  );
};

export default DocumentManagement; 