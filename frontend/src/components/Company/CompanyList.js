import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { companiesAPI } from '../../services/api';
import { Building2, Plus, Users } from 'lucide-react';

function CompanyList() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const response = await companiesAPI.list();
      setCompanies(response.data);
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            🏢 Select Your Company
          </h1>
          <p className="text-gray-600 text-lg">
            Choose your company to access the document management system
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {companies.map((company) => (
            <div
              key={company.id}
              className="bg-white rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 cursor-pointer border border-gray-200"
              onClick={() => navigate('/login', { state: { companyId: company.id } })}
            >
              <div className="p-6">
                <div className="flex items-center mb-4">
                  <Building2 className="h-8 w-8 text-blue-500 mr-3" />
                  <h3 className="text-xl font-semibold text-gray-800">
                    {company.name}
                  </h3>
                </div>
                <p className="text-gray-600 mb-4">{company.email}</p>
                <div className="flex items-center text-sm text-gray-500">
                  <Users className="h-4 w-4 mr-1" />
                  <span>Active since {new Date(company.created_at).getFullYear()}</span>
                </div>
              </div>
              <div className="bg-blue-50 px-6 py-3 rounded-b-xl">
                <span className="text-blue-600 font-medium">Click to Login →</span>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center">
          <div className="bg-white rounded-xl shadow-lg p-8 border-2 border-dashed border-gray-300">
            <Plus className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Company Not Listed?
            </h3>
            <p className="text-gray-600 mb-4">
              Register your company to get started with our document management system
            </p>
            <Link
              to="/companies/new"
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Register New Company
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CompanyList;