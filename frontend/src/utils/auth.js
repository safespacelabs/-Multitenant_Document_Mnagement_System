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
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('🔐 AuthProvider initializing...');
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    const savedCompany = localStorage.getItem('company');

    console.log('🔑 Token found:', !!token);
    console.log('👤 Saved user:', savedUser);
    console.log('🏢 Saved company:', savedCompany);

    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        console.log('✅ Setting user:', userData.username);
        
        // Validate that user data has required fields
        if (userData && userData.username && userData.role) {
          setUser(userData);
          
          // Company might be null for system users
          if (savedCompany && savedCompany !== 'null') {
            try {
              const companyData = JSON.parse(savedCompany);
              console.log('✅ Setting company:', companyData.name);
              setCompany(companyData);
            } catch (companyError) {
              console.error('❌ Failed to parse company data:', companyError);
              setCompany(null);
            }
          } else {
            console.log('ℹ️ No company data (system user)');
            setCompany(null);
          }
        } else {
          console.error('❌ Invalid user data - missing required fields:', userData);
          // Clear invalid data
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          localStorage.removeItem('company');
          setUser(null);
          setCompany(null);
        }
      } catch (userError) {
        console.error('❌ Failed to parse user data:', userError);
        // Clear invalid data
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('company');
        setUser(null);
        setCompany(null);
      }
    } else {
      console.log('❌ No token or user data found');
      // Clear any stale data
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('company');
      setUser(null);
      setCompany(null);
    }
    
    setLoading(false);
    console.log('🔐 AuthProvider initialization complete');
  }, []);

  const login = async (credentials, companyId = null) => {
    try {
      console.log('🔐 Login function called with:', { credentials, companyId });
      
      const payload = { ...credentials };
      if (companyId) {
        payload.company_id = companyId;
      }
      
      console.log('📤 Making login request with payload:', payload);
      const response = await authAPI.login(payload);
      console.log('✅ Login response received:', response);
      
      const { access_token, user: userData, company: companyData } = response;
      
      // Validate user data before storing
      if (!userData || !userData.username || !userData.role) {
        throw new Error('Invalid user data received from server');
      }
      
      console.log('💾 Storing token and user data...');
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // For system users, company might be null
      if (companyData) {
        console.log('🏢 Storing company data:', companyData.name);
        localStorage.setItem('company', JSON.stringify(companyData));
        setCompany(companyData);
      } else {
        console.log('ℹ️ No company data (system user)');
        localStorage.removeItem('company');
        setCompany(null);
      }
      
      console.log('👤 Setting user state:', userData.username);
      setUser(userData);
      
      console.log('✅ Login function completed successfully');
      return { user: userData, company: companyData };
    } catch (error) {
      console.error('❌ Login error:', error);
      setError(error.message);
      throw error;
    }
  };

  const systemAdminLogin = async (credentials) => {
    try {
      console.log('🔐 Attempting system admin login with credentials:', credentials);
      const response = await authAPI.systemAdminLogin(credentials);
      console.log('✅ System admin login response received:', response);
      
      const { access_token, user: userData, company: companyData, permissions } = response;
      
      // Validate user data before storing
      if (!userData || !userData.username || !userData.role) {
        throw new Error('Invalid user data received from server');
      }
      
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
      setError(error.message);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      const response = await authAPI.register(userData);
      const { access_token, user: newUser, company: companyData } = response;
      
      // Validate user data before storing
      if (!newUser || !newUser.username || !newUser.role) {
        throw new Error('Invalid user data received from server');
      }
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(newUser));
      localStorage.setItem('company', JSON.stringify(companyData));
      
      setUser(newUser);
      setCompany(companyData);
      
      return response;
    } catch (error) {
      console.error('Registration error:', error);
      setError(error.message);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('company');
    setUser(null);
    setCompany(null);
    setError(null);
  };

  const clearError = () => {
    setError(null);
  };

  const clearInvalidAuth = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('company');
    setUser(null);
    setCompany(null);
    setError(null);
  };

  const debugAuthState = () => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    const savedCompany = localStorage.getItem('company');
    
    console.log('🔍 Debug Auth State:');
    console.log('  Token:', token ? `${token.substring(0, 20)}...` : 'None');
    console.log('  Saved User:', savedUser);
    console.log('  Saved Company:', savedCompany);
    console.log('  Current User State:', user);
    console.log('  Current Company State:', company);
    console.log('  Loading:', loading);
    console.log('  Error:', error);
    
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        console.log('  Parsed User Data:', parsedUser);
        console.log('  Has Username:', !!parsedUser.username);
        console.log('  Has Role:', !!parsedUser.role);
      } catch (e) {
        console.log('  Failed to parse user data:', e);
      }
    }
  };

  const value = {
    user,
    company,
    login,
    systemAdminLogin,
    register,
    logout,
    loading,
    error,
    clearError,
    clearInvalidAuth,
    debugAuthState
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}