import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { companiesAPI } from '../../services/api';
import { 
  Building2, 
  Shield, 
  UserCheck, 
  Users, 
  BadgeCheck, 
  ArrowLeft,
  LogIn,
  UserPlus,
  Crown,
  Lock,
  Info
} from 'lucide-react';

const CompanyAccess = () => {
  const { companyId } = useParams();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRole, setSelectedRole] = useState('hr_admin');
  const navigate = useNavigate();

  useEffect(() => {
    loadCompany();
  }, [companyId]);

  const loadCompany = async () => {
    try {
      const response = await companiesAPI.getPublic(companyId);
      setCompany(response.data);
    } catch (error) {
      setError('Company not found');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (role) => {
    navigate(`/company/${companyId}/login`, { state: { role, company } });
  };

  const handleSignup = (role) => {
    navigate(`/company/${companyId}/signup`, { state: { role, company } });
  };

  const getRoles = () => [
    {
      role: 'hr_admin',
      name: 'HR Admin',
      icon: Shield,
      description: 'Full company access and management',
      color: 'bg-blue-500 text-white',
      borderColor: 'border-blue-200',
      canLogin: true,
      canSignup: true,
      signupNote: 'Initial HR Admin can be created by System Admin',
      level: 'Highest Company Authority'
    },
    {
      role: 'hr_manager',
      name: 'HR Manager',
      icon: UserCheck,
      description: 'Manage employees and customers',
      color: 'bg-cyan-500 text-white',
      borderColor: 'border-cyan-200',
      canLogin: true,
      canSignup: false,
      signupNote: 'Invitation required from HR Admin',
      level: 'Department Management'
    },
    {
      role: 'employee',
      name: 'Employee',
      icon: Users,
      description: 'Manage customers and documents',
      color: 'bg-green-500 text-white',
      borderColor: 'border-green-200',
      canLogin: true,
      canSignup: false,
      signupNote: 'Invitation required from HR Manager',
      level: 'Operational Level'
    },
    {
      role: 'customer',
      name: 'Customer',
      icon: BadgeCheck,
      description: 'Access personal documents',
      color: 'bg-purple-500 text-white',
      borderColor: 'border-purple-200',
      canLogin: true,
      canSignup: true,
      signupNote: 'Self-registration available',
      level: 'Client Access'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading company information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <Building2 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Company Not Found</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Link 
            to="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Main Portal
          </Link>
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
            <Link 
              to="/"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Main Portal
            </Link>
            <div className="flex items-center space-x-3">
              <Building2 className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-semibold text-gray-900">{company?.name}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Company Info */}
        <div className="text-center mb-12">
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl p-8 mb-8">
            <Building2 className="h-16 w-16 mx-auto mb-4" />
            <h1 className="text-3xl font-bold mb-2">{company?.name}</h1>
            <p className="text-blue-100 mb-4">{company?.email}</p>
            <div className="flex justify-center items-center space-x-4">
              <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                company?.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {company?.is_active ? 'Active Company' : 'Inactive Company'}
              </span>
            </div>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Choose Your Access Level
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Select your role to access company resources. Different roles have different 
            capabilities and access levels within the organization.
          </p>
        </div>

        {/* Role Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {getRoles().map((roleInfo) => (
            <div
              key={roleInfo.role}
              className={`bg-white rounded-xl shadow-lg overflow-hidden border-2 ${roleInfo.borderColor} hover:shadow-xl transition-all duration-200`}
            >
              {/* Role Header */}
              <div className={`${roleInfo.color} px-6 py-4`}>
                <div className="flex items-center justify-center mb-2">
                  <roleInfo.icon className="h-8 w-8" />
                </div>
                <h3 className="text-lg font-bold text-center">{roleInfo.name}</h3>
                <p className="text-xs text-center opacity-90">{roleInfo.level}</p>
              </div>

              {/* Role Content */}
              <div className="p-6">
                <p className="text-sm text-gray-600 mb-4 text-center">
                  {roleInfo.description}
                </p>

                {/* Action Buttons */}
                <div className="space-y-3">
                  {roleInfo.canLogin && (
                    <button
                      onClick={() => handleLogin(roleInfo.role)}
                      disabled={!company?.is_active}
                      className={`w-full py-2 px-4 rounded-lg transition-colors flex items-center justify-center ${
                        company?.is_active
                          ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <LogIn className="h-4 w-4 mr-2" />
                      Login
                    </button>
                  )}

                  {roleInfo.canSignup ? (
                    <button
                      onClick={() => handleSignup(roleInfo.role)}
                      disabled={!company?.is_active}
                      className={`w-full py-2 px-4 rounded-lg transition-colors flex items-center justify-center ${
                        company?.is_active
                          ? `${roleInfo.color.replace('text-white', 'text-white hover:opacity-90')}`
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      <UserPlus className="h-4 w-4 mr-2" />
                      Sign Up
                    </button>
                  ) : (
                    <div className="w-full py-2 px-4 rounded-lg bg-gray-100 text-gray-500 flex items-center justify-center cursor-not-allowed">
                      <Lock className="h-4 w-4 mr-2" />
                      Invitation Only
                    </div>
                  )}
                </div>

                {/* Signup Note */}
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-start">
                    <Info className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-gray-600">{roleInfo.signupNote}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Access Flow Information */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">
            Role-Based Access Flow
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Access Hierarchy */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Role Hierarchy</h4>
              <div className="space-y-3">
                <div className="flex items-center p-3 bg-blue-50 rounded-lg">
                  <Shield className="h-5 w-5 text-blue-500 mr-3" />
                  <div>
                    <div className="font-medium text-blue-900">HR Admin</div>
                    <div className="text-sm text-blue-700">Manages entire company</div>
                  </div>
                </div>
                <div className="flex items-center p-3 bg-cyan-50 rounded-lg">
                  <UserCheck className="h-5 w-5 text-cyan-500 mr-3" />
                  <div>
                    <div className="font-medium text-cyan-900">HR Manager</div>
                    <div className="text-sm text-cyan-700">Manages departments</div>
                  </div>
                </div>
                <div className="flex items-center p-3 bg-green-50 rounded-lg">
                  <Users className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <div className="font-medium text-green-900">Employee</div>
                    <div className="text-sm text-green-700">Operational tasks</div>
                  </div>
                </div>
                <div className="flex items-center p-3 bg-purple-50 rounded-lg">
                  <BadgeCheck className="h-5 w-5 text-purple-500 mr-3" />
                  <div>
                    <div className="font-medium text-purple-900">Customer</div>
                    <div className="text-sm text-purple-700">Personal access</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Registration Process */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Registration Process</h4>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <strong className="text-blue-900">HR Admin:</strong> Created by System Admin during company setup
                </div>
                <div className="p-3 bg-cyan-50 rounded-lg">
                  <strong className="text-cyan-900">HR Manager:</strong> Invited by HR Admin through internal system
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <strong className="text-green-900">Employee:</strong> Invited by HR Manager or HR Admin
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <strong className="text-purple-900">Customer:</strong> Can self-register or be invited by employees
                </div>
              </div>
            </div>
          </div>

          {/* Company Status Notice */}
          {!company?.is_active && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <Crown className="h-5 w-5 text-red-500 mr-2" />
                <div>
                  <h4 className="text-red-800 font-medium">Company Inactive</h4>
                  <p className="text-red-700 text-sm">
                    This company is currently inactive. Contact your system administrator 
                    to reactivate company access.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompanyAccess; 