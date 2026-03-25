# IDP Rechnungsverarbeitung - Flussdiagramm

## 📊 Pipeline Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│              IDP RECHNUNGSVERARBEITUNG PIPELINE                 │
│            Stromrechnung Extraktion & Export                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  KONFIGURATION                                                  │
│  ───────────────                                                │
│  • EXPORT_FORMAT = csv                                          │
│  • VALIDATE_GERMAN_INVOICE = False                              │
│  • OCR_ENABLED = True                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 1: RECHNUNGEN ERKENNEN                                 │
│  ─────────────────────────                                      │
│  • input/ Ordner nach PDFs durchsuchen                          │
│  • Alle PDF-Dateien sammeln                                     │
│  • Alphabetisch sortieren                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 2: TEXT EXTRAKTION                                     │
│  ────────────────────────                                       │
│  • PyPDF2 / PyMuPDF extrahiert Text                             │
│  • OCR-Fallback (Tesseract, PaddleOCR)                          │
│  • Ausgabe: Rohtext                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 3: LLM FELDER EXTRAKTION                               │
│  ───────────────────────────                                    │
│  • Modell: minimax-m2.5:cloud (Ollama)                         │
│  • Temperatur: 0.1 (deterministisch)                            │
│  • Ausgabe: Strukturierte JSON-Daten                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 4: ZAHLEN PARSING                                      │
│  ───────────────────────                                        │
│  • Deutsche Zahlen konvertieren                                 │
│  • 40.000,00 → 40000.00                                         │
│  • Währungssymbole entfernen                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 5: DATENKLASSE FÜLLEN                                  │
│  ─────────────────────────                                      │
│  • ExtractedInvoice Objekt                                      │
│  • Alle Felder zuweisen                                         │
│  • Konfidenzwert berechnen                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 6: VALIDIERUNG (ÜBERSPRUNGEN)                          │
│  ─────────────────────────────                                  │
│  • §14 UStG Validierung deaktiviert                             │
│  • Alle Rechnungen als gültig markiert                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHRITT 7: CSV EXPORT                                          │
│  ───────────────────                                            │
│  • Nach Datum sortieren (neueste zuerst)                        │
│  • output/invoices_YYYYMMDD_HHMMSS.csv                          │
│  • output/line_items_YYYYMMDD_HHMMSS.csv                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AUSGABE                                                        │
│  ───────                                                        │
│  • CSV-Dateien für Datenbank-Import                             │
│  • Bereit für SAP HANA / PostgreSQL / MySQL                     │
│  • Excel-kompatibel                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Verarbeitungsschleife (pro Rechnung)

```
┌────────────────────────────────────────────────────────────────────┐
│                    FÜR JEDER RECHNUNG (6x)                         │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  1. PDF lesen   │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  2. Text        │
                          │     extrahieren │──→ raw_text
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  3. LLM         │
                          │     Extraktion  │──→ JSON
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  4. Zahlen      │
                          │     parsen      │──→ 40000.00
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  5. Datenklasse │
                          │     füllen      │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  6. Konfidenz   │
                          │     berechnen   │──→ 0.85
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │  7. Export      │
                          │     Liste       │
                          └─────────────────┘
```

---

## 📋 Datenflussdiagramm

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   EINGABE   │     │ VERARBEITUNG│     │   AUSGABE   │
│             │     │             │     │             │
│ input/      │────▶│  Extraktor  │────▶│ output/     │
│ ├── 1.pdf   │     │  ├── Text   │     │ ├── *.csv   │
│ ├── 2.pdf   │     │  ├── LLM    │     │ └── *.log   │
│ ├── 3.pdf   │     │  └── Parse  │     │
│ ├── 4.pdf   │     │             │     │
│ ├── 5.pdf   │     │  Validator  │     │
│ └── 6.pdf   │     │  (skip)     │     │
└─────────────┘     │             │     └─────────────┘
                    │  Exporter   │
                    │  └── CSV    │
                    └─────────────┘
```

---

## 🏗️ Komponentenarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│                         app/                                │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ pipeline/       │  │ exporters/   │  │ validators/   │ │
│  │ ├── config.py   │  │ ├── __init__.│  │ ├── german_   │ │
│  │ ├── orchestrator│  │ └── CSV      │  │ └── validator │ │
│  │ ├── invoice_    │  │   Exporter   │  └───────────────┘ │
│  │ └── extractor   │  └──────────────┘                    │
│  └─────────────────┘                                      │
│  ┌─────────────────┐  ┌──────────────┐                    │
│  │ document_       │  │ llm_client.  │                    │
│  │ processor.py    │  │ py           │                    │
│  │ (PyPDF2,        │  │ (Ollama,     │                    │
│  │  PyMuPDF)       │  │  minimax)    │                    │
│  └─────────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Extrahierte Felder

```
┌──────────────────────────────────────────────────────────────┐
│                    EXTRAKTIONSFELDER                         │
├──────────────────────────────────────────────────────────────┤
│  RECHNUNGSKOPF                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ invoice_number      → Rechnungsnummer                 │ │
│  │ invoice_date        → Rechnungsdatum (YYYY-MM-DD)     │ │
│  │ due_date            → Fälligkeitsdatum                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  VERKÄUFER (LIEFERANT)                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ vendor_name         → Lieferant                       │ │
│  │ vendor_vat_id       → MWST-Nr. (CHE-...)              │ │
│  │ vendor_number       → Kundennummer                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  BETRÄGE                                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ subtotal            → Nettobetrag                     │ │
│  │ tax_rate            → Steuersatz (8.1%, 7.7%)         │ │
│  │ tax_amount          → Steuerbetrag                    │ │
│  │ total               → Gesamtbetrag                    │ │
│  │ currency            → Währung (CHF/EUR)               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ZAHLUNG                                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ payment_terms       → Zahlungsbedingungen             │ │
│  │ iban                → IBAN                            │ │
│  │ payment_account     → Konto Zahlbar an                │ │
│  │ reference_number    → Referenznummer                  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 📈 Verarbeitungsergebnisse

```
┌──────────────────────────────────────────────────────────────┐
│                    ERGEBNISSE (6 RECHNUNGEN)                 │
├───────────────┬────────────┬──────────┬──────────────────────┤
│ RECHNUNG      │ DATUM      │ BETRAG   │ REFERENZ             │
├───────────────┼────────────┼──────────┼──────────────────────┤
│ 3032069       │ 2025-07-25 │ 210.55   │ 70 23000...03206    │
│ 3020954       │ 2025-04-01 │ 241.70   │ 70 23000...02095    │
│ 2728924       │ 2024-07-22 │ 206.55   │ 70 23000...72892    │
│ 2702925       │ 2024-04-20 │ 260.90   │ 70 23000...70292    │
│ 2674564       │ 2024-01-19 │ 170.90   │ 70 23000...67456    │
│ 2648917       │ 2023-10-20 │ 149.25   │ 70 23000...64891    │
├───────────────┴────────────┴──────────┴──────────────────────┤
│ GESAMT: CHF 1,240.05                                         │
│ KONFIDENZ: Ø 84.3%                                           │
│ DAUER: ~3 Minuten                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Schnellstart

```bash
# 1. Umgebung aktivieren
source /Users/usermacrtx/Documents/Demos/demos_env/bin/activate

# 2. PDFs in input/ kopieren
cp *.pdf input/

# 3. Pipeline starten
cd /Users/usermacrtx/Documents/Demos/IDP_App_Invoice_ERP_DE
python3 app/pipeline/orchestrator.py

# 4. Ausgabe prüfen
ls -la output/
cat output/invoices_*.csv
```

---

## ⚙️ Konfiguration

```
┌─────────────────────────────────────────────────────────────┐
│  UMGEBUNGSVARIABLEN                                         │
├──────────────────────────────┬──────────────────────────────┤
│ VARIABLE                     │ WERT                         │
├──────────────────────────────┼──────────────────────────────┤
│ PADDLE_PDX_DISABLE_...       │ True (schnellerer Start)     │
│ EXPORT_FORMAT                │ csv                          │
│ EXPORT_ON_VALIDATION_FAIL    │ True                         │
│ VALIDATE_GERMAN_INVOICE      │ False                        │
│ EXTRACTION_MODEL             │ minimax-m2.5:cloud           │
│ OCR_ENABLED                  │ True                         │
└──────────────────────────────┴──────────────────────────────┘
```

---

**Erstellt:** 25. März 2026  
**Version:** 1.0  
**Status:** ✅ Produktiv
