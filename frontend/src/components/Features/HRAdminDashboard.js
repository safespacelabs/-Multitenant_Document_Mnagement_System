import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../utils/auth';
import { documentsAPI } from '../../services/api';
import { 
  Users,
  FileText,
  BarChart3,
  Upload,
  Search,
  Filter,
  Download,
  Share,
  Edit,
  Trash2,
  Eye,
  CheckCircle,
  X,
  Clock,
  Calendar,
  UserPlus,
  Shield,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  FolderOpen,
  Archive,
  Lock,
  Unlock,
  Bell,
  Settings,
  Plus,
  Grid,
  List,
  ChevronDown,
  MoreVertical,
  Star,
  BookOpen,
  Clipboard,
  Target,
  Award,
  Clock1,
  UserCheck,
  FileSignature
} from 'lucide-react';

const HRAdminDashboard = () => {
  const { user, company } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Dashboard data
  const [stats, setStats] = useState({});
  const [employees, setEmployees] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [complianceViolations, setComplianceViolations] = useState([]);
  const [analytics, setAnalytics] = useState({});

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load HR dashboard stats
      const statsResponse = await documentsAPI.getHRDashboardStats();
      setStats(statsResponse);

      // Load employees list
      const employeesResponse = await documentsAPI.getHREmployeesList();
      setEmployees(employeesResponse);

      // Load documents list
      const documentsResponse = await documentsAPI.list();
      setDocuments(documentsResponse.data || documentsResponse || []);

      // Load workflows (placeholder for now)
      const workflowsResponse = await documentsAPI.getHRWorkflowsList();
      setWorkflows(workflowsResponse);

      // Load compliance violations (placeholder for now)
      const complianceResponse = await documentsAPI.getHRComplianceViolations();
      setComplianceViolations(complianceResponse);

      // Load analytics summary
      const analyticsResponse = await documentsAPI.getDocumentAnalyticsSummary();
      setAnalytics(analyticsResponse);

    } catch (err) {
      console.error('Failed to load HR dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadDashboardData}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">HR Admin Dashboard</h1>
        <p className="text-gray-600">Manage employees, documents, and compliance for {company?.name}</p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-1 bg-white p-1 rounded-xl shadow-sm">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'employees', label: 'Employees', icon: Users },
            { id: 'documents', label: 'Documents', icon: FileText },
            { id: 'workflows', label: 'Workflows', icon: Clipboard },
            { id: 'compliance', label: 'Compliance', icon: Shield },
            { id: 'analytics', label: 'Analytics', icon: TrendingUp }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {activeTab === 'overview' && <OverviewTab stats={stats} />}
        {activeTab === 'employees' && <EmployeesTab employees={employees} navigate={navigate} />}
        {activeTab === 'documents' && <DocumentsTab documents={documents} navigate={navigate} />}
        {activeTab === 'workflows' && <WorkflowsTab workflows={workflows} navigate={navigate} />}
        {activeTab === 'compliance' && <ComplianceTab violations={complianceViolations} navigate={navigate} />}
        {activeTab === 'analytics' && <AnalyticsTab analytics={analytics} navigate={navigate} />}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ stats }) => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
    
    {/* Stats Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="bg-blue-50 p-6 rounded-xl border border-blue-200">
        <div className="flex items-center space-x-3">
          <Users className="h-8 w-8 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-600">Total Employees</p>
            <p className="text-2xl font-bold text-blue-900">{stats.total_employees || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-green-50 p-6 rounded-xl border border-green-200">
        <div className="flex items-center space-x-3">
          <FileText className="h-8 w-8 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-600">Total Documents</p>
            <p className="text-2xl font-bold text-green-900">{stats.total_documents || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-200">
        <div className="flex items-center space-x-3">
          <Clock className="h-8 w-8 text-yellow-600" />
          <div>
            <p className="text-sm font-medium text-yellow-600">Pending Approvals</p>
            <p className="text-2xl font-bold text-yellow-900">{stats.pending_approvals || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-red-50 p-6 rounded-xl border border-red-200">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-8 w-8 text-red-600" />
          <div>
            <p className="text-sm font-medium text-red-600">Compliance Alerts</p>
            <p className="text-2xl font-bold text-red-900">{stats.compliance_alerts || 0}</p>
          </div>
        </div>
      </div>
    </div>

    {/* Quick Actions */}
    <div className="bg-gray-50 p-6 rounded-xl">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => navigate('/dashboard/users')}
          className="bg-blue-600 text-white p-4 rounded-xl hover:bg-blue-700 transition-colors text-left"
        >
          <div className="flex items-center space-x-3">
            <UserPlus className="h-6 w-6" />
            <div>
              <div className="font-medium">Add New Employee</div>
              <div className="text-sm opacity-90">Register new team member</div>
            </div>
          </div>
        </button>
        
        <button
          onClick={() => navigate('/dashboard/documents')}
          className="bg-green-600 text-white p-4 rounded-xl hover:bg-green-700 transition-colors text-left"
        >
          <div className="flex items-center space-x-3">
            <Upload className="h-6 w-6" />
            <div>
              <div className="font-medium">Upload Document</div>
              <div className="text-sm opacity-90">Add new file to system</div>
            </div>
          </div>
        </button>
        
        <button
          onClick={() => navigate('/dashboard/analytics')}
          className="bg-purple-600 text-white p-4 rounded-xl hover:bg-purple-700 transition-colors text-left"
        >
          <div className="flex items-center space-x-3">
            <BarChart3 className="h-6 w-6" />
            <div>
              <div className="font-medium">View Reports</div>
              <div className="text-sm opacity-90">Generate HR reports</div>
            </div>
          </div>
        </button>
      </div>
    </div>

    {/* Storage Info */}
    <div className="bg-gray-50 p-6 rounded-xl">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Usage</h3>
      <div className="flex items-center space-x-4">
        <div className="flex-1">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Used: {stats.storage_used_gb || 0} GB</span>
            <span>Limit: {stats.storage_limit_gb || 100} GB</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(((stats.storage_used_gb || 0) / (stats.storage_limit_gb || 100)) * 100, 100)}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Employees Tab Component
const EmployeesTab = ({ employees, navigate }) => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <h2 className="text-2xl font-bold text-gray-900">Employee Management</h2>
      <button
        onClick={() => navigate('/dashboard/users')}
        className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors flex items-center space-x-2"
      >
        <UserPlus className="h-4 w-4" />
        <span>Add New Employee</span>
      </button>
    </div>

    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Employee
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Department
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Documents
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {employees.map((employee) => (
              <tr key={employee.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-700">
                          {(employee.full_name || employee.username || 'U').charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{employee.full_name || employee.username}</div>
                      <div className="text-sm text-gray-500">{employee.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                    {employee.role?.replace('_', ' ').toUpperCase() || 'EMPLOYEE'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {employee.department || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    Active
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {employee.documents_count || 0}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <button className="text-blue-600 hover:text-blue-900">View</button>
                    <button className="text-green-600 hover:text-green-900">Edit</button>
                    <button className="text-purple-600 hover:text-purple-900">Documents</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </div>
);

// Documents Tab Component
const DocumentsTab = ({ documents, navigate }) => (
  <div className="space-y-6">
    <div className="flex items-center justify-between">
      <h2 className="text-2xl font-bold text-gray-900">Document Management</h2>
      <button
        onClick={() => navigate('/dashboard/documents')}
        className="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors flex items-center space-x-2"
      >
        <FileText className="h-4 w-4" />
        <span>View All Documents</span>
      </button>
    </div>

    {/* Search and Filters */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center space-x-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search documents..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-xl leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <select
          className="px-4 py-2 border border-gray-300 rounded-xl focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Categories</option>
          <option value="HR">HR</option>
          <option value="Legal">Legal</option>
          <option value="Finance">Finance</option>
          <option value="Marketing">Marketing</option>
        </select>
        <select
          className="px-4 py-2 border border-gray-300 rounded-xl focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="pending_approval">Pending Approval</option>
          <option value="archived">Archived</option>
        </select>
      </div>
    </div>

    {/* Documents Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {documents.slice(0, 8).map((doc) => (
        <div key={doc.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between mb-3">
            <FileText className="h-8 w-8 text-blue-500" />
            <input
              type="checkbox"
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
          </div>
          
          <div className="space-y-2">
            <h3 className="font-medium text-gray-900 truncate" title={doc.original_filename || doc.name}>
              {doc.original_filename || doc.name}
            </h3>
            
            <div className="text-sm text-gray-500 space-y-1">
              <div className="flex items-center space-x-2">
                <span>{doc.file_type || 'Unknown'}</span>
                <span>•</span>
                <span>{doc.file_size || '0 B'}</span>
              </div>
              
              <div className="flex items-center space-x-2">
                <User className="h-3 w-3" />
                <span>{doc.user?.full_name || 'Unknown'}</span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Folder className="h-3 w-3" />
                <span>{doc.category || 'General'}</span>
              </div>
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <button className="p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors" title="Download">
                <Download className="h-4 w-4" />
              </button>
              <button className="p-2 rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-colors" title="Share">
                <Share className="h-4 w-4" />
              </button>
              <button className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors" title="Delete">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// Workflows Tab Component
const WorkflowsTab = ({ workflows, navigate }) => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Workflow Management</h2>

    {/* Pending Workflows */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Pending Workflows</h3>
      <div className="space-y-4">
        {workflows.map((workflow) => (
          <div key={workflow.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800`}>
                  {workflow.priority}
                </span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800`}>
                  {workflow.status}
                </span>
              </div>
              <span className="text-sm text-gray-500">{workflow.created}</span>
            </div>
            
            <div className="mb-3">
              <h4 className="font-medium text-gray-900">{workflow.employee}</h4>
              <p className="text-sm text-gray-600 capitalize">{workflow.type.replace('_', ' ')}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Required Documents:</p>
              <div className="flex flex-wrap gap-2">
                {workflow.documents.map((doc, index) => (
                  <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                    {doc}
                  </span>
                ))}
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button
                onClick={() => console.log(`Approve workflow ${workflow.id}`)}
                className="flex-1 bg-green-500 text-white p-2 rounded-lg hover:bg-green-600 flex items-center justify-center space-x-2"
              >
                <CheckCircle className="h-4 w-4" />
                <span>Approve</span>
              </button>
              <button
                onClick={() => console.log(`Reject workflow ${workflow.id}`)}
                className="flex-1 bg-red-500 text-white p-2 rounded-lg hover:bg-red-600 flex items-center justify-center space-x-2"
              >
                <X className="h-4 w-4" />
                <span>Reject</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Completed Workflows */}
    {/* This section would typically fetch completed workflows from the backend */}
    {/* For now, it's a placeholder */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Completed Workflows</h3>
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">Workflow Type</p>
            <p className="text-sm text-gray-600">Employee Name</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
              Completed
            </span>
            <span className="text-sm text-gray-500">Date</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// Compliance Tab Component
const ComplianceTab = ({ violations, navigate }) => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Compliance & Security</h2>

    {/* Compliance Overview */}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-green-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Documents Compliant</p>
            <p className="text-2xl font-bold text-gray-900">98%</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-8 w-8 text-yellow-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Pending Reviews</p>
            <p className="text-2xl font-bold text-gray-900">3</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <Clock className="h-8 w-8 text-red-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Expiring Soon</p>
            <p className="text-2xl font-bold text-gray-900">5</p>
          </div>
        </div>
      </div>
    </div>

    {/* Compliance Alerts */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Compliance Alerts</h3>
      <div className="space-y-3">
        {violations.map((violation, index) => (
          <div key={index} className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            <div>
              <p className="font-medium text-gray-900">{violation.description}</p>
              <p className="text-sm text-gray-600">{violation.details}</p>
            </div>
          </div>
        ))}
      </div>
    </div>

    {/* Audit Trail */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Audit Activity</h3>
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <User className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-900">User accessed employee records</span>
          </div>
          <span className="text-sm text-gray-500">2 hours ago</span>
        </div>
        
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <FileText className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-900">Document updated</span>
          </div>
          <span className="text-sm text-gray-500">4 hours ago</span>
        </div>
      </div>
    </div>
  </div>
);

// Analytics Tab Component
const AnalyticsTab = ({ analytics, navigate }) => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">HR Analytics & Reports</h2>

    {/* Key Metrics */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <Users className="h-8 w-8 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Total Employees</p>
            <p className="text-2xl font-bold text-gray-900">{analytics.total_employees || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <FileText className="h-8 w-8 text-green-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Total Documents</p>
            <p className="text-2xl font-bold text-gray-900">{analytics.total_documents || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <Clock className="h-8 w-8 text-yellow-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
            <p className="text-2xl font-bold text-gray-900">{analytics.pending_approvals || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <Shield className="h-8 w-8 text-red-600" />
          <div>
            <p className="text-sm font-medium text-gray-600">Compliance Alerts</p>
            <p className="text-2xl font-bold text-gray-900">{analytics.compliance_alerts || 0}</p>
          </div>
        </div>
      </div>
    </div>

    {/* Charts Placeholder */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Employee Growth</h3>
        <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500">Chart visualization would go here</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Categories</h3>
        <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-500">Chart visualization would go here</p>
          </div>
        </div>
      </div>
    </div>

    {/* Quick Reports */}
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Reports</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => navigate('/dashboard/users')}
          className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
        >
          <div className="flex items-center space-x-3">
            <Users className="h-6 w-6 text-blue-600" />
            <div>
              <div className="font-medium">Employee Roster</div>
              <div className="text-sm text-gray-500">Export employee list</div>
            </div>
          </div>
        </button>
        
        <button
          onClick={() => navigate('/dashboard/documents')}
          className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
        >
          <div className="flex items-center space-x-3">
            <FileText className="h-6 w-6 text-green-600" />
            <div>
              <div className="font-medium">Document Inventory</div>
              <div className="text-sm text-gray-500">Export document list</div>
            </div>
          </div>
        </button>
        
        <button
          onClick={() => navigate('/dashboard/analytics')}
          className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
        >
          <div className="flex items-center space-x-3">
            <BarChart3 className="h-6 w-6 text-purple-600" />
            <div>
              <div className="font-medium">HR Metrics</div>
              <div className="text-sm text-gray-500">Export analytics data</div>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
);

export default HRAdminDashboard;
