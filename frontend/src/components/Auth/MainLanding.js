import React, { useState, useEffect } from 'react';
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
  BadgeCheck
} from 'lucide-react';

const MainLanding = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      // We'll need to create a public endpoint to list companies
      const response = await companiesAPI.listPublic();
      setCompanies(response.data);
    } catch (error) {
      console.error('Failed to load companies:', error);
      setError('Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  const handleSystemAdminLogin = () => {
    navigate('/system-admin-login');
  };

  const handleCompanyAccess = (company) => {
    navigate(`/company/${company.id}/access`);
  };

  const getRoleHierarchy = () => [
    {
      role: 'System Admin',
      icon: Crown,
      description: 'Manages all companies and system-level operations',
      color: 'bg-red-500 text-white',
      level: 'System Level'
    },
    {
      role: 'HR Admin',
      icon: Shield,
      description: 'Full company access, manages HR Managers',
      color: 'bg-blue-500 text-white',
      level: 'Company Level'
    },
    {
      role: 'HR Manager',
      icon: UserCheck,
      description: 'Manages employees and customers',
      color: 'bg-cyan-500 text-white',
      level: 'Company Level'
    },
    {
      role: 'Employee',
      icon: Users,
      description: 'Manages customers and documents',
      color: 'bg-green-500 text-white',
      level: 'Company Level'
    },
    {
      role: 'Customer',
      icon: BadgeCheck,
      description: 'Access to personal documents',
      color: 'bg-purple-500 text-white',
      level: 'Company Level'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading companies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Building2 className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Welcome Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to Your Document Management Portal
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Secure, scalable, and intelligent document management for modern enterprises. 
            Choose your access level below to get started.
          </p>
        </div>

        {/* System Admin Access */}
        <div className="mb-12">
          <div className="bg-white rounded-xl shadow-lg overflow-hidden border-2 border-red-200">
            <div className="bg-red-500 text-white px-6 py-4">
              <div className="flex items-center">
                <Crown className="h-6 w-6 mr-3" />
                <h3 className="text-xl font-bold">System Administration</h3>
              </div>
            </div>
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    System Admin Access
                  </h4>
                  <p className="text-gray-600">
                    Manage all companies, databases, and system-level configurations
                  </p>
                  <div className="mt-3 flex items-center text-sm text-gray-500">
                    <Lock className="h-4 w-4 mr-1" />
                    <span>Highest security clearance required</span>
                  </div>
                </div>
                <button
                  onClick={handleSystemAdminLogin}
                  className="bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition-colors flex items-center"
                >
                  <Shield className="h-5 w-5 mr-2" />
                  System Admin Login
                  <ArrowRight className="h-4 w-4 ml-2" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Companies Section */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Company Access</h3>
            <p className="text-gray-600">
              Select your company to access role-based features and documents
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {companies.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <Building className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Companies Available</h3>
              <p className="text-gray-500">
                Contact your system administrator to set up company access
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {companies.map((company) => (
                <div
                  key={company.id}
                  className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow border border-gray-200 overflow-hidden"
                >
                  <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-6 py-4">
                    <div className="flex items-center">
                      <Building2 className="h-6 w-6 mr-3" />
                      <h4 className="text-lg font-bold truncate">{company.name}</h4>
                    </div>
                  </div>
                  
                  <div className="p-6">
                    <div className="mb-4">
                      <p className="text-sm text-gray-500 mb-2">Company Email</p>
                      <p className="text-gray-700">{company.email}</p>
                    </div>
                    
                    <div className="mb-4">
                      <p className="text-sm text-gray-500 mb-2">Status</p>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        company.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {company.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    <div className="mb-6">
                      <p className="text-sm text-gray-500 mb-2">Available Roles</p>
                      <div className="text-xs text-gray-600">
                        HR Admin • HR Manager • Employee • Customer
                      </div>
                    </div>

                    <button
                      onClick={() => handleCompanyAccess(company)}
                      disabled={!company.is_active}
                      className={`w-full py-3 px-4 rounded-lg transition-colors flex items-center justify-center ${
                        company.is_active
                          ? 'bg-blue-500 text-white hover:bg-blue-600'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <Users className="h-4 w-4 mr-2" />
                      Access Company
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Role Hierarchy Section */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Role Hierarchy & Access Levels
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {getRoleHierarchy().map((role, index) => (
              <div key={role.role} className="text-center">
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${role.color} mb-3`}>
                  <role.icon className="h-8 w-8" />
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">{role.role}</h4>
                <p className="text-xs text-gray-600 mb-2">{role.level}</p>
                <p className="text-sm text-gray-500">{role.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Access Flow:</h4>
            <p className="text-sm text-gray-600">
              <strong>System Admin</strong> creates companies → 
              <strong> HR Admin</strong> manages company → 
              <strong> HR Manager</strong> invites employees → 
              <strong> Employee</strong> can invite customers → 
              <strong> Customer</strong> self-registration
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500">
          <p className="text-sm">
            Secure multi-tenant document management • Role-based access control • AI-powered metadata extraction
          </p>
        </div>
      </div>
    </div>
  );
};

export default MainLanding; 