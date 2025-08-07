import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { companiesAPI } from '../../services/api';
import { 
  Building2, 
  Shield, 
  Users, 
  ArrowRight, 
  Globe,
  Lock,
  UserCheck,
  Building,
  Crown,
  BadgeCheck,
  Search
} from 'lucide-react';

const MainLanding = () => {
  const [companyId, setCompanyId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSystemAdminLogin = () => {
    navigate('/system-admin-login');
  };

  const handleCompanyAccess = async () => {
    if (!companyId.trim()) {
      setError('Please enter a Company ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // First test the API connection with simple GET
      console.log('🧪 Testing API connection...');
      const testResponse = await fetch('https://multitenant-backend-mlap.onrender.com/test-cors', {
        method: 'GET',
        mode: 'cors'
      });
      console.log('🔗 API test response:', testResponse.status, testResponse.ok);
      
      if (!testResponse.ok) {
        throw new Error(`API connection failed: ${testResponse.status}`);
      }

      // Verify company exists before redirecting
      console.log('🔍 Looking up company:', companyId.trim());
      
      // Test the specific company endpoint directly
      const companyResponse = await fetch(`https://multitenant-backend-mlap.onrender.com/api/companies/${companyId.trim()}/public`, {
        method: 'GET',
        mode: 'cors'
      });
      console.log('🏢 Company API response:', companyResponse.status, companyResponse.ok);
      
      if (!companyResponse.ok) {
        throw new Error(`Company lookup failed: ${companyResponse.status}`);
      }
      
      const companyData = await companyResponse.json();
      console.log('📋 Company data:', companyData);
      
      await companiesAPI.getPublic(companyId.trim());
      console.log('✅ Company found, navigating...');
      navigate(`/company/${companyId.trim()}/access`);
    } catch (error) {
      console.error('❌ Company verification failed:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response,
        status: error.response?.status
      });
      
      if (error.message.includes('API connection failed')) {
        setError('Unable to connect to the server. Please try again later.');
      } else if (error.response?.status === 404) {
        setError('Company ID not found. Please check your Company ID and try again.');
      } else {
        setError(`Error: ${error.message || 'Unable to verify company. Please try again.'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCompanyIdKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleCompanyAccess();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-5">
            <div className="flex items-center">
              <Building2 className="h-7 w-7 text-blue-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">
                Multi-Tenant Document Management System
              </h1>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Globe className="h-4 w-4" />
              <span>Enterprise Portal</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Welcome Section */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            Welcome to Your Document Management Portal
          </h2>
          <p className="text-base text-gray-600 max-w-2xl mx-auto">
            Secure, scalable, and intelligent document management for modern enterprises. 
            Choose your access method below to get started.
          </p>
        </div>

        {/* Main Access Options */}
        <div className="space-y-6 mb-10">
          
          {/* System Admin Access Row */}
          <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-xl p-1.5 shadow-lg">
            <div className="bg-white rounded-lg shadow-md overflow-hidden border border-red-100">
              <div className="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-4">
                <div className="flex items-center justify-center">
                  <Crown className="h-7 w-7 mr-3" />
                  <h3 className="text-xl font-bold">System Administration</h3>
                </div>
              </div>
              <div className="p-8 text-center">
                <div className="mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-red-100 to-red-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-md">
                    <Shield className="h-8 w-8 text-red-600" />
                  </div>
                  <h4 className="text-xl font-bold text-gray-900 mb-3">
                    System Admin Access
                  </h4>
                  <p className="text-base text-gray-600 mb-4 max-w-xl mx-auto">
                    Complete control over the entire system. Manage all companies, databases, 
                    user accounts, and system-level configurations.
                  </p>
                  <div className="flex items-center justify-center text-sm text-gray-500 mb-6">
                    <Lock className="h-4 w-4 mr-2" />
                    <span className="font-medium">Highest security clearance required</span>
                  </div>
                </div>
                <div className="max-w-sm mx-auto">
                  <button
                    onClick={handleSystemAdminLogin}
                    className="w-full bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-lg hover:from-red-600 hover:to-red-700 transition-all duration-200 flex items-center justify-center text-base font-semibold shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                  >
                    <Shield className="h-5 w-5 mr-2" />
                    System Admin Login
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Company Access Row */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-1.5 shadow-lg">
            <div className="bg-white rounded-lg shadow-md overflow-hidden border border-blue-100">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-4">
                <div className="flex items-center justify-center">
                  <Building className="h-7 w-7 mr-3" />
                  <h3 className="text-xl font-bold">Company Access Portal</h3>
                </div>
              </div>
              <div className="p-8 text-center">
                <div className="mb-6">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-md">
                    <Users className="h-8 w-8 text-blue-600" />
                  </div>
                  <h4 className="text-xl font-bold text-gray-900 mb-3">
                    Enter Your Company ID
                  </h4>
                  <p className="text-base text-gray-600 mb-6 max-w-xl mx-auto">
                    Access your organization's secure document management portal. 
                    Each company operates in complete isolation with role-based access control.
                  </p>
                  
                  {/* Company ID Input */}
                  <div className="max-w-sm mx-auto mb-6">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        value={companyId}
                        onChange={(e) => setCompanyId(e.target.value)}
                        onKeyPress={handleCompanyIdKeyPress}
                        placeholder="Enter your Company ID"
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center text-base font-medium shadow-sm transition-all duration-200"
                      />
                    </div>
                    {error && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-700 text-sm font-medium">{error}</p>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="max-w-sm mx-auto">
                  <button
                    onClick={handleCompanyAccess}
                    disabled={loading || !companyId.trim()}
                    className={`w-full px-6 py-3 rounded-lg transition-all duration-200 flex items-center justify-center text-base font-semibold shadow-md transform ${
                      loading || !companyId.trim()
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 hover:shadow-lg hover:-translate-y-0.5'
                    }`}
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Verifying...
                      </>
                    ) : (
                      <>
                        <Building className="h-5 w-5 mr-2" />
                        Access Company Portal
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="bg-gradient-to-br from-gray-50 to-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              How It Works
            </h3>
            <p className="text-base text-gray-600 max-w-xl mx-auto">
              Simple, secure access tailored to your role and organization
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* System Admin Flow */}
            <div className="bg-white rounded-lg p-6 shadow-md border border-red-100">
              <div className="text-center mb-5">
                <div className="w-14 h-14 bg-gradient-to-br from-red-100 to-red-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
                  <Crown className="h-7 w-7 text-red-600" />
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">System Administrator</h4>
                <p className="text-sm text-gray-600 mb-4">Ultimate control and oversight</p>
              </div>
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Manage all companies in the system</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Create and configure company accounts</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Monitor system-wide performance</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Access all system features and settings</p>
                </div>
              </div>
            </div>

            {/* Company User Flow */}
            <div className="bg-white rounded-lg p-6 shadow-md border border-blue-100">
              <div className="text-center mb-5">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
                  <Building className="h-7 w-7 text-blue-600" />
                </div>
                <h4 className="text-lg font-bold text-gray-900 mb-2">Company Users</h4>
                <p className="text-sm text-gray-600 mb-4">Secure company-specific access</p>
              </div>
              <div className="space-y-3">
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Enter your unique Company ID</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Access your company's secure portal</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Login with your role (HR Admin, HR Manager, Employee, Customer)</p>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-sm text-gray-700">Manage documents and collaborate securely</p>
                </div>
              </div>
            </div>
          </div>

          {/* Security Notice */}
          <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
            <div className="flex items-center justify-center mb-3">
              <Lock className="h-6 w-6 text-blue-600 mr-2" />
              <h4 className="text-lg font-bold text-blue-900">Security & Privacy Guarantee</h4>
            </div>
            <p className="text-base text-blue-800 text-center max-w-3xl mx-auto leading-relaxed">
              Each company operates in <strong>complete isolation</strong>. Company data, users, and documents are 
              fully separated with military-grade encryption, ensuring maximum security and privacy for your organization.
            </p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-blue-700">
              <div className="flex items-center">
                <Shield className="h-4 w-4 mr-2" />
                <span className="text-sm font-medium">End-to-End Encryption</span>
              </div>
              <div className="flex items-center">
                <UserCheck className="h-4 w-4 mr-2" />
                <span className="text-sm font-medium">Role-Based Access</span>
              </div>
              <div className="flex items-center">
                <Lock className="h-4 w-4 mr-2" />
                <span className="text-sm font-medium">Data Isolation</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <div className="border-t border-gray-200 pt-6">
            <div className="flex flex-wrap items-center justify-center gap-4 text-gray-600 mb-3">
              <div className="flex items-center space-x-1.5">
                <Shield className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">Secure Multi-Tenant</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <UserCheck className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">Role-Based Access</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <Building2 className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium">AI-Powered Intelligence</span>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              © 2024 Multi-Tenant Document Management System. Built for enterprise security and scalability.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainLanding; 