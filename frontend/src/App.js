import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './utils/auth';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import CompanyList from './components/Company/CompanyList';
import CompanyRegister from './components/Company/CompanyRegister';
import CompanyDashboard from './components/Company/CompanyDashboard';
import './App.css';

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App min-h-screen bg-gray-50">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/companies" element={<CompanyList />} />
            <Route path="/companies/new" element={<CompanyRegister />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <CompanyDashboard />
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/companies" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;