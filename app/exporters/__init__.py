"""
Export Adapters for Invoice Data
Exports extracted invoice data to various backend systems
"""

import os
import sys
import json
import csv
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.config import PipelineConfig, HANAConfig, APIConfig
from pipeline.invoice_extractor import ExtractedInvoice

logger = logging.getLogger(__name__)


class ExportResult:
    """Result of an export operation."""
    
    def __init__(
        self,
        success: bool,
        message: str,
        exported_count: int = 0,
        failed_count: int = 0,
        export_path: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.message = message
        self.exported_count = exported_count
        self.failed_count = failed_count
        self.export_path = export_path
        self.error = error
    
    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} {self.message}"


class BaseExporter(ABC):
    """Abstract base class for exporters."""
    
    @abstractmethod
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        """Export invoices to the target system."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get exporter name."""
        pass


class JSONExporter(BaseExporter):
    """Export invoices to JSON files."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_name(self) -> str:
        return "JSON"
    
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"invoices_{timestamp}.json"
        
        try:
            data = {
                "export_date": datetime.now().isoformat(),
                "export_format": "json",
                "invoice_count": len(invoices),
                "invoices": [inv.to_dict() for inv in invoices]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            return ExportResult(
                success=True,
                message=f"Exported {len(invoices)} invoices to {output_file}",
                exported_count=len(invoices),
                export_path=str(output_file),
            )
        except Exception as e:
            return ExportResult(
                success=False,
                message=f"JSON export failed: {e}",
                error=str(e),
            )


class CSVExporter(BaseExporter):
    """Export invoices to CSV files."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_name(self) -> str:
        return "CSV"
    
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"invoices_{timestamp}.csv"
        line_items_file = self.output_dir / f"line_items_{timestamp}.csv"

        try:
            # Sort invoices by date (newest first)
            sorted_invoices = sorted(
                invoices,
                key=lambda x: x.invoice_date or '',
                reverse=True
            )

            # Export invoice headers
            invoice_fields = [
                'source_file', 'invoice_number', 'invoice_date', 'due_date',
                'vendor_name', 'vendor_vat_id', 'vendor_number',
                'customer_name', 'customer_vat_id',
                'subtotal', 'tax_rate', 'tax_amount', 'total', 'currency',
                'payment_terms', 'iban', 'bic', 'payment_account', 'reference_number',
                'confidence_score', 'validation_errors'
            ]

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=invoice_fields, extrasaction='ignore')
                writer.writeheader()

                for inv in sorted_invoices:
                    row = {
                        'source_file': inv.source_file,
                        'invoice_number': inv.invoice_number,
                        'invoice_date': inv.invoice_date,
                        'due_date': inv.due_date,
                        'vendor_name': inv.vendor_name,
                        'vendor_vat_id': inv.vendor_vat_id,
                        'vendor_number': inv.vendor_number,
                        'customer_name': inv.customer_name or '[PLACEHOLDER - Privacy Redacted]',
                        'customer_vat_id': inv.customer_vat_id,
                        'subtotal': inv.subtotal,
                        'tax_rate': inv.tax_rate,
                        'tax_amount': inv.tax_amount,
                        'total': inv.total,
                        'currency': inv.currency,
                        'payment_terms': inv.payment_terms,
                        'iban': inv.iban,
                        'bic': inv.bic,
                        'payment_account': inv.payment_account,
                        'reference_number': inv.reference_number,
                        'confidence_score': inv.confidence_score,
                        'validation_errors': '; '.join(inv.validation_errors) if inv.validation_errors else '',
                    }
                    writer.writerow(row)
            
            # Export line items separately
            with open(line_items_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'invoice_number', 'position', 'beschreibung', 'menge',
                    'einzelpreis', 'betrag'
                ])
                
                for inv in invoices:
                    for i, item in enumerate(inv.line_items, 1):
                        writer.writerow([
                            inv.invoice_number,
                            i,
                            item.get('beschreibung', item.get('description', '')),
                            item.get('menge', item.get('quantity', '')),
                            item.get('einzelpreis', item.get('unit_price', '')),
                            item.get('betrag', item.get('total', '')),
                        ])
            
            return ExportResult(
                success=True,
                message=f"Exported {len(invoices)} invoices to {output_file} and {line_items_file}",
                exported_count=len(invoices),
                export_path=str(output_file),
            )
        except Exception as e:
            return ExportResult(
                success=False,
                message=f"CSV export failed: {e}",
                error=str(e),
            )


class XMLEXporter(BaseExporter):
    """Export invoices to XML format (ZUGFeRD-compatible structure)."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_name(self) -> str:
        return "XML"
    
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"invoices_{timestamp}.xml"
        
        try:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content += '<Invoices xmlns="http://example.com/invoices">\n'
            
            for inv in invoices:
                xml_content += self._invoice_to_xml(inv)
            
            xml_content += '</Invoices>'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            return ExportResult(
                success=True,
                message=f"Exported {len(invoices)} invoices to {output_file}",
                exported_count=len(invoices),
                export_path=str(output_file),
            )
        except Exception as e:
            return ExportResult(
                success=False,
                message=f"XML export failed: {e}",
                error=str(e),
            )
    
    def _invoice_to_xml(self, inv: ExtractedInvoice, indent: int = 2) -> str:
        """Convert single invoice to XML."""
        base_indent = ' ' * indent
        
        def escape_xml(s: str) -> str:
            if s is None:
                return ''
            return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        def xml_element(name: str, value: Any) -> str:
            if value is None:
                return ''
            return f'{base_indent}  <{name}>{escape_xml(value)}</{name}>\n'
        
        xml = f'{base_indent}<Invoice>\n'
        xml += xml_element('InvoiceNumber', inv.invoice_number)
        xml += xml_element('InvoiceDate', inv.invoice_date)
        xml += xml_element('DueDate', inv.due_date)
        
        xml += f'{base_indent}  <Seller>\n'
        xml += xml_element('Name', inv.vendor_name)
        xml += xml_element('Address', inv.vendor_address)
        xml += xml_element('TaxID', inv.vendor_tax_id)
        xml += xml_element('VATID', inv.vendor_vat_id)
        xml += f'{base_indent}  </Seller>\n'
        
        xml += f'{base_indent}  <Buyer>\n'
        xml += xml_element('Name', inv.customer_name)
        xml += xml_element('Address', inv.customer_address)
        xml += xml_element('VATID', inv.customer_vat_id)
        xml += f'{base_indent}  </Buyer>\n'
        
        xml += f'{base_indent}  <LineItems>\n'
        for i, item in enumerate(inv.line_items, 1):
            xml += f'{base_indent}    <Item>\n'
            xml += xml_element('Position', i)
            xml += xml_element('Description', item.get('beschreibung', item.get('description', '')))
            xml += xml_element('Quantity', item.get('menge', item.get('quantity', '')))
            xml += xml_element('UnitPrice', item.get('einzelpreis', item.get('unit_price', '')))
            xml += xml_element('Total', item.get('betrag', item.get('total', '')))
            xml += f'{base_indent}    </Item>\n'
        xml += f'{base_indent}  </LineItems>\n'
        
        xml += xml_element('Subtotal', inv.subtotal)
        xml += xml_element('TaxRate', inv.tax_rate)
        xml += xml_element('TaxAmount', inv.tax_amount)
        xml += xml_element('Total', inv.total)
        xml += xml_element('Currency', inv.currency)
        xml += xml_element('ConfidenceScore', inv.confidence_score)
        
        xml += f'{base_indent}</Invoice>\n'
        return xml


class HANAExporter(BaseExporter):
    """
    Export invoices to SAP HANA database.
    
    Supports both hdbcli (official SAP driver) and pyhdb (open source).
    """
    
    def __init__(self, config: HANAConfig):
        self.config = config
        self.connection = None
    
    def get_name(self) -> str:
        return "SAP HANA"
    
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        try:
            # Connect to HANA
            conn = self._connect()
            if conn is None:
                return ExportResult(
                    success=False,
                    message="HANA connection failed - driver not available",
                    error="HANA driver not installed",
                )
            
            cursor = conn.cursor()
            
            # Create table if not exists
            self._create_table(cursor)
            
            # Insert invoices
            exported = 0
            failed = 0
            
            for inv in invoices:
                try:
                    self._insert_invoice(cursor, inv)
                    exported += 1
                except Exception as e:
                    logger.error(f"Failed to insert invoice {inv.invoice_number}: {e}")
                    failed += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return ExportResult(
                success=failed == 0,
                message=f"Exported {exported}/{len(invoices)} invoices to HANA",
                exported_count=exported,
                failed_count=failed,
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                message=f"HANA export failed: {e}",
                error=str(e),
            )
    
    def _connect(self):
        """Connect to SAP HANA."""
        # Try hdbcli first (official driver)
        try:
            import hdbcli.dbapi
            conn = hdbcli.dbapi.connect(
                address=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                encrypt=self.config.use_ssl,
                sslValidateCertificate=self.config.ssl_validate_certificate,
            )
            logger.info("Connected to HANA using hdbcli")
            return conn
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"hdbcli connection failed: {e}")
        
        # Try pyhdb (open source alternative)
        try:
            import pyhdb
            conn = pyhdb.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
            )
            logger.info("Connected to HANA using pyhdb")
            return conn
        except ImportError:
            logger.warning("No HANA driver available (hdbcli or pyhdb)")
        except Exception as e:
            logger.warning(f"pyhdb connection failed: {e}")
        
        return None
    
    def _create_table(self, cursor):
        """Create invoice table in HANA."""
        schema = self.config.schema
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.INVOICES (
            ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            SOURCE_FILE NVARCHAR(500),
            INVOICE_NUMBER NVARCHAR(100),
            INVOICE_DATE DATE,
            DUE_DATE DATE,
            VENDOR_NAME NVARCHAR(200),
            VENDOR_ADDRESS NCLOB,
            VENDOR_TAX_ID NVARCHAR(50),
            VENDOR_VAT_ID NVARCHAR(20),
            CUSTOMER_NAME NVARCHAR(200),
            CUSTOMER_ADDRESS NCLOB,
            CUSTOMER_VAT_ID NVARCHAR(20),
            SUBTOTAL DECIMAL(15,2),
            TAX_RATE DECIMAL(5,2),
            TAX_AMOUNT DECIMAL(15,2),
            TOTAL DECIMAL(15,2),
            CURRENCY NVARCHAR(3),
            PAYMENT_TERMS NCLOB,
            IBAN NVARCHAR(34),
            BIC NVARCHAR(11),
            CONFIDENCE_SCORE DECIMAL(3,2),
            VALIDATION_ERRORS NCLOB,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        try:
            cursor.execute(create_table_sql)
            logger.info(f"Created table {schema}.INVOICES")
        except Exception as e:
            logger.warning(f"Table creation note: {e}")
        
        # Create line items table
        create_items_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema}.INVOICE_ITEMS (
            ID INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            INVOICE_ID INTEGER,
            POSITION INTEGER,
            DESCRIPTION NCLOB,
            QUANTITY DECIMAL(15,4),
            UNIT_PRICE DECIMAL(15,2),
            TOTAL DECIMAL(15,2),
            FOREIGN KEY (INVOICE_ID) REFERENCES {schema}.INVOICES(ID)
        )
        """
        
        try:
            cursor.execute(create_items_sql)
            logger.info(f"Created table {schema}.INVOICE_ITEMS")
        except Exception as e:
            logger.warning(f"Table creation note: {e}")
    
    def _insert_invoice(self, cursor, inv: ExtractedInvoice):
        """Insert invoice into HANA."""
        # Insert header
        insert_sql = f"""
        INSERT INTO {self.config.schema}.INVOICES (
            SOURCE_FILE, INVOICE_NUMBER, INVOICE_DATE, DUE_DATE,
            VENDOR_NAME, VENDOR_ADDRESS, VENDOR_TAX_ID, VENDOR_VAT_ID,
            CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_VAT_ID,
            SUBTOTAL, TAX_RATE, TAX_AMOUNT, TOTAL, CURRENCY,
            PAYMENT_TERMS, IBAN, BIC, CONFIDENCE_SCORE, VALIDATION_ERRORS
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_sql, (
            inv.source_file,
            inv.invoice_number,
            self._parse_date(inv.invoice_date),
            self._parse_date(inv.due_date),
            inv.vendor_name,
            inv.vendor_address,
            inv.vendor_tax_id,
            inv.vendor_vat_id,
            inv.customer_name,
            inv.customer_address,
            inv.customer_vat_id,
            inv.subtotal,
            inv.tax_rate,
            inv.tax_amount,
            inv.total,
            inv.currency,
            inv.payment_terms,
            inv.iban,
            inv.bic,
            inv.confidence_score,
            '; '.join(inv.validation_errors) if inv.validation_errors else None,
        ))
        
        # Get inserted ID
        cursor.execute("SELECT CURRENT_IDENTITY_VALUE() FROM DUMMY")
        invoice_id = cursor.fetchone()[0]
        
        # Insert line items
        insert_item_sql = f"""
        INSERT INTO {self.config.schema}.INVOICE_ITEMS (
            INVOICE_ID, POSITION, DESCRIPTION, QUANTITY, UNIT_PRICE, TOTAL
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        
        for i, item in enumerate(inv.line_items, 1):
            cursor.execute(insert_item_sql, (
                invoice_id,
                i,
                item.get('beschreibung', item.get('description', '')),
                item.get('menge', item.get('quantity', 0)),
                item.get('einzelpreis', item.get('unit_price', 0)),
                item.get('betrag', item.get('total', 0)),
            ))
    
    def _parse_date(self, date_str: Optional[str]):
        """Parse date string for HANA."""
        if not date_str:
            return None
        
        from datetime import datetime
        
        formats = ['%Y-%m-%d', '%d.%m.%Y', '%Y%m%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None


class APIExporter(BaseExporter):
    """Export invoices to REST API endpoint."""
    
    def __init__(self, config: APIConfig):
        self.config = config
    
    def get_name(self) -> str:
        return "REST API"
    
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        try:
            import requests
        except ImportError:
            return ExportResult(
                success=False,
                message="requests library not installed",
                error="Install with: pip install requests",
            )
        
        url = f"{self.config.base_url}/api/invoices"
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.config.api_key:
            headers['Authorization'] = f"Bearer {self.config.api_key}"
        
        # Prepare payload
        payload = {
            'invoices': [inv.to_dict() for inv in invoices],
            'export_date': datetime.now().isoformat(),
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            
            response.raise_for_status()
            
            result = response.json() if response.content else {}
            
            return ExportResult(
                success=True,
                message=f"Exported {len(invoices)} invoices to API: {url}",
                exported_count=len(invoices),
            )
            
        except requests.exceptions.RequestException as e:
            return ExportResult(
                success=False,
                message=f"API export failed: {e}",
                error=str(e),
            )


class CompositeExporter(BaseExporter):
    """Export to multiple targets simultaneously."""
    
    def __init__(self, exporters: List[BaseExporter]):
        self.exporters = exporters
    
    def get_name(self) -> str:
        return "Composite"
    
    def export(self, invoices: List[ExtractedInvoice]) -> ExportResult:
        results = []
        total_exported = 0
        total_failed = 0
        all_success = True
        
        for exporter in self.exporters:
            logger.info(f"Exporting to {exporter.get_name()}...")
            result = exporter.export(invoices)
            results.append(result)
            
            if result.success:
                total_exported += result.exported_count
            else:
                all_success = False
                total_failed += result.failed_count or len(invoices)
        
        messages = [str(r) for r in results]
        
        return ExportResult(
            success=all_success,
            message="; ".join(messages),
            exported_count=total_exported,
            failed_count=total_failed,
        )


def get_exporter(export_format: str, config: PipelineConfig) -> BaseExporter:
    """Factory function to get exporter by format name."""
    exporters = {
        'json': lambda: JSONExporter(config.output_dir),
        'csv': lambda: CSVExporter(config.output_dir),
        'xml': lambda: XMLEXporter(config.output_dir),
        'hana': lambda: HANAExporter(config.hana),
        'api': lambda: APIExporter(config.api),
    }
    
    if export_format.lower() not in exporters:
        raise ValueError(
            f"Unknown export format: {export_format}. "
            f"Available: {list(exporters.keys())}"
        )
    
    return exporters[export_format.lower()]()
