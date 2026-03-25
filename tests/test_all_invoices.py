#!/usr/bin/env python3
"""Test invoice extraction on all PDFs and show which are real invoices."""

import sys
from pathlib import Path

# Add app to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'app'))

from pipeline.config import PipelineConfig
from pipeline.invoice_extractor import GermanInvoiceExtractor

# Get all PDFs from input folder
input_dir = Path("./input")
pdf_files = list(input_dir.glob("*.pdf"))

if not pdf_files:
    print("❌ No PDF files found in ./input")
    sys.exit(1)

print(f"📊 Testing {len(pdf_files)} PDF files...\n")
print("=" * 80)

# Configure
config = PipelineConfig(
    input_dir=input_dir,
    output_dir=Path("./output"),
    extraction_model="minimax-m2.5:cloud",
    confidence_threshold=0.5,
)

results = []

for pdf_file in pdf_files:
    test_file = str(pdf_file)
    print(f"\n📄 {pdf_file.name}")
    print("-" * 60)
    
    try:
        # Extract
        extractor = GermanInvoiceExtractor(config)
        result = extractor.extract(test_file)
        
        # Check if it's a real invoice
        is_invoice = (
            result.invoice_number and 
            result.total and 
            result.confidence_score > 0.3
        )
        
        if is_invoice:
            print(f"   ✅ REAL INVOICE")
            print(f"      Number: {result.invoice_number}")
            print(f"      Date: {result.invoice_date}")
            print(f"      Vendor: {result.vendor_name[:40]}..." if result.vendor_name and len(result.vendor_name) > 40 else f"      Vendor: {result.vendor_name}")
            print(f"      Total: €{result.total:.2f}")
            print(f"      Confidence: {result.confidence_score:.2f}")
        else:
            print(f"   ⚠️  NOT AN INVOICE (guide/document)")
            print(f"      Confidence: {result.confidence_score:.2f}")
            if result.raw_text:
                preview = result.raw_text[:100].replace('\n', ' ')
                print(f"      Preview: {preview}...")
        
        results.append({
            'file': pdf_file.name,
            'is_invoice': is_invoice,
            'invoice_number': result.invoice_number,
            'total': result.total,
            'confidence': result.confidence_score
        })
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results.append({
            'file': pdf_file.name,
            'is_invoice': False,
            'error': str(e)
        })

# Summary
print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)

invoices = [r for r in results if r.get('is_invoice', False)]
documents = [r for r in results if not r.get('is_invoice', False)]

print(f"\n✅ REAL INVOICES ({len(invoices)}):")
for inv in invoices:
    print(f"   • {inv['file']} - {inv['invoice_number']} - €{inv['total']:.2f}")

print(f"\n⚠️  DOCUMENTS/GUIDES ({len(documents)}):")
for doc in documents:
    print(f"   • {doc['file']}")

print("\n" + "=" * 80)
