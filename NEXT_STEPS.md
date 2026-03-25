# IDP Pipeline - Next Steps & TODOs

**Date:** March 24, 2026  
**Status:** Core extraction working, ready for mass processing

---

## ✅ Completed

### Core Features
- [x] German invoice extraction pipeline
- [x] Multi-page PDF text extraction
- [x] German number format parsing (40.000,00 → 40000.00)
- [x] LLM-powered field extraction (Ollama + minimax-m2.5:cloud)
- [x] German tax compliance validation (§14 UStG)
- [x] Streamlit UI with preview tab
- [x] Nginx proxy integration (https://gpt.myddns.me/invoice-erp/)

### Extraction Fields (Current)
```python
{
    "invoice_number": str,
    "invoice_date": str,
    "due_date": str,
    "vendor_name": str,
    "vendor_address": str,
    "vendor_vat_id": str,
    "customer_name": str,
    "customer_address": str,
    "line_items": List[dict],
    "subtotal": float,
    "tax_rate": float,
    "tax_amount": float,
    "total": float,
    "currency": str,
    "payment_terms": str,
    "iban": str,
    "bic": str,
}
```

### Export Options
- [x] JSON export
- [ ] CSV export (needs implementation)
- [ ] XML export
- [ ] SAP HANA direct insert
- [ ] REST API export

---

## 📋 Next Steps (User Requirements)

### 1. Find Identical Invoices
**Goal:** Detect duplicate invoices to avoid processing same invoice twice

**Approach:**
- Compare invoice hash (content-based)
- Check invoice_number + vendor_name + total + date
- Store processed invoices in database
- Flag potential duplicates

**Implementation:**
```python
# Add to pipeline/orchestrator.py
def check_duplicate(invoice: ExtractedInvoice, db_path: str) -> bool:
    """Check if invoice already processed."""
    invoice_hash = hash(
        f"{invoice.invoice_number}{invoice.vendor_name}{invoice.total}{invoice.invoice_date}"
    )
    # Check against database of processed invoices
    # Return True if duplicate found
```

---

### 2. Upload Electric Bills (Stromrechnung)
**User has electric bills to process**

**Expected Fields for Electric Bills:**
```python
{
    "invoice_number": str,           # Rechnungsnummer
    "invoice_date": str,             # Rechnungsdatum
    "customer_name": str,            # Kundenname
    "customer_address": str,         # Kundenadresse
    "customer_number": str,          # Kundennummer
    "meter_number": str,             # Zählernummer
    "consumption_kwh": float,        # Verbrauch in kWh
    "price_per_kwh": float,          # Preis pro kWh
    "base_fee": float,               # Grundgebühr
    "energy_cost": float,            # Energiekosten
    "tax_rate": float,               # Steuersatz (19%)
    "tax_amount": float,             # Steuerbetrag
    "total": float,                  # Gesamtbetrag
    "billing_period_start": str,     # Abrechnungszeitraum von
    "billing_period_end": str,       # Abrechnungszeitraum bis
    "supplier_name": str,            # Lieferant
    "supplier_vat_id": str,          # USt-IdNr
}
```

**Action Items:**
1. User will upload electric bill PDFs to `input/` folder
2. Test extraction on electric bills
3. Adjust extraction prompt for utility-specific fields
4. Verify meter numbers and consumption data extracted correctly

---

### 3. Define Custom Extraction Fields
**Goal:** Allow users to define custom fields for different invoice types

**Approach:**
```python
# Add custom field configuration
CUSTOM_FIELDS = {
    "electric_bill": {
        "meter_number": "Zählernummer",
        "consumption_kwh": "Verbrauch in kWh",
        "price_per_kwh": "Arbeitspreis pro kWh",
        "base_fee": "Grundpreis",
        "billing_period": "Abrechnungszeitraum",
    },
    "telekom_bill": {
        "phone_number": "Rufnummer",
        "contract_number": "Vertragskonto",
        "connection_fee": "Anschlussgebühr",
    },
    "generic_invoice": {
        # Default fields
    }
}
```

**UI Enhancement:**
- Add dropdown for invoice type selection
- Show/hide fields based on type
- Allow custom field definitions

---

### 4. Mass Processing
**Goal:** Process hundreds/thousands of invoices efficiently

**Requirements:**
- Batch processing (100+ invoices)
- Progress tracking
- Error handling & retry logic
- Parallel processing (multiprocessing)
- Memory-efficient streaming

**Implementation Plan:**
```python
# scripts/batch_process.py
#!/usr/bin/env python3
"""Batch process all invoices in folder."""

import multiprocessing as mp
from pipeline.orchestrator import InvoicePipeline

def process_batch(input_folder: str, output_folder: str, workers: int = 4):
    """Process all invoices in parallel."""
    # Get all PDFs
    pdf_files = list(Path(input_folder).glob("*.pdf"))
    
    # Process in batches
    with mp.Pool(workers) as pool:
        results = pool.map(process_single_invoice, pdf_files)
    
    # Aggregate results
    export_to_csv(results, output_folder)
```

**Features to Add:**
- [ ] Progress bar (tqdm)
- [ ] Resume from checkpoint
- [ ] Error log for failed invoices
- [ ] Summary statistics
- [ ] Duplicate detection

---

### 5. CSV Export for Database Import
**Goal:** Create CSV file ready for database import

**CSV Format:**
```csv
invoice_number,invoice_date,vendor_name,customer_name,subtotal,tax_amount,total,currency,iban,bic,processing_date
XXXXXXX,2023-04-01,Kyndryl GmbH,COMPANY NAME,50000.00,9500.00,59500.00,EUR,DE89...,XXXX...,2026-03-24
```

**Implementation:**
```python
# exporters/csv_exporter.py
def export_to_csv(invoices: List[ExtractedInvoice], output_path: str):
    """Export invoices to CSV for database import."""
    import csv
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'invoice_number', 'invoice_date', 'vendor_name', 'customer_name',
            'subtotal', 'tax_amount', 'total', 'currency',
            'iban', 'bic', 'processing_date'
        ])
        # Data
        for inv in invoices:
            writer.writerow([
                inv.invoice_number,
                inv.invoice_date,
                inv.vendor_name,
                inv.customer_name,
                inv.subtotal,
                inv.tax_amount,
                inv.total,
                inv.currency,
                inv.iban,
                inv.bic,
                datetime.now().isoformat()
            ])
```

---

### 6. Database Table Import
**Goal:** Load CSV into database table (SAP HANA / PostgreSQL / MySQL)

**Target Table Schema:**
```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number VARCHAR(100),
    invoice_date DATE,
    vendor_name VARCHAR(200),
    vendor_vat_id VARCHAR(20),
    customer_name VARCHAR(200),
    customer_number VARCHAR(100),
    subtotal DECIMAL(15,2),
    tax_rate DECIMAL(5,2),
    tax_amount DECIMAL(15,2),
    total DECIMAL(15,2),
    currency VARCHAR(3),
    iban VARCHAR(34),
    bic VARCHAR(11),
    processing_date TIMESTAMP,
    source_file VARCHAR(500),
    confidence_score DECIMAL(3,2),
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(invoice_number, vendor_name, total, invoice_date)
);
```

**Import Options:**

**Option A: Direct Database Insert**
```python
# exporters/db_exporter.py
def export_to_hana(invoices: List[ExtractedInvoice], hana_config: dict):
    """Direct insert into SAP HANA."""
    import pyhdb
    conn = pyhdb.connect(**hana_config)
    cursor = conn.cursor()
    
    for inv in invoices:
        cursor.execute("""
            INSERT INTO invoices (...) VALUES (?, ?, ?, ...)
        """, (
            inv.invoice_number, inv.invoice_date, inv.vendor_name, ...
        ))
    conn.commit()
```

**Option B: CSV Load (Bulk Import)**
```bash
# SAP HANA
IMPORT FROM CSV FILE '/path/to/invoices.csv' INTO INVOICES WITH THREADS 4;

# PostgreSQL
COPY invoices FROM '/path/to/invoices.csv' WITH CSV HEADER;

# MySQL
LOAD DATA INFILE '/path/to/invoices.csv' INTO TABLE invoices ...;
```

**Option C: REST API to Backend**
```python
# Send to ERP system
import requests
requests.post(
    "https://erp-backend/api/invoices",
    json={"invoices": [inv.to_dict() for inv in invoices]},
    headers={"Authorization": "Bearer TOKEN"}
)
```

---

## 📊 Mass Processing Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  UPLOAD     │────▶│  PROCESS    │────▶│  DEDUPE     │
│  (100+ PDF) │     │  (Parallel) │     │  Check      │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  DATABASE   │◀────│  CSV        │◀────│  EXPORT     │
│  INSERT     │     │  Export     │     │  (JSON/CSV) │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 🔧 Files to Create/Modify

### New Files
```
app/
├── exporters/
│   ├── csv_exporter.py          # CSV export for DB import
│   ├── db_exporter.py           # Direct DB insert
│   └── erp_api_exporter.py      # REST API export
├── validators/
│   └── duplicate_checker.py     # Duplicate detection
├── config/
│   └── field_templates.py       # Custom field definitions
└── scripts/
    ├── batch_process.py         # Mass processing script
    └── import_to_db.py          # Database import script

data/
└── processed_log.db             # SQLite log of processed invoices
```

### Modified Files
```
app/pipeline/orchestrator.py      # Add duplicate check
app/ui/streamlit_app.py           # Add invoice type selector
app/pipeline/invoice_extractor.py # Add custom field support
```

---

## 📅 Priority Order

1. **Upload Electric Bills** - Test extraction on real utility bills
2. **Define Custom Fields** - Add electric bill-specific fields
3. **CSV Export** - Implement CSV export for database import
4. **Duplicate Detection** - Prevent processing same invoice twice
5. **Mass Processing** - Batch processing with progress tracking
6. **Database Import** - Direct insert or CSV load

---

## 🎯 End Goal

**Automated Invoice Processing Pipeline:**
1. Upload 100+ invoices (PDF)
2. Automatic extraction of all fields
3. Duplicate detection & flagging
4. Export to CSV with all data
5. One-click import to database table
6. Ready for ERP system consumption

**Timeline:** Ready for mass processing after electric bill testing

---

**Next Session:**
- [ ] Upload electric bills to `input/` folder
- [ ] Test extraction on utility invoices
- [ ] Define custom fields for electric bills
- [ ] Implement CSV export
- [ ] Test mass processing (10+ invoices)
