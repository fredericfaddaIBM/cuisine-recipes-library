#!/bin/bash

# Recipe Library - Container Startup Script
# This script builds and starts the container (supports Docker and Podman)

echo "🍳 Recipe Library - Container Setup"
echo "===================================="
echo ""

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    COMPOSE_CMD="podman-compose"
    echo "✅ Using Podman"
    
    # Check if Podman machine is running (macOS/Windows)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Checking Podman machine status..."
        if ! podman machine list 2>/dev/null | grep -q "Currently running"; then
            echo "⚠️  Podman machine is not running"
            echo ""
            echo "Starting Podman machine..."
            
            # Check if machine exists
            if ! podman machine list 2>/dev/null | grep -q "podman-machine-default"; then
                echo "Initializing Podman machine (this may take a few minutes)..."
                podman machine init
            fi
            
            echo "Starting Podman machine..."
            podman machine start
            
            if [ $? -eq 0 ]; then
                echo "✅ Podman machine started successfully"
            else
                echo "❌ Failed to start Podman machine"
                echo "Please run manually: podman machine start"
                exit 1
            fi
        else
            echo "✅ Podman machine is running"
        fi
    fi
    
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    COMPOSE_CMD="docker-compose"
    echo "✅ Using Docker"
else
    echo "❌ Error: Neither Docker nor Podman is installed"
    echo "Please install Docker or Podman"
    exit 1
fi

# Check if compose is available
if ! command -v $COMPOSE_CMD &> /dev/null; then
    echo "❌ Error: $COMPOSE_CMD is not installed"
    if [ "$CONTAINER_CMD" = "podman" ]; then
        echo "Please install podman-compose: pip3 install podman-compose"
    else
        echo "Please install docker-compose"
    fi
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
echo "Building and starting container with $COMPOSE_CMD..."
$COMPOSE_CMD up --build

# Note: The script will keep running and show logs
# Press Ctrl+C to stop the container

# Made with Bob
