#!/bin/bash

# Render.com Deployment Helper Script
# This script prepares your project for Render.com deployment

set -e

echo "🚀 Render.com Deployment Preparation"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ render.yaml not found. Make sure you're in the project root."
    exit 1
fi

echo "✅ Found render.yaml configuration"

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 You have uncommitted changes. Committing them..."
    git add .
    git commit -m "Add Render.com deployment configuration"
else
    echo "✅ Working directory is clean"
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin development

echo ""
echo "🎉 Ready for Render.com deployment!"
echo ""
echo "Next steps:"
echo "1. Go to https://render.com and sign up with GitHub"
echo "2. Create a new Web Service from your GitHub repo"
echo "3. Follow the RENDER_DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
echo "Repository: safespacelabs/-Multitenant_Document_Mnagement_System"
echo "Branch: development" 
echo "Backend Root Directory: backend"
echo "Frontend Root Directory: frontend"
echo ""
echo "📖 Check RENDER_DEPLOYMENT_GUIDE.md for complete setup instructions"