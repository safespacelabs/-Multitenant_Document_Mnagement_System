import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Send, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Download, 
  Eye,
  Users,
  AlertTriangle,
  Plus,
  PenTool
} from 'lucide-react';
import api from '../../services/api';
import DocumentSigning from './DocumentSigning';

const ESignatureManager = ({ userRole, userId }) => {
  const [signatureRequests, setSignatureRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSigningModal, setShowSigningModal] = useState(null);

  useEffect(() => {
    fetchSignatureRequests();
  }, [filter]);

  const fetchSignatureRequests = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/esignature/list${filter !== 'all' ? `?status=${filter}` : ''}`);
      setSignatureRequests(response.data);
    } catch (error) {
      console.error('Error fetching signature requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'sent':
        return <Send className="w-4 h-4 text-blue-500" />;
      case 'signed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'expired':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'sent':
        return 'bg-blue-100 text-blue-800';
      case 'signed':
        return 'bg-green-100 text-green-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const canCreateSignatureRequest = () => {
    return ['system_admin', 'hr_admin', 'hr_manager', 'employee'].includes(userRole || '');
  };

  const canSendSignatureRequest = () => {
    return ['system_admin', 'hr_admin', 'hr_manager', 'employee'].includes(userRole || '');
  };

  const canCancelSignatureRequest = (request) => {
    if (['hr_admin', 'hr_manager'].includes(userRole || '')) return true;
    return request.created_by_user_id === userId;
  };

  const canSignDocument = (request) => {
    // Check if current user is a recipient of this signature request
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    const currentUserEmail = currentUser.email || '';
    
    // System admins can sign any document that's in a signable state
    if ((userRole || '') === 'system_admin') {
      return ['sent', 'signed'].includes(request.status);
    }
    
    // Find if current user is a recipient (with safety check)
    const userRecipient = (request.recipients || []).find(recipient => 
      recipient.email === currentUserEmail
    );
    
    // User can sign if they are a recipient and haven't signed yet
    return userRecipient && !userRecipient.is_signed && ['sent', 'signed'].includes(request.status);
  };

  const sendSignatureRequest = async (requestId) => {
    try {
      await api.post(`/api/esignature/${requestId}/send`);
      fetchSignatureRequests();
      alert('Signature request sent successfully!');
    } catch (error) {
      console.error('Error sending signature request:', error);
      alert('Failed to send signature request');
    }
  };

  const cancelSignatureRequest = async (requestId) => {
    if (!window.confirm('Are you sure you want to cancel this signature request?')) return;
    
    try {
      await api.post(`/api/esignature/${requestId}/cancel`);
      fetchSignatureRequests();
      alert('Signature request cancelled successfully!');
    } catch (error) {
      console.error('Error cancelling signature request:', error);
      alert('Failed to cancel signature request');
    }
  };

  const downloadSignedDocument = async (requestId, title) => {
    try {
      const response = await api.get(`/api/esignature/${requestId}/download-signed`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `signed_${title}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading signed document:', error);
      alert('Failed to download signed document');
    }
  };

  const handleSigningComplete = (signingData) => {
    // Refresh the signature requests list
    fetchSignatureRequests();
    setShowSigningModal(null);
    alert('Document signed successfully!');
  };

  const viewSignatureStatus = async (requestId) => {
    try {
      const response = await api.get(`/api/esignature/${requestId}/status`);
      const statusData = response.data;
      
      // Create a modal to display the status information
      const statusModal = document.createElement('div');
      statusModal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
      statusModal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
          <div class="mt-3 text-center">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Signature Request Status</h3>
            <div class="mt-4 text-left">
              <div class="mb-4">
                <h4 class="font-semibold text-gray-700">Document Information:</h4>
                <p><strong>Title:</strong> ${statusData.title}</p>
                <p><strong>Status:</strong> <span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">${statusData.status}</span></p>
                <p><strong>Message:</strong> ${statusData.message || 'N/A'}</p>
                <p><strong>Created:</strong> ${new Date(statusData.created_at).toLocaleString()}</p>
                <p><strong>Expires:</strong> ${new Date(statusData.expires_at).toLocaleString()}</p>
              </div>
              
              <div class="mb-4">
                <h4 class="font-semibold text-gray-700 mb-2">Recipients:</h4>
                ${statusData.recipients.map(recipient => `
                  <div class="flex items-center justify-between p-2 border rounded mb-2">
                    <div>
                      <p class="font-medium">${recipient.full_name}</p>
                      <p class="text-sm text-gray-600">${recipient.email}</p>
                      <p class="text-xs text-gray-500">Role: ${recipient.role || 'N/A'}</p>
                    </div>
                    <div class="text-right">
                      ${recipient.is_signed ? 
                        `<span class="text-green-600 font-medium">✓ Signed</span><br>
                         <span class="text-xs text-gray-500">${new Date(recipient.signed_at).toLocaleString()}</span>` :
                        '<span class="text-gray-500">○ Pending</span>'
                      }
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
            
            <div class="flex space-x-3 pt-4 border-t">
              <button onclick="this.closest('.fixed').remove()" 
                      class="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600">
                Close
              </button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(statusModal);
      
      // Close modal when clicking outside
      statusModal.addEventListener('click', (e) => {
        if (e.target === statusModal) {
          statusModal.remove();
        }
      });
      
    } catch (error) {
      console.error('Error fetching signature status:', error);
      alert('Failed to load signature status');
    }
  };

  // Role-specific use case buttons
  const getRoleSpecificActions = () => {
    const actions = [];

    if (userRole === 'hr_admin') {
      actions.push(
        <button
          key="policy"
          onClick={() => setShowCreateModal({ type: 'policy-acknowledgment' })}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
        >
          <FileText className="w-4 h-4 mr-2" />
          Policy Acknowledgment
        </button>
      );
    }

    if (['hr_admin', 'hr_manager'].includes(userRole || '')) {
      actions.push(
        <button
          key="contract"
          onClick={() => setShowCreateModal({ type: 'contract-approval' })}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <FileText className="w-4 h-4 mr-2" />
          Contract Approval
        </button>
      );
    }

    if (['hr_manager', 'employee'].includes(userRole || '')) {
      actions.push(
        <button
          key="budget"
          onClick={() => setShowCreateModal({ type: 'budget-approval' })}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          <FileText className="w-4 h-4 mr-2" />
          Budget Approval
        </button>
      );
    }

    if (['employee', 'customer', 'hr_manager', 'hr_admin'].includes(userRole || '')) {
      actions.push(
        <button
          key="customer"
          onClick={() => setShowCreateModal({ type: 'customer-agreement' })}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Users className="w-4 h-4 mr-2" />
          Customer Agreement
        </button>
      );
    }

    return actions;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">E-Signature Management</h1>
        <div className="flex space-x-3">
          {getRoleSpecificActions()}
          {canCreateSignatureRequest() && (
            <button
              onClick={() => setShowCreateModal({ type: 'general' })}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Request
            </button>
          )}
        </div>
      </div>

      {/* Role-specific information banner */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-sm font-medium text-blue-800 mb-2">
          E-Signature Use Cases for {(userRole || 'user').charAt(0).toUpperCase() + (userRole || 'user').slice(1).replace('_', ' ')}
        </h3>
        <div className="text-sm text-blue-700">
          {userRole === 'hr_admin' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Company-wide policy acknowledgments</li>
              <li>Executive contract approvals</li>
              <li>HR policy updates and compliance documents</li>
              <li>Bulk employee agreement processing</li>
            </ul>
          )}
          {userRole === 'hr_manager' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Department contract approvals</li>
              <li>Employee performance review agreements</li>
              <li>Budget approval workflows</li>
              <li>Team policy acknowledgments</li>
            </ul>
          )}
          {userRole === 'employee' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Customer service agreements</li>
              <li>Project approval documents</li>
              <li>Client contract processing</li>
              <li>Budget request approvals</li>
            </ul>
          )}
          {userRole === 'customer' && (
            <ul className="list-disc list-inside space-y-1">
              <li>Service agreement acceptance</li>
              <li>Terms and conditions acknowledgment</li>
              <li>Order confirmations</li>
              <li>Privacy policy agreements</li>
            </ul>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="mb-4">
        <nav className="flex space-x-8">
          {['all', 'pending', 'sent', 'signed', 'completed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`${
                filter === status
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm capitalize`}
            >
              {status === 'all' ? 'All Requests' : status}
            </button>
          ))}
        </nav>
      </div>

      {/* Signature requests list */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading signature requests...</p>
        </div>
      ) : signatureRequests.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No signature requests found</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {signatureRequests.map((request) => (
              <li key={request.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {getStatusIcon(request.status)}
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">{request.title}</p>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center text-sm text-gray-500">
                        <Users className="w-4 h-4 mr-1" />
                        <span>{request.recipients?.length || 0} recipient(s)</span>
                        <span className="mx-2">•</span>
                        <span>Expires: {new Date(request.expires_at).toLocaleDateString()}</span>
                      </div>
                      {request.message && (
                        <p className="mt-1 text-sm text-gray-600">{request.message}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => viewSignatureStatus(request.id)}
                      className="text-blue-600 hover:text-blue-800"
                      title="View Status"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    
                    {canSignDocument(request) && (
                      <button
                        onClick={() => setShowSigningModal(request.id)}
                        className="text-green-600 hover:text-green-800"
                        title="Sign Document"
                      >
                        <PenTool className="w-4 h-4" />
                      </button>
                    )}
                    
                    {request.status === 'pending' && canSendSignatureRequest() && (
                      <button
                        onClick={() => sendSignatureRequest(request.id)}
                        className="text-green-600 hover:text-green-800"
                        title="Send Request"
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    )}
                    
                    {request.status === 'completed' && (
                      <button
                        onClick={() => downloadSignedDocument(request.id, request.title)}
                        className="text-purple-600 hover:text-purple-800"
                        title="Download Signed Document"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    )}
                    
                    {['pending', 'sent'].includes(request.status) && canCancelSignatureRequest(request) && (
                      <button
                        onClick={() => cancelSignatureRequest(request.id)}
                        className="text-red-600 hover:text-red-800"
                        title="Cancel Request"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Recipients preview */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {(request.recipients || []).slice(0, 3).map((recipient, index) => (
                    <span
                      key={index}
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        recipient.is_signed
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {recipient.full_name}
                      {recipient.is_signed && (
                        <CheckCircle className="w-3 h-3 ml-1" />
                      )}
                    </span>
                  ))}
                  {(request.recipients?.length || 0) > 3 && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      +{(request.recipients?.length || 0) - 3} more
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Create signature request modal - we'll implement this separately */}
      {showCreateModal && (
        <CreateSignatureModal
          type={showCreateModal.type}
          userRole={userRole}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchSignatureRequests();
          }}
        />
      )}

      {/* Document signing modal */}
      {showSigningModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-4 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
            <DocumentSigning
              documentId={showSigningModal}
              onSigningComplete={handleSigningComplete}
              onCancel={() => setShowSigningModal(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const CreateSignatureModal = ({ type, userRole, onClose, onSuccess }) => {
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [recipients, setRecipients] = useState([{ email: '', full_name: '', role: '' }]);
  const [expiresInDays, setExpiresInDays] = useState(14);
  const [requireAllSignatures, setRequireAllSignatures] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(true);

  useEffect(() => {
    loadDocuments();
    setDefaultTemplate();
  }, [type]);

  const loadDocuments = async () => {
    try {
      setLoadingDocs(true);
      let response;
      if (userRole === 'system_admin') {
        response = await api.get('/api/documents/system/');
      } else {
        response = await api.get('/api/documents/');
      }
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  };

  const setDefaultTemplate = () => {
    const templates = {
      'policy-acknowledgment': {
        title: 'Policy Acknowledgment Required',
        message: 'Please review and acknowledge the attached policy document.',
        recipients: [{ email: '', full_name: '', role: 'employee' }]
      },
      'contract-approval': {
        title: 'Contract Approval Request',
        message: 'Please review and approve the attached contract.',
        recipients: [{ email: '', full_name: '', role: 'manager' }]
      },
      'budget-approval': {
        title: 'Budget Approval Request',
        message: 'Please review and approve the budget proposal.',
        recipients: [{ email: '', full_name: '', role: 'manager' }]
      },
      'customer-agreement': {
        title: 'Customer Agreement',
        message: 'Please review and sign the service agreement.',
        recipients: [{ email: '', full_name: '', role: 'customer' }]
      },
      'general': {
        title: 'Signature Request',
        message: 'Please review and sign the attached document.',
        recipients: [{ email: '', full_name: '', role: '' }]
      }
    };
    
    const template = templates[type?.type || 'general'];
    setTitle(template.title);
    setMessage(template.message);
    setRecipients(template.recipients);
  };

  const addRecipient = () => {
    setRecipients([...recipients, { email: '', full_name: '', role: '' }]);
  };

  const removeRecipient = (index) => {
    if (recipients.length > 1) {
      setRecipients(recipients.filter((_, i) => i !== index));
    }
  };

  const updateRecipient = (index, field, value) => {
    const updated = recipients.map((recipient, i) => 
      i === index ? { ...recipient, [field]: value } : recipient
    );
    setRecipients(updated);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedDocumentId) {
      alert('Please select a document');
      return;
    }
    
    if (!title.trim()) {
      alert('Please enter a title');
      return;
    }
    
    if (recipients.some(r => !r.email.trim() || !r.full_name.trim())) {
      alert('Please fill in all recipient details');
      return;
    }

    try {
      setLoading(true);
      
      const response = await api.post('/api/esignature/create-request', {
        document_id: selectedDocumentId,
        title: title.trim(),
        message: message.trim(),
        recipients: recipients.map(r => ({
          email: r.email.trim(),
          full_name: r.full_name.trim(),
          role: r.role.trim() || 'recipient'
        })),
        require_all_signatures: requireAllSignatures,
        expires_in_days: expiresInDays
      });

      onSuccess?.(response.data);
      onClose();
      alert('Signature request created successfully!');
      
    } catch (error) {
      console.error('Error creating signature request:', error);
      alert('Failed to create signature request: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mb-4">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Create {type?.type?.replace('-', ' ').toUpperCase() || 'SIGNATURE'} Request
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Document Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Document *
            </label>
            {loadingDocs ? (
              <div className="text-gray-500">Loading documents...</div>
            ) : (
              <select
                value={selectedDocumentId}
                onChange={(e) => setSelectedDocumentId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Choose a document...</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.original_filename}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Request Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter signature request title"
              required
            />
          </div>

          {/* Message */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message to Recipients
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Enter message for recipients"
            />
          </div>

          {/* Recipients */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Recipients *
            </label>
            {recipients.map((recipient, index) => (
              <div key={index} className="flex space-x-2 mb-2">
                <input
                  type="email"
                  value={recipient.email}
                  onChange={(e) => updateRecipient(index, 'email', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Email address"
                  required
                />
                <input
                  type="text"
                  value={recipient.full_name}
                  onChange={(e) => updateRecipient(index, 'full_name', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Full name"
                  required
                />
                <input
                  type="text"
                  value={recipient.role}
                  onChange={(e) => updateRecipient(index, 'role', e.target.value)}
                  className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Role"
                />
                {recipients.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeRecipient(index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
            <button
              type="button"
              onClick={addRecipient}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              + Add Another Recipient
            </button>
          </div>

          {/* Settings */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Expires In (Days)
              </label>
              <input
                type="number"
                value={expiresInDays}
                onChange={(e) => setExpiresInDays(parseInt(e.target.value) || 14)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="365"
              />
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="requireAll"
                checked={requireAllSignatures}
                onChange={(e) => setRequireAllSignatures(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="requireAll" className="text-sm text-gray-700">
                Require all signatures
              </label>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              disabled={loading || loadingDocs}
            >
              {loading ? 'Creating...' : 'Create Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ESignatureManager; 