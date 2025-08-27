import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { 
  Mail, 
  Send, 
  Users, 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle,
  Plus,
  Trash2,
  Eye,
  Download
} from 'lucide-react';

const MailingSystem = () => {
  const { user, company } = useAuth();
  const [loading, setLoading] = useState(false);
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [sentEmails, setSentEmails] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [emailForm, setEmailForm] = useState({
    subject: '',
    body: '',
    recipients: [],
    template: '',
    attachments: []
  });

  useEffect(() => {
    if (user && company) {
      loadEmailData();
    }
  }, [user, company]);

  const loadEmailData = async () => {
    try {
      setLoading(true);
      // Load email templates and sent emails from backend
      // This would integrate with your backend email service
      console.log('Loading email data for company:', company.id);
      
      // Placeholder data - replace with actual API calls
      setEmailTemplates([
        { id: 1, name: 'Welcome Email', subject: 'Welcome to our platform', body: 'Welcome message...' },
        { id: 2, name: 'Document Notification', subject: 'New document available', body: 'Document notification...' },
        { id: 3, name: 'System Update', subject: 'System maintenance notice', body: 'Maintenance notice...' }
      ]);
      
      setSentEmails([
        { id: 1, subject: 'Welcome Email', recipients: ['user1@company.com'], status: 'sent', sent_at: '2024-01-15 10:30 AM' },
        { id: 2, subject: 'Document Update', recipients: ['team@company.com'], status: 'delivered', sent_at: '2024-01-14 02:15 PM' }
      ]);
    } catch (error) {
      console.error('Failed to load email data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    
    if (!emailForm.subject || !emailForm.body || emailForm.recipients.length === 0) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      
      // This would integrate with your backend email service
      const emailData = {
        ...emailForm,
        company_id: company.id,
        sender_id: user.id,
        sent_at: new Date().toISOString()
      };
      
      console.log('Sending email:', emailData);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Add to sent emails
      const newEmail = {
        id: Date.now(),
        subject: emailForm.subject,
        recipients: emailForm.recipients,
        status: 'sent',
        sent_at: new Date().toLocaleString()
      };
      
      setSentEmails(prev => [newEmail, ...prev]);
      setShowCreateModal(false);
      setEmailForm({ subject: '', body: '', recipients: [], template: '', attachments: [] });
      
      alert('Email sent successfully!');
    } catch (error) {
      console.error('Failed to send email:', error);
      alert('Failed to send email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const addRecipient = () => {
    setEmailForm(prev => ({
      ...prev,
      recipients: [...prev.recipients, '']
    }));
  };

  const updateRecipient = (index, value) => {
    setEmailForm(prev => ({
      ...prev,
      recipients: prev.recipients.map((recipient, i) => i === index ? value : recipient)
    }));
  };

  const removeRecipient = (index) => {
    setEmailForm(prev => ({
      ...prev,
      recipients: prev.recipients.filter((_, i) => i !== index)
    }));
  };

  const useTemplate = (template) => {
    setEmailForm(prev => ({
      ...prev,
      subject: template.subject,
      body: template.body,
      template: template.name
    }));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent':
        return <Send className="w-4 h-4 text-blue-500" />;
      case 'delivered':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent':
        return 'bg-blue-100 text-blue-800';
      case 'delivered':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!user || !company) {
    return (
      <div className="p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading mailing system...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Mailing System</h1>
        <p className="text-gray-600">Send emails, manage templates, and track delivery status</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Mail className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Total Sent</p>
              <p className="text-2xl font-bold text-gray-900">{sentEmails.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Templates</p>
              <p className="text-2xl font-bold text-gray-900">{emailTemplates.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Delivery Rate</p>
              <p className="text-2xl font-bold text-gray-900">98.5%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Email Templates */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Email Templates</h2>
            <p className="text-sm text-gray-600 mt-1">Pre-configured email templates for common use cases</p>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {emailTemplates.map((template) => (
                <div key={template.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                  <div>
                    <h3 className="font-medium text-gray-900">{template.name}</h3>
                    <p className="text-sm text-gray-600">{template.subject}</p>
                  </div>
                  <button
                    onClick={() => {
                      setEmailForm(prev => ({
                        ...prev,
                        subject: template.subject,
                        body: template.body
                      }));
                      setShowCreateModal(true);
                    }}
                    className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md"
                  >
                    Use Template
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Sent Emails */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Sent Emails</h2>
            <p className="text-sm text-gray-600 mt-1">Track the status of your sent emails</p>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {sentEmails.slice(0, 5).map((email) => (
                <div key={email.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{email.subject}</h3>
                    <p className="text-sm text-gray-600">{email.recipients.join(', ')}</p>
                    <p className="text-xs text-gray-500 mt-1">{email.sent_at}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(email.status)}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(email.status)}`}>
                      {email.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Send New Email Button */}
      <div className="mt-8 text-center">
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <Plus className="h-5 w-5" />
          <span>Send New Email</span>
        </button>
      </div>

      {/* Create Email Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Send New Email</h3>
              <form onSubmit={handleSendEmail} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subject *
                  </label>
                  <input
                    type="text"
                    value={emailForm.subject}
                    onChange={(e) => setEmailForm(prev => ({ ...prev, subject: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recipients *
                  </label>
                  <div className="space-y-2">
                    {emailForm.recipients.map((recipient, index) => (
                      <div key={index} className="flex space-x-2">
                        <input
                          type="email"
                          value={recipient}
                          onChange={(e) => updateRecipient(index, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="recipient@example.com"
                          required
                        />
                        <button
                          type="button"
                          onClick={() => removeRecipient(index)}
                          className="px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={addRecipient}
                      className="text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-2 py-1 rounded-md"
                    >
                      + Add Recipient
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Message Body *
                  </label>
                  <textarea
                    value={emailForm.body}
                    onChange={(e) => setEmailForm(prev => ({ ...prev, body: e.target.value }))}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50"
                  >
                    {loading ? 'Sending...' : 'Send Email'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600"
                  >
                    Cancel
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

export default MailingSystem;
