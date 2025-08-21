# Troubleshooting CORS and API Issues

## Current Problem
The frontend is receiving HTML responses instead of JSON from the backend API, specifically when calling `/api/companies/{companyId}/public`.

## Root Causes Identified

### 1. **Conflicting Route Handler** ✅ FIXED
- **Problem**: The `@app.options("/{full_path:path}")` route was catching all requests before they reached the API routers
- **Solution**: Commented out this conflicting route
- **Status**: Fixed in code

### 2. **CORS Configuration** ✅ FIXED
- **Problem**: Backend was not detecting production environment
- **Solution**: Added `ENVIRONMENT: production` to render.yaml and improved CORS logic
- **Status**: Fixed in code

### 3. **Route Ordering** ✅ VERIFIED
- **Problem**: Potential route conflicts in companies router
- **Status**: Routes are properly ordered

## Immediate Actions Required

### 1. **Deploy the Fixed Backend**
```bash
git add .
git commit -m "Fix CORS and API routing issues"
git push origin main
```

### 2. **Wait for Render Deployment**
- Monitor the backend service deployment in Render dashboard
- Check logs for the new debug messages

### 3. **Test the Backend Endpoints**
After deployment, test these endpoints:

#### Test CORS Configuration
```bash
curl https://multitenant-backend-mlap.onrender.com/test-cors
```

#### Test Companies Router
```bash
curl https://multitenant-backend-mlap.onrender.com/test-companies-router
```

#### Test Company Endpoint (with a valid company ID)
```bash
curl https://multitenant-backend-mlap.onrender.com/api/companies/comp_3e6dab46/public
```

## Debugging Steps

### 1. **Check Backend Logs in Render**
Look for these messages:
```
🔧 Including API routers...
✅ Companies router included
🔍 Company verification request for company_id: comp_3e6dab46
```

### 2. **Check Frontend Console**
The enhanced logging will show:
- API URL being called
- Response status and headers
- Detailed error information

### 3. **Verify Environment Variables**
In Render dashboard, ensure:
- `ENVIRONMENT=production`
- `CORS_ORIGINS=https://multitenant-frontend.onrender.com,http://localhost:3000,http://127.0.0.1:3000`

## Expected Behavior After Fix

### ✅ **Backend Startup**
```
🚀 Starting Multi-Tenant Document Management System
🔍 Environment detection: ENVIRONMENT=production, IS_PRODUCTION=True, IS_DEVELOPMENT=False
🔧 CORS Origins from environment variable: ['https://multitenant-frontend.onrender.com', 'http://localhost:3000', 'http://127.0.0.1:3000']
🔧 Including API routers...
✅ Companies router included
```

### ✅ **API Requests**
```
🔍 CORS Middleware - Origin: https://multitenant-frontend.onrender.com, Environment: production, IS_PRODUCTION: True
✅ Origin https://multitenant-frontend.onrender.com is in allowed CORS origins
🔍 Company verification request for company_id: comp_3e6dab46
✅ Company found: Company Name (ID: comp_3e6dab46)
```

### ✅ **Frontend Console**
```
🔍 Fetching company: comp_3e6dab46
🌐 API URL: https://multitenant-backend-mlap.onrender.com/api/companies/comp_3e6dab46/public
📥 Response status: 200
✅ Company data received: {id: "comp_3e6dab46", name: "Company Name", ...}
```

## If Issues Persist

### 1. **Check Render Service Status**
- Verify the backend service is running
- Check for any deployment errors
- Ensure environment variables are set correctly

### 2. **Test Backend Health**
```bash
curl https://multitenant-backend-mlap.onrender.com/health
```

### 3. **Check Database Connection**
```bash
curl https://multitenant-backend-mlap.onrender.com/api/system/status
```

### 4. **Verify Company Exists**
The company ID `comp_3e6dab46` must exist in the management database.

## Common Issues and Solutions

### **Issue**: Still getting HTML responses
**Solution**: The backend might not be properly deployed. Check Render logs and redeploy.

### **Issue**: CORS errors persist
**Solution**: Verify the `ENVIRONMENT=production` variable is set in Render.

### **Issue**: Company not found
**Solution**: Check if the company ID exists in the database. You may need to create a test company first.

### **Issue**: Database connection errors
**Solution**: Verify the database connection strings in Render environment variables.

## Next Steps

1. **Deploy the fixes** to Render
2. **Monitor the deployment** logs
3. **Test the endpoints** using the curl commands above
4. **Check the frontend** to see if company verification works
5. **Report back** with any remaining issues

## Support Commands

If you need to test locally:
```bash
# Test CORS configuration
python -c "
import os
os.environ['ENVIRONMENT'] = 'production'
os.environ['CORS_ORIGINS'] = 'https://multitenant-frontend.onrender.com,http://localhost:3000,http://127.0.0.1:3000'
from backend.app.config import get_cors_origins, ENVIRONMENT, IS_PRODUCTION
print(f'Environment: {ENVIRONMENT}')
print(f'Is Production: {IS_PRODUCTION}')
print(f'CORS Origins: {get_cors_origins()}')
"
```
