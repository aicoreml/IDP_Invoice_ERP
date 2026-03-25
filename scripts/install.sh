#!/bin/bash
# IDP_App Installation Script

set -e

echo "=== IDP_App Installation ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Tesseract (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "Checking Tesseract installation..."
    if ! command -v tesseract &> /dev/null; then
        echo "Tesseract not found. Installing via Homebrew..."
        brew install tesseract
        brew install tesseract-lang
    else
        echo "Tesseract already installed: $(tesseract --version | head -1)"
    fi
    
    # Install poppler for pdf2image
    if ! command -v pdftoppm &> /dev/null; then
        echo "Installing poppler for PDF processing..."
        brew install poppler
    fi
fi

# Check Ollama
echo ""
echo "Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama not found. Please install from: https://ollama.ai"
    echo "After installation, run: ollama pull llama3.2"
else
    echo "Ollama installed: $(ollama --version)"
    
    # Pull default model
    echo ""
    read -p "Pull default model (llama3.2)? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama pull llama3.2
    fi
fi

# Create directories
echo ""
echo "Creating data directories..."
mkdir -p data/uploads
mkdir -p data/processed
mkdir -p data/chroma_db
mkdir -p docs/sample_documents
mkdir -p docs/templates

# Copy env example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file if needed"
echo "2. Run: ./run.sh"
echo "3. Open browser: http://localhost:7860"