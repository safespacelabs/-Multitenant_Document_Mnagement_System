import React, { useState, useEffect } from 'react';
import { 
  TrendingUp,
  TrendingDown,
  Users,
  FileText,
  Download,
  Upload,
  Eye,
  Clock,
  Calendar,
  BarChart3,
  PieChart,
  Activity,
  Target,
  CheckCircle,
  AlertCircle,
  X,
  ChevronDown,
  Filter,
  RefreshCw,
  Download as DownloadIcon,
  Share2,
  MoreVertical
} from 'lucide-react';

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('month');
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({
    totalDocuments: 1247,
    totalUsers: 89,
    storageUsed: '2.4 GB',
    activeUsers: 67,
    documentsUploaded: 156,
    documentsDownloaded: 89,
    averageResponseTime: '2.3s',
    completionRate: 94.2
  });

  const [chartData, setChartData] = useState({
    uploadsByMonth: [45, 52, 38, 67, 89, 76, 54, 78, 91, 83, 67, 89],
    downloadsByMonth: [32, 45, 28, 56, 78, 65, 43, 67, 82, 74, 58, 71],
    userActivity: [67, 72, 68, 75, 82, 79, 73, 81, 88, 85, 78, 83],
    categoryDistribution: [
      { name: 'HR Documents', value: 35, color: 'bg-blue-500' },
      { name: 'Legal Files', value: 25, color: 'bg-green-500' },
      { name: 'Financial Reports', value: 20, color: 'bg-purple-500' },
      { name: 'Marketing Materials', value: 15, color: 'bg-orange-500' },
      { name: 'Other', value: 5, color: 'bg-gray-500' }
    ]
  });

  const [recentActivity, setRecentActivity] = useState([
    { id: 1, type: 'upload', user: 'John Doe', document: 'Q4 Report.pdf', time: '2 min ago', status: 'completed' },
    { id: 2, type: 'download', user: 'Jane Smith', document: 'Employee Handbook.docx', time: '5 min ago', status: 'completed' },
    { id: 3, type: 'share', user: 'HR Admin', document: 'Company Policy.pdf', time: '12 min ago', status: 'pending' },
    { id: 4, type: 'sign', user: 'Manager', document: 'Contract Agreement.pdf', time: '1 hour ago', status: 'completed' },
    { id: 5, type: 'upload', user: 'Marketing Team', document: 'Brand Guidelines.pdf', time: '2 hours ago', status: 'completed' }
  ]);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update metrics based on time range
      const timeMultiplier = timeRange === 'week' ? 0.25 : timeRange === 'month' ? 1 : timeRange === 'quarter' ? 3 : 12;
      
      setMetrics(prev => ({
        ...prev,
        totalDocuments: Math.floor(1247 * timeMultiplier),
        documentsUploaded: Math.floor(156 * timeMultiplier),
        documentsDownloaded: Math.floor(89 * timeMultiplier)
      }));
      
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'upload':
        return <Upload className="h-4 w-4 text-blue-600" />;
      case 'download':
        return <Download className="h-4 w-4 text-green-600" />;
      case 'share':
        return <Share2 className="h-4 w-4 text-purple-600" />;
      case 'sign':
        return <CheckCircle className="h-4 w-4 text-orange-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
          <p className="text-gray-600">Monitor your document management system performance</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="quarter">Last Quarter</option>
            <option value="year">Last Year</option>
          </select>
          
          <button
            onClick={loadAnalytics}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.totalDocuments)}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-xl">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            <span className="text-green-600">+12.5%</span>
            <span className="text-gray-500 ml-1">from last period</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Users</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.activeUsers}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-xl">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            <span className="text-green-600">+8.2%</span>
            <span className="text-gray-500 ml-1">from last period</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Storage Used</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.storageUsed}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-xl">
              <Download className="h-6 w-6 text-purple-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            <span className="text-red-600">-2.1%</span>
            <span className="text-gray-500 ml-1">from last period</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.completionRate}%</p>
            </div>
            <div className="p-3 bg-orange-100 rounded-xl">
              <Target className="h-6 w-6 text-orange-600" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            <span className="text-green-600">+3.2%</span>
            <span className="text-gray-500 ml-1">from last period</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uploads vs Downloads Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Document Activity</h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Uploads</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-sm text-gray-600">Downloads</span>
              </div>
            </div>
          </div>
          
          <div className="h-64 flex items-end justify-between space-x-2">
            {chartData.uploadsByMonth.map((value, index) => (
              <div key={index} className="flex-1 flex flex-col items-center space-y-2">
                <div className="w-full bg-gray-200 rounded-t">
                  <div 
                    className="bg-blue-500 rounded-t transition-all duration-500"
                    style={{ height: `${(value / 100) * 200}px` }}
                  ></div>
                </div>
                <div className="w-full bg-gray-200 rounded-t">
                  <div 
                    className="bg-green-500 rounded-t transition-all duration-500"
                    style={{ height: `${(chartData.downloadsByMonth[index] / 100) * 200}px` }}
                  ></div>
                </div>
                <span className="text-xs text-gray-500">{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][index]}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Category Distribution */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Document Categories</h3>
          
          <div className="space-y-4">
            {chartData.categoryDistribution.map((category, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded-full ${category.color}`}></div>
                  <span className="text-sm text-gray-700">{category.name}</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${category.color.replace('bg-', 'bg-')}`}
                      style={{ width: `${category.value}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900 w-8 text-right">{category.value}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Upload Performance</h3>
            <Upload className="h-6 w-6 text-blue-600" />
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Documents Uploaded</span>
              <span className="text-lg font-semibold text-gray-900">{metrics.documentsUploaded}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Success Rate</span>
              <span className="text-lg font-semibold text-green-600">98.5%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Average Size</span>
              <span className="text-lg font-semibold text-gray-900">2.3 MB</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">User Engagement</h3>
            <Users className="h-6 w-6 text-green-600" />
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Active Users</span>
              <span className="text-lg font-semibold text-gray-900">{metrics.activeUsers}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Session Duration</span>
              <span className="text-lg font-semibold text-gray-900">24 min</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Return Rate</span>
              <span className="text-lg font-semibold text-green-600">87.3%</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">System Performance</h3>
            <Activity className="h-6 w-6 text-purple-600" />
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Response Time</span>
              <span className="text-lg font-semibold text-gray-900">{metrics.averageResponseTime}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Uptime</span>
              <span className="text-lg font-semibold text-green-600">99.9%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Error Rate</span>
              <span className="text-lg font-semibold text-red-600">0.1%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          <button className="text-sm text-blue-600 hover:text-blue-700">View All</button>
        </div>
        
        <div className="space-y-4">
          {recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50">
              <div className="flex-shrink-0">
                {getActivityIcon(activity.type)}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {activity.user} {activity.type === 'upload' ? 'uploaded' : 
                                  activity.type === 'download' ? 'downloaded' : 
                                  activity.type === 'share' ? 'shared' : 'signed'} {activity.document}
                </p>
                <p className="text-sm text-gray-500">{activity.time}</p>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(activity.status)}`}>
                  {activity.status}
                </span>
                <button className="p-1 text-gray-400 hover:text-gray-600">
                  <MoreVertical className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <DownloadIcon className="h-6 w-6 text-blue-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Export Report</p>
              <p className="text-sm text-gray-500">Download analytics data</p>
            </div>
          </button>
          
          <button className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Share2 className="h-6 w-6 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Share Dashboard</p>
              <p className="text-sm text-gray-500">Send to team members</p>
            </div>
          </button>
          
          <button className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <Calendar className="h-6 w-6 text-purple-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">Schedule Report</p>
              <p className="text-sm text-gray-500">Set up recurring reports</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 