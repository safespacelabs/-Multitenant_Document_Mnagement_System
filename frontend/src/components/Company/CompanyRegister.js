import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { companiesAPI } from '../../services/api';
import { Building2, ArrowLeft, CheckCircle } from 'lucide-react';

function CompanyRegister() {
  const [formData, setFormData] = useState({
    name: '',
    email: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

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
      const response = await companiesAPI.create(formData);
      setSuccess(true);
      
      // Redirect to registration page with company ID after 2 seconds
      setTimeout(() => {
        navigate('/register', { state: { companyId: response.data.id } });
      }, 2000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to register company');
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center p-6">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">Company Registered!</h1>
            <p className="text-gray-600 mb-6">
              Your company has been successfully registered. AWS S3 bucket and database have been provisioned.
            </p>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-sm text-gray-500">Redirecting to user registration...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
              <Building2 className="h-8 w-8 text-blue-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">Register Your Company</h1>
            <p className="text-gray-600 mt-2">
              Create a new company workspace with automatic AWS S3 and database setup
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Company Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                placeholder="Enter your company name"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Company Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                placeholder="company@example.com"
              />
              <p className="text-sm text-gray-500 mt-1">
                This will be used for company-wide communications
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-800 mb-2">What happens next?</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• AWS S3 bucket will be created for your company</li>
                <li>• Dedicated PostgreSQL database will be provisioned</li>
                <li>• Multi-tenant isolation will be configured</li>
                <li>• You'll be redirected to create your admin account</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Setting up infrastructure...
                </div>
              ) : (
                'Register Company'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/companies"
              className="inline-flex items-center text-gray-500 hover:text-gray-700 text-sm"
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to company list
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompanyRegister; 