import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './utils/auth';
import MainLanding from './components/Auth/MainLanding';
import SystemAdminLogin from './components/Auth/SystemAdminLogin';
import CompanyAccess from './components/Auth/CompanyAccess';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import PasswordSetup from './components/Auth/PasswordSetup';
import CompanyLogin from './components/Auth/CompanyLogin';
import CompanyRegister from './components/Auth/CompanyRegister';
import CompanyDashboard from './components/Company/CompanyDashboard';
import Dashboard from './components/Dashboard/Dashboard';
import TestingInterface from './components/Testing/TestingInterface';
import ESignatureManager from './components/ESignature/ESignatureManager';
import EmailDocumentSigning from './components/ESignature/EmailDocumentSigning';
import {
  SystemOverview,
  SystemAdminManagement,
  UserManagement,
  DocumentManagement,
  CompanyManagement,
  ChatInterface,
  Analytics,
  Settings,
  HRAdminDashboard
} from './components/Features';
import { EnhancedDocumentManager } from './components/Documents';
import './App.css';

function ProtectedRoute({ children, allowedRoles = [] }) {
  const { user } = useAuth();
  
  if (!user) {
    return <Navigate to="/" replace />;
  }
  
  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
}

function ESignatureWrapper() {
  const { user } = useAuth();
  return <ESignatureManager userRole={user?.role} userId={user?.id} />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App min-h-screen bg-gray-50">
          <Routes>
            {/* Main Landing Page */}
            <Route path="/" element={<MainLanding />} />
            
            {/* System Admin Routes */}
            <Route path="/system-admin-login" element={<SystemAdminLogin />} />
            
            {/* Company Access Routes */}
            <Route path="/company/:companyId/access" element={<CompanyAccess />} />
            <Route path="/company/:companyId/login" element={<CompanyLogin />} />
            <Route path="/company/:companyId/signup" element={<CompanyRegister />} />
            
            {/* New Company Login Route */}
            <Route path="/company-login" element={<CompanyLogin />} />
            <Route path="/company-dashboard" element={<CompanyDashboard />} />
            
            {/* Legacy Authentication Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/setup-password/:uniqueId" element={<PasswordSetup />} />
            
            {/* Protected Dashboard Routes with Nested Routes */}
            <Route path="/dashboard/*" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard/documents" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard/users" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard/hr-admin" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard/analytics" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard/esignature" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard/chat" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/system-dashboard/*" element={
              <ProtectedRoute allowedRoles={['system_admin']}>
                <Dashboard />
              </ProtectedRoute>
            } />
            
            {/* Feature Routes */}
            <Route path="/overview" element={
              <ProtectedRoute>
                <SystemOverview />
              </ProtectedRoute>
            } />
            
            <Route path="/system-admins" element={
              <ProtectedRoute allowedRoles={['system_admin']}>
                <SystemAdminManagement />
              </ProtectedRoute>
            } />
            
            <Route path="/users" element={
              <ProtectedRoute allowedRoles={['hr_admin', 'hr_manager']}>
                <UserManagement />
              </ProtectedRoute>
            } />
            
            <Route path="/hr-admin-dashboard" element={
              <ProtectedRoute allowedRoles={['hr_admin', 'system_admin']}>
                <HRAdminDashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/documents" element={
              <ProtectedRoute>
                <EnhancedDocumentManager />
              </ProtectedRoute>
            } />
            
            <Route path="/esignature" element={
              <ProtectedRoute allowedRoles={['system_admin', 'hr_admin', 'hr_manager', 'employee', 'customer']}>
                <ESignatureWrapper />
              </ProtectedRoute>
            } />
            
            {/* Direct Document Signing - No Auth Required */}
            <Route path="/esignature/sign/:documentId" element={<EmailDocumentSigning />} />
            
            <Route path="/companies" element={
              <ProtectedRoute allowedRoles={['system_admin']}>
                <CompanyManagement />
              </ProtectedRoute>
            } />
            
            <Route path="/chat" element={
              <ProtectedRoute>
                <ChatInterface />
              </ProtectedRoute>
            } />
            
            <Route path="/analytics" element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            } />
            
            <Route path="/settings" element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            } />
            
            <Route path="/testing" element={
              <ProtectedRoute>
                <TestingInterface />
              </ProtectedRoute>
            } />
            
            {/* Fallback Routes */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;