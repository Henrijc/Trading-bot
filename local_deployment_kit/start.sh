#!/bin/bash

# AI Crypto Trading Coach - Quick Start Script
# This script helps you get started quickly with the local deployment

echo "🚀 AI Crypto Trading Coach - Local Deployment Setup"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Setting up environment configuration..."
    if [ -f ".env.backend.example" ]; then
        cp .env.backend.example .env
        echo "✅ Environment template copied to .env"
        echo "⚠️  IMPORTANT: Edit .env file and add your API keys before continuing!"
        echo ""
        echo "Required API keys:"
        echo "  - LUNO_API_KEY (from https://www.luno.com/wallet/security/api_keys)"
        echo "  - LUNO_SECRET"
        echo "  - GEMINI_API_KEY (from https://makersuite.google.com/app/apikey)"
        echo ""
        read -p "Have you added your API keys to .env? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Please edit .env file first, then run this script again."
            exit 1
        fi
    else
        echo "❌ Error: .env.backend.example not found"
        exit 1
    fi
else
    echo "✅ Environment file exists"
fi

# Check if frontend .env exists
if [ ! -f "app/frontend/.env" ]; then
    if [ -f ".env.frontend.example" ]; then
        cp .env.frontend.example app/frontend/.env
        echo "✅ Frontend environment configured"
    fi
fi

# Check if Freqtrade config exists
if [ ! -f "app/freqtrade/config.json" ]; then
    if [ -f "config.luno.example.json" ]; then
        cp config.luno.example.json app/freqtrade/config.json
        echo "✅ Freqtrade configuration set up"
    fi
fi

echo ""
echo "🐳 Starting AI Crypto Trading Coach services..."
echo "This may take a few minutes on first run..."
echo ""

# Start the services
docker-compose up --build

echo ""
echo "🎉 Setup complete! Your AI Crypto Trading Coach is now running:"
echo "   Dashboard: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo ""
echo "To stop the services:"
echo "   Press Ctrl+C, then run: docker-compose down"