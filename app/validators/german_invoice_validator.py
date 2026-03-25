"""
German Invoice Validator
Validates extracted invoices against German tax law requirements
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of invoice validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    compliance_score: float  # 0.0 to 1.0


class GermanInvoiceValidator:
    """
    Validates German invoices against tax law requirements.
    
    References:
    - §14 UStG (Umsatzsteuergesetz) - Invoice requirements
    - §14b UStG - Record keeping requirements
    """
    
    # German tax ID patterns
    STEUERNUMMER_PATTERN = r'^\d{2,3}/\d{3,4}/\d{4,5}$'  # e.g., 12/345/67890
    UST_ID_PATTERN = r'^DE\d{9}$'  # e.g., DE123456789
    
    # Required fields per §14 UStG
    REQUIRED_FIELDS = [
        'invoice_number',
        'invoice_date',
        'vendor_name',
        'vendor_address',
        'customer_name',
        'customer_address',
        'line_items',
        'subtotal',
        'tax_rate',
        'tax_amount',
        'total',
    ]
    
    # Conditional required fields
    VAT_ID_REQUIRED_IF = {
        'vendor_vat_id': lambda inv: inv.total and inv.total > 250,  # Over €250
    }
    
    # Valid tax rates in Germany
    VALID_TAX_RATES = [0, 7, 19]  # 0% (tax exempt), 7% (reduced), 19% (standard)
    
    # Invoice types
    VALID_INVOICE_TYPES = [
        'rechnung',
        'gutschrift',
        'abschlagsrechnung',
        'schlussrechnung',
        'teilrechnung',
        'selbst ausgestellte rechnung',
        'kleinunternehmerrechnung',
    ]
    
    def validate(self, invoice) -> ValidationResult:
        """
        Validate a German invoice.
        
        Args:
            invoice: ExtractedInvoice object
            
        Returns:
            ValidationResult with errors, warnings, and compliance score
        """
        errors = []
        warnings = []
        
        # 1. Check required fields
        field_errors = self._check_required_fields(invoice)
        errors.extend(field_errors)
        
        # 2. Validate invoice number (fortlaufende Nummer)
        number_errors = self._validate_invoice_number(invoice.invoice_number)
        errors.extend(number_errors)
        
        # 3. Validate dates
        date_errors, date_warnings = self._validate_dates(invoice)
        errors.extend(date_errors)
        warnings.extend(date_warnings)
        
        # 4. Validate tax IDs
        tax_errors, tax_warnings = self._validate_tax_ids(invoice)
        errors.extend(tax_errors)
        warnings.extend(tax_warnings)
        
        # 5. Validate amounts
        amount_errors = self._validate_amounts(invoice)
        errors.extend(amount_errors)
        
        # 6. Validate line items
        item_errors = self._validate_line_items(invoice)
        errors.extend(item_errors)
        
        # 7. Validate German-specific requirements
        de_errors, de_warnings = self._validate_german_requirements(invoice)
        errors.extend(de_errors)
        warnings.extend(de_warnings)
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(
            invoice, len(errors), len(warnings)
        )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            compliance_score=compliance_score,
        )
    
    def _check_required_fields(self, invoice) -> List[str]:
        """Check if all required fields are present."""
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            value = getattr(invoice, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Fehlendes Pflichtfeld gemäß §14 UStG: {field}")
            elif isinstance(value, list) and len(value) == 0:
                errors.append(f"Fehlendes Pflichtfeld: {field} (leere Liste)")
        
        return errors
    
    def _validate_invoice_number(self, invoice_number: Optional[str]) -> List[str]:
        """Validate invoice number format."""
        errors = []

        if not invoice_number:
            return errors  # Already caught in required fields

        # Convert to string if numeric (LLM may return float/int)
        invoice_number_str = str(invoice_number)

        # Check for reasonable length
        if len(invoice_number_str) < 3 or len(invoice_number_str) > 50:
            errors.append(f"Ungültige Rechnungsnummer Länge: {invoice_number}")

        # Check for sequential pattern (simple heuristic)
        # Real validation would require checking against previous invoices

        return errors
    
    def _validate_dates(self, invoice) -> Tuple[List[str], List[str]]:
        """Validate invoice dates."""
        errors = []
        warnings = []
        
        # Parse invoice date
        if invoice.invoice_date:
            try:
                inv_date = self._parse_date(invoice.invoice_date)
                if inv_date > datetime.now():
                    errors.append(f"Rechnungsdatum liegt in der Zukunft: {invoice.invoice_date}")
            except ValueError:
                errors.append(f"Ungültiges Rechnungsdatum: {invoice.invoice_date}")
        
        # Parse due date
        if invoice.due_date and invoice.invoice_date:
            try:
                due_date = self._parse_date(invoice.due_date)
                inv_date = self._parse_date(invoice.invoice_date)
                if due_date < inv_date:
                    errors.append(f"Fälligkeitsdatum liegt vor Rechnungsdatum: {invoice.due_date}")
            except ValueError:
                warnings.append(f"Ungültiges Fälligkeitsdatum: {invoice.due_date}")
        
        # Parse delivery date
        if invoice.delivery_date and invoice.invoice_date:
            try:
                delivery_date = self._parse_date(invoice.delivery_date)
                inv_date = self._parse_date(invoice.invoice_date)
                # Delivery can be before invoice (common)
                if delivery_date > datetime.now():
                    warnings.append(f"Lieferdatum liegt in der Zukunft: {invoice.delivery_date}")
            except ValueError:
                warnings.append(f"Ungültiges Lieferdatum: {invoice.delivery_date}")
        
        return errors, warnings
    
    def _validate_tax_ids(self, invoice) -> Tuple[List[str], List[str]]:
        """Validate German tax IDs."""
        errors = []
        warnings = []
        
        # Validate vendor tax ID (Steuernummer)
        if invoice.vendor_tax_id:
            if not re.match(self.STEUERNUMMER_PATTERN, invoice.vendor_tax_id):
                # Try alternative formats
                cleaned = invoice.vendor_tax_id.replace(' ', '').replace('.', '')
                if not re.match(self.STEUERNUMMER_PATTERN, cleaned):
                    warnings.append(f"Ungültiges Steuernummer-Format: {invoice.vendor_tax_id}")
        
        # Validate vendor VAT ID (USt-IdNr)
        if invoice.vendor_vat_id:
            if not re.match(self.UST_ID_PATTERN, invoice.vendor_vat_id):
                errors.append(f"Ungültige USt-IdNr: {invoice.vendor_vat_id}")
        
        # Check if VAT ID is required (for invoices > €250)
        if invoice.total and invoice.total > 250:
            if not invoice.vendor_vat_id and not invoice.tax_exempt_reason:
                warnings.append(
                    "Keine USt-IdNr für Rechnung > €250. "
                    "Möglicherweise Kleinunternehmer gemäß §19 UStG"
                )
        
        return errors, warnings
    
    def _validate_amounts(self, invoice) -> List[str]:
        """Validate invoice amounts."""
        errors = []
        
        # Check that total = subtotal + tax
        if invoice.subtotal is not None and invoice.tax_amount is not None:
            expected_total = invoice.subtotal + invoice.tax_amount
            if invoice.total is not None:
                # Allow small rounding differences
                if abs(expected_total - invoice.total) > 0.02:
                    errors.append(
                        f"Summenfehler: {invoice.subtotal} + {invoice.tax_amount} ≠ {invoice.total}"
                    )
        
        # Check tax calculation
        if invoice.subtotal is not None and invoice.tax_rate is not None:
            expected_tax = invoice.subtotal * (invoice.tax_rate / 100)
            if invoice.tax_amount is not None:
                if abs(expected_tax - invoice.tax_amount) > 0.02:
                    errors.append(
                        f"Steuerfehler: {invoice.subtotal} × {invoice.tax_rate}% ≠ {invoice.tax_amount}"
                    )
        
        # Check for negative amounts
        for field in ['subtotal', 'tax_amount', 'total']:
            value = getattr(invoice, field, None)
            if value is not None and value < 0:
                errors.append(f"Negativer Betrag in {field}: {value}")
        
        # Validate tax rate
        if invoice.tax_rate is not None:
            if invoice.tax_rate not in self.VALID_TAX_RATES:
                # Allow small variations (e.g., 18.9999 due to rounding)
                closest = min(self.VALID_TAX_RATES, key=lambda x: abs(x - invoice.tax_rate))
                if abs(closest - invoice.tax_rate) > 0.1:
                    errors.append(f"Ungültiger Steuersatz: {invoice.tax_rate}%")
        
        return errors
    
    def _validate_line_items(self, invoice) -> List[str]:
        """Validate line items."""
        errors = []
        
        if not invoice.line_items:
            return errors
        
        for i, item in enumerate(invoice.line_items):
            if not isinstance(item, dict):
                errors.append(f"Position {i+1}: Ungültiges Format")
                continue
            
            # Check required item fields
            if 'beschreibung' not in item and 'description' not in item:
                errors.append(f"Position {i+1}: Fehlende Beschreibung")
            
            # Validate amounts
            quantity = item.get('menge', item.get('quantity', 0))
            unit_price = item.get('einzelpreis', item.get('unit_price', 0))
            total = item.get('betrag', item.get('total', 0))
            
            if quantity and unit_price and total:
                expected = quantity * unit_price
                if abs(expected - total) > 0.02:
                    errors.append(
                        f"Position {i+1}: {quantity} × {unit_price} ≠ {total}"
                    )
        
        return errors
    
    def _validate_german_requirements(self, invoice) -> Tuple[List[str], List[str]]:
        """Validate German-specific requirements."""
        errors = []
        warnings = []
        
        # Check for Kleinunternehmer (small business) indicator
        if invoice.tax_exempt_reason:
            if '§19 UStG' not in invoice.tax_exempt_reason and \
               'Kleinunternehmer' not in invoice.tax_exempt_reason:
                warnings.append(
                    f"Steuerbefreiung ohne §19 UStG Hinweis: {invoice.tax_exempt_reason}"
                )
        
        # Check for reverse charge indicator
        if invoice.reverse_charge:
            if not invoice.customer_vat_id:
                errors.append("Reverse Charge: Kunden-USt-IdNr erforderlich")
            if invoice.tax_rate and invoice.tax_rate != 0:
                warnings.append("Reverse Charge: Steuersatz sollte 0% sein")
        
        # Validate invoice type
        if invoice.invoice_type:
            inv_type_lower = invoice.invoice_type.lower()
            if not any(t in inv_type_lower for t in self.VALID_INVOICE_TYPES):
                warnings.append(f"Ungewöhnlicher Rechnungstyp: {invoice.invoice_type}")
        
        # Check for German language indicators (optional)
        if invoice.raw_text:
            german_keywords = ['Rechnung', 'Rechnungsnummer', 'Umsatzsteuer', 'Mehrwertsteuer']
            has_german = any(kw in invoice.raw_text for kw in german_keywords)
            if not has_german:
                warnings.append("Keine deutschen Rechnungs-Schlüsselwörter erkannt")
        
        return errors, warnings
    
    def _calculate_compliance_score(
        self, invoice, error_count: int, warning_count: int
    ) -> float:
        """Calculate compliance score (0.0 to 1.0)."""
        # Start with perfect score
        score = 1.0
        
        # Deduct for errors (critical)
        score -= error_count * 0.15
        
        # Deduct for warnings (minor)
        score -= warning_count * 0.05
        
        # Bonus for complete data
        optional_fields = [
            'due_date', 'payment_terms', 'iban', 'bic',
            'vendor_email', 'vendor_phone', 'customer_vat_id'
        ]
        filled_optional = sum(
            1 for field in optional_fields
            if getattr(invoice, field, None)
        )
        score += filled_optional * 0.02
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        formats = [
            '%Y-%m-%d',      # 2024-03-15
            '%d.%m.%Y',      # 15.03.2024
            '%d.%m.%y',      # 15.03.24
            '%Y%m%d',        # 20240315
            '%d/%m/%Y',      # 15/03/2024
            '%m/%d/%Y',      # 03/15/2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
