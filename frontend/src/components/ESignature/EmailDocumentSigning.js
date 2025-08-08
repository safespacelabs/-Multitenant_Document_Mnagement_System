import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../utils/auth';
import { documentsAPI, esignatureAPI } from '../../services/api';

const EmailDocumentSigning = () => {
  const { documentId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, login } = useAuth();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [documentDetails, setDocumentDetails] = useState(null);
  const [signatureText, setSignatureText] = useState('');
  const [isDocumentLoaded, setIsDocumentLoaded] = useState(false);
  
  // Get email from URL parameters
  const recipientEmail = searchParams.get('email');

  // Skip auto-login for direct signing - we'll handle authentication differently

  // Load document details - use public endpoint for email recipients
  useEffect(() => {
    const loadDocumentDetails = async () => {
      if (!documentId || !recipientEmail) return;
      
      try {
        setLoading(true);
        
        // Use the public endpoint that doesn't require authentication
        const response = await esignatureAPI.getPublicStatus(documentId, recipientEmail);
                  setDocumentDetails(response);
        setIsDocumentLoaded(true);
        
      } catch (err) {
        if (err.response?.status === 404) {
          setError('Document not found or you are not a recipient of this signature request.');
        } else if (err.response?.status === 401) {
          setError('Invalid link or access expired. Please contact the sender for a new link.');
        } else {
          setError('Failed to load document details. Please check the link or contact the sender.');
        }
        console.error('Error loading document:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDocumentDetails();
  }, [documentId, recipientEmail]);

  // Set default signature text from recipient info or user
  useEffect(() => {
    if (user?.full_name && !signatureText) {
      setSignatureText(user.full_name);
    } else if (documentDetails && recipientEmail && !signatureText) {
      // Find the recipient in the document and use their name
      const recipient = documentDetails.recipients?.find(r => r.email === recipientEmail);
      if (recipient?.full_name) {
        setSignatureText(recipient.full_name);
      }
    }
  }, [user, signatureText, documentDetails, recipientEmail]);

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
        ip_address: '127.0.0.1',
        user_agent: navigator.userAgent,
        recipient_email: recipientEmail // Include recipient email for verification
      };

              const response = await esignatureAPI.signDocument(documentId, signRequest);
      
      setSuccess({
        message: response.data.message,
        status: response.data.document_status,
        progress: response.data.progress
      });

    } catch (err) {
      console.error('Error signing document:', err);
      if (err.response?.status === 401) {
        setError('Authentication required. Please verify you are the intended recipient.');
      } else {
        setError(err.response?.data?.detail || 'Failed to sign document');
      }
    } finally {
      setLoading(false);
    }
  };

  const isCurrentUserRecipient = () => {
    if (!documentDetails || !recipientEmail) return false;
    return documentDetails.recipients?.some(recipient => 
      recipient.email === recipientEmail || (user && recipient.email === user.email)
    );
  };

  const getCurrentUserRecipient = () => {
    if (!documentDetails || !recipientEmail) return null;
    return documentDetails.recipients?.find(recipient => 
      recipient.email === recipientEmail || (user && recipient.email === user.email)
    );
  };

  const canSignDocument = () => {
    const recipient = getCurrentUserRecipient();
    return recipient && !recipient.is_signed;
  };

  // No need to check user authentication for direct signing

  if (loading && !isDocumentLoaded) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error && !documentDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="text-red-600 text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-red-800 mb-2">Document Access Error</h2>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!isCurrentUserRecipient()) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="text-yellow-600 text-4xl mb-4">🔒</div>
            <h2 className="text-xl font-semibold text-yellow-800 mb-2">Access Not Permitted</h2>
            <p className="text-yellow-700 mb-4">
              You don't have permission to sign this document. Please check if you're using the correct email address.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="text-green-600 text-4xl mb-4">✅</div>
            <h2 className="text-xl font-semibold text-green-800 mb-2">Document Signed Successfully!</h2>
            <p className="text-green-700 mb-2">{success.message}</p>
            {success.progress && (
              <p className="text-sm text-green-600 mb-4">
                Progress: {success.progress.signed_count} of {success.progress.total_recipients} signatures complete
              </p>
            )}
            <div className="space-y-2">
              <button
                onClick={() => navigate('/esignature')}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                View E-Signature Dashboard
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
              >
                Go to Main Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📝 Sign Document</h1>
              <p className="text-gray-600 mt-1">
                Please review and sign the document: <strong>{documentDetails?.title}</strong>
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Signing as:</p>
              <p className="font-medium text-gray-900">
                {getCurrentUserRecipient()?.full_name || recipientEmail || (user && (user.full_name || user.email))}
              </p>
            </div>
          </div>
        </div>

        {/* Document Details */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Document Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Document Title</p>
              <p className="font-medium text-gray-900">{documentDetails?.title}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                documentDetails?.status === 'completed' ? 'bg-green-100 text-green-800' :
                documentDetails?.status === 'signed' ? 'bg-blue-100 text-blue-800' :
                documentDetails?.status === 'sent' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {documentDetails?.status}
              </span>
            </div>
            {documentDetails?.message && (
              <div className="md:col-span-2">
                <p className="text-sm text-gray-500">Message</p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-1">
                  <p className="text-blue-800 italic">"{documentDetails.message}"</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Signing Form */}
        {canSignDocument() ? (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Add Your Signature</h2>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="signature" className="block text-sm font-medium text-gray-700 mb-2">
                  Digital Signature Text *
                </label>
                <input
                  type="text"
                  id="signature"
                  value={signatureText}
                  onChange={(e) => setSignatureText(e.target.value)}
                  placeholder="Enter your full name as your signature"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <p className="text-sm text-gray-500 mt-1">
                  This will be your legal digital signature on the document.
                </p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}

              <div className="flex space-x-4">
                <button
                  onClick={handleSignDocument}
                  disabled={loading || !signatureText.trim()}
                  className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
                >
                  {loading ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Signing...
                    </span>
                  ) : (
                    '✍️ Sign Document'
                  )}
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="text-yellow-600 text-xl mr-3">ℹ️</div>
              <div>
                <h3 className="text-lg font-medium text-yellow-800">Document Already Signed</h3>
                <p className="text-yellow-700">
                  You have already signed this document. Thank you for your prompt response!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recipients Status */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Signature Status</h2>
          <div className="space-y-3">
            {documentDetails?.recipients?.map((recipient, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{recipient.full_name}</p>
                  <p className="text-sm text-gray-600">{recipient.email}</p>
                </div>
                <div className="flex items-center">
                  {recipient.is_signed ? (
                    <span className="flex items-center text-green-600">
                      <div className="w-2 h-2 bg-green-600 rounded-full mr-2"></div>
                      Signed
                    </span>
                  ) : (
                    <span className="flex items-center text-yellow-600">
                      <div className="w-2 h-2 bg-yellow-600 rounded-full mr-2"></div>
                      Pending
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailDocumentSigning;