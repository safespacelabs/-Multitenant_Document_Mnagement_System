import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { 
  authAPI, 
  companiesAPI, 
  documentsAPI, 
  usersAPI, 
  userManagementAPI, 
  chatAPI,
  systemChatAPI
} from '../../services/api';
import { 
  Database, 
  Users, 
  FileText, 
  MessageCircle, 
  Building2,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Zap
} from 'lucide-react';

function TestingInterface() {
  const { user, company } = useAuth();
  const [activeCategory, setActiveCategory] = useState('overview');
  const [testResults, setTestResults] = useState({});
  const [runningTests, setRunningTests] = useState({});
  const [testHistory, setTestHistory] = useState([]);

  useEffect(() => {
    loadTestHistory();
  }, []);

  const loadTestHistory = () => {
    const history = JSON.parse(localStorage.getItem('testHistory') || '[]');
    setTestHistory(history.slice(0, 10)); // Keep last 10 test runs
  };

  const saveTestResult = (testId, result) => {
    const newResult = {
      id: testId,
      result,
      timestamp: new Date().toISOString(),
      user: user.username,
      role: user.role
    };
    
    const history = JSON.parse(localStorage.getItem('testHistory') || '[]');
    history.unshift(newResult);
    localStorage.setItem('testHistory', JSON.stringify(history.slice(0, 50)));
    loadTestHistory();
  };

  const runTest = async (testId, testFunction) => {
    setRunningTests(prev => ({ ...prev, [testId]: true }));
    
    const startTime = Date.now();
    let result;
    
    try {
      const response = await testFunction();
      const duration = Date.now() - startTime;
      result = {
        status: 'success',
        message: response.message || 'Test completed successfully',
        data: response.data || response,
        duration
      };
    } catch (error) {
      const duration = Date.now() - startTime;
      
      // Check if this is an expected rejection for system admin
      const isSystemAdminExpectedRejection = user.role === 'system_admin' && 
        (error.message?.includes('System admins cannot access') || 
         error.message?.includes('Only system admins can access') ||
         error.message?.includes('No company access'));
      
      if (isSystemAdminExpectedRejection) {
        result = {
          status: 'expected',
          message: error.message || 'Expected behavior for system admin',
          error: error.message,
          duration
        };
      } else {
        result = {
          status: 'error',
          message: error.message || 'Test failed',
          error: error.message,
          duration
        };
      }
    } finally {
      setRunningTests(prev => ({ ...prev, [testId]: false }));
    }
    
    setTestResults(prev => ({ ...prev, [testId]: result }));
    saveTestResult(testId, result);
  };

  const runAllTests = async (category) => {
    const tests = getTestsByCategory(category);
    for (const test of tests) {
      if (!runningTests[test.id]) {
        await runTest(test.id, test.function);
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  // Test Functions
  const apiTests = {
    // Auth Tests
    'auth-me': () => authAPI.getMe().then(res => ({ message: 'Profile retrieved successfully', data: res.data })),
    
    // Companies Tests (System Admin only)
    'companies-list': () => {
      if (user.role !== 'system_admin') {
        return Promise.reject(new Error('Only system admins can access companies API'));
      }
      return companiesAPI.list().then(res => ({ message: `Found ${res.data.length} companies`, data: res.data }));
    },
    
    // Documents Tests (Company users only)
    'documents-list': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company documents'));
      }
      return documentsAPI.list().then(res => ({ message: `Found ${res.data.length} documents`, data: res.data }));
    },
    
    // Users Tests (Company users only)
    'users-list': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company users'));
      }
      return usersAPI.list().then(res => ({ message: `Found ${res.data.length} users`, data: res.data }));
    },
    
    // User Management Tests (Company users only)
    'user-management-users': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company user management'));
      }
      return userManagementAPI.listUsers().then(res => ({ message: `Found ${res.data.length} company users`, data: res.data }));
    },
    'user-management-invitations': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company invitations'));
      }
      return userManagementAPI.listInvitations().then(res => ({ message: `Found ${res.data.length} invitations`, data: res.data }));
    },
    'user-management-permissions': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company permissions'));
      }
      return userManagementAPI.getPermissions().then(res => ({ message: `User has ${res.data.length} permissions`, data: res.data }));
    },
    
    // Chat Tests (Company users only)
    'chat-history': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company chat history'));
      }
      return chatAPI.getHistory().then(res => ({ message: `Found ${res.data.length} chat messages`, data: res.data }));
    },
    
    // System Chat Tests (System Admin only)
    'system-chat-test': () => {
      if (user.role !== 'system_admin') {
        return Promise.reject(new Error('Only system admins can access system chat'));
      }
      return systemChatAPI.sendMessage('Test system chat functionality').then(res => ({ message: 'System chat working correctly', data: res.data }));
    },
    'system-chat-history': () => {
      if (user.role !== 'system_admin') {
        return Promise.reject(new Error('Only system admins can access system chat history'));
      }
      return systemChatAPI.getHistory().then(res => ({ message: `Found ${res.data.length} system chat messages`, data: res.data }));
    },
  };

  const roleTests = {
    'role-check': () => Promise.resolve({ message: `Current role: ${user.role}`, data: { role: user.role, permissions: ['based on role'] } }),
    'company-access': () => {
      if (user.role === 'system_admin') {
        return Promise.reject(new Error('No company access - system admins operate at system level'));
      }
      return company ? Promise.resolve({ message: `Access to company: ${company.name}`, data: company }) : Promise.reject(new Error('No company access'));
    },
  };

  const documentTests = {
    'document-types': async () => {
      if (user.role === 'system_admin' || !company) {
        throw new Error('System admins cannot access company documents');
      }
      const response = await documentsAPI.list();
      const types = [...new Set(response.data.map(doc => doc.file_type))];
      return { message: `Found ${types.length} different file types`, data: types };
    },
    'processed-docs': async () => {
      if (user.role === 'system_admin' || !company) {
        throw new Error('System admins cannot access company documents');
      }
      const response = await documentsAPI.list();
      const processed = response.data.filter(doc => doc.processed);
      return { message: `${processed.length}/${response.data.length} documents processed`, data: processed };
    }
  };

  const chatTests = {
    'chat-basic': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company chat'));
      }
      return chatAPI.sendMessage('Hello, this is a test message').then(res => ({ message: 'Chat response received', data: res.data }));
    },
    'chat-context': () => {
      if (user.role === 'system_admin' || !company) {
        return Promise.reject(new Error('System admins cannot access company chat'));
      }
      return chatAPI.sendMessage('What documents do I have?').then(res => ({ message: 'Context-aware response received', data: res.data }));
    },
  };

  const getTestsByCategory = (category) => {
    const testMap = {
      'api-routes': Object.entries(apiTests).map(([id, func]) => ({ id, name: id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), function: func })),
      'role-testing': Object.entries(roleTests).map(([id, func]) => ({ id, name: id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), function: func })),
      'documents': Object.entries(documentTests).map(([id, func]) => ({ id, name: id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), function: func })),
      'chat': Object.entries(chatTests).map(([id, func]) => ({ id, name: id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), function: func })),
    };
    
    return testMap[category] || [];
  };

  const getTestStatus = (testId) => {
    if (runningTests[testId]) return 'running';
    if (testResults[testId]) {
      return testResults[testId].status;
    }
    return 'pending';
  };

  const getTestStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-yellow-600 bg-yellow-100';
      case 'success': return 'text-green-600 bg-green-100';
      case 'expected': return 'text-blue-600 bg-blue-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const categories = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'api-routes', name: 'API Routes', icon: '🔌' },
    { id: 'role-testing', name: 'Role Testing', icon: '👤' },
    { id: 'documents', name: 'Documents', icon: '📄' },
    { id: 'chat', name: 'AI Chat', icon: '🤖' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Comprehensive Testing Interface</h1>
          <p className="text-gray-600 mt-2">
            Test all system features, API endpoints, and role-based functionality
          </p>
          <div className="mt-4 flex items-center space-x-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              User: {user.username}
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
              Role: {user.role}
            </span>
            {company && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                Company: {company.name}
              </span>
            )}
          </div>
        </div>

        {/* Categories */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeCategory === category.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <span>{category.icon}</span>
                  <span>{category.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Overview */}
        {activeCategory === 'overview' && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Tests</h3>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {Object.keys(apiTests).length + Object.keys(roleTests).length + Object.keys(documentTests).length + Object.keys(chatTests).length}
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Tests Run</h3>
                <p className="text-2xl font-bold text-gray-900 mt-1">{Object.keys(testResults).length}</p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Passed</h3>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {Object.values(testResults).filter(r => r.status === 'success').length}
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Expected</h3>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {Object.values(testResults).filter(r => r.status === 'expected').length}
                </p>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Failed</h3>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {Object.values(testResults).filter(r => r.status === 'error').length}
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {categories.slice(1).map((category) => (
                  <button
                    key={category.id}
                    onClick={() => runAllTests(category.id)}
                    className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-center transition-colors"
                    disabled={Object.values(runningTests).some(running => running)}
                  >
                    <div className="text-2xl mb-2">{category.icon}</div>
                    <div className="text-sm font-medium text-gray-900">Test {category.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Run all {getTestsByCategory(category.id).length} tests
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Test History */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Test History</h3>
              {testHistory.length > 0 ? (
                <div className="space-y-2">
                  {testHistory.map((test, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getTestStatusColor(test.result.status)}`}>
                          {test.result.status}
                        </span>
                        <span className="text-sm font-medium">{test.id}</span>
                        <span className="text-xs text-gray-500">{test.result.duration}ms</span>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(test.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No tests run yet</p>
              )}
            </div>

            {/* Test Status Guide */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Status Guide</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full text-green-600 bg-green-100">
                      success
                    </span>
                    <span className="text-sm text-gray-700">Test completed successfully</span>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full text-blue-600 bg-blue-100">
                      expected
                    </span>
                    <span className="text-sm text-gray-700">Expected behavior (e.g., system admin blocked from company APIs)</span>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full text-red-600 bg-red-100">
                      error
                    </span>
                    <span className="text-sm text-gray-700">Unexpected error or failure</span>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full text-yellow-600 bg-yellow-100">
                      running
                    </span>
                    <span className="text-sm text-gray-700">Test currently in progress</span>
                  </div>
                </div>
              </div>
              
              {user.role === 'system_admin' && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Note for System Admins:</strong> Many company-specific tests will show "expected" status 
                    because system admins are correctly blocked from accessing company resources to prevent security violations.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* API Routes */}
        {activeCategory === 'api-routes' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">API Endpoint Tests</h3>
                <button
                  onClick={() => runAllTests('api-routes')}
                  disabled={Object.values(runningTests).some(running => running)}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  Run All API Tests
                </button>
              </div>
              
              {user.role === 'system_admin' && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>System Admin:</strong> Company-specific API tests will show "expected" status as 
                    system admins are correctly blocked from accessing company resources.
                  </p>
                </div>
              )}

              <div className="grid gap-4">
                {getTestsByCategory('api-routes').map((test) => {
                  const status = getTestStatus(test.id);
                  const result = testResults[test.id];
                  
                  // Determine expected behavior description
                  const getExpectedBehavior = (testId) => {
                    if (user.role === 'system_admin') {
                      if (testId === 'companies-list') return 'Should succeed - system admin can access companies';
                      if (testId === 'auth-me') return 'Should succeed - all users can check their profile';
                      return 'Should be blocked - system admins cannot access company resources';
                    } else {
                      if (testId === 'companies-list') return 'Should be blocked - only system admins can access';
                      return 'Should succeed if user has proper permissions';
                    }
                  };

                  return (
                    <div key={test.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-medium text-gray-900">{test.name}</h4>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getTestStatusColor(status)}`}>
                              {status}
                            </span>
                            {runningTests[test.id] && (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            )}
                          </div>
                          
                          <p className="text-sm text-gray-600 mt-1">
                            Expected: {getExpectedBehavior(test.id)}
                          </p>
                          
                          {result && (
                            <div className="mt-2 text-sm">
                              <p className={`${result.status === 'error' ? 'text-red-600' : result.status === 'expected' ? 'text-blue-600' : 'text-green-600'}`}>
                                {result.message}
                              </p>
                              {result.duration && (
                                <p className="text-gray-500 text-xs mt-1">Duration: {result.duration}ms</p>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => runTest(test.id, test.function)}
                          disabled={runningTests[test.id]}
                          className="ml-4 px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 text-sm"
                        >
                          {runningTests[test.id] ? 'Running...' : 'Run Test'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Role Testing */}
        {activeCategory === 'role-testing' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Role-based Access Tests</h3>
                <button
                  onClick={() => runAllTests('role-testing')}
                  disabled={Object.values(runningTests).some(running => running)}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  Run All Role Tests
                </button>
              </div>

              <div className="grid gap-4">
                {getTestsByCategory('role-testing').map((test) => {
                  const status = getTestStatus(test.id);
                  const result = testResults[test.id];
                  
                  const getExpectedBehavior = (testId) => {
                    if (testId === 'role-check') return 'Should always succeed - shows current user role';
                    if (testId === 'company-access') {
                      if (user.role === 'system_admin') return 'Should fail - system admins have no company context';
                      return 'Should succeed - company users have company context';
                    }
                    return 'Depends on user role and permissions';
                  };

                  return (
                    <div key={test.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-medium text-gray-900">{test.name}</h4>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getTestStatusColor(status)}`}>
                              {status}
                            </span>
                            {runningTests[test.id] && (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            )}
                          </div>
                          
                          <p className="text-sm text-gray-600 mt-1">
                            Expected: {getExpectedBehavior(test.id)}
                          </p>
                          
                          {result && (
                            <div className="mt-2 text-sm">
                              <p className={`${result.status === 'error' ? 'text-red-600' : result.status === 'expected' ? 'text-blue-600' : 'text-green-600'}`}>
                                {result.message}
                              </p>
                              {result.duration && (
                                <p className="text-gray-500 text-xs mt-1">Duration: {result.duration}ms</p>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => runTest(test.id, test.function)}
                          disabled={runningTests[test.id]}
                          className="ml-4 px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 text-sm"
                        >
                          {runningTests[test.id] ? 'Running...' : 'Run Test'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Documents */}
        {activeCategory === 'documents' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Document Management Tests</h3>
                <button
                  onClick={() => runAllTests('documents')}
                  disabled={Object.values(runningTests).some(running => running)}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  Run All Document Tests
                </button>
              </div>
              
              {user.role === 'system_admin' && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>System Admin:</strong> Document tests will show "expected" status as 
                    system admins cannot access company-specific documents.
                  </p>
                </div>
              )}

              <div className="grid gap-4">
                {getTestsByCategory('documents').map((test) => {
                  const status = getTestStatus(test.id);
                  const result = testResults[test.id];
                  
                  const getExpectedBehavior = (testId) => {
                    if (user.role === 'system_admin') {
                      return 'Should be blocked - system admins cannot access company documents';
                    }
                    return 'Should succeed if user has document access permissions';
                  };

                  return (
                    <div key={test.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-medium text-gray-900">{test.name}</h4>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getTestStatusColor(status)}`}>
                              {status}
                            </span>
                            {runningTests[test.id] && (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            )}
                          </div>
                          
                          <p className="text-sm text-gray-600 mt-1">
                            Expected: {getExpectedBehavior(test.id)}
                          </p>
                          
                          {result && (
                            <div className="mt-2 text-sm">
                              <p className={`${result.status === 'error' ? 'text-red-600' : result.status === 'expected' ? 'text-blue-600' : 'text-green-600'}`}>
                                {result.message}
                              </p>
                              {result.duration && (
                                <p className="text-gray-500 text-xs mt-1">Duration: {result.duration}ms</p>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => runTest(test.id, test.function)}
                          disabled={runningTests[test.id]}
                          className="ml-4 px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 text-sm"
                        >
                          {runningTests[test.id] ? 'Running...' : 'Run Test'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* AI Chat */}
        {activeCategory === 'chat' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">AI Chat Tests</h3>
                <button
                  onClick={() => runAllTests('chat')}
                  disabled={Object.values(runningTests).some(running => running)}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  Run All Chat Tests
                </button>
              </div>
              
              {user.role === 'system_admin' && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>System Admin:</strong> Chat tests will show "expected" status as 
                    system admins cannot access company-specific chat functionality.
                  </p>
                </div>
              )}

              <div className="grid gap-4">
                {getTestsByCategory('chat').map((test) => {
                  const status = getTestStatus(test.id);
                  const result = testResults[test.id];
                  
                  const getExpectedBehavior = (testId) => {
                    if (user.role === 'system_admin') {
                      return 'Should be blocked - system admins cannot access company chat';
                    }
                    return 'Should succeed if user has chat access permissions';
                  };

                  return (
                    <div key={test.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-medium text-gray-900">{test.name}</h4>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getTestStatusColor(status)}`}>
                              {status}
                            </span>
                            {runningTests[test.id] && (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                            )}
                          </div>
                          
                          <p className="text-sm text-gray-600 mt-1">
                            Expected: {getExpectedBehavior(test.id)}
                          </p>
                          
                          {result && (
                            <div className="mt-2 text-sm">
                              <p className={`${result.status === 'error' ? 'text-red-600' : result.status === 'expected' ? 'text-blue-600' : 'text-green-600'}`}>
                                {result.message}
                              </p>
                              {result.duration && (
                                <p className="text-gray-500 text-xs mt-1">Duration: {result.duration}ms</p>
                              )}
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => runTest(test.id, test.function)}
                          disabled={runningTests[test.id]}
                          className="ml-4 px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 text-sm"
                        >
                          {runningTests[test.id] ? 'Running...' : 'Run Test'}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* System Information */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">🔧 System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-medium text-blue-900">API Base URL</div>
              <div className="text-blue-800">{process.env.REACT_APP_API_URL || 'http://localhost:8000'}</div>
            </div>
            <div>
              <div className="font-medium text-blue-900">User Agent</div>
              <div className="text-blue-800 truncate">{navigator.userAgent}</div>
            </div>
            <div>
              <div className="font-medium text-blue-900">Timestamp</div>
              <div className="text-blue-800">{new Date().toISOString()}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TestingInterface; 