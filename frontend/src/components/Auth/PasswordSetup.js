import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { userManagementAPI } from '../../services/api';
import { 
  Key, 
  User, 
  Mail, 
  Building2, 
  CheckCircle, 
  AlertTriangle,
  Eye,
  EyeOff,
  Clock
} from 'lucide-react';

const PasswordSetup = () => {
  const { uniqueId } = useParams();
  const navigate = useNavigate();
  
  const [invitationData, setInvitationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const [setupForm, setSetupForm] = useState({
    username: '',
    password: '',
    confirmPassword: ''
  });
  
  const [passwordValidation, setPasswordValidation] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false
  });

  useEffect(() => {
    fetchInvitationDetails();
  }, [uniqueId]);

  useEffect(() => {
    validatePassword(setupForm.password);
  }, [setupForm.password]);

  const fetchInvitationDetails = async () => {
    try {
      const response = await userManagementAPI.getInvitationDetails(uniqueId);
      setInvitationData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired invitation link');
    } finally {
      setLoading(false);
    }
  };

  const validatePassword = (password) => {
    setPasswordValidation({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    });
  };

  const isPasswordValid = () => {
    return Object.values(passwordValidation).every(Boolean);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (setupForm.password !== setupForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!isPasswordValid()) {
      setError('Password does not meet requirements');
      return;
    }

    if (!setupForm.username.trim()) {
      setError('Username is required');
      return;
    }

    setLoading(true);
    try {
      await userManagementAPI.setupPassword({
        unique_id: uniqueId,
        username: setupForm.username,
        password: setupForm.password
      });
      
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to set password');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !invitationData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Validating invitation...</p>
        </div>
      </div>
    );
  }

  if (error && !invitationData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mt-4">Invalid Invitation</h3>
          <p className="text-sm text-gray-500 mt-2">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mt-4">Password Set Successfully!</h3>
          <p className="text-sm text-gray-500 mt-2">
            Your account has been created. You will be redirected to the login page shortly.
          </p>
          <div className="mt-4 bg-blue-50 rounded-md p-3">
            <p className="text-sm text-blue-800">
              <strong>Username:</strong> {setupForm.username}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-lg">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-white bg-opacity-20">
              <Key className="h-6 w-6" />
            </div>
            <h2 className="text-2xl font-bold mt-4">Set Your Password</h2>
            <p className="text-blue-100 mt-2">Complete your account setup</p>
          </div>
        </div>

        {/* Invitation Details */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Invitation Details</h3>
          <div className="space-y-3">
            <div className="flex items-center text-sm">
              <User className="w-4 h-4 text-gray-400 mr-3" />
              <span className="text-gray-600">Name:</span>
              <span className="ml-2 font-medium">{invitationData?.full_name}</span>
            </div>
            <div className="flex items-center text-sm">
              <Mail className="w-4 h-4 text-gray-400 mr-3" />
              <span className="text-gray-600">Email:</span>
              <span className="ml-2 font-medium">{invitationData?.email}</span>
            </div>
            <div className="flex items-center text-sm">
              <Building2 className="w-4 h-4 text-gray-400 mr-3" />
              <span className="text-gray-600">Company:</span>
              <span className="ml-2 font-medium">{invitationData?.company_name}</span>
            </div>
            <div className="flex items-center text-sm">
              <Clock className="w-4 h-4 text-gray-400 mr-3" />
              <span className="text-gray-600">Role:</span>
              <span className="ml-2 font-medium capitalize">{invitationData?.role?.replace('_', ' ')}</span>
            </div>
          </div>
        </div>

        {/* Setup Form */}
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Choose a Username *
              </label>
              <input
                type="text"
                required
                value={setupForm.username}
                onChange={(e) => setSetupForm({...setupForm, username: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Create Password *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={setupForm.password}
                  onChange={(e) => setSetupForm({...setupForm, password: e.target.value})}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
              
              {/* Password Requirements */}
              <div className="mt-2 space-y-1">
                <p className="text-xs text-gray-600">Password must contain:</p>
                <div className="grid grid-cols-1 gap-1 text-xs">
                  <div className={`flex items-center ${passwordValidation.length ? 'text-green-600' : 'text-gray-400'}`}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    At least 8 characters
                  </div>
                  <div className={`flex items-center ${passwordValidation.uppercase ? 'text-green-600' : 'text-gray-400'}`}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    One uppercase letter
                  </div>
                  <div className={`flex items-center ${passwordValidation.lowercase ? 'text-green-600' : 'text-gray-400'}`}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    One lowercase letter
                  </div>
                  <div className={`flex items-center ${passwordValidation.number ? 'text-green-600' : 'text-gray-400'}`}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    One number
                  </div>
                  <div className={`flex items-center ${passwordValidation.special ? 'text-green-600' : 'text-gray-400'}`}>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    One special character
                  </div>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password *
              </label>
              <input
                type="password"
                required
                value={setupForm.confirmPassword}
                onChange={(e) => setSetupForm({...setupForm, confirmPassword: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Confirm your password"
              />
              {setupForm.confirmPassword && setupForm.password !== setupForm.confirmPassword && (
                <p className="text-xs text-red-600 mt-1">Passwords do not match</p>
              )}
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !isPasswordValid() || setupForm.password !== setupForm.confirmPassword}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? 'Setting up...' : 'Complete Setup'}
            </button>
          </form>
        </div>

        <div className="bg-gray-50 px-6 py-3 rounded-b-lg">
          <p className="text-xs text-gray-600 text-center">
            After setting up your password, you'll be able to login to the document management system.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PasswordSetup; 