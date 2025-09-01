#!/bin/bash
# Quick Production Deploy Script

echo "🚀 SmartLearn Production Deploy"

# 1. Build distribution
echo "📦 Building distribution..."
mkdir -p dist
cp templates/index.html dist/
cp -r static dist/

# 2. Update HTML for production
echo "🔧 Updating paths for production..."
# sed commands would go here to update asset paths

# 3. Deploy to Firebase
echo "🔥 Deploying to Firebase..."
firebase deploy

echo "✅ Production deployment complete!"
echo "🌐 Your app is live at: https://smartlearn-ai-90942.web.app"
