import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

// Utility function to extract error messages from FastAPI validation errors
export function extractErrorMessage(error, defaultMessage = 'An error occurred') {
  if (!error.response?.data) {
    return defaultMessage;
  }

  const data = error.response.data;
  
  // Check if detail is a string
  if (typeof data.detail === 'string') {
    return data.detail;
  }
  
  // Check if detail is an array of validation errors
  if (Array.isArray(data.detail)) {
    return data.detail.map(err => err.msg || err.message || 'Validation error').join(', ');
  }
  
  // Check if the response is directly an array of validation errors
  if (Array.isArray(data)) {
    return data.map(err => err.msg || err.message || 'Validation error').join(', ');
  }
  
  return defaultMessage;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    const savedCompany = localStorage.getItem('company');

    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      // Company might be null for system users
      if (savedCompany && savedCompany !== 'null') {
        setCompany(JSON.parse(savedCompany));
      }
    }
    setLoading(false);
  }, []);

  const login = async (credentials, companyId = null) => {
    try {
      const payload = { ...credentials };
      if (companyId) {
        payload.company_id = companyId;
      }
      
      const response = await authAPI.login(payload);
      const { access_token, user: userData, company: companyData } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // For system users, company might be null
      if (companyData) {
        localStorage.setItem('company', JSON.stringify(companyData));
        setCompany(companyData);
      } else {
        localStorage.removeItem('company');
        setCompany(null);
      }
      
      setUser(userData);
      
      return { user: userData, company: companyData };
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const systemAdminLogin = async (credentials) => {
    try {
      const response = await authAPI.systemAdminLogin(credentials);
      const { access_token, user: userData, company: companyData, permissions } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // For system users, company is typically null
      if (companyData) {
        localStorage.setItem('company', JSON.stringify(companyData));
        setCompany(companyData);
      } else {
        localStorage.removeItem('company');
        setCompany(null);
      }
      
      setUser(userData);
      
      return { user: userData, company: companyData, permissions };
    } catch (error) {
      console.error('System admin login error:', error);
      throw error;
    }
  };

  const register = async (userData) => {
    const response = await authAPI.register(userData);
    const { access_token, user: newUser, company: companyData } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(newUser));
    localStorage.setItem('company', JSON.stringify(companyData));
    
    setUser(newUser);
    setCompany(companyData);
    
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('company');
    setUser(null);
    setCompany(null);
  };

  const value = {
    user,
    company,
    login,
    systemAdminLogin,
    register,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}