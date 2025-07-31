import React, { useState } from 'react';
import { useAuth } from '../../utils/auth';

const TestingInterface = () => {
  const { user, company } = useAuth();
  const [testResults, setTestResults] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  const runCredentialTest = async () => {
    setIsRunning(true);
    setTestResults([]);
    
    try {
      const response = await fetch('/api/test/credentials', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      setTestResults(data.results || []);
    } catch (error) {
      setTestResults([
        {
          service: 'Connection',
          test: 'API Test',
          status: '❌ FAIL',
          message: `Connection failed: ${error.message}`,
          success: false
        }
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  const runSystemTest = async () => {
    setIsRunning(true);
    setTestResults([]);
    
    try {
      const response = await fetch('/api/test/system', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      setTestResults(data.results || []);
    } catch (error) {
      setTestResults([
        {
          service: 'System',
          test: 'System Test',
          status: '❌ FAIL',
          message: `System test failed: ${error.message}`,
          success: false
        }
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          🧪 System Testing Interface
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-blue-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">
              Credential Tests
            </h3>
            <p className="text-blue-700 mb-4">
              Test all external API credentials and database connections
            </p>
            <button
              onClick={runCredentialTest}
              disabled={isRunning}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isRunning ? 'Running...' : 'Run Credential Tests'}
            </button>
          </div>
          
          <div className="bg-green-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-green-900 mb-4">
              System Tests
            </h3>
            <p className="text-green-700 mb-4">
              Test system functionality and integrations
            </p>
            <button
              onClick={runSystemTest}
              disabled={isRunning}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {isRunning ? 'Running...' : 'Run System Tests'}
            </button>
          </div>
        </div>

        {/* Test Results */}
        {testResults.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Test Results
            </h3>
            <div className="space-y-4">
              {testResults.map((result, index) => (
                <div 
                  key={index}
                  className={`p-4 rounded-lg border-l-4 ${
                    result.success 
                      ? 'bg-green-50 border-green-400' 
                      : 'bg-red-50 border-red-400'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold">
                        {result.service} - {result.test}
                      </h4>
                      <p className={`text-sm ${
                        result.success ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {result.message}
                      </p>
                      {result.details && (
                        <p className="text-xs text-gray-500 mt-1">
                          {result.details}
                        </p>
                      )}
                    </div>
                    <span className="text-lg">
                      {result.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* User Info */}
        {user && (
          <div className="mt-8 bg-gray-100 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Current User Context</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">User:</span> {user.username}
              </div>
              <div>
                <span className="text-gray-600">Role:</span> {user.role}
              </div>
              {company && (
                <>
                  <div>
                    <span className="text-gray-600">Company:</span> {company.name}
                  </div>
                  <div>
                    <span className="text-gray-600">Company ID:</span> {company.id}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestingInterface; 