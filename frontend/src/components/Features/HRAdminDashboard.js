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
  FileSignature,
  User,
  Folder,
  Activity
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

      // Load HR dashboard stats with error handling
      try {
        const statsResponse = await documentsAPI.getHRDashboardStats();
        setStats(statsResponse);
      } catch (err) {
        console.error('Failed to load HR stats:', err);
        // Provide fallback stats
        setStats({
          totalEmployees: 0,
          activeEmployees: 0,
          totalDocuments: 0,
          pendingApprovals: 0,
          complianceScore: 0
        });
      }

      // Load employees list with error handling
      try {
        const employeesResponse = await documentsAPI.getHREmployeesList();
        setEmployees(employeesResponse);
      } catch (err) {
        console.error('Failed to load HR employees:', err);
        setEmployees([]);
      }

      // Load documents list with error handling
      try {
        const documentsResponse = await documentsAPI.list();
        setDocuments(documentsResponse.data || documentsResponse || []);
      } catch (err) {
        console.error('Failed to load documents:', err);
        setDocuments([]);
      }

      // Load workflows with error handling
      try {
        const workflowsResponse = await documentsAPI.getHRWorkflowsList();
        setWorkflows(workflowsResponse);
      } catch (err) {
        console.error('Failed to load HR workflows:', err);
        setWorkflows([]);
      }

      // Load compliance violations with error handling
      try {
        const complianceResponse = await documentsAPI.getHRComplianceViolations();
        setComplianceViolations(complianceResponse);
      } catch (err) {
        console.error('Failed to load HR compliance:', err);
        setComplianceViolations([]);
      }

      // Load analytics summary with error handling
      try {
        const analyticsResponse = await documentsAPI.getDocumentAnalyticsSummary();
        setAnalytics(analyticsResponse);
      } catch (err) {
        console.error('Failed to load analytics:', err);
        setAnalytics({});
      }

    } catch (err) {
      console.error('Failed to load HR dashboard data:', err);
      setError('Some dashboard data failed to load. Please refresh to try again.');
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
            { id: 'analytics', label: 'Analytics', icon: TrendingUp },
            { id: 'health', label: 'Document Health', icon: Activity }
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
        {activeTab === 'overview' && <OverviewTab stats={stats} navigate={navigate} />}
        {activeTab === 'employees' && <EmployeesTab employees={employees} navigate={navigate} />}
        {activeTab === 'documents' && <DocumentsTab documents={documents} navigate={navigate} />}
        {activeTab === 'workflows' && <WorkflowsTab workflows={workflows} navigate={navigate} />}
        {activeTab === 'compliance' && <ComplianceTab violations={complianceViolations} navigate={navigate} />}
        {activeTab === 'analytics' && <AnalyticsTab analytics={analytics} navigate={navigate} />}
        {activeTab === 'health' && <DocumentHealthTab />}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ stats, navigate }) => (
  <div className="p-6 space-y-6">
    <h2 className="text-2xl font-bold text-gray-900">Dashboard Overview</h2>
    
    {/* Stats Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="bg-blue-50 p-6 rounded-xl border border-blue-200">
        <div className="flex items-center space-x-3">
          <Users className="h-8 w-8 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-600">Total Employees</p>
            <p className="text-2xl font-bold text-blue-900">{stats.totalEmployees || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-green-50 p-6 rounded-xl border border-green-200">
        <div className="flex items-center space-x-3">
          <FileText className="h-8 w-8 text-green-600" />
          <div>
            <p className="text-sm font-medium text-green-600">Total Documents</p>
            <p className="text-2xl font-bold text-green-900">{stats.totalDocuments || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-200">
        <div className="flex items-center space-x-3">
          <Clock className="h-8 w-8 text-yellow-600" />
          <div>
            <p className="text-sm font-medium text-yellow-600">Pending Approvals</p>
            <p className="text-2xl font-bold text-yellow-900">{stats.pendingApprovals || 0}</p>
          </div>
        </div>
      </div>
      
      <div className="bg-red-50 p-6 rounded-xl border border-red-200">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-8 w-8 text-red-600" />
          <div>
            <p className="text-sm font-medium text-red-600">Compliance Alerts</p>
            <p className="text-2xl font-bold text-red-900">{stats.complianceScore || 0}%</p>
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

// Document Health Tab Component
const DocumentHealthTab = () => {
  const { user } = useAuth();
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [processingDocs, setProcessingDocs] = useState(false);
  const [processResult, setProcessResult] = useState(null);

  // Check if current user is HR or Manager
  const isHROrManager = user?.role && ['hr_admin', 'hr_manager', 'manager'].includes(user.role);

  const loadEmployees = async () => {
    if (!isHROrManager) return; // Only load employees for HR/Manager

    try {
      setLoadingEmployees(true);
      const employeesList = await documentsAPI.getHREmployeesList();
      setEmployees(employeesList || []);
    } catch (err) {
      console.error('Failed to load employees:', err);
    } finally {
      setLoadingEmployees(false);
    }
  };

  const loadHealthData = async (userId = null) => {
    try {
      setError(null);
      setLoading(true);
      const data = await documentsAPI.getHRHealthSnapshot(userId);
      setHealthData(data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Failed to load health snapshot:', err);
      setError(err.message || 'Failed to load document health data');
      setLoading(false);
    }
  };

  const handleProcessUnanalyzedDocs = async () => {
    if (!isHROrManager) return;

    try {
      setProcessingDocs(true);
      setProcessResult(null);
      const result = await documentsAPI.processUnanalyzedDocuments();
      setProcessResult(result);

      // Reload health data after processing
      if (result.processed > 0) {
        await loadHealthData(selectedUserId);
      }
    } catch (err) {
      console.error('Failed to process documents:', err);
      setProcessResult({
        message: err.message || 'Failed to process documents',
        processed: 0,
        failed: 0,
        total: 0,
        errors: [err.message]
      });
    } finally {
      setProcessingDocs(false);
    }
  };

  useEffect(() => {
    loadEmployees(); // Load employees list for dropdown
    loadHealthData(selectedUserId); // Load initial health data
  }, []);

  useEffect(() => {
    // Reload data when selected user changes
    loadHealthData(selectedUserId);

    // Set up polling only if no specific user is selected (viewing all)
    if (!selectedUserId) {
      const interval = setInterval(() => loadHealthData(selectedUserId), 30000);
      return () => clearInterval(interval);
    }
  }, [selectedUserId]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-gray-500">Loading document health data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-semibold">Error loading data</span>
          </div>
          <p className="text-red-700 mt-2">{error}</p>
          <button
            onClick={loadHealthData}
            className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!healthData) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <div className="text-gray-500">No data available</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with Live Indicator and User Selector */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Document Health Snapshot</h2>
          <p className="text-gray-600 mt-1">
            {selectedUserId
              ? `Viewing compliance status for selected employee`
              : `Compliance posture across all HR evidence documents`}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          {/* User Selector Dropdown - Only for HR/Manager */}
          {isHROrManager && (
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-gray-500" />
              <select
                value={selectedUserId || ''}
                onChange={(e) => setSelectedUserId(e.target.value || null)}
                disabled={loadingEmployees}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm min-w-[200px]"
              >
                <option value="">All Employees</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.full_name || emp.email}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Process Unanalyzed Documents Button - Only for HR/Manager */}
          {isHROrManager && (
            <button
              onClick={handleProcessUnanalyzedDocs}
              disabled={processingDocs}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {processingDocs ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Processing...
                </>
              ) : (
                <>
                  <Activity className="h-4 w-4" />
                  Analyze Documents
                </>
              )}
            </button>
          )}

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Live
            </div>
            {lastUpdated && (
              <div className="text-sm text-gray-600">
                Updated {Math.floor((new Date() - lastUpdated) / 1000 / 60)} min ago
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Processing Result Banner */}
      {processResult && (
        <div className={`rounded-lg p-4 ${processResult.processed > 0 ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className={`font-semibold ${processResult.processed > 0 ? 'text-green-800' : 'text-yellow-800'}`}>
                {processResult.message}
              </p>
              {processResult.total > 0 && (
                <p className={`text-sm mt-1 ${processResult.processed > 0 ? 'text-green-700' : 'text-yellow-700'}`}>
                  Processed: {processResult.processed} / {processResult.total} documents
                  {processResult.failed > 0 && ` (${processResult.failed} failed)`}
                </p>
              )}
              {processResult.errors && processResult.errors.length > 0 && (
                <details className="mt-2">
                  <summary className={`text-sm cursor-pointer ${processResult.processed > 0 ? 'text-green-700' : 'text-yellow-700'}`}>
                    View errors
                  </summary>
                  <ul className={`text-xs mt-1 space-y-1 ${processResult.processed > 0 ? 'text-green-600' : 'text-yellow-600'}`}>
                    {processResult.errors.map((err, idx) => (
                      <li key={idx}>• {err}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
            <button
              onClick={() => setProcessResult(null)}
              className={`ml-4 ${processResult.processed > 0 ? 'text-green-600 hover:text-green-800' : 'text-yellow-600 hover:text-yellow-800'}`}
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-blue-50 p-6 rounded-xl border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <FileText className="h-10 w-10 text-blue-600" />
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-500">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-blue-900 mb-1">{healthData.total_documents.toLocaleString()}</div>
          <div className="text-sm font-semibold text-blue-700">Total Documents</div>
          <div className="text-xs text-blue-600 mt-1">Tracked across employees, contractors, cases</div>
          <div className="flex items-center gap-1 mt-3">
            <TrendingUp className="h-3 w-3 text-green-600" />
            <span className="text-xs font-semibold text-green-600">
              +{healthData.trends?.total_documents_change || 5} ({healthData.trends?.total_documents_percent || 12}%) vs last 30 days
            </span>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-xl border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="h-10 w-10 text-green-600" />
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-500">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-green-900 mb-1">{healthData.compliant_percentage}%</div>
          <div className="text-sm font-semibold text-green-700">Compliant</div>
          <div className="text-xs text-green-600 mt-1">Meets policy + regulatory checks</div>
          <div className="flex items-center gap-1 mt-3">
            <TrendingUp className="h-3 w-3 text-green-600" />
            <span className="text-xs font-semibold text-green-600">
              +{healthData.trends?.compliant_change || 3}% vs last 30 days
            </span>
          </div>
        </div>

        <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-200">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="h-10 w-10 text-yellow-600" />
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500">
              <TrendingDown className="h-5 w-5 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-yellow-900 mb-1">{healthData.at_risk_percentage}%</div>
          <div className="text-sm font-semibold text-yellow-700">At Risk</div>
          <div className="text-xs text-yellow-600 mt-1">Due soon or missing metadata</div>
          <div className="flex items-center gap-1 mt-3">
            <TrendingDown className="h-3 w-3 text-green-600" />
            <span className="text-xs font-semibold text-green-600">
              -{healthData.trends?.at_risk_change || 2}% vs last 30 days
            </span>
          </div>
        </div>

        <div className="bg-red-50 p-6 rounded-xl border border-red-200">
          <div className="flex items-center justify-between mb-2">
            <X className="h-10 w-10 text-red-600" />
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500">
              <TrendingDown className="h-5 w-5 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-red-900 mb-1">{healthData.non_compliant_percentage}%</div>
          <div className="text-sm font-semibold text-red-700">Non-Compliant</div>
          <div className="text-xs text-red-600 mt-1">Action required to reduce exposure</div>
          <div className="flex items-center gap-1 mt-3">
            <TrendingDown className="h-3 w-3 text-green-600" />
            <span className="text-xs font-semibold text-green-600">
              -{healthData.trends?.non_compliant_change || 4}% vs last 30 days
            </span>
          </div>
        </div>
      </div>

      {/* Overall Compliance Progress Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">Overall compliance</h3>
          <span className="text-sm text-gray-600">Target ≥ {healthData.target_threshold}%</span>
        </div>

        <div className="w-full h-8 bg-gray-200 rounded-full overflow-hidden flex">
          {healthData.compliant_percentage > 0 && (
            <div
              className="bg-green-600 flex items-center justify-center text-white text-xs font-semibold"
              style={{ width: `${healthData.compliant_percentage}%` }}
            >
              {healthData.compliant_percentage > 10 && `${healthData.compliant_percentage}%`}
            </div>
          )}
          {healthData.at_risk_percentage > 0 && (
            <div
              className="bg-yellow-500 flex items-center justify-center text-white text-xs font-semibold"
              style={{ width: `${healthData.at_risk_percentage}%` }}
            >
              {healthData.at_risk_percentage > 5 && `${healthData.at_risk_percentage}%`}
            </div>
          )}
          {healthData.non_compliant_percentage > 0 && (
            <div
              className="bg-red-500 flex items-center justify-center text-white text-xs font-semibold"
              style={{ width: `${healthData.non_compliant_percentage}%` }}
            >
              {healthData.non_compliant_percentage > 5 && `${healthData.non_compliant_percentage}%`}
            </div>
          )}
        </div>

        <div className="flex gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-600 rounded"></div>
            <span>{healthData.compliant_percentage}% compliant</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded"></div>
            <span>{healthData.at_risk_percentage}% at risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>{healthData.non_compliant_percentage}% non-compliant</span>
          </div>
        </div>
      </div>

      {/* Category Compliance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {healthData.categories.map(category => (
          <div
            key={category.category_key}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => setSelectedCategory(category)}
          >
            <div className="flex items-center gap-3 mb-4">
              {category.icon === 'briefcase' && <FileSignature className="h-8 w-8 text-blue-600" />}
              {category.icon === 'shield' && <Shield className="h-8 w-8 text-blue-600" />}
              {category.icon === 'dollar-sign' && <Target className="h-8 w-8 text-blue-600" />}
              {category.icon === 'users' && <Users className="h-8 w-8 text-blue-600" />}
              <h3 className="text-lg font-semibold">{category.category_name}</h3>
            </div>

            <div className="text-4xl font-bold mb-2">{category.compliance_percentage}%</div>
            <div className="text-sm text-gray-600 mb-2">{category.compliant_count} compliant</div>

            <div className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold mb-4 ${
              category.status === 'Healthy' ? 'bg-green-100 text-green-800' :
              category.status === 'Watch' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {category.status}
            </div>

            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
              <div
                className={`h-full ${
                  category.status === 'Healthy' ? 'bg-green-600' :
                  category.status === 'Watch' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${category.compliance_percentage}%` }}
              ></div>
            </div>

            <div className="space-y-1 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>At Risk:</span>
                <span className="font-semibold">{category.at_risk_count}</span>
              </div>
              <div className="flex justify-between">
                <span>Non-Compliant:</span>
                <span className="font-semibold">{category.non_compliant_count}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-sm text-gray-600 bg-blue-50 p-4 rounded-lg border border-blue-200">
        <strong>Tip:</strong> Click any category to drill into affected employees/cases, see missing fields, and apply AI auto-classification or remediation workflows.
      </div>

      {/* Drill-down Modal */}
      {selectedCategory && (
        <CategoryDrillDownModal
          category={selectedCategory}
          onClose={() => setSelectedCategory(null)}
        />
      )}
    </div>
  );
};

// Category Drill-Down Modal Component
const CategoryDrillDownModal = ({ category, onClose }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
        <div>
          <h2 className="text-2xl font-bold">{category.category_name}</h2>
          <p className="text-gray-600 mt-1">Affected Employees & Documents</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <X className="h-6 w-6 text-gray-400" />
        </button>
      </div>

      {/* Stats Summary */}
      <div className="p-6 bg-gray-50 border-b border-gray-200 flex-shrink-0">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{category.total_documents}</div>
            <div className="text-sm text-gray-600">Total Documents</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{category.compliant_count}</div>
            <div className="text-sm text-gray-600">Compliant</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{category.at_risk_count}</div>
            <div className="text-sm text-gray-600">At Risk</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{category.non_compliant_count}</div>
            <div className="text-sm text-gray-600">Non-Compliant</div>
          </div>
        </div>
      </div>

      {/* Scrollable Employee List */}
      <div className="flex-1 overflow-y-auto p-6">
        {category.affected_employees.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
            <p>All documents in this category are compliant!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {category.affected_employees.map(employee => (
              <div key={employee.user_id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                {/* Employee Header */}
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-lg truncate">{employee.full_name}</div>
                    <div className="text-sm text-gray-600 truncate">{employee.email}</div>
                    {employee.department && (
                      <div className="text-sm text-gray-600">{employee.department}</div>
                    )}
                  </div>
                  <div className="flex-shrink-0">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">
                      {employee.documents.length} {employee.documents.length === 1 ? 'doc' : 'docs'}
                    </span>
                  </div>
                </div>

                {/* Document List */}
                <div className="space-y-2">
                  {employee.documents.map(doc => (
                    <div key={doc.document_id} className="bg-white rounded border border-gray-200 overflow-hidden">
                      <div className="flex items-center justify-between p-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <FileText className="h-5 w-5 text-gray-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{doc.filename}</div>
                            <div className="text-sm text-gray-600">
                              {doc.document_type || 'Unknown type'}
                              {doc.expiry_date && ` • Expires: ${new Date(doc.expiry_date).toLocaleDateString()}`}
                              {doc.days_until_expiry !== null && doc.days_until_expiry >= 0 && ` (${doc.days_until_expiry} days)`}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                            doc.status === 'compliant' ? 'bg-green-100 text-green-800' :
                            doc.status === 'at_risk' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {doc.status === 'compliant' ? 'COMPLIANT' :
                             doc.status === 'at_risk' ? 'AT RISK' :
                             'NON-COMPLIANT'}
                          </span>
                          <button className="p-2 hover:bg-gray-100 rounded transition-colors">
                            <Download className="h-4 w-4 text-gray-600" />
                          </button>
                        </div>
                      </div>

                      {/* Detailed Reasons Section */}
                      {doc.reasons && doc.reasons.length > 0 && (
                        <div className="px-3 pb-3 border-t border-gray-100 pt-2 space-y-2">
                          {doc.reasons.map((reason, idx) => (
                            <div key={idx} className={`flex items-start gap-2 p-2 rounded text-xs ${
                              reason.severity === 'high' ? 'bg-red-50 border-l-2 border-red-500' :
                              reason.severity === 'medium' ? 'bg-yellow-50 border-l-2 border-yellow-500' :
                              'bg-blue-50 border-l-2 border-blue-500'
                            }`}>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  {reason.severity === 'high' && <AlertTriangle className="h-3 w-3 text-red-600" />}
                                  {reason.severity === 'medium' && <Clock className="h-3 w-3 text-yellow-600" />}
                                  {reason.severity === 'low' && <CheckCircle className="h-3 w-3 text-blue-600" />}
                                  <span className={`font-semibold ${
                                    reason.severity === 'high' ? 'text-red-800' :
                                    reason.severity === 'medium' ? 'text-yellow-800' :
                                    'text-blue-800'
                                  }`}>
                                    {reason.reason_message}
                                  </span>
                                </div>
                                {reason.details && reason.details.action_required && (
                                  <div className={`text-xs mt-1 ${
                                    reason.severity === 'high' ? 'text-red-700' :
                                    reason.severity === 'medium' ? 'text-yellow-700' :
                                    'text-blue-700'
                                  }`}>
                                    Action: {reason.details.action_required}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t border-gray-200 flex gap-4 flex-shrink-0">
        <button className="flex-1 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold">
          Export Report
        </button>
        <button className="flex-1 bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition-colors font-semibold">
          Send Reminders
        </button>
        <button
          onClick={onClose}
          className="flex-1 bg-gray-200 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
        >
          Close
        </button>
      </div>
    </div>
  </div>
);

export default HRAdminDashboard;
export { DocumentHealthTab, CategoryDrillDownModal };
