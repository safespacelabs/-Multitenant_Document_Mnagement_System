#!/bin/bash

# Railway Deployment Script for Multi-Tenant Document Management System
# This script helps automate the Railway deployment process

set -e

echo "🚀 Railway Deployment Script"
echo "================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

echo "📋 Select deployment option:"
echo "1. Deploy Backend Only"
echo "2. Deploy Frontend Only" 
echo "3. Deploy Both (Recommended)"
read -p "Enter your choice (1-3): " choice

deploy_backend() {
    echo "🔧 Deploying Backend Service..."
    cd backend
    
    # Create project if it doesn't exist
    if ! railway status &> /dev/null; then
        echo "📝 Creating new Railway project for backend..."
        railway create multitenant-backend
    fi
    
    echo "🚀 Deploying backend..."
    railway up
    
    echo "✅ Backend deployed successfully!"
    echo "📋 Don't forget to set environment variables:"
    echo "   - DATABASE_URL"
    echo "   - SECRET_KEY"
    echo "   - AWS credentials"
    echo "   - GROQ_API_KEY"
    echo "   - Email settings"
    
    cd ..
}

deploy_frontend() {
    echo "🎨 Deploying Frontend Service..."
    cd frontend
    
    # Create project if it doesn't exist
    if ! railway status &> /dev/null; then
        echo "📝 Creating new Railway project for frontend..."
        railway create multitenant-frontend
    fi
    
    echo "🚀 Deploying frontend..."
    railway up
    
    echo "✅ Frontend deployed successfully!"
    echo "📋 Don't forget to set environment variables:"
    echo "   - REACT_APP_API_URL (backend URL)"
    
    cd ..
}

case $choice in
    1)
        deploy_backend
        ;;
    2)
        deploy_frontend
        ;;
    3)
        deploy_backend
        echo ""
        deploy_frontend
        ;;
    *)
        echo "❌ Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment completed!"
echo "📖 Check RAILWAY_DEPLOYMENT_GUIDE.md for detailed setup instructions"
echo "🔧 Remember to configure environment variables in Railway dashboard"