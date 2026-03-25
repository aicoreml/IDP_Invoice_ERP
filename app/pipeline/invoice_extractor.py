"""
German Invoice Extraction Pipeline
Extracts structured data from German invoices using LLM-powered extraction
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.config import PipelineConfig, get_config
from document_processor import DocumentProcessor
from ocr_processor import OCRProcessor
from llm_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ExtractedInvoice:
    """Represents an extracted German invoice."""
    # File info
    source_file: str
    extraction_date: str
    processing_time_ms: float

    # Invoice header
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    delivery_date: Optional[str] = None

    # Vendor (Lieferant)
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None  # Steuernummer / USt-IdNr
    vendor_vat_id: Optional[str] = None
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None

    # Customer (Käufer)
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_tax_id: Optional[str] = None
    customer_vat_id: Optional[str] = None
    vendor_number: Optional[str] = None  # Kundennummer / Vendor number (for utility bills)

    # Line items
    line_items: List[Dict[str, Any]] = None

    # Totals
    subtotal: Optional[float] = None  # Nettobetrag
    tax_rate: Optional[float] = None  # Steuersatz (19%, 7%, etc.)
    tax_amount: Optional[float] = None  # Steuerbetrag
    total: Optional[float] = None  # Gesamtbetrag (Brutto)
    discount: Optional[float] = None  # Rabatt / Skonto

    # Payment
    currency: str = "EUR"
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    bank_account: Optional[str] = None
    bank_code: Optional[str] = None  # BLZ
    iban: Optional[str] = None
    bic: Optional[str] = None
    payment_account: Optional[str] = None  # Konto Zahlbar an (for Swiss bills)
    reference_number: Optional[str] = None  # Referenz (for Swiss bills)

    # Additional German-specific fields
    invoice_type: Optional[str] = None  # Rechnung, Gutschrift, Abschlagsrechnung, etc.
    tax_exempt_reason: Optional[str] = None  # Steuerbefreiung (Kleinunternehmer, etc.)
    reverse_charge: bool = False  # Steuerschuldnerschaft des Leistungsempfängers

    # Utility bill specific fields
    meter_number: Optional[str] = None  # Zählernummer
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None
    consumption_kwh: Optional[float] = None
    price_per_kwh: Optional[float] = None
    base_fee: Optional[float] = None

    # Validation
    validation_errors: List[str] = None
    validation_warnings: List[str] = None
    confidence_score: float = 0.0
    raw_text: str = ""
    
    def __post_init__(self):
        if self.line_items is None:
            self.line_items = []
        if self.validation_errors is None:
            self.validation_errors = []
        if self.validation_warnings is None:
            self.validation_warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)
    
    def is_valid(self) -> bool:
        """Check if invoice passed validation."""
        return len(self.validation_errors) == 0


class GermanInvoiceExtractor:
    """
    Extracts structured data from German invoices.
    
    Supports various German invoice types:
    - Standard Rechnung (Invoice)
    - Gutschrift (Credit Note)
    - Abschlagsrechnung (Partial Invoice)
    - Schlussrechnung (Final Invoice)
    - Kleinunternehmerrechnung (Small Business Invoice)
    """
    
    # German invoice extraction prompt
    EXTRACTION_PROMPT = """
Du bist ein Experte für die Extraktion von Daten aus deutschen Rechnungen.
Extrahiere ALLE folgenden Felder aus dem Rechnungstext. Antworte NUR mit gültigem JSON.

WICHTIGE HINWEISE ZUR ZAHLENFORMATIERUNG:
- Deutsche Zahlen verwenden Punkte als Tausendertrennzeichen und Komma als Dezimaltrennzeichen
- Beispiel: "40.000,00 EUR" bedeutet 40000.00 (vierzigtausend Euro)
- Beispiel: "7.600,00" bedeutet 7600.00
- Beispiel: "1.234,56" bedeutet 1234.56
- Konvertiere ALLE deutschen Zahlen in JSON als reine Zahlen OHNE Formatierung
- Verwende IMMER Punkt als Dezimaltrennzeichen im JSON: 40000.00 NICHT "40.000,00"
- Entferne Tausendertrennzeichen (Punkte bei deutschen Zahlen): 40.000 → 40000
- Alle Geldbeträge als Zahl ohne Währungssymbol im JSON

Datumsformat: YYYY-MM-DD (z.B. 2024-03-15)
Wenn ein Feld nicht gefunden wird, verwende null

ZU EXTRAHIERENDE FELDER:
{schema}

Rechnungstext:
{text}

Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text.
"""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or get_config()
        self.doc_processor = DocumentProcessor()
        self.ocr_processor = OCRProcessor() if self.config.ocr_enabled else None
        
        # Parse model name correctly (handle "minimax-m2.5:cloud" format)
        model_name = self.config.extraction_model
        ollama_host = "localhost:11434"
        
        self.llm_client = OllamaClient(
            host=ollama_host,
            model=model_name
        )
        
        # German invoice schema
        self.schema = {
            "invoice_number": "Rechnungsnummer (fortlaufende Nummer)",
            "invoice_date": "Rechnungsdatum (Ausstellungsdatum)",
            "due_date": "Fälligkeitsdatum",
            "delivery_date": "Lieferdatum / Leistungsdatum",
            "vendor_name": "Name des Verkäufers / Rechnungsstellers",
            "vendor_address": "Vollständige Adresse des Verkäufers",
            "vendor_tax_id": "Steuernummer des Verkäufers",
            "vendor_vat_id": "Umsatzsteuer-ID (USt-IdNr) des Verkäufers",
            "vendor_email": "E-Mail des Verkäufers",
            "vendor_phone": "Telefon des Verkäufers",
            "customer_name": "Name des Käufers / Rechnungsempfängers",
            "customer_address": "Adresse des Käufers",
            "vendor_number": "Kundennummer / Vendor number",
            "customer_tax_id": "Steuernummer des Käufers",
            "customer_vat_id": "Umsatzsteuer-ID des Käufers",
            "line_items": "Array von Positionen: [{beschreibung, menge, einzelpreis, betrag}]",
            "subtotal": "Nettobetrag (Summe vor Steuer)",
            "tax_rate": "Steuersatz in Prozent (z.B. 19 für 19%)",
            "tax_amount": "Steuerbetrag",
            "total": "Gesamtbetrag (Brutto, Endsumme)",
            "discount": "Rabatt oder Skonto",
            "currency": "Währung (meist EUR, CHF)",
            "payment_terms": "Zahlungsbedingungen",
            "payment_method": "Zahlungsmethode (Überweisung, Lastschrift, etc.)",
            "bank_account": "Kontonummer",
            "bank_code": "Bankleitzahl (BLZ)",
            "iban": "IBAN",
            "bic": "BIC/SWIFT",
            "payment_account": "Konto Zahlbar an (für Schweizer Rechnungen)",
            "reference_number": "Referenznummer / Referenz (z.B. QR-Rechnung Referenz)",
            "invoice_type": "Rechnungstyp (Rechnung, Gutschrift, Abschlagsrechnung, etc.)",
            "tax_exempt_reason": "Grund für Steuerbefreiung (z.B. §19 UStG Kleinunternehmer)",
            "reverse_charge": "Boolean: Steuerschuldnerschaft des Leistungsempfängers (true/false)",
            "meter_number": "Zählernummer (für Stromrechnungen)",
            "billing_period_start": "Abrechnungszeitraum von",
            "billing_period_end": "Abrechnungszeitraum bis",
            "consumption_kwh": "Verbrauch in kWh",
            "price_per_kwh": "Preis pro kWh",
            "base_fee": "Grundgebühr"
        }
    
    def extract(self, file_path: str) -> ExtractedInvoice:
        """
        Extract data from a German invoice.
        
        Args:
            file_path: Path to the invoice PDF or image
            
        Returns:
            ExtractedInvoice object with structured data
        """
        start_time = datetime.now()
        logger.info(f"Extrahiere Rechnung: {file_path}")
        
        # Initialize result
        result = ExtractedInvoice(
            source_file=str(file_path),
            extraction_date=start_time.isoformat(),
            processing_time_ms=0,
        )
        
        try:
            # Step 1: Extract text from document
            text = self._extract_text(file_path)
            result.raw_text = text
            
            if not text or len(text.strip()) < 50:
                result.validation_errors.append("Kein oder zu wenig Text im Dokument extrahiert")
                result.confidence_score = 0.0
                return result
            
            # Step 2: Use LLM for structured extraction
            extracted_data = self._extract_with_llm(text)
            
            # Step 3: Populate result object
            self._populate_result(result, extracted_data)
            
            # Step 4: Calculate confidence score
            result.confidence_score = self._calculate_confidence(result)
            
        except Exception as e:
            logger.error(f"Fehler bei der Extraktion: {e}")
            result.validation_errors.append(f"Extraktionsfehler: {str(e)}")
            result.confidence_score = 0.0
        
        # Calculate processing time
        end_time = datetime.now()
        result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(f"Extraktion abgeschlossen in {result.processing_time_ms:.0f}ms, "
                   f"Konfidenz: {result.confidence_score:.2f}")
        
        return result
    
    def _extract_text(self, file_path: str) -> str:
        """Extract text from document using appropriate method."""
        file_ext = Path(file_path).suffix.lower()
        
        # Try OCR for images or scanned PDFs
        if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            if self.ocr_processor:
                return self.ocr_processor.process_image(file_path)
        
        # Standard document processing
        try:
            return self.doc_processor.process_file(file_path)
        except Exception as e:
            logger.warning(f"Standard-Extraktion fehlgeschlagen: {e}")
            # Fallback to OCR for PDFs
            if self.ocr_processor and file_ext == '.pdf':
                try:
                    return self.ocr_processor.process_pdf(file_path)
                except Exception as ocr_error:
                    logger.error(f"OCR-Fallback fehlgeschlagen: {ocr_error}")
            return ""
    
    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """Extract structured data using LLM."""
        # Build prompt
        schema_str = json.dumps(self.schema, indent=2, ensure_ascii=False)
        prompt = self.EXTRACTION_PROMPT.format(schema=schema_str, text=text)

        try:
            # Call LLM with JSON output using chat method for better results
            response = self.llm_client.chat(
                message=prompt,
                system="Du bist ein Experte für die Extraktion von Daten aus deutschen Rechnungen. Antworte NUR mit gültigem JSON.",
                temperature=0.1,  # Low temperature for consistent extraction
            )

            # Parse JSON response
            return self._parse_json_response(response)

        except Exception as e:
            logger.error(f"LLM-Extraktion fehlgeschlagen: {e}")
            return {}
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        # Clean response - extract JSON block
        response = response.strip()
        
        # Try to find JSON in response
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response[start_idx:end_idx]
        else:
            json_str = response
        
        # Remove markdown code blocks if present
        json_str = json_str.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parsing fehlgeschlagen: {e}")
            logger.debug(f"Ungültiges JSON: {json_str[:500]}")
            return {}
    
    def _populate_result(self, result: ExtractedInvoice, data: Dict[str, Any]):
        """Populate result object with extracted data."""
        # Map extracted fields to result attributes
        field_mapping = {
            'invoice_number': 'invoice_number',
            'invoice_date': 'invoice_date',
            'due_date': 'due_date',
            'delivery_date': 'delivery_date',
            'vendor_name': 'vendor_name',
            'vendor_address': 'vendor_address',
            'vendor_tax_id': 'vendor_tax_id',
            'vendor_vat_id': 'vendor_vat_id',
            'vendor_email': 'vendor_email',
            'vendor_phone': 'vendor_phone',
            'customer_name': 'customer_name',
            'customer_address': 'customer_address',
            'vendor_number': 'vendor_number',
            'customer_tax_id': 'customer_tax_id',
            'customer_vat_id': 'customer_vat_id',
            'line_items': 'line_items',
            'subtotal': 'subtotal',
            'tax_rate': 'tax_rate',
            'tax_amount': 'tax_amount',
            'total': 'total',
            'discount': 'discount',
            'currency': 'currency',
            'payment_terms': 'payment_terms',
            'payment_method': 'payment_method',
            'bank_account': 'bank_account',
            'bank_code': 'bank_code',
            'iban': 'iban',
            'bic': 'bic',
            'payment_account': 'payment_account',
            'reference_number': 'reference_number',
            'invoice_type': 'invoice_type',
            'tax_exempt_reason': 'tax_exempt_reason',
            'reverse_charge': 'reverse_charge',
            'meter_number': 'meter_number',
            'billing_period_start': 'billing_period_start',
            'billing_period_end': 'billing_period_end',
            'consumption_kwh': 'consumption_kwh',
            'price_per_kwh': 'price_per_kwh',
            'base_fee': 'base_fee',
        }
        
        for source_field, target_field in field_mapping.items():
            value = data.get(source_field)
            if value is not None:
                # Convert German number format to float if it's a string
                if isinstance(value, str):
                    value = self._parse_german_number(value)
                setattr(result, target_field, value)
        
        # Ensure line_items is a list
        if result.line_items is None:
            result.line_items = []
        elif not isinstance(result.line_items, list):
            result.line_items = [result.line_items] if result.line_items else []
        
        # Parse line item amounts
        for item in result.line_items:
            if isinstance(item, dict):
                for key in ['menge', 'quantity', 'einzelpreis', 'unit_price', 'betrag', 'total']:
                    if key in item and isinstance(item[key], str):
                        item[key] = self._parse_german_number(item[key])
    
    def _parse_german_number(self, value: str) -> float | str:
        """
        Convert German number format to float.
        German: 40.000,00 → 40000.00 (US format)
        
        If value is already a number (int/float), return as-is.
        """
        # Skip if already a number (LLM already parsed it)
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return value
        
        # Remove currency symbols and whitespace
        cleaned = value.strip().replace('EUR', '').replace('€', '').replace('$', '').strip()
        
        # Skip if empty
        if not cleaned:
            return value
        
        # Check if it's a German number (has comma as decimal separator)
        if ',' in cleaned and '.' in cleaned:
            # German format: 40.000,00 → 40000.00
            # Remove thousand separators (dots), replace comma with dot
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned and '.' not in cleaned:
            # Could be German decimal: 12,50 → 12.50
            # Only if it looks like a decimal (2 digits after comma)
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned)
        except ValueError:
            return value  # Return original if parsing fails
    
    def _calculate_confidence(self, result: ExtractedInvoice) -> float:
        """Calculate confidence score based on extracted fields."""
        # Critical fields for German invoices
        critical_fields = [
            'invoice_number',
            'invoice_date',
            'vendor_name',
            'customer_name',
            'total',
        ]
        
        # Important fields
        important_fields = [
            'vendor_vat_id',
            'subtotal',
            'tax_amount',
            'line_items',
        ]
        
        # Optional fields
        optional_fields = [
            'due_date',
            'payment_terms',
            'iban',
            'bic',
        ]
        
        score = 0.0
        max_score = 0.0
        
        # Check critical fields (3 points each)
        for field in critical_fields:
            max_score += 3
            if getattr(result, field, None):
                score += 3
        
        # Check important fields (2 points each)
        for field in important_fields:
            max_score += 2
            value = getattr(result, field, None)
            if value:
                if field == 'line_items' and len(value) > 0:
                    score += 2
                elif field != 'line_items':
                    score += 2
        
        # Check optional fields (1 point each)
        for field in optional_fields:
            max_score += 1
            if getattr(result, field, None):
                score += 1
        
        return score / max_score if max_score > 0 else 0.0
    
    def batch_extract(self, file_paths: List[str]) -> List[ExtractedInvoice]:
        """
        Extract data from multiple invoices.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of ExtractedInvoice objects
        """
        results = []
        
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"Verarbeite Rechnung {i}/{len(file_paths)}: {file_path}")
            result = self.extract(file_path)
            results.append(result)
        
        return results
