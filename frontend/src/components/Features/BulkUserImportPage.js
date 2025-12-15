import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../utils/auth';
import BulkUserImport from '../Users/BulkUserImport';
import { ArrowLeft, Upload, AlertCircle, Users, FileSpreadsheet, CheckCircle } from 'lucide-react';

const BulkUserImportPage = () => {
  const { user, company } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = (result) => {
    // Success is handled within BulkUserImport component
    // Optionally navigate after showing results
    console.log('Bulk import completed:', result);
  };

  const handleBack = () => {
    navigate('/dashboard/users');
  };

  // Check permissions - only HR Admin can bulk import
  if (user?.role !== 'hr_admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="h-8 w-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            Bulk user import is restricted to HR Admins only. Please contact your system administrator.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="h-8 w-8 text-yellow-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Company Context</h2>
          <p className="text-gray-600 mb-6">
            Bulk user import requires a company context. Please ensure you're properly logged in to a company.
          </p>
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={handleBack}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to User Management
          </button>

          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
              <Upload className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Bulk User Import</h1>
              <p className="text-gray-600 mt-1">
                Import multiple users at once using CSV file format
              </p>
            </div>
          </div>
        </div>

        {/* Info Banners */}
        <div className="space-y-4 mb-6">
          {/* How it Works */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <FileSpreadsheet className="h-5 w-5 text-blue-600" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">How It Works</h3>
                <div className="text-sm text-blue-700 mt-1">
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Download the CSV template with pre-filled examples</li>
                    <li>Fill in your user data following the template format</li>
                    <li>Upload the CSV file to import all users at once</li>
                    <li>Review import results and fix any errors if needed</li>
                  </ol>
                </div>
              </div>
            </div>
          </div>

          {/* Requirements */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">CSV Requirements</h3>
                <div className="text-sm text-green-700 mt-1">
                  <ul className="list-disc list-inside space-y-1">
                    <li>All required fields must be filled (marked with * in template)</li>
                    <li>USERNAME, EMAIL, and EMPID must be unique across all users</li>
                    <li>Date format: MM/DD/YYYY, YYYY-MM-DD, or DD/MM/YYYY</li>
                    <li>Gender must be: M, F, Other, or Not Specified</li>
                    <li>Status must be: active or inactive</li>
                    <li>Use "NO_MANAGER" if employee has no manager</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Important Notes</h3>
                <div className="text-sm text-yellow-700 mt-1">
                  <ul className="list-disc list-inside space-y-1">
                    <li>This operation cannot be undone - users will be created immediately</li>
                    <li>Errors will prevent that row from being imported</li>
                    <li>Successfully imported users will be created even if some rows fail</li>
                    <li>Download error report to fix issues and re-import failed rows</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Import Card */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <BulkUserImport onSuccess={handleSuccess} />
        </div>

        {/* Help Section */}
        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <Users className="h-5 w-5 mr-2 text-gray-600" />
            Need Help?
          </h3>
          <div className="text-sm text-gray-600 space-y-2">
            <p>
              <strong>Common Issues:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li><strong>Duplicate errors:</strong> Ensure USERNAME, EMAIL, and EMPID are unique</li>
              <li><strong>Date format errors:</strong> Use MM/DD/YYYY format consistently</li>
              <li><strong>Missing required fields:</strong> Check all required columns are filled</li>
              <li><strong>Invalid values:</strong> Verify gender and status values match requirements</li>
            </ul>
            <p className="mt-4">
              <strong>Best Practices:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Test with a small batch (3-5 users) first before importing hundreds</li>
              <li>Keep a backup copy of your CSV file before uploading</li>
              <li>Review the template examples to understand the expected format</li>
              <li>Use Excel or Google Sheets to edit the CSV for better formatting</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkUserImportPage;
