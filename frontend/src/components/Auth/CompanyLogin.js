import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams, useLocation } from 'react-router-dom';
import { useAuth, extractErrorMessage } from '../../utils/auth';
import { LogIn, Eye, EyeOff, Building2, Shield, Users, UserCheck, BadgeCheck, ArrowLeft } from 'lucide-react';
import { companiesAPI } from '../../services/api';

function CompanyLogin() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [companyInfo, setCompanyInfo] = useState(null);
  const [loadingCompany, setLoadingCompany] = useState(true);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  const { companyId } = useParams();
  const location = useLocation();
  const { role, company } = location.state || {};

  useEffect(() => {
    if (company) {
      setCompanyInfo(company);
      setLoadingCompany(false);
    } else if (companyId) {
      fetchCompanyInfo();
    }
  }, [companyId, company]);

  const fetchCompanyInfo = async () => {
    try {
      setLoadingCompany(true);
      const response = await companiesAPI.getPublic(companyId);
      setCompanyInfo(response.data);
    } catch (error) {
      setError('Company not found');
      console.error('Error fetching company:', error);
    } finally {
      setLoadingCompany(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await login(formData, companyId);
      const { user, company } = response;
      
      // Company users should go to dashboard
      if (company && user.role !== 'system_admin') {
        navigate('/dashboard');
      } else {
        navigate('/companies');
      }
    } catch (error) {
      setError(extractErrorMessage(error, 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  if (loadingCompany) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading company information...</p>
        </div>
      </div>
    );
  }

  if (!companyInfo && !loadingCompany) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-red-600 mb-4">
              <Building2 className="h-16 w-16 mx-auto" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">Company Not Found</h1>
            <p className="text-gray-600 mb-6">The company you're looking for doesn't exist or has been deactivated.</p>
            <Link
              to="/"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Building2 className="h-4 w-4 mr-2" />
              Back to Main Portal
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const getRoleInfo = (userRole) => {
    const roles = {
      hr_admin: {
        name: 'HR Admin',
        icon: Shield,
        color: 'blue',
        description: 'Full company access and management'
      },
      hr_manager: {
        name: 'HR Manager',
        icon: UserCheck,
        color: 'cyan',
        description: 'Manage employees and customers'
      },
      employee: {
        name: 'Employee',
        icon: Users,
        color: 'green',
        description: 'Manage customers and documents'
      },
      customer: {
        name: 'Customer',
        icon: BadgeCheck,
        color: 'purple',
        description: 'Access personal documents'
      }
    };
    return roles[userRole] || roles.customer;
  };

  const getCompanyTheme = () => {
    if (!companyInfo) return { primary: 'blue', secondary: 'indigo' };
    
    // If we have role info, use role-based theming
    if (role) {
      const roleInfo = getRoleInfo(role);
      return { 
        primary: roleInfo.color, 
        secondary: roleInfo.color, 
        gradient: `from-${roleInfo.color}-50 to-${roleInfo.color}-100` 
      };
    }
    
    const themes = {
      'amazon': { primary: 'orange', secondary: 'yellow', gradient: 'from-orange-50 to-yellow-100' },
      'microsoft': { primary: 'blue', secondary: 'cyan', gradient: 'from-blue-50 to-cyan-100' },
      'safespacelabs': { primary: 'green', secondary: 'emerald', gradient: 'from-green-50 to-emerald-100' }
    };
    
    const normalizedName = companyInfo.name.toLowerCase().replace(/\s+/g, '');
    return themes[normalizedName] || { primary: 'blue', secondary: 'indigo', gradient: 'from-blue-50 to-indigo-100' };
  };

  const theme = getCompanyTheme();
  const roleInfo = role ? getRoleInfo(role) : null;

  return (
    <div className={`min-h-screen bg-gradient-to-br ${theme.gradient}`}>
      {/* Header with back button */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <Link 
              to={`/company/${companyId}/access`}
              className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Company Access
            </Link>
            <div className="flex items-center space-x-3">
              <Building2 className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-semibold text-gray-900">{companyInfo?.name}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center py-12 px-6">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8">
            {/* Role Header */}
            {roleInfo && (
              <div className="text-center mb-6">
                <div className={`inline-flex items-center justify-center w-16 h-16 bg-${roleInfo.color}-100 rounded-full mb-4`}>
                  <roleInfo.icon className={`h-8 w-8 text-${roleInfo.color}-600`} />
                </div>
                <h1 className="text-2xl font-bold text-gray-800">{roleInfo.name} Login</h1>
                <p className="text-gray-600 mt-1">{roleInfo.description}</p>
              </div>
            )}

            {/* Company Header */}
            <div className="text-center mb-8">
              {!roleInfo && (
                <div className={`inline-flex items-center justify-center w-16 h-16 bg-${theme.primary}-100 rounded-full mb-4`}>
                  <Building2 className={`h-8 w-8 text-${theme.primary}-600`} />
                </div>
              )}
              <h2 className={`${roleInfo ? 'text-lg' : 'text-2xl'} font-bold text-gray-800`}>{companyInfo?.name}</h2>
              <p className="text-gray-600 mt-1">{roleInfo ? 'Company Portal' : 'Employee & Customer Portal'}</p>
              <div className="flex items-center justify-center mt-3 text-sm text-gray-500">
                <Shield className="h-4 w-4 mr-1" />
                Secure Access • Company ID: {companyId}
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors`}
                  placeholder="Enter your username"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors pr-12`}
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className={`w-full bg-${theme.primary}-600 text-white py-3 px-4 rounded-lg hover:bg-${theme.primary}-700 focus:ring-2 focus:ring-${theme.primary}-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium`}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Signing in...
                  </div>
                ) : (
                  <>
                    <LogIn className="inline h-5 w-5 mr-2" />
                    Sign In{roleInfo ? ` as ${roleInfo.name}` : ` to ${companyInfo?.name}`}
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-600">
                Need an account?{' '}
                <Link
                  to={`/company/${companyId}/signup`}
                  state={{ role, company: companyInfo }}
                  className={`text-${theme.primary}-600 hover:text-${theme.primary}-700 font-medium`}
                >
                  Sign up here
                </Link>
              </p>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 text-center">
              <Link
                to="/"
                className="inline-flex items-center text-gray-500 hover:text-gray-700 text-sm"
              >
                <Building2 className="h-4 w-4 mr-1" />
                Choose different company
              </Link>
            </div>

            {/* Company Info Footer */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>ID: {companyInfo?.id}</span>
                <span className="flex items-center">
                  <Users className="h-3 w-3 mr-1" />
                  Enterprise Portal
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompanyLogin; 