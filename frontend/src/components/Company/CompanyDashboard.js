import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { EnhancedDocumentManager } from '../Documents/EnhancedDocumentManager';

const CompanyDashboard = () => {
  const [userData, setUserData] = useState(null);
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Get user data from localStorage
    const userDataStr = localStorage.getItem('user_data');
    const companyId = localStorage.getItem('company_id');
    
    if (userDataStr && companyId) {
      try {
        const user = JSON.parse(userDataStr);
        setUserData(user);
        
        // You can fetch company data here if needed
        setCompanyData({
          id: companyId,
          name: user.company_name || 'Your Company'
        });
      } catch (error) {
        console.error('Error parsing user data:', error);
        navigate('/company-login');
      }
    } else {
      navigate('/company-login');
    }
    
    setLoading(false);
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('company_id');
    localStorage.removeItem('user_data');
    navigate('/company-login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!userData || !companyData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
          <p className="text-gray-600 mb-6">Please log in to access your company dashboard.</p>
          <button
            onClick={() => navigate('/company-login')}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="h-10 w-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{companyData.name}</h1>
                <p className="text-sm text-gray-600">Document Management System</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{userData.full_name || userData.username}</p>
                <p className="text-xs text-gray-500 capitalize">{userData.role || 'User'}</p>
              </div>
              <button
                onClick={handleLogout}
                className="bg-gray-100 text-gray-700 px-3 py-2 rounded-md text-sm hover:bg-gray-200 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Welcome back, {userData.full_name || userData.username}!
          </h2>
          <p className="text-gray-600">
            Manage your company's documents, collaborate with team members, and stay organized.
          </p>
        </div>

        {/* Document Management Section */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Document Management</h3>
            <p className="text-sm text-gray-600">Organize, search, and manage your company documents</p>
          </div>
          <div className="p-6">
            <EnhancedDocumentManager />
          </div>
        </div>
      </main>
    </div>
  );
};

export default CompanyDashboard;