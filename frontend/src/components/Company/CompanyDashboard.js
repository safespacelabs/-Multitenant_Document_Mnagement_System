import React, { useState } from 'react';
import { useAuth } from '../../utils/auth';
import Header from '../Layout/Header';
import Sidebar from '../Layout/Sidebar';
import DocumentUpload from '../Documents/DocumentUpload';
import DocumentList from '../Documents/DocumentList';
import Chatbot from '../Chat/Chatbot';

function CompanyDashboard() {
  const { user, company } = useAuth();
  const [activeTab, setActiveTab] = useState('documents');

  const renderContent = () => {
    switch (activeTab) {
      case 'documents':
        return (
          <div className="space-y-6">
            <DocumentUpload />
            <DocumentList />
          </div>
        );
      case 'chat':
        return <Chatbot />;
      case 'analytics':
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold mb-4">Analytics</h2>
            <p className="text-gray-600">Analytics dashboard coming soon...</p>
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
              Welcome, {user.full_name}
            </h1>
            <p className="text-gray-600">
              {company.name} • {user.role === 'admin' ? 'Administrator' : 'Employee'}
            </p>
          </div>
          
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default CompanyDashboard;