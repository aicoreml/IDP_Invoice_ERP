# IDP Pipeline - German Invoice Processing for ERP/HANA

Intelligent Document Processing (IDP) pipeline for extracting structured data from German invoices and exporting to ERP systems or SAP HANA databases.

![Status](https://img.shields.io/badge/status-ready-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

- **German Invoice Extraction**: LLM-powered extraction of 30+ fields from German invoices
- **OCR Support**: Tesseract-based OCR for scanned invoices
- **German Tax Compliance**: Validation against §14 UStG requirements
- **Multiple Export Formats**: JSON, CSV, XML, SAP HANA, REST API
- **Batch Processing**: Process entire folders of invoices
- **Confidence Scoring**: Quality metrics for extracted data
- **Error Handling**: Comprehensive logging and error reporting

## 📋 Extracted Fields

| Category | Fields |
|----------|--------|
| **Invoice Header** | Invoice Number, Date, Due Date, Delivery Date, Type |
| **Vendor (Lieferant)** | Name, Address, Tax ID, VAT ID, Email, Phone |
| **Customer (Käufer)** | Name, Address, Tax ID, VAT ID |
| **Line Items** | Description, Quantity, Unit Price, Total |
| **Totals** | Subtotal, Tax Rate, Tax Amount, Total, Discount |
| **Payment** | Currency, Terms, Method, IBAN, BIC |
| **German-Specific** | Reverse Charge, Tax Exempt Reason (§19 UStG) |

## 🚀 Quick Start

### 1. Installation

```bash
# Install Python dependencies
source /Users/usermacrtx/Documents/Demos/demos_env/bin/activate
pip install -r requirements.txt

# Install system dependencies (macOS)
brew install tesseract tesseract-lang poppler

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required model
ollama pull minimax-m2.5:cloud
```

### 2. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings (optional for JSON export)
nano .env
```

### 3. Run Pipeline

**Option A: Command Line**
```bash
# Process all invoices in ./input folder
python scripts/process_invoices.py

# Process with specific export format
python scripts/process_invoices.py --export csv

# Process specific files
python scripts/process_invoices.py --files input/inv1.pdf input/inv2.pdf
```

**Option B: Web UI (Streamlit)**
```bash
# Start the web UI
./run_streamlit.sh

# Or manually:
source /Users/usermacrtx/Documents/Demos/demos_env/bin/activate
streamlit run app/ui/streamlit_app.py --server.port 8502
```

Then open http://localhost:8502 in your browser.

### 4. View Results

```bash
# Check output folder
ls -la output/

# View pipeline log
cat idp_pipeline.log
```

## 📁 Project Structure

```
IDP_App_Invoice_ERP_DE/
├── app/
│   ├── pipeline/
│   │   ├── config.py              # Configuration management
│   │   ├── invoice_extractor.py   # German invoice extraction
│   │   └── orchestrator.py        # Pipeline workflow
│   ├── validators/
│   │   └── german_invoice_validator.py  # §14 UStG validation
│   ├── exporters/
│   │   └── __init__.py            # JSON, CSV, XML, HANA, API exporters
│   ├── extractors/
│   │   └── __init__.py            # Document extractors
│   ├── document_processor.py      # PDF/text extraction
│   ├── ocr_processor.py           # OCR processing
│   └── llm_client.py              # Ollama LLM client
├── scripts/
│   └── process_invoices.py        # CLI batch processor
├── tests/
│   └── test_invoice_pipeline.py   # Test script
├── input/                         # Input invoices
├── output/                        # Exported data
└── requirements.txt
```

## 🔧 Usage Examples

### Basic Processing (JSON Export)

```bash
python scripts/process_invoices.py
```

### Export to CSV

```bash
python scripts/process_invoices.py --export csv
```

### Export to SAP HANA

```bash
python scripts/process_invoices.py \
  --export hana \
  --hana-host myhana.server.com \
  --hana-user SYSTEM \
  --hana-password secret \
  --hana-schema INVOICES
```

### Export to REST API

```bash
python scripts/process_invoices.py \
  --export api \
  --api-url http://erp.local:8080 \
  --api-key your-api-key
```

### Export to All Formats

```bash
python scripts/process_invoices.py --export all
```

### Skip Validation

```bash
python scripts/process_invoices.py --no-validation
```

### Adjust Confidence Threshold

```bash
python scripts/process_invoices.py --confidence-threshold 0.5
```

## 📊 Pipeline Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   INPUT     │────▶│  EXTRACT    │────▶│  VALIDATE   │────▶│   EXPORT    │
│  Invoices   │     │  LLM+OCR    │     │  §14 UStG   │     │ JSON/CSV/   │
│  (PDF,Img)  │     │  30+ Fields │     │  Compliance │     │ HANA/API    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Step 1: Extraction

- Load PDF or image
- Extract text (native or OCR)
- LLM extracts structured fields
- Calculate confidence score

### Step 2: Validation

- Check required fields (§14 UStG)
- Validate tax IDs (Steuernummer, USt-IdNr)
- Verify amount calculations
- Check German-specific requirements

### Step 3: Export

- Transform to target format
- Write to file or database
- Handle errors and retries

## 🔍 Validation Rules

The pipeline validates German invoices against tax law requirements:

| Rule | Description |
|------|-------------|
| **Required Fields** | Invoice number, date, vendor/customer info, amounts |
| **Tax ID Format** | Steuernummer: `12/345/67890`, USt-IdNr: `DE123456789` |
| **Amount Check** | Subtotal + Tax = Total |
| **Tax Rate** | Valid German rates: 0%, 7%, 19% |
| **Date Logic** | Due date ≥ Invoice date |
| **Kleinunternehmer** | §19 UStG indicator for small businesses |
| **Reverse Charge** | Customer VAT ID required |

## 📤 Export Formats

### JSON

```json
{
  "export_date": "2024-03-24T20:00:00",
  "invoice_count": 10,
  "invoices": [
    {
      "invoice_number": "RE-2024-001",
      "invoice_date": "2024-03-15",
      "vendor_name": "Muster GmbH",
      "vendor_vat_id": "DE123456789",
      "total": 1190.00,
      "currency": "EUR",
      "line_items": [...]
    }
  ]
}
```

### CSV

Two files generated:
- `invoices_YYYYMMDD_HHMMSS.csv` - Invoice headers
- `line_items_YYYYMMDD_HHMMSS.csv` - Line item details

### SAP HANA

Creates two tables:
- `INVOICES` - Invoice header data
- `INVOICE_ITEMS` - Line items (foreign key to INVOICES)

```sql
SELECT * FROM INVOICES.INVOICES ORDER BY CREATED_AT DESC;
SELECT * FROM INVOICES.INVOICE_ITEMS WHERE INVOICE_ID = 1;
```

### REST API

POST to configured endpoint:

```json
{
  "invoices": [...],
  "export_date": "2024-03-24T20:00:00"
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INPUT_DIR` | `./input` | Input directory |
| `OUTPUT_DIR` | `./output` | Output directory |
| `EXPORT_FORMAT` | `json` | Export format |
| `EXTRACTION_MODEL` | `minimax-m2.5:cloud` | Ollama model |
| `CONFIDENCE_THRESHOLD` | `0.7` | Min confidence |
| `VALIDATE_GERMAN_INVOICE` | `true` | Enable validation |

### SAP HANA Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HANA_HOST` | `localhost` | HANA server |
| `HANA_PORT` | `30015` | HANA port |
| `HANA_USER` | `SYSTEM` | Username |
| `HANA_PASSWORD` | - | Password |
| `HANA_SCHEMA` | `INVOICES` | Schema name |

## 🧪 Testing

Run the test script with the 10 sample invoices:

```bash
python tests/test_invoice_pipeline.py
```

This will:
1. Process all PDFs in `./input`
2. Extract structured data
3. Validate against German requirements
4. Export to JSON
5. Display detailed results

## 📈 Sample Output

```
======================================================================
📊 PIPELINE RESULTS
======================================================================
   Total invoices:           10
   Successful extractions:   9
   Failed extractions:       1
   Validated:                8
   Validation failed:        2
   Exported:                 8
   Duration:                 45.32s

📋 EXTRACTION DETAILS:
   ✅ german_invoice_template_01.pdf
      Invoice#: RE-2024-001
      Confidence: 0.92
      Time: 3421ms
   ✅ german_invoice_kyndryl_sample.pdf
      Invoice#: INV-2024-0315
      Confidence: 0.88
      Time: 4102ms
   ...
```

## 🔐 Security Notes

- Store sensitive credentials in `.env` file (not in version control)
- Use SSL/TLS for HANA connections in production
- Rotate API keys regularly
- Review exported data for PII before sharing

## 🐛 Troubleshooting

### "No invoices found"

Ensure PDF files are in the input directory:
```bash
ls -la input/*.pdf
```

### "LLM connection failed"

Check Ollama is running:
```bash
ollama list
ollama run minimax-m2.5:cloud "Hello"
```

### "HANA connection failed"

Install HANA driver:
```bash
pip install pyhdb
# Or download hdbcli from SAP
```

### Low confidence scores

- Ensure invoices are clear scans (not photos)
- Check OCR language includes German: `OCR_LANGUAGES=deu+eng`
- Try different extraction model

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a Pull Request

## 📧 Support

For issues and questions:
- Check the troubleshooting section
- Review pipeline logs: `cat idp_pipeline.log`
- Open an issue on GitHub

---

**Built with ❤️ for German Invoice Processing**
