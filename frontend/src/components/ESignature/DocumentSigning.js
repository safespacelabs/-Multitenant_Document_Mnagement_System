import React, { useState, useEffect } from 'react';
import { documentsAPI, esignatureAPI } from '../../services/api';

const DocumentSigning = ({ documentId, onSigningComplete, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [documentDetails, setDocumentDetails] = useState(null);
  const [signatureText, setSignatureText] = useState('');
  const [isDocumentLoaded, setIsDocumentLoaded] = useState(false);

  // Load document details
  useEffect(() => {
    const loadDocumentDetails = async () => {
      try {
        setLoading(true);
        const response = await esignatureAPI.getStatus(documentId);
                  setDocumentDetails(response);
        setIsDocumentLoaded(true);
      } catch (err) {
        setError('Failed to load document details');
        console.error('Error loading document:', err);
      } finally {
        setLoading(false);
      }
    };

    if (documentId) {
      loadDocumentDetails();
    }
  }, [documentId]);

  // Get current user's full name for default signature
  useEffect(() => {
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    if (currentUser.full_name && !signatureText) {
      setSignatureText(currentUser.full_name);
    }
  }, [signatureText]);

  const handleSignDocument = async () => {
    if (!signatureText.trim()) {
      setError('Please enter your signature');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const signRequest = {
        signature_text: signatureText.trim(),
        ip_address: '127.0.0.1', // In production, this would be captured properly
        user_agent: navigator.userAgent
      };

              const response = await esignatureAPI.signDocument(documentId, signRequest);
      
      setSuccess({
        message: response.data.message,
        status: response.data.document_status,
        progress: response.data.progress
      });

      // Notify parent component
      if (onSigningComplete) {
        onSigningComplete(response.data);
      }

    } catch (err) {
      console.error('Error signing document:', err);
      setError(err.response?.data?.detail || 'Failed to sign document');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentUserEmail = () => {
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    return currentUser.email || '';
  };

  const isCurrentUserRecipient = () => {
    const currentEmail = getCurrentUserEmail();
    return documentDetails?.recipients?.some(recipient => 
      recipient.email === currentEmail
    );
  };

  const getCurrentUserRecipient = () => {
    const currentEmail = getCurrentUserEmail();
    return documentDetails?.recipients?.find(recipient => 
      recipient.email === currentEmail
    );
  };

  const canSignDocument = () => {
    const recipient = getCurrentUserRecipient();
    return recipient && !recipient.is_signed;
  };

  if (loading && !isDocumentLoaded) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading document...</span>
      </div>
    );
  }

  if (error && !isDocumentLoaded) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!documentDetails) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-500">Document not found</p>
      </div>
    );
  }

  if (!isCurrentUserRecipient()) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">Access Denied</h3>
            <p className="mt-1 text-sm text-yellow-700">You are not a recipient of this signature request.</p>
          </div>
        </div>
      </div>
    );
  }

  const currentRecipient = getCurrentUserRecipient();
  const hasAlreadySigned = currentRecipient?.is_signed;

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <div className="border-b pb-4 mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Document Signing</h2>
        <p className="text-gray-600 mt-1">Sign the following document electronically</p>
      </div>

      {/* Document Information */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Document Details</h3>
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div><strong>Title:</strong> {documentDetails.title}</div>
          <div><strong>Status:</strong> 
            <span className={`ml-2 px-2 py-1 rounded text-sm ${
              documentDetails.status === 'completed' ? 'bg-green-100 text-green-800' :
              documentDetails.status === 'signed' ? 'bg-blue-100 text-blue-800' :
              documentDetails.status === 'sent' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {documentDetails.status}
            </span>
          </div>
          {documentDetails.message && (
            <div><strong>Message:</strong> {documentDetails.message}</div>
          )}
          <div><strong>Created:</strong> {new Date(documentDetails.created_at).toLocaleString()}</div>
          {documentDetails.expires_at && (
            <div><strong>Expires:</strong> {new Date(documentDetails.expires_at).toLocaleString()}</div>
          )}
        </div>
      </div>

      {/* Recipients Status */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Signing Progress</h3>
        <div className="space-y-2">
          {documentDetails.recipients.map((recipient, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium">{recipient.full_name}</div>
                <div className="text-sm text-gray-600">{recipient.email}</div>
                {recipient.role && (
                  <div className="text-xs text-gray-500">Role: {recipient.role}</div>
                )}
              </div>
              <div className="flex items-center">
                {recipient.is_signed ? (
                  <div className="flex items-center text-green-600">
                    <svg className="h-5 w-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Signed</span>
                    {recipient.signed_at && (
                      <span className="ml-2 text-xs text-gray-500">
                        {new Date(recipient.signed_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center text-yellow-600">
                    <svg className="h-5 w-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                    <span>Pending</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Signing Form */}
      {!hasAlreadySigned && canSignDocument() && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Your Signature</h3>
          <div className="space-y-4">
            <div>
              <label htmlFor="signature" className="block text-sm font-medium text-gray-700 mb-2">
                Enter your full name as your electronic signature
              </label>
              <input
                id="signature"
                type="text"
                value={signatureText}
                onChange={(e) => setSignatureText(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your full name"
                style={{ fontFamily: 'cursive' }}
              />
            </div>
            
            <div className="text-sm text-gray-600">
              <p>By signing this document, you agree that your electronic signature is equivalent to your handwritten signature and is legally binding.</p>
            </div>
          </div>
        </div>
      )}

      {/* Already Signed Message */}
      {hasAlreadySigned && (
        <div className="mb-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Document Signed</h3>
                <p className="mt-1 text-sm text-green-700">
                  You have already signed this document on {new Date(currentRecipient.signed_at).toLocaleString()}.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Display */}
      {success && (
        <div className="mb-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Success!</h3>
                <p className="mt-1 text-sm text-green-700">{success.message}</p>
                <p className="mt-1 text-sm text-green-700">
                  Progress: {success.progress.signed_count} of {success.progress.total_recipients} recipients have signed
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Back to List
        </button>
        
        {!hasAlreadySigned && canSignDocument() && (
          <button
            onClick={handleSignDocument}
            disabled={loading || !signatureText.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Signing...
              </div>
            ) : (
              'Sign Document'
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default DocumentSigning; 