import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { documentsAPI } from '../../services/api';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';

function DocumentUpload({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadStatus(null);

    try {
      await documentsAPI.upload(file);
      setUploadStatus({ type: 'success', message: 'Document uploaded successfully!' });
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