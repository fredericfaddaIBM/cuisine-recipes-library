#!/bin/bash

# Security Fixes Installation Script
# This script installs the required dependencies for the security fixes

echo "🔒 Installing Security Fixes for Recipe Library"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"
echo ""

# Install dependencies
echo "Installing required dependencies..."
echo ""

# Check if pip3 is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 not found. Please install Python 3 and pip3."
    exit 1
fi

# Install from requirements.txt
echo "Installing packages from requirements.txt..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies"
    exit 1
fi

echo ""

# Check for libmagic on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Checking for libmagic (required for python-magic)..."
    if command -v brew &> /dev/null; then
        if brew list libmagic &> /dev/null; then
            echo "✅ libmagic is already installed"
        else
            echo "⚠️  libmagic not found. Installing via Homebrew..."
            brew install libmagic
            if [ $? -eq 0 ]; then
                echo "✅ libmagic installed successfully"
            else
                echo "⚠️  Warning: Could not install libmagic. File validation will use PIL only."
            fi
        fi
    else
        echo "⚠️  Homebrew not found. Please install libmagic manually:"
        echo "   brew install libmagic"
        echo "   File validation will use PIL only for now."
    fi
    echo ""
fi

# Test python-magic import
echo "Testing python-magic installation..."
python3 -c "import magic; print('✅ python-magic is working')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: python-magic import failed. File validation will use PIL only."
    echo "   This is not critical, but for better security, install libmagic:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   brew install libmagic"
    else
        echo "   sudo apt-get install libmagic1  # On Ubuntu/Debian"
    fi
fi

echo ""
echo "================================================"
echo "✅ Security fixes installation complete!"
echo ""
echo "Next steps:"
echo "1. Review the changes in docs/SECURITY-FIXES-IMPLEMENTATION.md"
echo "2. Test the application: python3 app.py"
echo "3. Run security tests (see documentation)"
echo ""
echo "The following security fixes are now active:"
echo "  ✅ Path traversal protection"
echo "  ✅ File upload content validation"
echo "  ✅ Proper error handling"
echo ""
echo "For more information, see:"
echo "  - docs/SECURITY-FIXES-IMPLEMENTATION.md"
echo "  - docs/SECURITY-REVIEW.md"
echo ""

# Made with Bob
