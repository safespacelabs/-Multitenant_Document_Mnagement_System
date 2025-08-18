import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../../services/api';

const CompanyLogin = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    companyId: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [companies, setCompanies] = useState([]);
  const [showCompanySelect, setShowCompanySelect] = useState(false);
  const navigate = useNavigate();

  // Fetch companies on component mount
  React.useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await authAPI.getCompanies();
      setCompanies(response);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user types
  };

  const handleCompanySelect = (companyId) => {
    setFormData({
      ...formData,
      companyId: companyId
    });
    setShowCompanySelect(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // First, get company details to get the database URL
      const companyResponse = await authAPI.getCompany(formData.companyId);
      
      if (!companyResponse || !companyResponse.database_url) {
        throw new Error('Invalid company selected');
      }

      // Login with company context
      const loginResponse = await authAPI.loginCompany(
        formData.username,
        formData.password,
        formData.companyId,
        companyResponse.database_url
      );

      if (loginResponse.access_token) {
        localStorage.setItem('access_token', loginResponse.access_token);
        localStorage.setItem('user_type', 'company_user');
        localStorage.setItem('company_id', formData.companyId);
        localStorage.setItem('user_data', JSON.stringify(loginResponse.user));
        
        // Navigate to company dashboard
        navigate('/company-dashboard');
      }
    } catch (error) {
      console.error('Login error:', error);
      setError(error.response?.data?.detail || error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToMain = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-full flex items-center justify-center">
            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Company Login
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Access your company's document management system
          </p>
        </div>

        {/* Back to Main Button */}
        <div className="text-center">
          <button
            onClick={handleBackToMain}
            className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
          >
            ← Back to Main
          </button>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            {/* Company Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Company
              </label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowCompanySelect(!showCompanySelect)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-left focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {formData.companyId ? 
                    companies.find(c => c.id === formData.companyId)?.name || 'Select Company' :
                    'Select Company'
                  }
                </button>
                
                {showCompanySelect && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                    {companies.map((company) => (
                      <button
                        key={company.id}
                        type="button"
                        onClick={() => handleCompanySelect(company.id)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                      >
                        {company.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Username */}
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Username"
                value={formData.username}
                onChange={handleInputChange}
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    {error}
                  </h3>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={loading || !formData.companyId}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="h-5 w-5 text-indigo-500 group-hover:text-indigo-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
              )}
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          {/* Additional Links */}
          <div className="text-center space-y-2">
            <div>
              <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500 text-sm">
                Forgot your password?
              </a>
            </div>
            <div>
              <span className="text-sm text-gray-600">
                Don't have an account?{' '}
                <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">
                  Contact your administrator
                </a>
              </span>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CompanyLogin; 