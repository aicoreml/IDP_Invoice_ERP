#!/bin/bash
# IDP_App - Intelligente Dokumentenverarbeitung
# Startskript für die Gradio-Anwendung

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  IDP_App - Intelligente Dokumentenverarbeitung"
echo "========================================"
echo ""

# Virtuelle Umgebung aktivieren
echo "Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# Ollama überprüfen
echo "Überprüfe Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama nicht gefunden. Bitte installieren von: https://ollama.ai"
    exit 1
fi

# Prüfen ob Ollama läuft
if ! curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo "⚠️  Ollama läuft nicht. Starte Ollama..."
    ollama serve &
    sleep 3
fi

# Nach erforderlichem Modell suchen
echo "Suche nach erforderlichem Modell (minimax-m2.5:cloud)..."
if ! ollama list | grep -q "minimax-m2.5"; then
    echo "⚠️  minimax-m2.5:cloud Modell nicht lokal gefunden."
    echo "Hinweis: Dies ist ein Cloud-Modell - stellen Sie sicher, dass Ollama für Cloud-Zugriff konfiguriert ist"
fi

# Datenverzeichnisse erstellen
echo "Erstelle Datenverzeichnisse..."
mkdir -p data/uploads
mkdir -p data/processed
mkdir -p data/chroma_db

echo ""
echo "Starte IDP_App auf http://localhost:7862"
echo "Drücken Sie Strg+C zum Stoppen"
echo ""

# Gradio-App ausführen
python app/main.py
