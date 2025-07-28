import React from 'react';
import { useAuth } from '../../utils/auth';
import { LogOut, User, Settings } from 'lucide-react';

function Header() {
  const { user, company, logout } = useAuth();

  // Don't render header if user data is not loaded yet
  if (!user) {
    return null;
  }

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">
                  {company?.name?.charAt(0) || (user?.role === 'system_admin' ? 'S' : 'C')}
                </span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-800">
                  {company?.name || (user?.role === 'system_admin' ? 'System Administration' : 'Company')}
                </h1>
                <p className="text-sm text-gray-500">
                  {user?.role === 'system_admin' ? 'Multi-Tenant Management' : 'Document Management System'}
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium text-gray-700">{user?.full_name || 'User'}</p>
              <p className="text-xs text-gray-500">
                {user?.role === 'system_admin' ? 'System Administrator' : 
                 user?.role === 'hr_admin' ? 'HR Administrator' : 
                 user?.role === 'hr_manager' ? 'HR Manager' : 'Employee'}
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                <Settings className="h-5 w-5" />
              </button>

              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header; 