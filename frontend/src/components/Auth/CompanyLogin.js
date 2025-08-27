import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../utils/auth';
import { authAPI } from '../../services/api';
import { Building2, Eye, EyeOff, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

const CompanyLogin = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [step, setStep] = useState('company'); // 'company' or 'login'
  const [formData, setFormData] = useState({
    companyId: location.state?.companyId || '',
    username: '',
    password: ''
  });
  const [companyData, setCompanyData] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleCompanySubmit = async (e) => {
    e.preventDefault();
    if (!formData.companyId.trim()) {
      setError('Please enter a Company ID');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Verify company exists
      const companyResponse = await authAPI.getCompany(formData.companyId.trim());
      setCompanyData(companyResponse);
      setStep('login');
      setError('');
    } catch (error) {
      console.error('Company verification failed:', error);
      if (error.message.includes('Company not found')) {
        setError('Company ID not found. Please check your Company ID and try again.');
      } else {
        setError('Unable to verify company. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('🔐 Attempting company login with:', formData);
      
      // Use the main auth context login function
      const result = await login(formData, formData.companyId);
      
      console.log('✅ Company login successful:', result);
      setSuccess('Login successful! Redirecting...');
      
      // Redirect to dashboard after successful login
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
      
    } catch (error) {
      console.error('❌ Company login failed:', error);
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToCompany = () => {
    setStep('company');
    setCompanyData(null);
    setFormData({ ...formData, username: '', password: '' });
    setError('');
  };

  // Company ID Entry Step
  if (step === 'company') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          {/* Header */}
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Building2 className="h-8 w-8 text-white" />
            </div>
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              Company Login
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Enter your Company ID to access your secure portal
            </p>
          </div>

          {/* Company ID Form */}
          <form className="mt-8 space-y-6" onSubmit={handleCompanySubmit}>
            <div>
              <label htmlFor="companyId" className="block text-sm font-medium text-gray-700 mb-2">
                Company ID
              </label>
              <div className="relative">
                <input
                  id="companyId"
                  name="companyId"
                  type="text"
                  required
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-center text-base font-medium shadow-sm transition-all duration-200"
                  placeholder="Enter Company ID"
                  value={formData.companyId}
                  onChange={(e) => setFormData({ ...formData, companyId: e.target.value })}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-5 h-5 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-xs text-gray-600">?</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      {error}
                    </h3>
                  </div>
                </div>
              </div>
            )}

            {/* Continue Button */}
            <div>
              <button
                type="submit"
                disabled={loading || !formData.companyId.trim()}
                className={`w-full px-6 py-3 rounded-lg transition-all duration-200 flex items-center justify-center text-base font-semibold shadow-md transform ${
                  loading || !formData.companyId.trim()
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-lg hover:-translate-y-0.5'
                }`}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Verifying...
                  </>
                ) : (
                  'Continue'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // Login Step
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h2 className="mt-6 text-2xl font-extrabold text-gray-900">
            Welcome to {companyData?.name}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Enter your username and password to access your company portal
          </p>
        </div>

        {/* Back to Company Selection */}
        <div className="text-center">
          <button
            onClick={handleBackToCompany}
            className="text-indigo-600 hover:text-indigo-500 text-sm font-medium flex items-center justify-center mx-auto"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Company Selection
          </button>
        </div>

        {/* Success Message */}
        {success && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="flex">
              <CheckCircle className="h-5 w-5 text-green-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">
                  {success}
                </h3>
              </div>
            </div>
          </div>
        )}

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleLoginSubmit}>
          <div className="space-y-4">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <div className="relative">
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                  placeholder="Enter your username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-5 h-5 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-xs text-gray-600">?</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>
          </div>

          {/* Forgot Password Link */}
          <div className="text-right">
            <a href="#" className="text-sm font-medium text-indigo-600 hover:text-indigo-500">
              Forgot Password?
            </a>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    {error}
                  </h3>
                </div>
              </div>
            </div>
          )}

          {/* Login Button */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2 inline"></div>
                  Logging in...
                </>
              ) : (
                'Log in'
              )}
            </button>
          </div>
        </form>

        {/* Company Info Footer */}
        <div className="text-center text-xs text-gray-500">
          <p>Company ID: {formData.companyId}</p>
          <p>Secure Company Portal</p>
        </div>
      </div>
    </div>
  );
};

export default CompanyLogin; 