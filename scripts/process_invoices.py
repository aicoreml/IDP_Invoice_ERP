#!/usr/bin/env python3
"""
Batch Invoice Processor
Process all invoices in the input folder and export to configured backend
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

from pipeline.config import PipelineConfig, load_config_from_file
from pipeline.orchestrator import InvoicePipeline, run_pipeline

def main():
    parser = argparse.ArgumentParser(
        description='Process German invoices and export to ERP/HANA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all invoices in default input folder
  python scripts/process_invoices.py

  # Process with custom config file
  python scripts/process_invoices.py --config config.json

  # Process specific files
  python scripts/process_invoices.py --files input/inv1.pdf input/inv2.pdf

  # Export to HANA
  python scripts/process_invoices.py --export hana --hana-host myhana.server.com

  # Export to REST API
  python scripts/process_invoices.py --export api --api-url http://erp.local:8080
        """
    )
    
    # Configuration
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to JSON configuration file'
    )
    
    # Input options
    parser.add_argument(
        '--input-dir', '-i',
        type=str,
        default='./input',
        help='Input directory containing invoices (default: ./input)'
    )
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        type=str,
        help='Specific invoice files to process'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./output',
        help='Output directory for exported data (default: ./output)'
    )
    parser.add_argument(
        '--export', '-e',
        type=str,
        choices=['json', 'csv', 'xml', 'hana', 'api', 'all'],
        default='json',
        help='Export format (default: json)'
    )
    
    # HANA options
    parser.add_argument(
        '--hana-host',
        type=str,
        help='SAP HANA host'
    )
    parser.add_argument(
        '--hana-port',
        type=int,
        default=30015,
        help='SAP HANA port (default: 30015)'
    )
    parser.add_argument(
        '--hana-user',
        type=str,
        help='SAP HANA username'
    )
    parser.add_argument(
        '--hana-password',
        type=str,
        help='SAP HANA password'
    )
    parser.add_argument(
        '--hana-schema',
        type=str,
        default='INVOICES',
        help='SAP HANA schema (default: INVOICES)'
    )
    
    # API options
    parser.add_argument(
        '--api-url',
        type=str,
        help='REST API base URL'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='REST API key'
    )
    
    # Processing options
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Skip German invoice validation'
    )
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.7,
        help='Minimum confidence threshold (default: 0.7)'
    )
    parser.add_argument(
        '--ocr-languages',
        type=str,
        default='deu+eng',
        help='OCR languages (default: deu+eng)'
    )
    
    # Logging
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='./idp_pipeline.log',
        help='Log file path (default: ./idp_pipeline.log)'
    )
    
    # Output
    parser.add_argument(
        '--output-result',
        type=str,
        help='Save pipeline result to JSON file'
    )
    
    args = parser.parse_args()
    
    # Load or create configuration
    if args.config:
        config = load_config_from_file(args.config)
    else:
        config = PipelineConfig.from_env()
    
    # Override with command line arguments
    config.input_dir = Path(args.input_dir)
    config.output_dir = Path(args.output_dir)
    config.export_format = args.export
    config.validate_german_invoice = not args.no_validation
    config.confidence_threshold = args.confidence_threshold
    config.ocr_languages = args.ocr_languages
    config.log_level = args.log_level
    config.log_file = args.log_file
    
    # Override HANA config
    if args.hana_host:
        config.hana.host = args.hana_host
    if args.hana_port:
        config.hana.port = args.hana_port
    if args.hana_user:
        config.hana.user = args.hana_user
    if args.hana_password:
        config.hana.password = args.hana_password
    if args.hana_schema:
        config.hana.schema = args.hana_schema
    
    # Override API config
    if args.api_url:
        config.api.base_url = args.api_url
    if args.api_key:
        config.api.api_key = args.api_key
    
    # Ensure directories exist
    config.ensure_directories()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file, encoding='utf-8'),
            logging.StreamHandler(),
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("German Invoice Processing Pipeline")
    logger.info("=" * 60)
    logger.info(f"Input directory: {config.input_dir}")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info(f"Export format: {config.export_format}")
    
    # Create and run pipeline
    pipeline = InvoicePipeline(config)
    
    try:
        result = pipeline.run(invoice_paths=args.files)
        
        # Save result if requested
        if args.output_result:
            with open(args.output_result, 'w', encoding='utf-8') as f:
                f.write(result.to_json(indent=2))
            logger.info(f"Pipeline result saved to: {args.output_result}")
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except KeyboardInterrupt:
        logger.error("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
