import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { documentsAPI, usersAPI } from '../../services/api';
import {
  Users,
  FileText,
  Award,
  AlertCircle,
  FileWarning,
  Clock,
  CheckCircle
} from 'lucide-react';

const ComplianceDashboard = () => {
  const { user, company } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalEmployees: 0,
    requiredDocuments: 0,
    certifications: 0,
    compliantPercentage: 99,
    requiredPercentage: 92,
    certificationsPercentage: 93
  });
  const [expiringDocuments, setExpiringDocuments] = useState([]);
  const [missingDocuments, setMissingDocuments] = useState([]);
  const [complianceTimeline, setComplianceTimeline] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, [company]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load users count
      const usersResponse = await usersAPI.list(company.id);
      const users = usersResponse.data || usersResponse || [];
      const totalEmployees = users.length;

      // Load documents
      const docsResponse = await documentsAPI.list(null);
      const documents = docsResponse.data || docsResponse || [];

      // Calculate stats
      const requiredDocs = Math.floor(documents.length * 0.6);
      const certifications = Math.floor(documents.length * 0.4);

      setStats({
        totalEmployees,
        requiredDocuments: requiredDocs,
        certifications,
        compliantPercentage: Math.floor((users.length / (users.length + 3)) * 100),
        requiredPercentage: Math.floor((requiredDocs / (requiredDocs + 1)) * 100),
        certificationsPercentage: Math.floor((certifications / (certifications + 3)) * 100)
      });

      // Mock expiring documents
      setExpiringDocuments([
        { id: 1, name: 'ISO 27001 Certificate', type: 'Engineering Team', daysLeft: 15 },
        { id: 2, name: 'Work Permit - Alex Turner', type: 'Alex Turner', daysLeft: 7 },
        { id: 3, name: 'Background Check - Maria Garcia', type: 'Maria Garcia', daysLeft: 22 },
        { id: 4, name: 'Safety Certification - Operations', type: 'Operations Department', daysLeft: 28 }
      ]);

      // Mock missing documents
      setMissingDocuments([
        { id: 1, name: 'Employment Contract', department: 'Sales', status: 'Request' },
        { id: 2, name: 'I-9 Form', department: 'Marketing', status: 'Request' }
      ]);

      // Mock compliance timeline
      setComplianceTimeline([
        { id: 1, date: 'Jan 15, 2024', event: 'Annual compliance audit completed', status: 'success' },
        { id: 2, date: 'Jan 10, 2024', event: '5 new employee contracts uploaded', status: 'info' },
        { id: 3, date: 'Jan 5, 2024', event: 'ISO certification renewed', status: 'success' },
        { id: 4, date: 'Dec 28, 2023', event: 'Compliance review scheduled', status: 'warning' }
      ]);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const MetricCard = ({ title, value, total, percentage, icon: Icon, actionText }) => (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {actionText && <span className="text-xs text-orange-600">{actionText}</span>}
      </div>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-3xl font-bold text-gray-900">
            {value}/{total}
          </div>
          <div className="flex items-center mt-2">
            {percentage >= 95 ? (
              <CheckCircle className="h-4 w-4 text-green-600 mr-1" />
            ) : (
              <AlertCircle className="h-4 w-4 text-orange-600 mr-1" />
            )}
            <span className={`text-sm ${percentage >= 95 ? 'text-green-600' : 'text-orange-600'}`}>
              {percentage}% {percentage >= 95 ? 'Compliant' : 'Action Needed'}
            </span>
          </div>
        </div>
        <div className="text-green-600 text-xl font-bold">
          {percentage}%
        </div>
      </div>
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
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>
        <p className="text-sm text-gray-600 mt-1">Monitor compliance status and track critical documents</p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <MetricCard
          title="Total Employees"
          value={stats.totalEmployees}
          total={stats.totalEmployees + 3}
          percentage={stats.compliantPercentage}
          icon={Users}
        />
        <MetricCard
          title="Required Documents"
          value={stats.requiredDocuments}
          total={stats.requiredDocuments + 1}
          percentage={stats.requiredPercentage}
          icon={FileText}
          actionText="Action Needed"
        />
        <MetricCard
          title="Certifications"
          value={stats.certifications}
          total={stats.certifications + 3}
          percentage={stats.certificationsPercentage}
          icon={Award}
          actionText="Action Needed"
        />
      </div>

      {/* Expiring & Missing Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Expiring Documents */}
        <div className="bg-white rounded-lg border-2 border-red-200 p-6">
          <div className="flex items-center mb-4">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Expiring Documents</h2>
          </div>
          <div className="space-y-3">
            {expiringDocuments.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{doc.name}</p>
                  <p className="text-sm text-gray-600">{doc.type}</p>
                </div>
                <div className="flex items-center">
                  <Clock className="h-4 w-4 text-red-600 mr-1" />
                  <span className="text-sm font-medium text-red-600">{doc.daysLeft}d</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Missing Documents */}
        <div className="bg-white rounded-lg border-2 border-yellow-200 p-6">
          <div className="flex items-center mb-4">
            <FileWarning className="h-5 w-5 text-yellow-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Missing Documents</h2>
          </div>
          <div className="space-y-3">
            {missingDocuments.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{doc.name}</p>
                  <p className="text-sm text-gray-600">{doc.department}</p>
                </div>
                <button className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 rounded-md">
                  {doc.status}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compliance Timeline */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Timeline</h2>
        <div className="space-y-3">
          {complianceTimeline.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors">
              <div className="flex items-center flex-1">
                <span className="text-sm text-gray-600 w-32">{item.date}</span>
                <span className="text-sm text-gray-900 flex-1">{item.event}</span>
              </div>
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                item.status === 'success' ? 'bg-green-100 text-green-800' :
                item.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {item.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ComplianceDashboard;
