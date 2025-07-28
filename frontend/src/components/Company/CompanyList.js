import React, { useState, useEffect } from 'react';
import api, { companiesAPI } from '../../services/api';
import { useAuth } from '../../utils/auth';
import UserManagement from '../Users/UserManagement';
import Header from '../Layout/Header';
import { 
  Plus, 
  Building2, 
  Users, 
  FileText, 
  BarChart3, 
  Settings, 
  Trash2, 
  Edit, 
  Search,
  Filter,
  Download,
  Upload,
  Calendar,
  Database,
  Cloud,
  Shield,
  AlertTriangle,
  CheckCircle,
  Eye,
  MoreVertical,
  LogIn
} from 'lucide-react';
import { Link } from 'react-router-dom';

function CompanyList() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'cards'
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [showUserManagement, setShowUserManagement] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState(null);
  const { user } = useAuth();

  // New company form state
  const [newCompany, setNewCompany] = useState({
    name: '',
    email: '',
    description: '',
    industry: '',
    size: ''
  });

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await companiesAPI.list();
      setCompanies(response.data);
    } catch (err) {
      setError('Failed to fetch companies');
      console.error('Error fetching companies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await companiesAPI.create(newCompany);
      setShowCreateModal(false);
      setNewCompany({ name: '', email: '', description: '', industry: '', size: '' });
      await fetchCompanies();
    } catch (err) {
      setError('Failed to create company');
      console.error('Error creating company:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (company) => {
    setSelectedCompany(company);
    setShowDeleteModal(true);
    setDeleteConfirmText('');
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirmText !== selectedCompany.name) {
      setError('Company name does not match');
      return;
    }

    setDeleting(true);
    try {
      const response = await companiesAPI.delete(selectedCompany.id);
      
      // Show success message
      alert(`Company "${selectedCompany.name}" has been deleted successfully.\n\n` +
            `Details:\n` +
            `- Users deleted: ${response.data.users_deleted}\n` +
            `- Documents deleted: ${response.data.documents_deleted}\n` +
            `- S3 bucket deleted: ${response.data.s3_bucket_deleted ? 'Yes' : 'No'}\n` +
            `- S3 bucket name: ${response.data.s3_bucket_name}`);
      
      await fetchCompanies();
      setShowDeleteModal(false);
      setSelectedCompany(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete company');
    } finally {
      setDeleting(false);
    }
  };

  const fetchCompanyStats = async (companyId) => {
    try {
      const response = await companiesAPI.getStats(companyId);
      const stats = response.data.stats;
      alert(`Company Statistics:\n\n` +
            `Users: ${stats.users}\n` +
            `Documents: ${stats.documents}\n` +
            `Chat History: ${stats.chats}\n` +
            `S3 Bucket: ${stats.s3_bucket || 'N/A'}`);
    } catch (err) {
      setError('Failed to fetch company statistics');
      console.error('Error fetching company stats:', err);
    }
  };

  const handleViewCompany = async (companyId) => {
    try {
      const response = await companiesAPI.get(companyId);
      const company = response.data;
      alert(`Company Details:\n\n` +
            `Name: ${company.name}\n` +
            `Email: ${company.email}\n` +
            `ID: ${company.id}\n` +
            `Database: ${company.database_name}\n` +
            `S3 Bucket: ${company.s3_bucket_name || 'N/A'}\n` +
            `Status: ${company.is_active ? 'Active' : 'Inactive'}\n` +
            `Created: ${new Date(company.created_at).toLocaleString()}`);
    } catch (err) {
      setError('Failed to fetch company details');
      console.error('Error fetching company details:', err);
    }
  };

  const handleManageUsers = (companyId) => {
    setSelectedCompanyId(companyId);
    setShowUserManagement(true);
  };

  const filteredCompanies = companies.filter(company => {
    const matchesSearch = company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         company.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && company.is_active) ||
                         (filterStatus === 'inactive' && !company.is_active);
    return matchesSearch && matchesFilter;
  });

  const sortedCompanies = [...filteredCompanies].sort((a, b) => {
    const aVal = a[sortBy]?.toLowerCase() || '';
    const bVal = b[sortBy]?.toLowerCase() || '';
    return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
  });

  if (loading && companies.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading enterprise data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-screen flex flex-col">
      {/* Header Section */}
      <div className="border-b border-gray-200 bg-gradient-to-r from-slate-50 to-gray-50 flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
                <Building2 className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Enterprise Organizations</h1>
                <p className="text-sm text-gray-600">Manage all organizations and their configurations</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Organization
              </button>
              <button className="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors">
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Controls Bar */}
      <div className="border-b border-gray-200 bg-gray-50 flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-4 flex-1">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search organizations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
              </div>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              >
                <option value="name">Sort by Name</option>
                <option value="email">Sort by Email</option>
                <option value="created_at">Sort by Date</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {filteredCompanies.length} of {companies.length} organizations
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center flex-shrink-0">
          <AlertTriangle className="w-5 h-5 mr-2" />
          {error}
        </div>
      )}

      {/* Table Section with Scroll */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-x-auto overflow-y-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Organization
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Storage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedCompanies.map((company) => (
                <tr key={company.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                          <span className="text-white font-semibold text-sm">
                            {company.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{company.name}</div>
                        <div className="text-sm text-gray-500">ID: {company.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{company.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-900">
                      <Calendar className="w-4 h-4 mr-1 text-gray-400" />
                      {new Date(company.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Cloud className="w-4 h-4 mr-1 text-gray-400" />
                      <span className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                        {company.s3_bucket_name || 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      company.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {company.is_active ? (
                        <>
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Active
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          Inactive
                        </>
                      )}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/company/${company.id}/login`}
                        className="inline-flex items-center px-3 py-1 bg-green-50 text-green-700 text-xs font-medium rounded hover:bg-green-100 transition-colors"
                      >
                        <LogIn className="w-3 h-3 mr-1" />
                        Portal
                      </Link>
                      <button
                        onClick={() => fetchCompanyStats(company.id)}
                        className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded hover:bg-blue-100 transition-colors"
                      >
                        <BarChart3 className="w-3 h-3 mr-1" />
                        Stats
                      </button>
                      <button
                        onClick={() => handleManageUsers(company.id)}
                        className="inline-flex items-center px-3 py-1 bg-purple-50 text-purple-700 text-xs font-medium rounded hover:bg-purple-100 transition-colors"
                      >
                        <Users className="w-3 h-3 mr-1" />
                        Users
                      </button>
                      <button
                        onClick={() => handleViewCompany(company.id)}
                        className="inline-flex items-center px-3 py-1 bg-gray-50 text-gray-700 text-xs font-medium rounded hover:bg-gray-100 transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        View
                      </button>
                      {user?.role === 'system_admin' && (
                        <>
                          <button
                            onClick={() => handleDeleteClick(company)}
                            className="inline-flex items-center px-3 py-1 bg-red-50 text-red-700 text-xs font-medium rounded hover:bg-red-100 transition-colors"
                            title="Delete Organization"
                          >
                            <Trash2 className="w-3 h-3 mr-1" />
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredCompanies.length === 0 && (
            <div className="text-center py-12">
              <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg font-medium">No organizations found</p>
              <p className="text-gray-400 text-sm">Create your first organization to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Company Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-lg bg-white">
            <div className="mt-3">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                <Plus className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4 text-center">Create New Organization</h3>
              <form onSubmit={handleCreateCompany} className="mt-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Organization Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newCompany.name}
                    onChange={(e) => setNewCompany({...newCompany, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter organization name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contact Email *
                  </label>
                  <input
                    type="email"
                    required
                    value={newCompany.email}
                    onChange={(e) => setNewCompany({...newCompany, email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="contact@organization.com"
                  />
                </div>
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      setNewCompany({ name: '', email: '', description: '', industry: '', size: '' });
                    }}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Creating...' : 'Create Organization'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mt-4 text-center">Delete Organization</h3>
              <div className="mt-4 px-4">
                <p className="text-sm text-gray-600 mb-4">
                  This action will permanently delete <strong>{selectedCompany?.name}</strong> and all associated data:
                </p>
                <ul className="text-sm text-gray-600 mb-4 list-disc list-inside bg-gray-50 p-3 rounded">
                  <li>All users and their accounts</li>
                  <li>All documents and files</li>
                  <li>All chat history and interactions</li>
                  <li>Complete S3 storage bucket</li>
                </ul>
                <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
                  <p className="text-sm text-red-800 font-medium">
                    ⚠️ This action cannot be undone!
                  </p>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Type "{selectedCompany?.name}" to confirm deletion:
                  </label>
                  <input
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    placeholder={selectedCompany?.name}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 px-4 pb-3">
                <button
                  onClick={() => {
                    setShowDeleteModal(false);
                    setSelectedCompany(null);
                    setDeleteConfirmText('');
                    setError('');
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                  disabled={deleting}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  disabled={deleteConfirmText !== selectedCompany?.name || deleting}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {deleting ? 'Deleting...' : 'Delete Organization'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Management Modal */}
      {showUserManagement && selectedCompanyId && (
        <UserManagement
          companyId={selectedCompanyId}
          onClose={() => {
            setShowUserManagement(false);
            setSelectedCompanyId(null);
          }}
        />
      )}
      </div>
    </div>
  );
}

export default CompanyList;