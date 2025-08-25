import React from 'react';
import { 
  FileText, 
  MessageCircle, 
  BarChart3, 
  Users, 
  Settings, 
  Building2, 
  Crown, 
  FileSignature,
  Home,
  Folder,
  Calendar,
  Star,
  FileText as FileTextIcon,
  Upload,
  LogOut,
  ChevronLeft,
  Search,
  Bell,
  User,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../../utils/auth';

function Sidebar({ activeTab, setActiveTab, collapsed, setCollapsed }) {
  const { user } = useAuth();

  const menuItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: Home,
      description: 'Dashboard overview',
      path: '/dashboard'
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: FileText,
      description: 'Upload and manage files',
      path: '/dashboard/documents'
    },
    {
      id: 'esignature',
      label: 'E-Signature',
      icon: FileSignature,
      description: 'Manage digital signatures',
      path: '/dashboard/esignature'
    },
    {
      id: 'chat',
      label: 'AI Assistant',
      icon: MessageCircle,
      description: 'Chat with your documents',
      path: '/dashboard/chat'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      description: 'Document insights',
      path: '/dashboard/analytics'
    }
  ];

  // Add role-based items
  if (user?.role === 'system_admin') {
    menuItems.push({
      id: 'system-admins',
      label: 'System Admins',
      icon: Crown,
      description: 'Manage system administrators',
      path: '/system-dashboard/system-admins',
      isSystemAdmin: true
    });
    
    menuItems.push({
      id: 'companies',
      label: 'Companies',
      icon: Building2,
      description: 'Manage all companies',
      path: '/system-dashboard/companies'
    });
  }
  
  if (['hr_admin', 'hr_manager'].includes(user?.role)) {
    menuItems.push({
      id: 'users',  
      label: 'User Management',
      icon: Users,
      description: 'Manage team members',
      path: '/dashboard/users'
    });
  }

  const navigationItems = [
    {
      id: 'my-files',
      label: 'My Files',
      icon: Folder,
      path: '/dashboard/documents'
    },
    {
      id: 'org-files',
      label: 'Org Files',
      icon: Users,
      path: '/dashboard/documents',
      active: true
    },
    {
      id: 'recent',
      label: 'Recent',
      icon: Calendar,
      path: '/dashboard/documents'
    },
    {
      id: 'starred',
      label: 'Starred',
      icon: Star,
      path: '/dashboard/documents'
    },
    {
      id: 'logs',
      label: 'Logs',
      icon: FileTextIcon,
      path: '/dashboard/documents'
    },
    {
      id: 'uploads',
      label: 'Uploads',
      icon: Upload,
      path: '/dashboard/documents'
    }
  ];

  const organizationFiles = [
    {
      id: 'hr-docs',
      label: 'HR Documents',
      icon: Users,
      count: 12
    },
    {
      id: 'legal-docs',
      label: 'Legal Documents',
      icon: FileText,
      count: 8
    },
    {
      id: 'financial-docs',
      label: 'Financial Reports',
      icon: BarChart3,
      count: 15
    }
  ];

  return (
    <aside className={`${collapsed ? 'w-16' : 'w-64'} bg-white shadow-lg border-r border-gray-200 min-h-screen transition-all duration-300`}>
      <div className="flex flex-col h-full">
        {/* Logo/Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">P</span>
            </div>
            {!collapsed && (
              <div>
                <span className="font-bold text-xl text-gray-900">PFile</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
          >
            <ChevronLeft className={`h-5 w-5 transition-transform ${collapsed ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Navigation Section */}
        <div className="flex-1 px-4 py-4">
          {!collapsed && (
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">NAVIGATION</h3>
            </div>
          )}
          
          <div className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.active;
              
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-3 rounded-xl text-left transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                  {!collapsed && <span className="font-medium">{item.label}</span>}
                </button>
              );
            })}
          </div>

          {/* Organization Files Section */}
          {!collapsed && (
            <div className="mt-8">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">ORGANISATION FILES</h3>
              <div className="space-y-2">
                {organizationFiles.map((item) => {
                  const Icon = item.icon;
                  
                  return (
                    <div
                      key={item.id}
                      className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-600">{item.label}</span>
                      </div>
                      <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded-full">
                        {item.count}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Main Menu Items */}
          {!collapsed && (
            <div className="mt-8">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">MAIN MENU</h3>
              <div className="space-y-2">
                {menuItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-3 py-3 rounded-xl text-left transition-all duration-200 ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                      }`}
                    >
                      <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{item.label}</span>
                          {item.isSystemAdmin && (
                            <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                              System
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Collapsed Menu Items */}
          {collapsed && (
            <div className="mt-8 space-y-2">
              {menuItems.slice(0, 5).map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-center p-3 rounded-xl transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                    title={item.label}
                  >
                    <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick Stats */}
        {!collapsed && (
          <div className="p-4 border-t border-gray-200">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Your Documents</span>
                <span className="font-semibold text-gray-900">24</span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Storage Used</span>
                <span className="font-semibold text-gray-900">2.4 GB</span>
              </div>
              
              {['system_admin', 'hr_admin', 'hr_manager'].includes(user?.role) && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Team Members</span>
                  <span className="font-semibold text-gray-900">18</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Settings & Logout */}
        <div className="p-4 border-t border-gray-200">
          {!collapsed && (
            <button className="w-full flex items-center space-x-3 px-3 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-800 rounded-xl transition-colors mb-2">
              <Settings className="h-5 w-5 text-gray-400" />
              <span className="font-medium">Settings</span>
            </button>
          )}
          
          <button className="w-full flex items-center space-x-3 px-3 py-3 text-red-600 hover:bg-red-50 transition-colors rounded-xl">
            <LogOut className="h-5 w-5" />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar; 