#!/usr/bin/env python3
"""
Test Script: Process the 10 downloaded German invoices
Demonstrates the complete IDP pipeline workflow
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add app directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'app'))

from pipeline.config import PipelineConfig
from pipeline.orchestrator import InvoicePipeline

def main():
    print("=" * 70)
    print("German Invoice IDP Pipeline - Test Run")
    print("=" * 70)
    print()
    
    # Configure for test run
    config = PipelineConfig(
        input_dir=Path(project_root) / "input",
        output_dir=Path(project_root) / "output" / "test_run",
        processed_dir=Path(project_root) / "data" / "processed",
        failed_dir=Path(project_root) / "data" / "failed",
        export_format="json",
        validate_german_invoice=True,
        confidence_threshold=0.5,  # Lower threshold for testing
        log_level="INFO",
        log_file=Path(project_root) / "idp_pipeline_test.log",
    )
    
    # Ensure directories exist
    config.ensure_directories()
    
    # List invoices to process
    input_dir = config.input_dir
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        print("Please ensure the input folder contains invoice PDFs.")
        return 1
    
    invoice_files = list(input_dir.glob("*.pdf"))
    
    if not invoice_files:
        print(f"❌ No PDF files found in: {input_dir}")
        return 1
    
    print(f"📁 Input directory: {input_dir}")
    print(f"📄 Found {len(invoice_files)} invoice files:")
    for f in invoice_files:
        print(f"   - {f.name}")
    print()
    
    # Create and run pipeline
    print("🚀 Starting pipeline...")
    print("-" * 70)
    
    pipeline = InvoicePipeline(config)
    result = pipeline.run()
    
    # Print summary
    print()
    print("=" * 70)
    print("📊 PIPELINE RESULTS")
    print("=" * 70)
    print(f"   Total invoices:           {result.total_invoices}")
    print(f"   Successful extractions:   {result.successful_extractions}")
    print(f"   Failed extractions:       {result.failed_extractions}")
    print(f"   Validated:                {result.validated_count}")
    print(f"   Validation failed:        {result.validation_failed_count}")
    print(f"   Exported:                 {result.exported_count}")
    print(f"   Duration:                 {result.total_duration_seconds:.2f}s")
    print()
    
    # Show extraction details
    print("📋 EXTRACTION DETAILS:")
    print("-" * 70)
    for ext in result.extraction_results:
        status = "✅" if ext['confidence'] >= config.confidence_threshold else "⚠️ "
        inv_num = ext.get('invoice_number') or 'N/A'
        print(f"   {status} {Path(ext['file']).name}")
        print(f"      Invoice#: {inv_num}")
        print(f"      Confidence: {ext['confidence']:.2f}")
        print(f"      Time: {ext['processing_time_ms']:.0f}ms")
        if ext.get('errors'):
            for err in ext['errors'][:2]:  # Show first 2 errors
                print(f"      ! {err}")
        print()
    
    # Show validation details
    print("✅ VALIDATION RESULTS:")
    print("-" * 70)
    for val in result.validation_results:
        status = "✅" if val['is_valid'] else "❌"
        inv_num = val.get('invoice_number') or 'N/A'
        print(f"   {status} Invoice: {inv_num}")
        print(f"      Compliance Score: {val['compliance_score']:.2f}")
        if val.get('errors'):
            print(f"      Errors: {len(val['errors'])}")
            for err in val['errors'][:2]:
                print(f"        - {err}")
        if val.get('warnings'):
            print(f"      Warnings: {len(val['warnings'])}")
        print()
    
    # Show export results
    print("📤 EXPORT RESULTS:")
    print("-" * 70)
    for exp in result.export_results:
        status = "✅" if exp['success'] else "❌"
        print(f"   {status} {exp['target']}")
        print(f"      Exported: {exp['exported']} invoices")
    print()
    
    # Save detailed results
    result_file = config.output_dir / "pipeline_result.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(result.to_json(indent=2))
    
    print(f"💾 Detailed results saved to: {result_file}")
    print()
    
    # Print sample extracted data
    if result.extraction_results:
        print("📝 SAMPLE EXTRACTED DATA (first invoice):")
        print("-" * 70)
        
        # Read the exported JSON to show sample
        export_files = list(config.output_dir.glob("invoices_*.json"))
        if export_files:
            with open(export_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('invoices'):
                    sample = data['invoices'][0]
                    print(json.dumps({
                        'invoice_number': sample.get('invoice_number'),
                        'invoice_date': sample.get('invoice_date'),
                        'vendor_name': sample.get('vendor_name'),
                        'customer_name': sample.get('customer_name'),
                        'subtotal': sample.get('subtotal'),
                        'tax_rate': sample.get('tax_rate'),
                        'tax_amount': sample.get('tax_amount'),
                        'total': sample.get('total'),
                        'currency': sample.get('currency'),
                        'line_items_count': len(sample.get('line_items', [])),
                    }, indent=2))
    
    print()
    print("=" * 70)
    if result.success:
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
    else:
        print("❌ PIPELINE COMPLETED WITH ERRORS")
    print("=" * 70)
    
    return 0 if result.success else 1


if __name__ == '__main__':
    sys.exit(main())
