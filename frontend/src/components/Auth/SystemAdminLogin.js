import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth, extractErrorMessage } from '../../utils/auth';
import { authAPI } from '../../services/api';
import { Crown, Shield, Lock, ArrowLeft, Eye, EyeOff } from 'lucide-react';

const SystemAdminLogin = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const { systemAdminLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await systemAdminLogin(credentials);
      navigate('/system-dashboard');
    } catch (error) {
      setError(extractErrorMessage(error, 'Invalid credentials'));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Back to Main */}
        <div className="flex justify-start">
          <Link 
            to="/"
            className="inline-flex items-center text-red-600 hover:text-red-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Main Portal
          </Link>
        </div>

        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center">
            <div className="bg-red-500 p-4 rounded-full">
              <Crown className="h-12 w-12 text-white" />
            </div>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            System Administrator
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            System-level access with highest security clearance
          </p>
        </div>

        {/* Security Notice */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <Shield className="h-5 w-5 text-red-500 mr-2" />
            <div>
              <h3 className="text-sm font-medium text-red-800">
                Restricted Access
              </h3>
              <p className="text-sm text-red-700 mt-1">
                This area is restricted to authorized system administrators only.
                All access attempts are logged and monitored.
              </p>
            </div>
          </div>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-lg" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                System Username
              </label>
              <div className="mt-1 relative">
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={credentials.username}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-red-500 focus:border-red-500 focus:z-10 sm:text-sm"
                  placeholder="Enter system username"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                System Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={credentials.password}
                  onChange={handleChange}
                  className="appearance-none relative block w-full px-3 py-3 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-red-500 focus:border-red-500 focus:z-10 sm:text-sm"
                  placeholder="Enter system password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-red-500 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                <Lock className="h-5 w-5 text-red-300 group-hover:text-red-200" />
              </span>
              {loading ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Authenticating...
                </span>
              ) : (
                'Access System Administration'
              )}
            </button>
          </div>

          {/* System Info */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">System Administrator Capabilities:</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Create and manage companies</li>
              <li>• Configure isolated databases</li>
              <li>• Monitor system-wide operations</li>
              <li>• Manage system users and security</li>
              <li>• Access system logs and analytics</li>
            </ul>
          </div>

          {/* Security Footer */}
          <div className="text-center text-xs text-gray-500">
            <div className="flex items-center justify-center space-x-1">
              <Lock className="h-3 w-3" />
              <span>Secure system access • All activity monitored</span>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SystemAdminLogin; 