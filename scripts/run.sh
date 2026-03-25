#!/bin/bash
# IDP_App Run Script

set -e

cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
export OLLAMA_HOST=${OLLAMA_HOST:-"localhost:11434"}
export OLLAMA_MODEL=${OLLAMA_MODEL:-"llama3.2"}
export EMBEDDING_MODEL=${EMBEDDING_MODEL:-"all-MiniLM-L6-v2"}
export CHROMA_PERSIST_DIR=${CHROMA_PERSIST_DIR:-"./data/chroma_db"}
export GRADIO_SERVER_NAME=${GRADIO_SERVER_NAME:-"0.0.0.0"}
export GRADIO_SERVER_PORT=${GRADIO_SERVER_PORT:-"7860"}

# Check Ollama
echo "Checking Ollama connection..."
if curl -s "http://${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
    echo "✓ Ollama connected at http://${OLLAMA_HOST}"
else
    echo "⚠ Warning: Cannot connect to Ollama at http://${OLLAMA_HOST}"
    echo "  Make sure Ollama is running: ollama serve"
fi

# Run application
echo ""
echo "Starting IDP_App..."
echo "Open browser: http://localhost:${GRADIO_SERVER_PORT}"
echo ""

python app/main.py