import React, { useState, useEffect } from 'react';
import { documentsAPI, systemDocumentsAPI } from '../../services/api';
import { FileText, Download, Trash2, Calendar, User, Tag, Folder, Filter } from 'lucide-react';
import DocumentESignatureIntegration from '../ESignature/DocumentESignatureIntegration';
import { useAuth } from '../../utils/auth';

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Get user context for e-signature permissions
  const { user } = useAuth();

  useEffect(() => {
    loadFolders();
    loadDocuments();
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [selectedFolder]);

  const loadFolders = async () => {
    try {
      let response;
      // Check if user is a system user
      if (user?.role === 'system_admin') {
        response = { data: await systemDocumentsAPI.getFolders() };
      } else {
        response = await documentsAPI.folders();
      }
      setFolders(response.data);
    } catch (error) {
      console.error('Failed to load folders:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      let response;
      // Check if user is a system user
      if (user?.role === 'system_admin') {
        response = { data: await systemDocumentsAPI.list(selectedFolder) };
      } else {
        response = await documentsAPI.list(selectedFolder);
      }
      setDocuments(response.data);
    } catch (error) {
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      // Check if user is a system user
      if (user?.role === 'system_admin') {
        await systemDocumentsAPI.delete(documentId);
      } else {
        await documentsAPI.delete(documentId);
      }
      setDocuments(documents.filter(doc => doc.id !== documentId));
      // Reload folders in case this was the last document in a folder
      loadFolders();
    } catch (error) {
      alert('Failed to delete document');
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
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getFileIcon = (fileType) => {
    if (fileType.includes('image')) return '🖼️';
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word')) return '📝';
    if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '📊';
    if (fileType.includes('powerpoint') || fileType.includes('presentation')) return '📋';
    return '📁';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold flex items-center">
            <FileText className="h-6 w-6 mr-2 text-blue-500" />
            Documents ({documents.length})
          </h2>
          
          {/* Folder Filter */}
          <div className="flex items-center space-x-3">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={selectedFolder || ''}
              onChange={(e) => setSelectedFolder(e.target.value || null)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Folders</option>
              <option value="">Root Folder</option>
              {Array.isArray(folders) && folders.map((folder) => (
                <option key={folder} value={folder}>
                  {folder}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Current Folder Display */}
        {selectedFolder !== null && (
          <div className="flex items-center space-x-2 text-sm text-gray-600 mb-2">
            <Folder className="h-4 w-4" />
            <span>
              Current folder: {selectedFolder === '' ? 'Root Folder' : selectedFolder}
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200 text-red-700">
          {error}
        </div>
      )}

      <div className="p-6">
        {documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">No documents yet</h3>
            <p className="text-gray-500">Upload your first document to get started</p>
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((document) => (
              <div
                key={document.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="text-2xl">
                      {getFileIcon(document.file_type)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-medium text-gray-800 truncate">
                        {document.original_filename}
                      </h3>
                      
                      <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
                        <span className="flex items-center">
                          <Calendar className="h-4 w-4 mr-1" />
                          {formatDate(document.created_at)}
                        </span>
                        
                        <span>{formatFileSize(document.file_size)}</span>
                        
                        <span className="flex items-center">
                          <Tag className="h-4 w-4 mr-1" />
                          {document.file_type}
                        </span>
                        
                        {document.folder_name && (
                          <span className="flex items-center">
                            <Folder className="h-4 w-4 mr-1" />
                            {document.folder_name}
                          </span>
                        )}
                        
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          document.processed 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {document.processed ? 'Processed' : 'Processing...'}
                        </span>
                      </div>

                      {document.metadata_json && document.processed && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                            {document.metadata_json.title && (
                              <div>
                                <span className="font-medium text-gray-700">Title:</span>
                                <span className="ml-2 text-gray-600">{document.metadata_json.title}</span>
                              </div>
                            )}
                            
                            {document.metadata_json.document_type && (
                              <div>
                                <span className="font-medium text-gray-700">Type:</span>
                                <span className="ml-2 text-gray-600">{document.metadata_json.document_type}</span>
                              </div>
                            )}
                            
                            {document.metadata_json.key_topics && document.metadata_json.key_topics.length > 0 && (
                              <div className="md:col-span-2">
                                <span className="font-medium text-gray-700">Topics:</span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {document.metadata_json.key_topics.slice(0, 5).map((topic, index) => (
                                    <span
                                      key={index}
                                      className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                                    >
                                      {topic}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {document.metadata_json.summary && (
                              <div className="md:col-span-2">
                                <span className="font-medium text-gray-700">Summary:</span>
                                <p className="ml-2 text-gray-600 text-sm mt-1 line-clamp-2">
                                  {document.metadata_json.summary}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {/* E-Signature Integration */}
                    {user && (
                      <DocumentESignatureIntegration
                        document={document}
                        userRole={user.role}
                        userId={user.id}
                        onSignatureRequestCreated={(signatureRequest) => {
                          // Optional: Show success notification or update UI
                          console.log('Signature request created:', signatureRequest);
                        }}
                      />
                    )}
                    
                    <button
                      onClick={() => handleDelete(document.id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete document"
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
    </div>
  );
}

export default DocumentList; 