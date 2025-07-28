import React from 'react';
import { FileText, MessageCircle, BarChart3, Users, Settings, Building2, Crown, FileSignature } from 'lucide-react';
import { useAuth } from '../../utils/auth';

function Sidebar({ activeTab, setActiveTab }) {
  const { user } = useAuth();

  const menuItems = [
    {
      id: 'documents',
      label: 'Documents',
      icon: FileText,
      description: 'Upload and manage files'
    },
    {
      id: 'esignature',
      label: 'E-Signature',
      icon: FileSignature,
      description: 'Manage digital signatures'
    },
    {
      id: 'chat',
      label: 'AI Assistant',
      icon: MessageCircle,
      description: 'Chat with your documents'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      description: 'Document insights',
      adminOnly: false
    }
  ];

  // Add role-based items
  if (user?.role === 'system_admin') {
    menuItems.push({
      id: 'system-admins',
      label: 'System Admins',
      icon: Crown,
      description: 'Manage system administrators',
      adminOnly: true,
      isSystemAdmin: true
    });
  }
  
  if (['hr_admin', 'hr_manager'].includes(user?.role)) {
    menuItems.push({
      id: 'users',  
      label: 'Users',
      icon: Users,
      description: 'Manage team members',
      adminOnly: true
    });
  }
  
  if (['system_admin', 'hr_admin'].includes(user?.role)) {
    menuItems.push({
      id: 'companies',
      label: 'Companies',
      icon: Building2,
      description: 'Manage all companies',
      adminOnly: true
    });
  }

  return (
    <aside className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
      <nav className="p-4">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
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
                    {item.adminOnly && !item.isSystemAdmin && (
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                        Admin
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-8 pt-4 border-t border-gray-200">
          <div className="px-4 py-2">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Quick Stats
            </h3>
          </div>
          
          <div className="space-y-2 px-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Your Documents</span>
              <span className="font-medium text-gray-800">0</span>
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Storage Used</span>
              <span className="font-medium text-gray-800">0 MB</span>
            </div>
            
            {['system_admin', 'hr_admin', 'hr_manager'].includes(user?.role) && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Team Members</span>
                <span className="font-medium text-gray-800">1</span>
              </div>
            )}
          </div>
        </div>

        <div className="mt-8 pt-4 border-t border-gray-200">
          <button className="w-full flex items-center space-x-3 px-4 py-3 text-gray-600 hover:bg-gray-50 hover:text-gray-800 rounded-lg transition-colors">
            <Settings className="h-5 w-5 text-gray-400" />
            <span className="font-medium">Settings</span>
          </button>
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar; 