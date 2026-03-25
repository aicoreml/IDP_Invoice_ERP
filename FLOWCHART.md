# IDP Invoice Processing Pipeline - Flowchart

**Swiss Electric Bill (Stromrechnung) Processing**

---

## 📊 Complete Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        IDP INVOICE PROCESSING PIPELINE                       │
│                     Swiss Electric Bill Extraction & Export                  │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 0: CONFIGURATION                                                      │
│  ─────────────────────                                                      │
│  • PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK = True (faster startup)           │
│  • EXPORT_FORMAT = csv                                                      │
│  • EXPORT_ON_VALIDATION_FAIL = True (export Swiss invoices)                │
│  • VALIDATE_GERMAN_INVOICE = False (Swiss invoices ≠ German law)           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: DISCOVER INVOICES                                                  │
│  ───────────────────────                                                    │
│  • Scan input/ folder for PDF files                                         │
│  • Found: 6 electric bills (SH-Power-Bill-1.pdf to 6.pdf)                  │
│  • Sort files alphabetically                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: TEXT EXTRACTION (per invoice)                                      │
│  ───────────────────────────────                                            │
│  • PyMuPDF4LLM / PyPDF2 extracts text from PDF                             │
│  • OCR fallback if needed (Tesseract, PaddleOCR)                           │
│  • Output: Raw text with German/Swiss invoice content                      │
│                                                                             │
│  Example extracted text:                                                    │
│  "Rechnung 3032069, Kundennummer 052 635 12 52,                            │
│   SH POWER, CHF 210.55, Referenz 70 23000..."                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: LLM-POWERED FIELD EXTRACTION                                       │
│  ─────────────────────────────────────                                      │
│  • Model: minimax-m2.5:cloud (via Ollama)                                  │
│  • Prompt: German invoice extraction schema                                │
│  • Temperature: 0.1 (deterministic output)                                 │
│                                                                             │
│  Extracted Fields:                                                          │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ invoice_number      → Rechnungsnummer (e.g., 3032069)         │        │
│  │ invoice_date        → Rechnungsdatum (YYYY-MM-DD)             │        │
│  │ due_date            → Fälligkeitsdatum                        │        │
│  │ vendor_name         → Lieferant (SH POWER)                    │        │
│  │ vendor_vat_id       → MWST-Nr. (CHE-130.340.240)             │        │
│  │ vendor_number       → Kundennummer (052 635 12 52)           │        │
│  │ customer_name       → [PLACEHOLDER - Privacy Redacted]        │        │
│  │ subtotal            → exkl. MWST (194.74)                     │        │
│  │ tax_rate            → MWST Satz (8.1%)                        │        │
│  │ tax_amount          → MWST Betrag (15.79)                     │        │
│  │ total               → Gesamtbetrag (210.55)                   │        │
│  │ currency            → Währung (CHF)                           │        │
│  │ payment_terms       → zahlbar bis ...                         │        │
│  │ iban                → IBAN (CH03...)                          │        │
│  │ payment_account     → Konto Zahlbar an                        │        │
│  │ reference_number    → Referenz (QR-Rechnung)                  │        │
│  │ confidence_score    → 0.0 - 1.0                               │        │
│  └────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: VALIDATION (SKIPPED FOR SWISS INVOICES)                            │
│  ──────────────────────────────────────────                                 │
│  • VALIDATE_GERMAN_INVOICE = False                                         │
│  • German §14 UStG validation not applicable to Swiss invoices             │
│  • All invoices marked as valid (compliance_score: 1.0)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: CSV EXPORT                                                         │
│  ───────────────────                                                        │
│  • Sort invoices by date (newest first)                                    │
│  • Export to: output/invoices_YYYYMMDD_HHMMSS.csv                          │
│  • Line items: output/line_items_YYYYMMDD_HHMMSS.csv                       │
│                                                                             │
│  CSV Columns:                                                               │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │ source_file │ invoice_number │ invoice_date │ due_date │       │        │
│  │ vendor_name │ vendor_vat_id  │ vendor_number │ customer_name │ │        │
│  │ subtotal │ tax_rate │ tax_amount │ total │ currency │         │        │
│  │ payment_terms │ iban │ payment_account │ reference_number │   │        │
│  │ confidence_score │ validation_errors │                        │        │
│  └────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: OUTPUT FILES                                                       │
│  ──────────────────                                                         │
│  • output/invoices_YYYYMMDD_HHMMSS.csv (main invoice data)                 │
│  • output/line_items_YYYYMMDD_HHMMSS.csv (position details)                │
│  • idp_pipeline.log (processing log)                                       │
│                                                                             │
│  Ready for:                                                                 │
│  • Database import (SAP HANA, PostgreSQL, MySQL)                           │
│  • ERP system integration                                                   │
│  • Manual review in Excel                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Processing Loop (per invoice)

```
┌──────────────────────────────────────────────────────────────────┐
│                    FOR EACH INVOICE (6x)                         │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────────┐
    │ 1. Read PDF │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────┐
    │ 2. Extract Text │ → raw_text (string)
    └──────┬──────────┘
           │
           ▼
    ┌─────────────────────────┐
    │ 3. LLM Extraction       │ → structured JSON
    │    (minimax-m2.5:cloud) │
    └──────┬──────────────────┘
           │
           ▼
    ┌─────────────────────────┐
    │ 4. Parse German Numbers │
    │    40.000,00 → 40000.00 │
    └──────┬──────────────────┘
           │
           ▼
    ┌─────────────────────────┐
    │ 5. Populate Dataclass   │
    │    ExtractedInvoice     │
    └──────┬──────────────────┘
           │
           ▼
    ┌─────────────────────────┐
    │ 6. Calculate Confidence │ → 0.85 (85%)
    └──────┬──────────────────┘
           │
           ▼
    ┌─────────────────────────┐
    │ 7. Add to Export List   │
    └─────────────────────────┘
```

---

## 📋 Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │     │  PROCESS    │     │   OUTPUT    │
│             │     │             │     │             │
│ input/      │────▶│  extractor  │────▶│ output/     │
│ ├── 1.pdf   │     │  ├── text   │     │ ├── *.csv   │
│ ├── 2.pdf   │     │  ├── LLM    │     │ └── *.log   │
│ ├── 3.pdf   │     │  └── parse  │     │
│ ├── 4.pdf   │     │             │     │
│ ├── 5.pdf   │     │  validator  │     │
│ └── 6.pdf   │     │  (skipped)  │     │
└─────────────┘     │             │     └─────────────┘
                    │  exporter   │
                    │  └── CSV    │
                    └─────────────┘
```

---

## 🔧 Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         app/                                        │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ pipeline/       │  │ exporters/   │  │ validators/         │   │
│  │ ├── config.py   │  │ ├── __init__.│  │ ├── german_invoice_ │   │
│  │ ├── orchestrator│  │ └── CSV      │  │ └── validator.py    │   │
│  │ ├── invoice_    │  │   Exporter   │  └─────────────────────┘   │
│  │ └── extractor.  │  └──────────────┘                            │
│  │    py           │                                              │
│  └─────────────────┘                                              │
│  ┌─────────────────┐  ┌──────────────┐                            │
│  │ document_       │  │ llm_client.  │                            │
│  │ processor.py    │  │ py           │                            │
│  │ (PyPDF2,        │  │ (Ollama,     │                            │
│  │  PyMuPDF)       │  │  minimax)    │                            │
│  └─────────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Extraction Results Summary

| Invoice # | Date | Vendor | Total (CHF) | Reference | Confidence |
|-----------|------|--------|-------------|-----------|------------|
| 3032069 | 2025-07-25 | SH POWER | 210.55 | 70 23000 00573 38003 03206 91003 | 0.85 |
| 3020954 | 2025-04-01 | SH POWER | 241.70 | 70 23000 00573 38003 02095 | 0.85 |
| 2728924 | 2024-07-22 | SH POWER | 206.55 | 70 23000 00507 76002 72892 | 0.81 |
| 2702925 | 2024-04-20 | SH POWER | 260.90 | 70 23000 00507 76002 70292 | 0.85 |
| 2674564 | 2024-01-19 | SH POWER | 170.90 | 70 23000 00507 76002 67456 | 0.85 |
| 2648917 | 2023-10-20 | SH POWER | 149.25 | 70 23000 00507 76002 64891 | 0.85 |

**Total Value:** CHF 1,240.05  
**Average Confidence:** 84.3%  
**Processing Time:** ~3 minutes (6 invoices)

---

## 🚀 Quick Start

```bash
# 1. Activate environment
source /Users/usermacrtx/Documents/Demos/demos_env/bin/activate

# 2. Place PDF invoices in input/ folder
cp *.pdf input/

# 3. Run pipeline
cd /Users/usermacrtx/Documents/Demos/IDP_App_Invoice_ERP_DE
python3 app/pipeline/orchestrator.py

# 4. Check output
ls -la output/
cat output/invoices_*.csv
```

---

## 📝 Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK` | `True` | Skip model connectivity check |
| `EXPORT_FORMAT` | `csv` | Output format (json/csv/xml) |
| `EXPORT_ON_VALIDATION_FAIL` | `True` | Export even if validation fails |
| `VALIDATE_GERMAN_INVOICE` | `False` | Skip German tax validation |
| `EXTRACTION_MODEL` | `minimax-m2.5:cloud` | LLM model for extraction |
| `OCR_ENABLED` | `True` | Enable OCR for scanned PDFs |

---

**Last Updated:** March 25, 2026  
**Pipeline Version:** 1.0  
**Status:** ✅ Production Ready
