import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams, useLocation } from 'react-router-dom';
import { Building2, UserPlus, Mail, User, Shield, AlertCircle, CheckCircle, ArrowLeft, Eye, EyeOff, UserCheck, Users, BadgeCheck } from 'lucide-react';
import { companiesAPI, authAPI } from '../../services/api';
import { useAuth, extractErrorMessage } from '../../utils/auth';

function CompanyRegister() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    department: '',
    reason: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [loadingCompany, setLoadingCompany] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  
  const navigate = useNavigate();
  const { companyId } = useParams();
  const location = useLocation();
  const { role, company } = location.state || {};
  const { login } = useAuth();

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
      // Check if this role can self-register (HR Admin, Customer)
      if (role === 'hr_admin' || role === 'customer') {
        // Actual registration
        const userData = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name,
          role: role
        };
        
        const response = await authAPI.register(userData, companyId);
        await login(response.data);
        
        // Navigate to dashboard
        navigate('/dashboard');
      } else {
        // Request access for roles that need invitation
        const requestData = {
          ...formData,
          role: role
        };
        await companiesAPI.requestAccess(companyId, requestData);
        setSuccess(true);
      }
    } catch (error) {
      setError(extractErrorMessage(error, 'Failed to submit request'));
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
              to="/companies"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Building2 className="h-4 w-4 mr-2" />
              Browse All Companies
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const getCompanyTheme = () => {
    if (!companyInfo) return { primary: 'blue', secondary: 'indigo' };
    
    const themes = {
      'amazon': { primary: 'orange', secondary: 'yellow', gradient: 'from-orange-50 to-yellow-100' },
      'microsoft': { primary: 'blue', secondary: 'cyan', gradient: 'from-blue-50 to-cyan-100' },
      'safespacelabs': { primary: 'green', secondary: 'emerald', gradient: 'from-green-50 to-emerald-100' }
    };
    
    const normalizedName = companyInfo.name.toLowerCase().replace(/\s+/g, '');
    return themes[normalizedName] || { primary: 'blue', secondary: 'indigo', gradient: 'from-blue-50 to-indigo-100' };
  };

  const theme = getCompanyTheme();

  if (success) {
    return (
      <div className={`min-h-screen bg-gradient-to-br ${theme.gradient} flex items-center justify-center p-6`}>
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="mb-6">
              <CheckCircle className="h-16 w-16 text-green-600 mx-auto" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">Request Submitted</h1>
            <p className="text-gray-600 mb-6">
              Your access request for <strong>{companyInfo?.name}</strong> has been submitted successfully. 
              An HR administrator will review your request and contact you via email.
            </p>
            <div className="space-y-3">
              <Link
                to={`/company/${companyId}/login`}
                className={`w-full inline-flex items-center justify-center px-4 py-2 bg-${theme.primary}-600 text-white rounded-lg hover:bg-${theme.primary}-700 transition-colors`}
              >
                Already have an account? Sign In
              </Link>
              <Link
                to="/companies"
                className="w-full inline-flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                <Building2 className="h-4 w-4 mr-2" />
                Browse Other Companies
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br ${theme.gradient} flex items-center justify-center p-6`}>
      <div className="max-w-md w-full">
        <div className="bg-white rounded-xl shadow-lg p-8 max-h-screen overflow-y-auto">
          {/* Company Header */}
          <div className="text-center mb-8">
            <div className={`inline-flex items-center justify-center w-16 h-16 bg-${theme.primary}-100 rounded-full mb-4`}>
              <UserPlus className={`h-8 w-8 text-${theme.primary}-600`} />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">Request Access</h1>
            <p className="text-gray-600 mt-1">Join <strong>{companyInfo?.name}</strong></p>
            <div className="flex items-center justify-center mt-3 text-sm text-gray-500">
              <Shield className="h-4 w-4 mr-1" />
              Secure Registration • Company ID: {companyId}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-start">
              <AlertCircle className="h-5 w-5 mt-0.5 mr-2 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                Full Name *
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  id="full_name"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                  className={`w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors`}
                  placeholder="Enter your full name"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className={`w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors`}
                  placeholder="your@email.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Username *
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors`}
                placeholder="Choose a username"
              />
            </div>

            <div>
              <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-2">
                Department/Role
              </label>
              <input
                type="text"
                id="department"
                name="department"
                value={formData.department}
                onChange={handleChange}
                className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors`}
                placeholder="e.g., Engineering, Sales, Customer"
              />
            </div>

            <div>
              <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
                Reason for Access Request
              </label>
              <textarea
                id="reason"
                name="reason"
                value={formData.reason}
                onChange={handleChange}
                rows="3"
                className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-${theme.primary}-500 focus:border-${theme.primary}-500 transition-colors`}
                placeholder="Brief description of why you need access..."
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Submitting Request...
                </div>
              ) : (
                <>
                  <UserPlus className="inline h-5 w-5 mr-2" />
                  Submit Access Request
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link
                to={`/company/${companyId}/login`}
                className={`text-${theme.primary}-600 hover:text-${theme.primary}-700 font-medium`}
              >
                Sign In
              </Link>
            </p>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200 text-center">
            <Link
              to="/companies"
              className="inline-flex items-center text-gray-500 hover:text-gray-700 text-sm"
            >
              <Building2 className="h-4 w-4 mr-1" />
              Browse other companies
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompanyRegister; 