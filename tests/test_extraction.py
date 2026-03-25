#!/usr/bin/env python3
"""Test invoice extraction with Ollama."""

import sys
import os
from pathlib import Path

# Add app to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'app'))

from pipeline.config import PipelineConfig
from pipeline.invoice_extractor import GermanInvoiceExtractor

# Get first PDF from input folder
input_dir = Path("./input")
pdf_files = list(input_dir.glob("*.pdf"))

if not pdf_files:
    print("❌ No PDF files found in ./input")
    sys.exit(1)

test_file = str(pdf_files[0])
print(f"📄 Testing extraction on: {Path(test_file).name}")

# Configure
config = PipelineConfig(
    input_dir=input_dir,
    output_dir=Path("./output"),
    extraction_model="minimax-m2.5:cloud",
    confidence_threshold=0.5,
)

# Extract
extractor = GermanInvoiceExtractor(config)
result = extractor.extract(test_file)

# Print results
print("\n" + "=" * 50)
print("EXTRACTION RESULTS")
print("=" * 50)
print(f"Invoice Number: {result.invoice_number}")
print(f"Invoice Date:   {result.invoice_date}")
print(f"Vendor:         {result.vendor_name}")
print(f"Customer:       {result.customer_name}")
print(f"Subtotal:       €{result.subtotal}")
print(f"Tax:            €{result.tax_amount} ({result.tax_rate}%)")
print(f"Total:          €{result.total}")
print(f"Currency:       {result.currency}")
print(f"Confidence:     {result.confidence_score:.2f}")
print(f"Processing Time: {result.processing_time_ms:.0f}ms")

if result.validation_errors:
    print("\n⚠️  Validation Errors:")
    for err in result.validation_errors:
        print(f"  - {err}")

print("=" * 50)

# Check if price was extracted
if result.total is None:
    print("\n❌ WARNING: Total price was not extracted!")
    print("\nRaw text preview:")
    print(result.raw_text[:500])
else:
    print("\n✅ SUCCESS: Price extracted correctly!")
