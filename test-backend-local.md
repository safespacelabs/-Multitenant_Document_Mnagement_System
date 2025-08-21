# Testing Backend from Local Machine

## Current Issue
Your frontend is running locally but trying to call the production backend. The API calls are failing because they're not reaching the correct endpoint.

## Quick Test Commands

### 1. **Test Backend Health (from your local machine)**
```bash
curl https://multitenant-backend-mlap.onrender.com/health
```

### 2. **Test CORS Configuration**
```bash
curl https://multitenant-backend-mlap.onrender.com/test-cors
```

### 3. **Test Companies Router**
```bash
curl https://multitenant-backend-mlap.onrender.com/test-companies-router
```

### 4. **Test Company Endpoint (with the company ID you're using)**
```bash
curl https://multitenant-backend-mlap.onrender.com/api/companies/comp_3e6dab46/public
```

## Expected Results

### ✅ **Health Check**
```json
{"status": "healthy", "message": "Backend is running"}
```

### ✅ **CORS Test**
```json
{
  "message": "CORS is working",
  "environment": "production",
  "is_production": true,
  "cors_origins": ["https://multitenant-backend-mlap.onrender.com", "http://localhost:3000", "http://127.0.0.1:3000"]
}
```

### ✅ **Companies Router Test**
```json
{
  "message": "Companies router is working!",
  "endpoints": ["/api/companies/", "/api/companies/public", "/api/companies/{company_id}/public"],
  "status": "active"
}
```

### ✅ **Company Endpoint Test**
```json
{
  "id": "comp_3e6dab46",
  "name": "Company Name",
  "email": "company@example.com",
  "database_url": "postgresql://...",
  "is_active": true
}
```

## If Backend Tests Fail

### **Issue**: Backend not responding
**Solution**: The backend might not be deployed or there's a deployment issue.

### **Issue**: Company not found
**Solution**: The company ID `comp_3e6dab46` doesn't exist in the database.

### **Issue**: CORS errors
**Solution**: The backend environment variables might not be set correctly.

## Next Steps

1. **Run the curl commands above** to test the backend
2. **Check the frontend console** for the new debug information
3. **Verify the API URLs** are correct (should show full production URLs)
4. **Report back** with the results of the curl commands

## Frontend Console Expected Output

After the fix, you should see:
```
🔧 API Configuration Debug:
  NODE_ENV: development
  API_BASE_URL: https://multitenant-backend-mlap.onrender.com
  Current location: http://localhost:3000/...

🔍 Fetching company: comp_3e6dab46
🌐 API URL: https://multitenant-backend-mlap.onrender.com/api/companies/comp_3e6dab46/public
🌐 Full URL being called: https://multitenant-backend-mlap.onrender.com/api/companies/comp_3e6dab46/public
📥 Response status: 200
✅ Company data received: {id: "comp_3e6dab46", ...}
```

## Troubleshooting

If you still get HTML responses:
1. **Check if the backend is deployed** in Render
2. **Verify the company ID exists** in the database
3. **Check Render logs** for any deployment errors
4. **Ensure environment variables** are set correctly in Render
