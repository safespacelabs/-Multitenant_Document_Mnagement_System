import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { documentsAPI, systemDocumentsAPI } from '../../services/api';
import { Upload, FileText, CheckCircle, AlertCircle, FolderPlus, Folder } from 'lucide-react';
import { useAuth } from '../../utils/auth';

function DocumentUpload({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [folders, setFolders] = useState([]);
  
  // Get user context for API routing
  const { user } = useAuth();

  useEffect(() => {
    loadFolders();
  }, []);

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

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadStatus(null);

    try {
      const folderToUse = showCreateFolder ? newFolderName.trim() : selectedFolder || null;
      
      // Check if user is a system user
      if (user?.role === 'system_admin') {
        await systemDocumentsAPI.upload(file, folderToUse);
      } else {
        await documentsAPI.upload(file, folderToUse);
      }
      setUploadStatus({ type: 'success', message: 'Document uploaded successfully!' });
      
      // Reset form
      setSelectedFolder('');
      setShowCreateFolder(false);
      setNewFolderName('');
      
      // Reload folders in case a new one was created
      if (folderToUse && !folders.includes(folderToUse)) {
        loadFolders();
      }
      
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: error.response?.data?.detail || 'Upload failed'
      });
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-4 flex items-center">
        <Upload className="h-6 w-6 mr-2 text-blue-500" />
        Upload Document
      </h2>

      {/* Folder Selection */}
      <div className="mb-6 space-y-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Folder (optional)
            </label>
            <select
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              disabled={showCreateFolder}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            >
              <option value="">Root Folder</option>
              {Array.isArray(folders) && folders.map((folder) => (
                <option key={folder} value={folder}>
                  {folder}
                </option>
              ))}
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => setShowCreateFolder(!showCreateFolder)}
              className={`px-4 py-2 rounded-md flex items-center space-x-2 transition-colors ${
                showCreateFolder
                  ? 'bg-gray-200 text-gray-700'
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
            >
              <FolderPlus className="h-4 w-4" />
              <span>{showCreateFolder ? 'Cancel' : 'New Folder'}</span>
            </button>
          </div>
        </div>

        {showCreateFolder && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Folder Name
            </label>
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Enter folder name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        )}
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        
        {uploading ? (
          <div>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <p className="text-blue-600 font-medium">Uploading and processing...</p>
          </div>
        ) : (
          <div>
            <p className="text-lg font-medium text-gray-700 mb-2">
              {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
            </p>
            <p className="text-gray-500">or click to select a file</p>
            <p className="text-sm text-gray-400 mt-2">Max file size: 10MB</p>
            
            {/* Show selected folder info */}
            {(selectedFolder || (showCreateFolder && newFolderName)) && (
              <div className="mt-3 flex items-center justify-center text-sm text-gray-600">
                <Folder className="h-4 w-4 mr-1" />
                <span>
                  Uploading to: {showCreateFolder ? newFolderName || 'New Folder' : selectedFolder || 'Root Folder'}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {uploadStatus && (
        <div className={`mt-4 p-4 rounded-lg flex items-center ${
          uploadStatus.type === 'success' 
            ? 'bg-green-50 text-green-700' 
            : 'bg-red-50 text-red-700'
        }`}>
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="h-5 w-5 mr-2" />
          ) : (
            <AlertCircle className="h-5 w-5 mr-2" />
          )}
          {uploadStatus.message}
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;