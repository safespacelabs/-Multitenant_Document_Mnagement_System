import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { documentsAPI, usersAPI } from '../../services/api';
import {
  Search,
  Upload,
  Download,
  Trash2,
  Eye,
  FileText,
  ChevronDown,
  X
} from 'lucide-react';

const DocumentsTable = () => {
  const { user, company } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('All Departments');
  const [selectedType, setSelectedType] = useState('All Types');
  const [selectedStatus, setSelectedStatus] = useState('All Status');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Filter dropdowns state
  const [showDeptDropdown, setShowDeptDropdown] = useState(false);
  const [showTypeDropdown, setShowTypeDropdown] = useState(false);
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);

  const departments = ['All Departments', 'Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Legal'];
  const types = ['All Types', 'Contract', 'Review', 'Certification', 'Agreement', 'Certificate'];
  const statuses = ['All Status', 'approved', 'pending', 'expired'];

  useEffect(() => {
    loadData();
  }, [company]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Load documents
      const docsResponse = await documentsAPI.list(null);
      const docsData = docsResponse.data || docsResponse || [];
      setDocuments(Array.isArray(docsData) ? docsData : []);

      // Load employees
      const usersResponse = await usersAPI.list(company.id);
      const usersData = usersResponse.data || usersResponse || [];
      setEmployees(Array.isArray(usersData) ? usersData : []);

    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    try {
      setUploadProgress(0);
      await documentsAPI.upload(uploadFile);
      setShowUploadModal(false);
      setUploadFile(null);
      loadData();
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload document');
    }
  };

  const handleDownload = async (doc) => {
    try {
      // Implement download logic
      console.log('Downloading:', doc);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await documentsAPI.delete(docId);
      loadData();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const getEmployeeName = (doc) => {
    // Try to find employee name from the document or employees list
    if (doc.user_id) {
      const emp = employees.find(e => e.id === doc.user_id);
      if (emp) return emp.full_name || emp.username;
    }
    return doc.uploaded_by || 'Unknown';
  };

  const getDocumentType = (doc) => {
    // Extract type from filename or category
    if (doc.category) return doc.category;
    const filename = doc.original_filename || doc.name || '';
    if (filename.includes('contract')) return 'Contract';
    if (filename.includes('review')) return 'Review';
    if (filename.includes('cert')) return 'Certification';
    return 'Document';
  };

  const getDepartment = (doc) => {
    // Mock department based on user or document properties
    const depts = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations'];
    return depts[Math.floor(Math.random() * depts.length)];
  };

  const getStatus = (doc) => {
    // Mock status - you can implement real status logic
    const statuses = ['approved', 'pending', 'expired'];
    return doc.status || statuses[Math.floor(Math.random() * statuses.length)];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const clearFilters = () => {
    setSelectedDepartment('All Departments');
    setSelectedType('All Types');
    setSelectedStatus('All Status');
    setSearchTerm('');
  };

  // Filter documents
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = (doc.original_filename || doc.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                          getEmployeeName(doc).toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDept = selectedDepartment === 'All Departments' || getDepartment(doc) === selectedDepartment;
    const matchesType = selectedType === 'All Types' || getDocumentType(doc) === selectedType;
    const matchesStatus = selectedStatus === 'All Status' || getStatus(doc) === selectedStatus;

    return matchesSearch && matchesDept && matchesType && matchesStatus;
  });

  const getStatusColor = (status) => {
    const colors = {
      'approved': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'expired': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const FilterDropdown = ({ label, options, selected, onSelect, show, setShow }) => (
    <div className="relative">
      <button
        onClick={() => setShow(!show)}
        className="flex items-center justify-between px-4 py-2 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 min-w-[180px]"
      >
        <span className="text-sm text-gray-700">{selected}</span>
        <ChevronDown className="h-4 w-4 text-gray-400 ml-2" />
      </button>
      {show && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {options.map((option) => (
            <button
              key={option}
              onClick={() => {
                onSelect(option);
                setShow(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 ${
                selected === option ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-sm text-gray-600 mt-1">Manage and organize all documents</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Upload className="h-4 w-4 mr-2" />
          Upload Document
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="relative flex-1 min-w-[300px]">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search documents, employees..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <FilterDropdown
          label="Department"
          options={departments}
          selected={selectedDepartment}
          onSelect={setSelectedDepartment}
          show={showDeptDropdown}
          setShow={setShowDeptDropdown}
        />

        <FilterDropdown
          label="Type"
          options={types}
          selected={selectedType}
          onSelect={setSelectedType}
          show={showTypeDropdown}
          setShow={setShowTypeDropdown}
        />

        <FilterDropdown
          label="Status"
          options={statuses}
          selected={selectedStatus}
          onSelect={setSelectedStatus}
          show={showStatusDropdown}
          setShow={setShowStatusDropdown}
        />

        <button
          onClick={clearFilters}
          className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Clear
        </button>
      </div>

      {/* Documents Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Document Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Upload Date
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
              {filteredDocuments.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                    No documents found
                  </td>
                </tr>
              ) : (
                filteredDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">
                          {doc.original_filename || doc.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {getEmployeeName(doc)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {getDocumentType(doc)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {getDepartment(doc)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {formatDate(doc.created_at || doc.upload_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(getStatus(doc))}`}>
                        {getStatus(doc)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleDownload(doc)}
                          className="p-1 text-gray-400 hover:text-blue-600"
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDownload(doc)}
                          className="p-1 text-gray-400 hover:text-green-600"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Upload Document</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select File
                </label>
                <input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  required
                />
              </div>

              {uploadFile && (
                <div className="text-sm text-gray-600">
                  Selected: {uploadFile.name}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                >
                  Upload
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsTable;
