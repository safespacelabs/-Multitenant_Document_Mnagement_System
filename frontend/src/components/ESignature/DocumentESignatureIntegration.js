import React, { useState } from 'react';
import { 
  FileSignature, 
  Send, 
  Users, 
  Clock,
  CheckCircle,
  ExternalLink,
  PenTool
} from 'lucide-react';
import { documentsAPI, esignatureAPI } from '../../services/api';

const DocumentESignatureIntegration = ({ document, userRole, userId, onSignatureRequestCreated }) => {
  const [showESignModal, setShowESignModal] = useState(false);
  const [showDirectSignModal, setShowDirectSignModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [directSignLoading, setDirectSignLoading] = useState(false);
  const [recipients, setRecipients] = useState([{ email: '', full_name: '', role: '' }]);
  const [requestTitle, setRequestTitle] = useState('');
  const [requestMessage, setRequestMessage] = useState('');
  const [expiresInDays, setExpiresInDays] = useState(14);
  const [signatureText, setSignatureText] = useState('');
  const [showDocument, setShowDocument] = useState(false);
  const [documentUrl, setDocumentUrl] = useState(null);

  // Check if user can create signature requests for this document
  const canCreateSignatureRequest = () => {
    if (!['hr_admin', 'hr_manager', 'employee', 'customer'].includes(userRole)) {
      return false;
    }
    
    // Document ownership/access check
    if (userRole === 'customer' && document.user_id !== userId) {
      return false;
    }
    
    if (userRole === 'employee' && document.user_id !== userId) {
      // Employees can create requests for their own docs or customer docs
      return document.user_role === 'customer';
    }
    
    return true;
  };

  // Check if user can sign documents directly (system admin only)
  const canSignDirectly = () => {
    console.log('🔍 canSignDirectly check:', {
      userRole: userRole,
      isSystemAdmin: userRole === 'system_admin',
      canSign: userRole === 'system_admin'
    });
    return userRole === 'system_admin';
  };

  // Function to view document
  const handleViewDocument = async () => {
    try {
      setLoading(true);
      const response = await esignatureAPI.viewOriginalDocument(document.id);
      
      // Create a blob URL for the document
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setDocumentUrl(url);
      setShowDocument(true);
    } catch (err) {
      console.error('Error viewing document:', err);
      alert('Failed to load document. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Function to close document view
  const handleCloseDocument = () => {
    setShowDocument(false);
    if (documentUrl) {
      URL.revokeObjectURL(documentUrl);
      setDocumentUrl(null);
    }
  };

  const signDocumentDirectly = async () => {
    if (!signatureText.trim()) {
      alert('Please enter your signature');
      return;
    }

    setDirectSignLoading(true);
    try {
              const response = await esignatureAPI.signDocumentDirectly(document.id, {
        signature_text: signatureText.trim(),
        ip_address: '127.0.0.1', // In a real app, get actual IP
        user_agent: navigator.userAgent
      });

      alert('Document signed successfully!');
      setShowDirectSignModal(false);
      setSignatureText('');
      
      if (onSignatureRequestCreated) {
        onSignatureRequestCreated(response.data);
      }
      
    } catch (error) {
      console.error('Error signing document directly:', error);
      let errorMessage = 'Unknown error';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert('Failed to sign document: ' + errorMessage);
    } finally {
      setDirectSignLoading(false);
    }
  };

  const addRecipient = () => {
    setRecipients([...recipients, { email: '', full_name: '', role: '' }]);
  };

  const removeRecipient = (index) => {
    setRecipients(recipients.filter((_, i) => i !== index));
  };

  const updateRecipient = (index, field, value) => {
    const updated = recipients.map((recipient, i) => 
      i === index ? { ...recipient, [field]: value } : recipient
    );
    setRecipients(updated);
  };

  const createSignatureRequest = async () => {
    if (!requestTitle || recipients.some(r => !r.email || !r.full_name)) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
              const response = await esignatureAPI.createRequest({
        document_id: document.id,
        title: requestTitle,
        message: requestMessage,
        recipients: recipients,
        require_all_signatures: true,
        expires_in_days: expiresInDays
      });

      alert('Signature request created successfully!');
      setShowESignModal(false);
      
      if (onSignatureRequestCreated) {
        onSignatureRequestCreated(response.data);
      }
      
      // Reset form
      setRequestTitle('');
      setRequestMessage('');
      setRecipients([{ email: '', full_name: '', role: '' }]);
      
    } catch (error) {
      console.error('Error creating signature request:', error);
      let errorMessage = 'Unknown error';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert('Failed to create signature request: ' + errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Get suggested recipients based on user role and document type
  const getSuggestedRecipients = () => {
    const suggestions = [];
    
    if (userRole === 'hr_admin') {
      suggestions.push(
        { label: 'All Employees', action: () => addAllEmployees() },
        { label: 'Department Heads', action: () => addDepartmentHeads() },
        { label: 'Legal Team', action: () => addLegalTeam() }
      );
    } else if (userRole === 'hr_manager') {
      suggestions.push(
        { label: 'Team Members', action: () => addTeamMembers() },
        { label: 'HR Admin', action: () => addHRAdmin() }
      );
    } else if (userRole === 'employee') {
      suggestions.push(
        { label: 'Manager', action: () => addManager() },
        { label: 'Customer', action: () => addCustomer() }
      );
    }
    
    return suggestions;
  };

  // Helper functions for suggested recipients (mock implementations)
  const addAllEmployees = () => {
    // In real implementation, this would fetch all employees
    setRecipients([
      { email: 'employee1@company.com', full_name: 'John Doe', role: 'employee' },
      { email: 'employee2@company.com', full_name: 'Jane Smith', role: 'employee' }
    ]);
  };

  const addDepartmentHeads = () => {
    setRecipients([
      { email: 'dept.head1@company.com', full_name: 'Alice Johnson', role: 'hr_manager' },
      { email: 'dept.head2@company.com', full_name: 'Bob Wilson', role: 'hr_manager' }
    ]);
  };

  const addLegalTeam = () => {
    setRecipients([
      { email: 'legal@company.com', full_name: 'Legal Team', role: 'hr_admin' }
    ]);
  };

  const addTeamMembers = () => {
    setRecipients([
      { email: 'team.member@company.com', full_name: 'Team Member', role: 'employee' }
    ]);
  };

  const addHRAdmin = () => {
    setRecipients([
      { email: 'hr.admin@company.com', full_name: 'HR Administrator', role: 'hr_admin' }
    ]);
  };

  const addManager = () => {
    setRecipients([
      { email: 'manager@company.com', full_name: 'Department Manager', role: 'hr_manager' }
    ]);
  };

  const addCustomer = () => {
    setRecipients([
      { email: 'customer@client.com', full_name: 'Customer Name', role: 'customer' }
    ]);
  };

  // Get role-specific use case templates
  const getUseCaseTemplates = () => {
    const templates = [];
    
    if (userRole === 'hr_admin') {
      templates.push(
        {
          title: 'Policy Acknowledgment',
          message: 'Please review and acknowledge the updated company policy.',
          recipients: [{ email: '', full_name: 'All Employees', role: 'employee' }]
        },
        {
          title: 'Executive Contract Approval',
          message: 'Please review and approve this executive contract.',
          recipients: [{ email: '', full_name: 'Legal Team', role: 'hr_admin' }]
        }
      );
    } else if (userRole === 'hr_manager') {
      templates.push(
        {
          title: 'Department Contract Approval',
          message: 'Please review and approve this department contract.',
          recipients: [{ email: '', full_name: 'HR Admin', role: 'hr_admin' }]
        },
        {
          title: 'Performance Review Agreement',
          message: 'Please sign to acknowledge your performance review.',
          recipients: [{ email: '', full_name: 'Employee', role: 'employee' }]
        }
      );
    } else if (userRole === 'employee') {
      templates.push(
        {
          title: 'Customer Service Agreement',
          message: 'Please review and sign this service agreement.',
          recipients: [{ email: '', full_name: 'Customer', role: 'customer' }]
        },
        {
          title: 'Project Approval Request',
          message: 'Please approve this project proposal.',
          recipients: [{ email: '', full_name: 'Manager', role: 'hr_manager' }]
        }
      );
    } else if (userRole === 'customer') {
      templates.push(
        {
          title: 'Service Agreement',
          message: 'Please review and sign this service agreement.',
          recipients: [{ email: '', full_name: 'Service Provider', role: 'employee' }]
        }
      );
    }
    
    return templates;
  };

  const applyTemplate = (template) => {
    setRequestTitle(template.title);
    setRequestMessage(template.message);
    setRecipients(template.recipients);
  };

  console.log('🔍 DocumentESignatureIntegration render:', {
    userRole: userRole,
    userId: userId,
    canCreateSignatureRequest: canCreateSignatureRequest(),
    canSignDirectly: canSignDirectly(),
    documentId: document?.id,
    documentName: document?.original_filename
  });

  if (!canCreateSignatureRequest() && !canSignDirectly()) {
    console.log('❌ No permissions - returning null');
    return null;
  }

  return (
    <>
      {canCreateSignatureRequest() && (
        <button
          onClick={() => {
            setRequestTitle(`Signature Request: ${document.original_filename}`);
            setShowESignModal(true);
          }}
          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 mr-2"
          title="Send for E-Signature"
        >
          <FileSignature className="w-4 h-4 mr-1" />
          Send for Signature
        </button>
      )}

      {canSignDirectly() && (
        <button
          onClick={() => setShowDirectSignModal(true)}
          className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          title="Sign Document Directly"
        >
          <PenTool className="w-4 h-4 mr-1" />
          Sign Document
        </button>
      )}

      {showESignModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Send Document for E-Signature
                </h3>
                <button
                  onClick={() => setShowESignModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Document info */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <FileSignature className="w-5 h-5 text-blue-500 mr-2" />
                  <div>
                    <p className="font-medium text-gray-900">{document.original_filename}</p>
                    <p className="text-sm text-gray-500">
                      Size: {(document.file_size / 1024).toFixed(1)} KB • 
                      Type: {document.file_type}
                    </p>
                  </div>
                </div>
              </div>

              {/* Templates */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quick Templates for {userRole.replace('_', ' ').toUpperCase()}
                </label>
                <div className="flex flex-wrap gap-2">
                  {getUseCaseTemplates().map((template, index) => (
                    <button
                      key={index}
                      onClick={() => applyTemplate(template)}
                      className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full hover:bg-blue-200"
                    >
                      {template.title}
                    </button>
                  ))}
                </div>
              </div>

              {/* Request details */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Request Title *
                  </label>
                  <input
                    type="text"
                    value={requestTitle}
                    onChange={(e) => setRequestTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter a title for this signature request"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message to Recipients
                  </label>
                  <textarea
                    value={requestMessage}
                    onChange={(e) => setRequestMessage(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Optional message to include with the signature request"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expires in (days)
                  </label>
                  <select
                    value={expiresInDays}
                    onChange={(e) => setExpiresInDays(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                    <option value={60}>60 days</option>
                  </select>
                </div>
              </div>

              {/* Recipients */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Recipients *
                  </label>
                  <div className="flex space-x-2">
                    {getSuggestedRecipients().map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={suggestion.action}
                        className="px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
                      >
                        {suggestion.label}
                      </button>
                    ))}
                  </div>
                </div>

                {recipients.map((recipient, index) => (
                  <div key={index} className="flex items-center space-x-2 mb-2">
                    <input
                      type="email"
                      value={recipient.email}
                      onChange={(e) => updateRecipient(index, 'email', e.target.value)}
                      placeholder="Email address"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <input
                      type="text"
                      value={recipient.full_name}
                      onChange={(e) => updateRecipient(index, 'full_name', e.target.value)}
                      placeholder="Full name"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                    <select
                      value={recipient.role}
                      onChange={(e) => updateRecipient(index, 'role', e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Role</option>
                      <option value="hr_admin">HR Admin</option>
                      <option value="hr_manager">HR Manager</option>
                      <option value="employee">Employee</option>
                      <option value="customer">Customer</option>
                    </select>
                    {recipients.length > 1 && (
                      <button
                        onClick={() => removeRecipient(index)}
                        className="p-2 text-red-600 hover:text-red-800"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}

                <button
                  onClick={addRecipient}
                  className="mt-2 inline-flex items-center px-3 py-1 border border-dashed border-gray-300 text-sm font-medium rounded text-gray-600 hover:border-gray-400 hover:text-gray-700"
                >
                  <Users className="w-4 h-4 mr-1" />
                  Add Recipient
                </button>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowESignModal(false)}
                  className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  onClick={createSignatureRequest}
                  disabled={loading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Creating...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Create Signature Request
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showDirectSignModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border max-w-lg shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Sign Document Directly
                </h3>
                <button
                  onClick={() => setShowDirectSignModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Document info */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <PenTool className="w-5 h-5 text-green-500 mr-2" />
                  <div>
                    <p className="font-medium text-gray-900">{document.original_filename}</p>
                    <p className="text-sm text-gray-500">
                      Size: {(document.file_size / 1024).toFixed(1)} KB • 
                      Type: {document.file_type}
                    </p>
                  </div>
                </div>
                
                {/* Document View Button */}
                <div className="mt-4 text-center">
                  <button
                    onClick={handleViewDocument}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center mx-auto space-x-2"
                  >
                    {loading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <span>View Document Before Signing</span>
                      </>
                    )}
                  </button>
                  <p className="text-sm text-gray-500 mt-2">
                    Review the document content before proceeding with your signature
                  </p>
                </div>
              </div>

              {/* Signature input */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Electronic Signature *
                </label>
                <input
                  type="text"
                  value={signatureText}
                  onChange={(e) => setSignatureText(e.target.value)}
                  placeholder="Type your full name as your signature"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  By typing your name, you agree to electronically sign this document
                </p>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDirectSignModal(false)}
                  className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  Cancel
                </button>
                <button
                  onClick={signDocumentDirectly}
                  disabled={directSignLoading || !signatureText.trim()}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                >
                  {directSignLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Signing...
                    </>
                  ) : (
                    <>
                      <PenTool className="w-4 h-4 mr-2" />
                      Sign Document
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Document View Modal */}
      {showDocument && documentUrl && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full h-5/6 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                Document Preview: {document?.original_filename}
              </h3>
              <button
                onClick={handleCloseDocument}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="flex-1 p-4 overflow-hidden">
              {documentUrl && (
                <iframe
                  src={documentUrl}
                  className="w-full h-full border-0 rounded"
                  title="Document Preview"
                />
              )}
            </div>
            
            <div className="p-4 border-t bg-gray-50">
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  Review the document carefully before signing
                </p>
                <button
                  onClick={handleCloseDocument}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  Close Preview
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentESignatureIntegration; 