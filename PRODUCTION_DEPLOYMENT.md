# Production Deployment Guide for Render

This guide explains how to deploy the Multi-Tenant Document Management System to production on Render.

## 🚀 Production Configuration

### Backend Configuration
- **Environment**: Forced to `production`
- **CORS Origins**: Only `https://multitenant-frontend.onrender.com`
- **Database**: Production PostgreSQL on Render
- **Security**: Production-grade JWT tokens

### Frontend Configuration
- **Environment**: `production`
- **API URL**: `https://multitenant-backend-mlap.onrender.com`
- **Build**: Production build with source maps disabled
- **Debug**: Disabled for production

## 🔧 Environment Variables

### Backend (render.yaml)
```yaml
envVars:
  - key: ENVIRONMENT
    value: "production"
  - key: CORS_ORIGINS
    value: "https://multitenant-frontend.onrender.com"
  - key: APP_URL
    value: "https://multitenant-frontend.onrender.com"
  - key: NODE_ENV
    value: "production"
```

### Frontend (render.yaml)
```yaml
envVars:
  - key: REACT_APP_API_URL
    value: https://multitenant-backend-mlap.onrender.com
  - key: NODE_ENV
    value: "production"
  - key: REACT_APP_ENVIRONMENT
    value: "production"
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] All environment variables set in render.yaml
- [ ] Backend CORS configured for production only
- [ ] Frontend API URL points to production backend
- [ ] Database connections configured for production
- [ ] Security settings reviewed

### Deployment
- [ ] Backend deployed and healthy
- [ ] Frontend built with production configuration
- [ ] CORS headers properly set
- [ ] All API endpoints responding correctly
- [ ] Frontend can communicate with backend

### Post-Deployment
- [ ] Test all major features
- [ ] Verify CORS is working
- [ ] Check authentication flows
- [ ] Test document upload/download
- [ ] Monitor error logs

## 🧪 Testing Production APIs

### Health Check
```bash
curl -X GET 'https://multitenant-backend-mlap.onrender.com/health'
```

### CORS Test
```bash
curl -X GET 'https://multitenant-backend-mlap.onrender.com/test-cors' \
  -H 'Origin: https://multitenant-frontend.onrender.com'
```

### Authentication Test
```bash
curl -X POST 'https://multitenant-backend-mlap.onrender.com/test-login'
```

## 🔍 Troubleshooting

### Common Issues
1. **CORS Errors**: Check CORS_ORIGINS environment variable
2. **Environment Detection**: Verify ENVIRONMENT is set to "production"
3. **API Connection**: Ensure frontend API_BASE_URL is correct
4. **Database Connection**: Check database URLs in environment variables

### Debug Endpoints
- `/health` - Basic health check
- `/test-cors` - CORS configuration test
- `/test-auth` - Authentication test
- `/test-login` - Login flow test

## 📊 Monitoring

### Backend Logs
- Environment detection logs
- CORS middleware logs
- API request/response logs
- Database connection logs

### Frontend Logs
- API configuration logs
- Request/response logs
- Error handling logs

## 🔐 Security Considerations

### Production Security
- JWT tokens with proper expiration
- CORS restricted to production frontend only
- Database connections secured
- Environment variables properly set
- Source maps disabled in production

### Access Control
- Role-based access control (RBAC)
- Company-level data isolation
- Document-level permissions
- Audit logging enabled

## 📈 Performance Optimization

### Backend
- Database connection pooling
- CORS headers optimized
- Response caching where appropriate
- Efficient database queries

### Frontend
- Production build optimization
- Source maps disabled
- Debug logging disabled
- Efficient API calls

## 🚨 Emergency Procedures

### Rollback
1. Revert to previous deployment
2. Check environment variables
3. Verify database connections
4. Test critical functionality

### Debug Mode
1. Enable debug logging temporarily
2. Check CORS configuration
3. Verify API endpoints
4. Monitor error logs

---

**Last Updated**: August 22, 2025
**Version**: 2.0.0
**Environment**: Production (Render)
