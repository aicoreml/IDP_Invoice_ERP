"""
IDP_App - Intelligent Document Processing Application
Main entry point with Gradio UI
"""

import os
import sys
from typing import List, Dict, Any, Optional
# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from typing import List, Tuple, Optional
from pathlib import Path
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
from document_processor import DocumentProcessor
from ocr_processor import OCRProcessor
from vector_store import VectorStore
from llm_client import OllamaClient

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "minimax-m2.5:cloud")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", "./data/processed"))

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

class IDPApplication:
    """Main IDP Application class."""

    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.ocr_processor = OCRProcessor()
        self.vector_store = VectorStore(
            persist_dir=CHROMA_PERSIST_DIR,
            embedding_model=EMBEDDING_MODEL
        )
        self.llm_client = OllamaClient(host=OLLAMA_HOST, model=OLLAMA_MODEL)
        self.uploaded_docs = []

    def process_document(self, file_path: str, progress=gr.Progress()) -> Tuple[str, dict]:
        """Process a single document."""
        progress(0.1, desc="Dokument wird geladen...")

        # Determine file type
        file_ext = Path(file_path).suffix.lower()

        progress(0.3, desc="Text wird extrahiert...")

        if file_ext in ['.pdf']:
            # Check if scanned PDF
            text = self.doc_processor.process_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            # Use OCR for images
            text = self.ocr_processor.process_image(file_path)
        else:
            # Standard document processing
            text = self.doc_processor.process_file(file_path)

        progress(0.5, desc="Embeddings werden erstellt...")

        # Store in vector database
        doc_id = self.vector_store.add_document(
            text=text,
            metadata={"source": file_path, "type": file_ext}
        )

        self.uploaded_docs.append({
            "id": doc_id,
            "path": file_path,
            "text_preview": text[:500] + "..." if len(text) > 500 else text
        })

        progress(1.0, desc="Fertig!")

        return f"Verarbeitet: {Path(file_path).name}", {"doc_id": doc_id, "chars": len(text)}
    
    def search_documents(self, query: str, top_k: int = 5) -> List[dict]:
        """Search documents using semantic search."""
        results = self.vector_store.search(query, top_k=top_k)
        return results
    
    def chat_with_documents(self, query: str, top_k: int = 5) -> str:
        """Chat with documents using RAG."""
        # Get relevant documents
        context_docs = self.vector_store.search(query, top_k=top_k)

        if not context_docs:
            return "Keine relevanten Dokumente gefunden. Bitte laden Sie zuerst einige Dokumente hoch."

        # Build context
        context = "\n\n".join([
            f"[Quelle: {doc['metadata']['source']}]\n{doc['text']}"
            for doc in context_docs
        ])

        # Generate response
        response = self.llm_client.chat(query, context=context)
        return response

    def extract_structured_data(self, file_path: str, template: str) -> dict:
        """Extract structured data from document."""
        from extractors import get_extractor

        extractor = get_extractor(template)
        result = extractor.extract(file_path)
        return result

    def get_document_list(self) -> List[str]:
        """Get list of uploaded documents."""
        return [doc["path"] for doc in self.uploaded_docs]

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get vector database storage statistics."""
        stats = self.vector_store.get_stats()

        # Check if persistence directory exists and has data
        persist_path = Path(self.vector_store.persist_dir)
        db_exists = persist_path.exists()
        db_size = sum(f.stat().st_size for f in persist_path.glob('**/*') if f.is_file()) if db_exists else 0

        return {
            **stats,
            "persistence_enabled": True,
            "database_exists": db_exists,
            "database_path": str(persist_path.absolute()),
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "status": "✅ Persistent" if db_exists and db_size > 0 else "⚠️ Leer (Dokumente hinzufügen)"
        }

# Initialize application
app = IDPApplication()

# Gradio Interface
def create_interface():
    """Create Gradio interface."""

    with gr.Blocks(title="IDP_App - Intelligente Dokumentenverarbeitung") as interface:
        gr.Markdown("# IDP_App - Intelligente Dokumentenverarbeitung")
        gr.Markdown("Verarbeiten, durchsuchen und extrahieren Sie strukturierte Daten aus Dokumenten")

        with gr.Tab("📤 Hochladen"):
            with gr.Row():
                file_input = gr.File(label="Dokument hochladen", file_types=[".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".tiff"])
            with gr.Row():
                upload_btn = gr.Button("Dokument verarbeiten")
                upload_status = gr.Textbox(label="Status")
                upload_info = gr.JSON(label="Dokumenteninfo")

            upload_btn.click(
                fn=app.process_document,
                inputs=[file_input],
                outputs=[upload_status, upload_info]
            )

        with gr.Tab("🔍 Suchen"):
            with gr.Row():
                search_input = gr.Textbox(label="Suchanfrage")
                search_top_k = gr.Slider(1, 20, value=5, label="Anzahl Ergebnisse")
            search_btn = gr.Button("Suchen")
            search_results = gr.JSON(label="Ergebnisse")

            search_btn.click(
                fn=app.search_documents,
                inputs=[search_input, search_top_k],
                outputs=[search_results]
            )

        with gr.Tab("💬 Chat"):
            with gr.Row():
                chat_input = gr.Textbox(label="Stellen Sie eine Frage zu Ihren Dokumenten")
            chat_btn = gr.Button("Fragen")
            chat_response = gr.Textbox(label="Antwort", lines=10)

            chat_btn.click(
                fn=app.chat_with_documents,
                inputs=[chat_input],
                outputs=[chat_response]
            )

        with gr.Tab("📋 Extrahieren"):
            with gr.Row():
                extract_file = gr.File(label="Dokument zur Extraktion")
                extract_template = gr.Dropdown(
                    choices=["invoice", "receipt", "id_document", "custom"],
                    value="invoice",
                    label="Extraktionsvorlage"
                )
            extract_btn = gr.Button("Daten extrahieren")
            extract_results = gr.JSON(label="Extrahierte Daten")

            extract_btn.click(
                fn=app.extract_structured_data,
                inputs=[extract_file, extract_template],
                outputs=[extract_results]
            )

        with gr.Tab("📁 Dokumente"):
            doc_list = gr.List(label="Hochgeladene Dokumente")
            refresh_btn = gr.Button("Liste aktualisieren")

            # Persistence status
            with gr.Accordion("📊 Speicherstatus", open=False):
                storage_stats = gr.JSON(label="Vektordatenbank Statistik")
                refresh_stats_btn = gr.Button("Statistik aktualisieren")
                stats_message = gr.Textbox(label="Status")

            def safe_get_stats():
                """Get storage stats with error handling."""
                try:
                    stats = app.get_storage_stats()
                    return stats, "✅ Datenbank bereit"
                except Exception as e:
                    return {"error": str(e)}, f"⚠️ Fehler: {str(e)}"

            refresh_btn.click(
                fn=app.get_document_list,
                outputs=[doc_list]
            )

            refresh_stats_btn.click(
                fn=safe_get_stats,
                outputs=[storage_stats, stats_message]
            )

    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(server_name="0.0.0.0", server_port=7862, root_path="/idp-de")