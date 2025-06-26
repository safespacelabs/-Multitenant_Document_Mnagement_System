import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    const savedCompany = localStorage.getItem('company');

    if (token && savedUser && savedCompany) {
      setUser(JSON.parse(savedUser));
      setCompany(JSON.parse(savedCompany));
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    const response = await authAPI.login(credentials);
    const { access_token, user: userData, company: companyData } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('company', JSON.stringify(companyData));
    
    setUser(userData);
    setCompany(companyData);
    
    return response.data;
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