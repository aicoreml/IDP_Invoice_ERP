#!/bin/bash
# Streamlit UI Launcher for German Invoice IDP Pipeline

# Activate virtual environment
source /Users/usermacrtx/Documents/Demos/demos_env/bin/activate

# Change to project directory
cd /Users/usermacrtx/Documents/Demos/IDP_App_Invoice_ERP_DE

# Run Streamlit on port 8502 (8501 is used by RAG_with_ingestion_at_start)
# Added server.baseUrl for nginx proxy support
echo "Starting German Invoice IDP Pipeline UI..."
echo "Open http://localhost:8502 or https://gpt.myddns.me/invoice-erp/"
echo ""

streamlit run app/ui/streamlit_app.py \
    --server.port 8502 \
    --server.address localhost \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.baseUrlPath /invoice-erp \
    --server.enableXsrfProtection true \
    --server.enableCORS false
