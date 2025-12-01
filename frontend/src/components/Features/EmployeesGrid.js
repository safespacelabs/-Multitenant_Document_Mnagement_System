import React, { useState, useEffect } from 'react';
import { useAuth } from '../../utils/auth';
import { usersAPI } from '../../services/api';
import { Search, MessageCircle, Mail, User } from 'lucide-react';

const EmployeesGrid = () => {
  const { user, company } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEmployees();
  }, [company]);

  const loadEmployees = async () => {
    try {
      setLoading(true);
      const response = await usersAPI.list(company.id);
      const usersData = response.data || response || [];
      setEmployees(Array.isArray(usersData) ? usersData : []);
      setError(null);
    } catch (error) {
      console.error('Failed to load employees:', error);
      setError('Failed to load employees');
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  };

  const handleChatAboutDocs = (employee) => {
    // Navigate to chat or open AI assistant for this employee
    console.log('Opening chat for employee:', employee);
    // You can implement navigation to AI Assistant here
  };

  const filteredEmployees = employees.filter(emp =>
    (emp.full_name || emp.username || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (emp.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (emp.role || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return parts[0][0] + parts[1][0];
    }
    return name.substring(0, 2);
  };

  const getRoleDisplay = (role) => {
    const roleMap = {
      'hr_admin': 'HR Admin',
      'hr_manager': 'HR Manager',
      'employee': 'Employee',
      'system_admin': 'System Admin'
    };
    return roleMap[role] || role;
  };

  const getDepartmentFromRole = (role) => {
    // Map roles to departments (you can customize this based on your data)
    const deptMap = {
      'hr_admin': 'HR',
      'hr_manager': 'HR',
      'employee': 'Operations',
      'system_admin': 'IT'
    };
    return deptMap[role] || 'General';
  };

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
        <h1 className="text-2xl font-bold text-gray-900">Employees</h1>
        <p className="text-sm text-gray-600 mt-1">Manage employee information and documents</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search employees..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Employees Grid */}
      {error ? (
        <div className="text-center py-8 text-red-600">
          {error}
        </div>
      ) : filteredEmployees.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No employees found
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredEmployees.map((employee) => (
            <div
              key={employee.id}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start space-x-4">
                {/* Avatar */}
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-semibold text-xl">
                    {getInitials(employee.full_name || employee.username)}
                  </div>
                </div>

                {/* Employee Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">
                    {employee.full_name || employee.username}
                  </h3>
                  <p className="text-sm text-gray-600 truncate">{getRoleDisplay(employee.role)}</p>
                  <p className="text-sm text-gray-500 truncate">{getDepartmentFromRole(employee.role)}</p>

                  {/* Email */}
                  <div className="flex items-center mt-2">
                    <Mail className="h-4 w-4 text-gray-400 mr-1" />
                    <span className="text-sm text-gray-600 truncate">{employee.email}</span>
                  </div>

                  {/* Chat Button */}
                  <button
                    onClick={() => handleChatAboutDocs(employee)}
                    className="mt-3 w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Chat About Docs
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EmployeesGrid;
