import React, { useState } from 'react';
import { useAuth } from '../../utils/auth';
import Header from '../Layout/Header';
import Sidebar from '../Layout/Sidebar';
import DocumentUpload from '../Documents/DocumentUpload';
import DocumentList from '../Documents/DocumentList';
import Chatbot from '../Chat/Chatbot';
import CompanyList from './CompanyList';
import UserManagement from '../Users/UserManagement';
import ESignatureManager from '../ESignature/ESignatureManager';

function CompanyDashboard() {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('documents');

  // Don't render if user data is not loaded yet
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Redirect system users to companies page
  if (user.role === 'system_admin' || !company) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">System Administrator</h2>
          <p className="text-gray-600 mb-6">You should be managing companies instead of viewing a company dashboard.</p>
          <button
            onClick={() => window.location.href = '/companies'}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Companies Management
          </button>
        </div>
      </div>
    );
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'documents':
        return (
          <div className="space-y-6">
            <DocumentUpload />
            <DocumentList />
          </div>
        );
      case 'esignature':
        return <ESignatureManager userRole={user.role} userId={user.id} />;
      case 'chat':
        return <Chatbot />;
      case 'analytics':
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">Analytics</h2>
            <p className="text-gray-600">Analytics dashboard coming soon...</p>
          </div>
        );
      case 'companies':
        return ['system_admin', 'hr_admin'].includes(user?.role) ? (
          <CompanyList />
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
            <p className="text-gray-600">Only system administrators and HR administrators can access company management.</p>
          </div>
        );
      case 'users':
        return ['system_admin', 'hr_admin', 'hr_manager'].includes(user?.role) ? (
          <UserManagement />
        ) : (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">Access Denied</h2>
            <p className="text-gray-600">Only administrators and HR personnel can access user management.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="flex">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-800">
              Welcome, {user?.full_name || 'User'}
            </h1>
            <p className="text-gray-600">
              {company?.name || 'Company'} • {user?.role === 'hr_admin' ? 'HR Administrator' : user?.role === 'hr_manager' ? 'HR Manager' : 'Employee'}
            </p>
          </div>
          
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default CompanyDashboard;