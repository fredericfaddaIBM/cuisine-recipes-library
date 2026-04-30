#!/bin/bash

# Recipe Library - Docker Startup Script
# This script builds and starts the Docker container

echo "🍳 Recipe Library - Docker Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi

# Check if Ollama is running
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Warning: Cannot connect to Ollama at http://localhost:11434"
    echo "   Make sure Ollama is running before processing images"
    echo ""
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p images recipes logs json-extract embeddings templates static

# Build and start the container
echo ""
echo "Building and starting Docker container..."
docker-compose up --build

# Note: The script will keep running and show logs
# Press Ctrl+C to stop the container

# Made with Bob
