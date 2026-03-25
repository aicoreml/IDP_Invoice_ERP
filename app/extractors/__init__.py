"""
Document Extractors - Template-based structured data extraction
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """Abstract base class for document extractors."""
    
    @abstractmethod
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract structured data from document."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, str]:
        """Return extraction schema."""
        pass


class InvoiceExtractor(BaseExtractor):
    """Extract data from invoices."""
    
    def get_schema(self) -> Dict[str, str]:
        return {
            "invoice_number": "Invoice number/ID",
            "invoice_date": "Invoice date",
            "due_date": "Payment due date",
            "vendor_name": "Vendor/supplier name",
            "vendor_address": "Vendor address",
            "vendor_tax_id": "Vendor tax ID/VAT number",
            "customer_name": "Customer/buyer name",
            "customer_address": "Customer address",
            "line_items": "List of items with description, quantity, unit price, total",
            "subtotal": "Subtotal before tax",
            "tax_rate": "Tax rate percentage",
            "tax_amount": "Tax amount",
            "total": "Total amount including tax",
            "currency": "Currency code",
            "payment_terms": "Payment terms",
            "payment_method": "Payment method"
        }
    
    def extract(self, file_path: str, llm_client=None) -> Dict[str, Any]:
        """Extract invoice data."""
        # Import here to avoid circular dependency
        from document_processor import DocumentProcessor
        from llm_client import OllamaClient
        
        # Process document
        processor = DocumentProcessor()
        text = processor.process_file(file_path)
        
        # Use LLM for extraction
        client = llm_client or OllamaClient()
        result = client.extract_structured(text, self.get_schema(), "invoice")
        
        return result


class ReceiptExtractor(BaseExtractor):
    """Extract data from receipts."""
    
    def get_schema(self) -> Dict[str, str]:
        return {
            "merchant_name": "Store/merchant name",
            "merchant_address": "Store address",
            "merchant_phone": "Store phone number",
            "receipt_date": "Date of purchase",
            "receipt_time": "Time of purchase",
            "receipt_number": "Receipt/transaction number",
            "items": "List of items with name, quantity, price",
            "subtotal": "Subtotal",
            "tax": "Tax amount",
            "total": "Total amount",
            "payment_method": "Payment method (cash, card, etc.)",
            "card_last4": "Last 4 digits of card (if card payment)",
            "cashier": "Cashier name/ID"
        }
    
    def extract(self, file_path: str, llm_client=None) -> Dict[str, Any]:
        """Extract receipt data."""
        from document_processor import DocumentProcessor
        from llm_client import OllamaClient
        
        processor = DocumentProcessor()
        text = processor.process_file(file_path)
        
        client = llm_client or OllamaClient()
        result = client.extract_structured(text, self.get_schema(), "receipt")
        
        return result


class IDDocumentExtractor(BaseExtractor):
    """Extract data from identity documents (IDs, passports, licenses)."""
    
    def get_schema(self) -> Dict[str, str]:
        return {
            "document_type": "Type of document (passport, ID card, driver license, etc.)",
            "document_number": "Document number",
            "first_name": "First name",
            "last_name": "Last name",
            "full_name": "Full name",
            "date_of_birth": "Date of birth",
            "place_of_birth": "Place of birth",
            "nationality": "Nationality",
            "gender": "Gender",
            "address": "Address",
            "issue_date": "Issue date",
            "expiry_date": "Expiry date",
            "issuing_authority": "Issuing authority",
            "photo_present": "Whether photo is present"
        }
    
    def extract(self, file_path: str, llm_client=None) -> Dict[str, Any]:
        """Extract ID document data."""
        from ocr_processor import OCRProcessor
        from llm_client import OllamaClient
        
        # Use OCR for ID documents (often scanned)
        ocr = OCRProcessor()
        text = ocr.process_image(file_path)
        
        client = llm_client or OllamaClient()
        result = client.extract_structured(text, self.get_schema(), "id_document")
        
        return result


class CustomExtractor(BaseExtractor):
    """Custom extractor for user-defined fields."""
    
    def __init__(self, fields: Dict[str, str]):
        """
        Initialize with custom fields.
        
        Args:
            fields: Dictionary of field names and descriptions
        """
        self.fields = fields
    
    def get_schema(self) -> Dict[str, str]:
        return self.fields
    
    def extract(self, file_path: str, llm_client=None) -> Dict[str, Any]:
        """Extract custom fields."""
        from document_processor import DocumentProcessor
        from llm_client import OllamaClient
        
        processor = DocumentProcessor()
        text = processor.process_file(file_path)
        
        client = llm_client or OllamaClient()
        result = client.extract_structured(text, self.fields, "custom")
        
        return result


# Factory function
def get_extractor(template: str, custom_fields: Optional[Dict[str, str]] = None) -> BaseExtractor:
    """
    Get extractor by template name.
    
    Args:
        template: Template name ('invoice', 'receipt', 'id_document', 'custom')
        custom_fields: Custom fields for 'custom' template
    
    Returns:
        Extractor instance
    """
    extractors = {
        'invoice': InvoiceExtractor,
        'receipt': ReceiptExtractor,
        'id_document': IDDocumentExtractor,
        'id': IDDocumentExtractor,  # Alias
    }
    
    if template == 'custom':
        if not custom_fields:
            raise ValueError("custom_fields required for custom template")
        return CustomExtractor(custom_fields)
    
    if template not in extractors:
        raise ValueError(f"Unknown template: {template}. Available: {list(extractors.keys())}")
    
    return extractors[template]()