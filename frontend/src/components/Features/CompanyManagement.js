import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { companiesAPI } from '../../services/api';
import { 
  Building2, 
  Plus, 
  Users, 
  Database, 
  Trash2, 
  Eye,
  Settings,
  Activity,
  Search,
  AlertCircle,
  CheckCircle,
  Clock,
  BarChart3
} from 'lucide-react';

const CompanyManagement = () => {
  console.log('🏢 CompanyManagement component rendering...');
  const { user } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    email: ''
  });
  const [testingConnections, setTestingConnections] = useState({});

  useEffect(() => {
    console.log('🏢 CompanyManagement useEffect triggered');
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    console.log('🏢 Loading companies...');
    try {
      setLoading(true);
      const response = await companiesAPI.list();
      console.log('✅ Companies loaded:', response);
      setCompanies(response);
      setError(null);
    } catch (error) {
      console.error('❌ Failed to load companies:', error);
      setError('Failed to load companies');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await companiesAPI.create(createForm);
      setShowCreateModal(false);
      setCreateForm({ name: '', email: '' });
      await loadCompanies();
      alert('Company created successfully!');
    } catch (error) {
      console.error('Failed to create company:', error);
      alert('Failed to create company: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCompany = async (companyId) => {
    if (!window.confirm('Are you sure you want to delete this company? This action cannot be undone and will delete all company data.')) {
      return;
    }
    
    try {
      await companiesAPI.delete(companyId);
      await loadCompanies();
      alert('Company deleted successfully!');
    } catch (error) {
      console.error('Failed to delete company:', error);
      alert('Failed to delete company: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleTestDatabase = async (companyId) => {
    try {
      setTestingConnections(prev => ({ ...prev, [companyId]: 'testing' }));
      
      // Test database connection
      const response = await companiesAPI.testDatabase(companyId);
      
      setTestingConnections(prev => ({ ...prev, [companyId]: 'success' }));
      alert('Database connection successful!');
      
      // Reset status after 3 seconds
      setTimeout(() => {
        setTestingConnections(prev => ({ ...prev, [companyId]: null }));
      }, 3000);
      
    } catch (error) {
      console.error('Database test failed:', error);
      setTestingConnections(prev => ({ ...prev, [companyId]: 'failed' }));
      alert('Database connection failed: ' + (error.response?.data?.detail || error.message));
      
      // Reset status after 3 seconds
      setTimeout(() => {
        setTestingConnections(prev => ({ ...prev, [companyId]: null }));
      }, 3000);
    }
  };

  const getCompanyStats = async (companyId) => {
    try {
      const response = await companiesAPI.getStats(companyId);
      const stats = response.data;
      
      alert(`Company Statistics:
Users: ${stats.user_count || 0}
Documents: ${stats.document_count || 0}
Storage Used: ${stats.storage_used || '0 MB'}
Database Status: ${stats.database_status || 'Unknown'}`);
      
    } catch (error) {
      console.error('Failed to get company stats:', error);
      alert('Failed to get company statistics');
    }
  };

  if (user.role !== 'system_admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">Only system administrators can access company management.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Company Management</h1>
          <p className="text-gray-600 mt-2">
            Manage multi-tenant companies, databases, and infrastructure
          </p>
          <div className="mt-2 flex items-center space-x-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
              System Administrator
            </span>
            <span className="text-sm text-gray-500">Database Isolation: Active</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mb-6 flex space-x-4">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Create New Company
          </button>
          <button
            onClick={loadCompanies}
            className="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Companies Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  Total Companies
                </h3>
                <p className="text-2xl font-bold text-gray-900 mt-1">{companies.length}</p>
              </div>
              <div className="p-3 rounded-full bg-blue-100">
                <div className="w-6 h-6 bg-blue-500 rounded-full"></div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  Active Companies
                </h3>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {companies.filter(c => c.is_active).length}
                </p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <div className="w-6 h-6 bg-green-500 rounded-full"></div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  Databases Created
                </h3>
                <p className="text-2xl font-bold text-gray-900 mt-1">{companies.length}</p>
                <p className="text-sm text-gray-600 mt-1">Isolated DBs</p>
              </div>
              <div className="p-3 rounded-full bg-purple-100">
                <div className="w-6 h-6 bg-purple-500 rounded-full"></div>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  System Health
                </h3>
                <p className="text-2xl font-bold text-green-600 mt-1">Operational</p>
                <p className="text-sm text-gray-600 mt-1">All systems running</p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <div className="w-6 h-6 bg-green-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Companies Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Companies ({companies.length})</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading companies...</p>
            </div>
          ) : companies.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-6xl mb-4">🏢</div>
              <p className="text-lg font-medium mb-2">No companies created yet</p>
              <p>Create your first company to get started with multi-tenant management</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Database</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {companies.map((company) => (
                    <tr key={company.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{company.name}</div>
                          <div className="text-sm text-gray-500">{company.email}</div>
                          <div className="text-xs text-gray-400">ID: {company.id}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{company.database_name}</div>
                        <div className="text-xs text-gray-500">{company.database_host}</div>
                        <div className="text-xs text-gray-400">Port: {company.database_port}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="space-y-1">
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            company.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {company.is_active ? 'Active' : 'Inactive'}
                          </span>
                          {company.s3_bucket_name && (
                            <div>
                              <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                                S3 Configured
                              </span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {new Date(company.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex flex-col space-y-2">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleTestDatabase(company.id)}
                              disabled={testingConnections[company.id] === 'testing'}
                              className={`px-3 py-1 rounded text-xs font-medium ${
                                testingConnections[company.id] === 'testing'
                                  ? 'bg-yellow-100 text-yellow-800 cursor-not-allowed'
                                  : testingConnections[company.id] === 'success'
                                  ? 'bg-green-100 text-green-800'
                                  : testingConnections[company.id] === 'failed'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                              }`}
                            >
                              {testingConnections[company.id] === 'testing'
                                ? 'Testing...'
                                : testingConnections[company.id] === 'success'
                                ? 'Connected ✓'
                                : testingConnections[company.id] === 'failed'
                                ? 'Failed ✗'
                                : 'Test DB'}
                            </button>
                            
                            <button
                              onClick={() => getCompanyStats(company.id)}
                              className="px-3 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium hover:bg-gray-200"
                            >
                              Stats
                            </button>
                          </div>
                          
                          <button
                            onClick={() => handleDeleteCompany(company.id)}
                            className="px-3 py-1 bg-red-100 text-red-800 rounded text-xs font-medium hover:bg-red-200"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Create Company Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Company</h3>
                <form onSubmit={handleCreateCompany} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Name
                    </label>
                    <input
                      type="text"
                      value={createForm.name}
                      onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                      placeholder="Enter company name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Email
                    </label>
                    <input
                      type="email"
                      value={createForm.email}
                      onChange={(e) => setCreateForm(prev => ({ ...prev, email: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                      placeholder="Enter company email"
                    />
                  </div>
                  
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                    <div className="flex">
                      <div className="text-yellow-400 mr-2">⚠️</div>
                      <div className="text-sm text-yellow-800">
                        <p className="font-medium">This will create:</p>
                        <ul className="mt-1 ml-4 text-xs list-disc">
                          <li>Isolated database for the company</li>
                          <li>S3 bucket for document storage</li>
                          <li>Database tables and schema</li>
                          <li>Company-specific user management</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-3 pt-4">
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading ? 'Creating...' : 'Create Company'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCreateModal(false)}
                      className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyManagement; 