#!/usr/bin/env python3
"""
Streamlit UI for German Invoice IDP Pipeline
With OCR/Text Preview and CSV/HANA Export
"""

import os
import sys
import json
import csv
import io
from pathlib import Path
from datetime import datetime

# Add app directory to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'app'))

import streamlit as st
import pandas as pd

# Plotly optional
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# PDF to image conversion
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

# PyMuPDF for page count
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'invoices' not in st.session_state:
    st.session_state.invoices = []
if 'db_config' not in st.session_state:
    st.session_state.db_config = {
        'host': 'localhost',
        'port': 30015,
        'user': 'SYSTEM',
        'password': '',
        'schema': 'INVOICES'
    }

st.set_page_config(
    page_title="German Invoice IDP",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 German Invoice IDP Pipeline")
st.markdown("Extract structured data from German invoices and export to ERP/HANA")

# Sidebar config
with st.sidebar:
    st.header("⚙️ Configuration")
    export_format = st.selectbox("Export Format", ['json', 'csv', 'xml'])
    confidence = st.slider("Confidence Threshold", 0.0, 1.0, 0.7)
    
    st.divider()
    st.subheader("Status")
    if HAS_PDF2IMAGE:
        st.success("✅ PDF preview enabled")
    else:
        st.warning("⚠️ Install pdf2image: pip install pdf2image")
    if HAS_PYMUPDF:
        st.success("✅ PyMuPDF available")

# Main tabs
tab_upload, tab_results, tab_preview, tab_analytics = st.tabs([
    "📤 Upload", "📊 Results", "👁️ Preview", "📈 Analytics"
])

with tab_upload:
    st.header("Upload Invoices")
    
    uploaded = st.file_uploader(
        "Drop PDF invoices here",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True
    )
    
    if uploaded:
        # Save to input folder
        input_dir = Path("./input/temp")
        input_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = []
        for f in uploaded:
            temp_path = input_dir / f.name
            with open(temp_path, 'wb') as fp:
                fp.write(f.getvalue())
            file_paths.append(str(temp_path))
        
        st.write(f"✅ {len(uploaded)} file(s) ready")
        
        if st.button("🚀 Process Invoices", type="primary"):
            with st.spinner("Processing invoices..."):
                try:
                    from pipeline.config import PipelineConfig
                    from pipeline.orchestrator import InvoicePipeline
                    
                    config = PipelineConfig(
                        input_dir=Path("./input"),
                        output_dir=Path("./output"),
                        export_format=export_format,
                        confidence_threshold=confidence,
                    )
                    config.ensure_directories()
                    
                    pipeline = InvoicePipeline(config)
                    result = pipeline.run(invoice_paths=file_paths)
                    
                    st.session_state.result = result
                    st.session_state.invoices = result.extraction_results
                    
                    st.success(f"✅ Processed {result.successful_extractions} invoices!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.exception(e)
    
    # Show last result
    if st.session_state.result:
        r = st.session_state.result
        st.subheader("Results Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", r.total_invoices)
        c2.metric("Extracted", r.successful_extractions)
        c3.metric("Validated", r.validated_count)
        c4.metric("Duration", f"{r.total_duration_seconds:.1f}s")

with tab_results:
    if not st.session_state.invoices:
        st.info("Process invoices first to see results")
    else:
        st.header("Extracted Data")

        # Build table
        rows = []
        for inv in st.session_state.invoices:
            rows.append({
                'File': Path(inv['file']).name,
                'Invoice': inv.get('invoice_number', 'N/A'),
                'Date': inv.get('invoice_date', ''),
                'Vendor': inv.get('vendor_name', '')[:30],
                'Total': f"{inv.get('currency', 'EUR')} {inv.get('total', 0):.2f}",
                'Confidence': f"{inv.get('confidence', 0):.2f}",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        st.divider()
        
        # Export buttons
        st.subheader("📤 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            if st.button("📥 Export CSV", type="primary", use_container_width=True):
                try:
                    # Build CSV in memory
                    output = io.StringIO()
                    fieldnames = [
                        'source_file', 'invoice_number', 'invoice_date', 'due_date',
                        'vendor_name', 'vendor_vat_id', 'vendor_number',
                        'customer_name', 'customer_vat_id',
                        'subtotal', 'tax_rate', 'tax_amount', 'total', 'currency',
                        'payment_terms', 'iban', 'bic', 'payment_account', 'reference_number',
                        'confidence_score'
                    ]
                    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    
                    for inv in st.session_state.invoices:
                        row = {
                            'source_file': inv.get('file', ''),
                            'invoice_number': inv.get('invoice_number', ''),
                            'invoice_date': inv.get('invoice_date', ''),
                            'due_date': inv.get('due_date', ''),
                            'vendor_name': inv.get('vendor_name', ''),
                            'vendor_vat_id': inv.get('vendor_vat_id', ''),
                            'vendor_number': inv.get('vendor_number', ''),
                            'customer_name': inv.get('customer_name') or '[PLACEHOLDER - Privacy Redacted]',
                            'customer_vat_id': inv.get('customer_vat_id', ''),
                            'subtotal': inv.get('subtotal', 0),
                            'tax_rate': inv.get('tax_rate', 0),
                            'tax_amount': inv.get('tax_amount', 0),
                            'total': inv.get('total', 0),
                            'currency': inv.get('currency', 'EUR'),
                            'payment_terms': inv.get('payment_terms', ''),
                            'iban': inv.get('iban', ''),
                            'bic': inv.get('bic', ''),
                            'payment_account': inv.get('payment_account', ''),
                            'reference_number': inv.get('reference_number', ''),
                            'confidence_score': inv.get('confidence', 0),
                        }
                        writer.writerow(row)
                    
                    csv_data = output.getvalue()
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"invoices_{timestamp}.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
                    st.success("✅ CSV ready for download")
                    
                except Exception as e:
                    st.error(f"CSV export failed: {e}")
        
        with col2:
            # JSON Export
            if st.button("📄 Export JSON", use_container_width=True):
                try:
                    json_data = json.dumps(st.session_state.invoices, indent=2, ensure_ascii=False, default=str)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_data,
                        file_name=f"invoices_{timestamp}.json",
                        mime="application/json",
                        key="download_json"
                    )
                    st.success("✅ JSON ready for download")
                    
                except Exception as e:
                    st.error(f"JSON export failed: {e}")
        
        with col3:
            # HANA DB Export
            if st.button("🗄️ Send to HANA DB", use_container_width=True):
                # Show HANA config in expander
                with st.expander("🔧 HANA Database Configuration"):
                    with st.form("hana_config_form"):
                        hana_host = st.text_input("Host", value=st.session_state.db_config['host'])
                        hana_port = st.number_input("Port", value=st.session_state.db_config['port'], min_value=1)
                        hana_user = st.text_input("User", value=st.session_state.db_config['user'])
                        hana_password = st.text_input("Password", type="password", value=st.session_state.db_config['password'])
                        hana_schema = st.text_input("Schema", value=st.session_state.db_config['schema'])
                        
                        submit_hana = st.form_submit_button("🚀 Insert to HANA", type="primary")
                        
                        if submit_hana:
                            st.session_state.db_config = {
                                'host': hana_host,
                                'port': hana_port,
                                'user': hana_user,
                                'password': hana_password,
                                'schema': hana_schema
                            }
                            
                            with st.spinner("Connecting to HANA and inserting invoices..."):
                                try:
                                    from pipeline.config import HANAConfig
                                    from exporters import HANAExporter, ExportResult
                                    
                                    # Create HANA config
                                    hana_config = HANAConfig(
                                        host=hana_host,
                                        port=hana_port,
                                        user=hana_user,
                                        password=hana_password,
                                        schema=hana_schema
                                    )
                                    
                                    # Get invoices from pipeline result
                                    if st.session_state.result:
                                        # Extract ExtractedInvoice objects from results
                                        from pipeline.invoice_extractor import ExtractedInvoice
                                        
                                        invoice_objects = []
                                        for inv_result in st.session_state.result.extraction_results:
                                            inv = ExtractedInvoice(
                                                source_file=inv_result.get('file', ''),
                                                invoice_number=str(inv_result.get('invoice_number', '')),
                                                invoice_date=inv_result.get('invoice_date', ''),
                                                due_date=inv_result.get('due_date', ''),
                                                vendor_name=inv_result.get('vendor_name', ''),
                                                vendor_vat_id=inv_result.get('vendor_vat_id', ''),
                                                customer_name=inv_result.get('customer_name'),
                                                subtotal=inv_result.get('subtotal'),
                                                tax_rate=inv_result.get('tax_rate'),
                                                tax_amount=inv_result.get('tax_amount'),
                                                total=inv_result.get('total'),
                                                currency=inv_result.get('currency', 'EUR'),
                                                payment_terms=inv_result.get('payment_terms'),
                                                iban=inv_result.get('iban'),
                                                bic=inv_result.get('bic'),
                                                confidence_score=inv_result.get('confidence', 0),
                                            )
                                            invoice_objects.append(inv)
                                        
                                        # Export to HANA
                                        exporter = HANAExporter(hana_config)
                                        result = exporter.export(invoice_objects)
                                        
                                        if result.success:
                                            st.success(f"✅ {result.exported_count} invoices inserted to HANA")
                                            st.info(result.message)
                                        else:
                                            st.error(f"❌ HANA export failed: {result.error}")
                                    else:
                                        st.error("No invoice data available")
                                        
                                except ImportError as e:
                                    st.error(f"HANA driver not installed. Install with: pip install hdbcli or pip install pyhdb")
                                    st.code(str(e))
                                except Exception as e:
                                    st.error(f"HANA export failed: {e}")
                                    st.exception(e)

with tab_preview:
    st.header("👁️ OCR/Text Preview")
    
    if not st.session_state.invoices:
        st.info("Process invoices first to see preview")
    else:
        # File selector
        file_options = [Path(inv['file']).name for inv in st.session_state.invoices]
        selected_file = st.selectbox("Select Invoice", options=file_options)
        
        if selected_file:
            idx = file_options.index(selected_file)
            inv_data = st.session_state.invoices[idx]
            file_path = inv_data['file']
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📄 Document Preview")
                
                # Show PDF preview if available
                if HAS_PDF2IMAGE and file_path.endswith('.pdf'):
                    try:
                        # Get page count
                        if HAS_PYMUPDF:
                            doc = fitz.open(file_path)
                            page_count = len(doc)
                        else:
                            page_count = 1
                        
                        # Page selector
                        if page_count > 1:
                            page_num = st.slider("Page", 1, page_count, 1, key=f"page_{file_path}")
                        else:
                            page_num = 1
                        
                        # Render page
                        images = convert_from_path(file_path, first_page=page_num, last_page=page_num, dpi=150)
                        if images:
                            st.image(images[0], caption=f"Page {page_num} of {page_count}", width=600)
                        else:
                            st.warning("Could not render PDF preview")
                            
                    except Exception as e:
                        st.error(f"Preview error: {e}")
                        
                elif file_path.endswith(('.png', '.jpg', '.jpeg')):
                    st.image(file_path, caption=Path(file_path).name, width=600)
                else:
                    st.info("📄 " + Path(file_path).name)
            
            with col2:
                st.subheader("📝 Extracted Text")
                
                # Get extracted text
                raw_text = inv_data.get('raw_text', 'No text available')
                st.text_area("OCR/Extracted Text", value=raw_text, height=300)
                
                st.subheader("📋 Extracted Fields")
                fields = {
                    'Invoice Number': inv_data.get('invoice_number', 'N/A'),
                    'Invoice Date': inv_data.get('invoice_date', 'N/A'),
                    'Due Date': inv_data.get('due_date', 'N/A'),
                    'Vendor': inv_data.get('vendor_name', 'N/A'),
                    'Vendor VAT ID': inv_data.get('vendor_vat_id', 'N/A'),
                    'Vendor Number': inv_data.get('vendor_number', 'N/A'),
                    'Customer': inv_data.get('customer_name') or '[PLACEHOLDER - Privacy Redacted]',
                    'Subtotal': f"{inv_data.get('currency', 'EUR')} {inv_data.get('subtotal', 0):.2f}",
                    'Tax Rate': f"{inv_data.get('tax_rate', 0):.1f}%",
                    'Tax Amount': f"{inv_data.get('currency', 'EUR')} {inv_data.get('tax_amount', 0):.2f}",
                    'Total': f"{inv_data.get('currency', 'EUR')} {inv_data.get('total', 0):.2f}",
                    'Payment Terms': inv_data.get('payment_terms', 'N/A'),
                    'IBAN': inv_data.get('iban', 'N/A'),
                    'Reference Number': inv_data.get('reference_number', 'N/A'),
                    'Payment Account': inv_data.get('payment_account', 'N/A'),
                    'Confidence': f"{inv_data.get('confidence', 0):.2f}",
                }
                st.json(fields)

with tab_analytics:
    if not st.session_state.invoices or not HAS_PLOTLY:
        st.info("Process invoices first (plotly required for charts)")
    else:
        st.header("Analytics")

        col1, col2 = st.columns(2)

        with col1:
            # Confidence chart
            scores = [inv.get('confidence', 0) for inv in st.session_state.invoices]
            fig = px.histogram(x=scores, nbins=10, title="Confidence Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Amounts chart
            totals = [inv.get('total', 0) for inv in st.session_state.invoices]
            currencies = [inv.get('currency', 'EUR') for inv in st.session_state.invoices]
            labels = [Path(inv['file']).name[:15] for inv in st.session_state.invoices]
            
            # Color by currency
            fig = px.bar(x=labels, y=totals, color=currencies, 
                        title="Invoice Amounts by Currency",
                        labels={'x': 'Invoice', 'y': 'Amount', 'color': 'Currency'})
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.divider()
st.caption("German Invoice IDP Pipeline | Built with Streamlit | Export: CSV, JSON, SAP HANA")
