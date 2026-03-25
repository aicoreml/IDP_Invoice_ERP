"""
IDP Pipeline Package
German Invoice Processing Pipeline for ERP/HANA Integration
"""

from pipeline.config import PipelineConfig, get_config, HANAConfig, APIConfig
from pipeline.invoice_extractor import GermanInvoiceExtractor, ExtractedInvoice
from pipeline.orchestrator import InvoicePipeline, PipelineResult, run_pipeline

__version__ = '1.0.0'
__all__ = [
    'PipelineConfig',
    'get_config',
    'HANAConfig',
    'APIConfig',
    'GermanInvoiceExtractor',
    'ExtractedInvoice',
    'InvoicePipeline',
    'PipelineResult',
    'run_pipeline',
]
