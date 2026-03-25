"""
IDP Pipeline Orchestrator
Chains extraction → validation → export for German invoice processing
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

# Disable Paddle model source check for faster startup
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
# Export to CSV and disable German validation (for Swiss invoices)
os.environ['EXPORT_FORMAT'] = 'csv'
os.environ['EXPORT_ON_VALIDATION_FAIL'] = 'True'
os.environ['VALIDATE_GERMAN_INVOICE'] = 'False'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.config import PipelineConfig, get_config
from pipeline.invoice_extractor import GermanInvoiceExtractor, ExtractedInvoice
from validators.german_invoice_validator import GermanInvoiceValidator, ValidationResult
from exporters import (
    get_exporter, JSONExporter, CSVExporter, XMLEXporter,
    HANAExporter, APIExporter, CompositeExporter, ExportResult
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    # Summary
    success: bool
    total_invoices: int
    successful_extractions: int
    failed_extractions: int
    validated_count: int
    validation_failed_count: int
    exported_count: int
    
    # Timing
    start_time: str
    end_time: str
    total_duration_seconds: float
    
    # Details
    extraction_results: List[Dict[str, Any]] = None
    validation_results: List[Dict[str, Any]] = None
    export_results: List[Dict[str, Any]] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.extraction_results is None:
            self.extraction_results = []
        if self.validation_results is None:
            self.validation_results = []
        if self.export_results is None:
            self.export_results = []
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, default=str, ensure_ascii=False)


class InvoicePipeline:
    """
    Main pipeline orchestrator for German invoice processing.
    
    Workflow:
    1. Discover invoices in input directory
    2. Extract structured data using LLM
    3. Validate against German tax requirements
    4. Export to configured backend (JSON/CSV/XML/HANA/API)
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or get_config()
        
        # Initialize components
        self.extractor = GermanInvoiceExtractor(self.config)
        self.validator = GermanInvoiceValidator()
        
        # Setup logging
        self._setup_logging()
        
        logger.info("Invoice Pipeline initialized")
        logger.info(f"Input directory: {self.config.input_dir}")
        logger.info(f"Output directory: {self.config.output_dir}")
        logger.info(f"Export format: {self.config.export_format}")
    
    def _setup_logging(self):
        """Configure logging for pipeline."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # File handler
        file_handler = logging.FileHandler(self.config.log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, self.config.log_level))
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config.log_level))
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Add to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    def run(self, invoice_paths: Optional[List[str]] = None) -> PipelineResult:
        """
        Run the complete invoice processing pipeline.
        
        Args:
            invoice_paths: Optional list of specific invoice paths to process.
                          If None, processes all PDFs in input directory.
        
        Returns:
            PipelineResult with execution summary
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting Invoice Processing Pipeline")
        logger.info("=" * 60)
        
        # Discover invoices
        if invoice_paths:
            invoices_to_process = invoice_paths
        else:
            invoices_to_process = self._discover_invoices()
        
        if not invoices_to_process:
            return PipelineResult(
                success=False,
                total_invoices=0,
                successful_extractions=0,
                failed_extractions=0,
                validated_count=0,
                validation_failed_count=0,
                exported_count=0,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                total_duration_seconds=0,
                errors=["No invoices found to process"],
            )
        
        logger.info(f"Found {len(invoices_to_process)} invoices to process")
        
        # Step 1: Extract
        logger.info("-" * 40)
        logger.info("STEP 1: Extracting invoice data")
        logger.info("-" * 40)
        
        extracted_invoices = self._run_extraction(invoices_to_process)
        successful_extractions = sum(
            1 for inv in extracted_invoices if inv.confidence_score > 0
        )
        
        # Step 2: Validate
        logger.info("-" * 40)
        logger.info("STEP 2: Validating invoices")
        logger.info("-" * 40)
        
        validation_results = self._run_validation(extracted_invoices)
        validated_count = sum(1 for vr in validation_results if vr.is_valid)
        
        # Step 3: Export
        logger.info("-" * 40)
        logger.info("STEP 3: Exporting invoices")
        logger.info("-" * 40)
        
        export_results = self._run_export(extracted_invoices, validation_results)
        
        # Calculate final statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = PipelineResult(
            success=True,
            total_invoices=len(invoices_to_process),
            successful_extractions=successful_extractions,
            failed_extractions=len(invoices_to_process) - successful_extractions,
            validated_count=validated_count,
            validation_failed_count=len(validation_results) - validated_count,
            exported_count=sum(r.exported_count for r in export_results),
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration_seconds=duration,
            extraction_results=[
                {
                    'file': inv.source_file,
                    'invoice_number': inv.invoice_number,
                    'invoice_date': inv.invoice_date,
                    'vendor_name': inv.vendor_name,
                    'customer_name': inv.customer_name,
                    'subtotal': inv.subtotal,
                    'tax_amount': inv.tax_amount,
                    'total': inv.total,
                    'confidence': inv.confidence_score,
                    'processing_time_ms': inv.processing_time_ms,
                    'errors': inv.validation_errors,
                    'raw_text': inv.raw_text[:2000] if inv.raw_text else '',  # Preview text
                }
                for inv in extracted_invoices
            ],
            validation_results=[
                {
                    'invoice_number': inv.invoice_number,
                    'is_valid': vr.is_valid,
                    'compliance_score': vr.compliance_score,
                    'errors': vr.errors,
                    'warnings': vr.warnings,
                }
                for inv, vr in zip(extracted_invoices, validation_results)
            ],
            export_results=[
                {
                    'target': r.message,
                    'success': r.success,
                    'exported': r.exported_count,
                    'failed': r.failed_count,
                }
                for r in export_results
            ],
        )
        
        # Log summary
        self._log_summary(result)
        
        return result
    
    def _discover_invoices(self) -> List[str]:
        """Discover invoice files in input directory."""
        invoice_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        invoices = []
        
        input_path = Path(self.config.input_dir)
        
        if not input_path.exists():
            logger.warning(f"Input directory does not exist: {input_path}")
            return []
        
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in invoice_extensions:
                invoices.append(str(file_path))
        
        # Sort for consistent ordering
        invoices.sort()
        
        return invoices
    
    def _run_extraction(self, invoice_paths: List[str]) -> List[ExtractedInvoice]:
        """Run extraction on all invoices."""
        extracted = []
        
        for i, path in enumerate(invoice_paths, 1):
            logger.info(f"[{i}/{len(invoice_paths)}] Extracting: {Path(path).name}")
            
            try:
                result = self.extractor.extract(path)
                extracted.append(result)
                
                if result.confidence_score >= self.config.confidence_threshold:
                    logger.info(f"  ✓ Confidence: {result.confidence_score:.2f}")
                else:
                    logger.warning(f"  ⚠ Low confidence: {result.confidence_score:.2f}")
                
                if result.validation_errors:
                    for err in result.validation_errors:
                        logger.warning(f"  ! {err}")
                
            except Exception as e:
                logger.error(f"  ✗ Extraction failed: {e}")
                # Create empty result
                extracted.append(ExtractedInvoice(
                    source_file=path,
                    extraction_date=datetime.now().isoformat(),
                    processing_time_ms=0,
                    confidence_score=0.0,
                    validation_errors=[f"Extraction error: {e}"],
                ))
        
        return extracted
    
    def _run_validation(
        self, invoices: List[ExtractedInvoice]
    ) -> List[ValidationResult]:
        """Run validation on all extracted invoices."""
        results = []
        
        for i, invoice in enumerate(invoices, 1):
            inv_num = invoice.invoice_number or Path(invoice.source_file).name
            logger.info(f"[{i}/{len(invoices)}] Validating: {inv_num}")
            
            if self.config.validate_german_invoice:
                result = self.validator.validate(invoice)
                results.append(result)
                
                if result.is_valid:
                    logger.info(f"  ✓ Valid (compliance: {result.compliance_score:.2f})")
                else:
                    logger.warning(f"  ✗ Invalid (compliance: {result.compliance_score:.2f})")
                    for err in result.errors:
                        logger.warning(f"    ERROR: {err}")
                    for warn in result.warnings:
                        logger.debug(f"    WARN: {warn}")
            else:
                # Skip validation
                results.append(ValidationResult(
                    is_valid=True,
                    errors=[],
                    warnings=[],
                    compliance_score=1.0,
                ))
                logger.info("  - Validation skipped")
        
        return results
    
    def _run_export(
        self,
        invoices: List[ExtractedInvoice],
        validation_results: List[ValidationResult],
    ) -> List[ExportResult]:
        """Run export to configured targets."""
        results = []

        # Filter invoices based on validation
        if self.config.export_on_validation_fail:
            # Export all invoices regardless of validation
            valid_invoices = invoices
        elif self.config.export_on_success:
            # Only export valid invoices
            valid_invoices = [
                inv for inv, vr in zip(invoices, validation_results)
                if vr.is_valid
            ]
        else:
            valid_invoices = []
        
        if not valid_invoices:
            logger.info("No invoices to export")
            return results
        
        logger.info(f"Exporting {len(valid_invoices)} invoices...")
        
        # Get exporter(s)
        try:
            if self.config.export_format == 'all':
                # Export to all formats
                exporters = [
                    JSONExporter(self.config.output_dir),
                    CSVExporter(self.config.output_dir),
                    XMLEXporter(self.config.output_dir),
                ]
                
                # Add HANA if configured
                if self.config.hana.password:
                    exporters.append(HANAExporter(self.config.hana))
                
                # Add API if configured
                if self.config.api.base_url:
                    exporters.append(APIExporter(self.config.api))
                
                exporter = CompositeExporter(exporters)
            else:
                exporter = get_exporter(self.config.export_format, self.config)
            
            result = exporter.export(valid_invoices)
            results.append(result)
            logger.info(str(result))
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            results.append(ExportResult(
                success=False,
                message=f"Export failed: {e}",
                error=str(e),
            ))
        
        return results
    
    def _log_summary(self, result: PipelineResult):
        """Log pipeline execution summary."""
        logger.info("=" * 60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Invoices:        {result.total_invoices}")
        logger.info(f"Successful Extractions: {result.successful_extractions}")
        logger.info(f"Failed Extractions:     {result.failed_extractions}")
        logger.info(f"Validated:              {result.validated_count}")
        logger.info(f"Validation Failed:      {result.validation_failed_count}")
        logger.info(f"Exported:               {result.exported_count}")
        logger.info(f"Duration:               {result.total_duration_seconds:.2f}s")
        logger.info(f"Status:                 {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        logger.info("=" * 60)
    
    def process_single(self, file_path: str) -> Tuple[ExtractedInvoice, Optional[ValidationResult]]:
        """
        Process a single invoice file.
        
        Args:
            file_path: Path to the invoice file
            
        Returns:
            Tuple of (ExtractedInvoice, ValidationResult)
        """
        logger.info(f"Processing single file: {file_path}")
        
        # Extract
        invoice = self.extractor.extract(file_path)
        
        # Validate
        validation = None
        if self.config.validate_german_invoice:
            validation = self.validator.validate(invoice)
        
        return invoice, validation


def run_pipeline(config: Optional[PipelineConfig] = None) -> PipelineResult:
    """
    Convenience function to run the pipeline.
    
    Args:
        config: Optional pipeline configuration
        
    Returns:
        PipelineResult
    """
    pipeline = InvoicePipeline(config)
    return pipeline.run()


if __name__ == "__main__":
    # Run pipeline when executed directly
    result = run_pipeline()
    print(result.to_json())
