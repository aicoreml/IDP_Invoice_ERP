"""
OCR Processor - Tesseract and PaddleOCR for scanned documents
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Process images and scanned documents using OCR."""
    
    def __init__(self, tesseract_lang: str = "eng+deu"):
        """
        Initialize OCR processor.
        
        Args:
            tesseract_lang: Languages for Tesseract (e.g., "eng+deu" for English+German)
        """
        self.tesseract_lang = tesseract_lang
        self.tesseract_available = self._check_tesseract()
        self.paddleocr_available = self._check_paddleocr()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            logger.warning("Tesseract not available. Install with: brew install tesseract")
            return False
    
    def _check_paddleocr(self) -> bool:
        """Check if PaddleOCR is available."""
        try:
            from paddleocr import PaddleOCR
            return True
        except:
            logger.warning("PaddleOCR not available. Install with: pip install paddleocr")
            return False
    
    def process_image(self, file_path: str, engine: str = "auto") -> str:
        """
        Process image with OCR.
        
        Args:
            file_path: Path to image file
            engine: OCR engine ("tesseract", "paddleocr", or "auto")
        
        Returns:
            Extracted text
        """
        # Convert PDF to images if needed
        if Path(file_path).suffix.lower() == '.pdf':
            return self._process_pdf_scanned(file_path, engine)
        
        # Choose engine
        if engine == "auto":
            engine = "paddleocr" if self.paddleocr_available else "tesseract"
        
        if engine == "paddleocr" and self.paddleocr_available:
            return self._process_with_paddleocr(file_path)
        elif self.tesseract_available:
            return self._process_with_tesseract(file_path)
        else:
            raise RuntimeError("No OCR engine available")
    
    def _process_with_tesseract(self, file_path: str) -> str:
        """Process image with Tesseract OCR."""
        import pytesseract
        from PIL import Image
        
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang=self.tesseract_lang)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return ""
    
    def _process_with_paddleocr(self, file_path: str) -> str:
        """Process image with PaddleOCR."""
        from paddleocr import PaddleOCR
        
        try:
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            result = ocr.ocr(file_path, cls=True)
            
            # Extract text from result
            text_lines = []
            for page in result:
                if page:
                    for line in page:
                        if line and len(line) >= 2:
                            text_lines.append(line[1][0])  # Extract text
            
            return "\n".join(text_lines)
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return ""
    
    def _process_pdf_scanned(self, file_path: str, engine: str = "auto") -> str:
        """Process scanned PDF by converting to images first."""
        from pdf2image import convert_from_path
        import tempfile
        
        try:
            # Convert PDF to images
            images = convert_from_path(file_path)
            all_text = []
            
            for i, img in enumerate(images):
                # Save image temporarily
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    img.save(tmp.name)
                    
                    # Process with OCR
                    text = self.process_image(tmp.name, engine)
                    if text:
                        all_text.append(f"--- Page {i+1} ---\n{text}")
                    
                    # Clean up
                    os.unlink(tmp.name)
            
            return "\n\n".join(all_text)
        
        except Exception as e:
            logger.error(f"Error processing scanned PDF: {e}")
            return ""
    
    def process_with_layout(self, file_path: str) -> Dict[str, Any]:
        """
        Process image with layout analysis.
        
        Returns:
            Dictionary with text, regions, and bounding boxes
        """
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            result = ocr.ocr(file_path, cls=True)
            
            regions = []
            full_text = []
            
            for page in result:
                if page:
                    for line in page:
                        if line and len(line) >= 2:
                            box = line[0]  # Bounding box
                            text = line[1][0]
                            confidence = line[1][1]
                            
                            regions.append({
                                "text": text,
                                "bbox": box,
                                "confidence": confidence
                            })
                            full_text.append(text)
            
            return {
                "text": "\n".join(full_text),
                "regions": regions,
                "page_count": len(result) if result else 0
            }
        
        except Exception as e:
            logger.error(f"Layout analysis error: {e}")
            return {"text": "", "regions": [], "page_count": 0}
    
    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract tables from image or PDF."""
        tables = []
        
        try:
            import camelot
            
            if Path(file_path).suffix.lower() == '.pdf':
                # Extract tables from PDF
                tables = camelot.read_pdf(file_path, pages='all')
                return [table.df.to_dict() for table in tables]
        
        except ImportError:
            logger.warning("Camelot not available. Install with: pip install camelot-py")
        
        except Exception as e:
            logger.error(f"Table extraction error: {e}")
        
        return tables