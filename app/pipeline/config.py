"""
Pipeline Configuration - ERP/HANA connection settings and pipeline parameters
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json


@dataclass
class HANAConfig:
    """SAP HANA database configuration."""
    host: str = "localhost"
    port: int = 30015
    user: str = "SYSTEM"
    password: str = ""
    tenant: str = "SYSTEMDB"
    schema: str = "INVOICES"
    use_ssl: bool = False
    ssl_validate_certificate: bool = True
    
    @classmethod
    def from_env(cls) -> "HANAConfig":
        return cls(
            host=os.getenv("HANA_HOST", "localhost"),
            port=int(os.getenv("HANA_PORT", "30015")),
            user=os.getenv("HANA_USER", "SYSTEM"),
            password=os.getenv("HANA_PASSWORD", ""),
            tenant=os.getenv("HANA_TENANT", "SYSTEMDB"),
            schema=os.getenv("HANA_SCHEMA", "INVOICES"),
            use_ssl=os.getenv("HANA_USE_SSL", "false").lower() == "true",
            ssl_validate_certificate=os.getenv("HANA_SSL_VALIDATE", "true").lower() == "true",
        )
    
    def get_connection_string(self) -> str:
        """Return HANA connection string."""
        return f"{self.host}:{self.port}"


@dataclass
class APIConfig:
    """REST API configuration for ERP integration."""
    base_url: str = "http://localhost:8080"
    api_key: str = ""
    username: str = ""
    password: str = ""
    timeout: int = 30
    verify_ssl: bool = True
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(
            base_url=os.getenv("ERP_API_URL", "http://localhost:8080"),
            api_key=os.getenv("ERP_API_KEY", ""),
            username=os.getenv("ERP_API_USERNAME", ""),
            password=os.getenv("ERP_API_PASSWORD", ""),
            timeout=int(os.getenv("ERP_API_TIMEOUT", "30")),
            verify_ssl=os.getenv("ERP_API_VERIFY_SSL", "true").lower() == "true",
        )


@dataclass
class PipelineConfig:
    """IDP Pipeline configuration."""
    # Input/Output
    input_dir: Path = field(default_factory=lambda: Path("./input"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    processed_dir: Path = field(default_factory=lambda: Path("./data/processed"))
    failed_dir: Path = field(default_factory=lambda: Path("./data/failed"))
    
    # Processing
    batch_size: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    ocr_enabled: bool = True
    ocr_languages: str = "deu+eng"
    
    # Extraction
    extraction_model: str = "minimax-m2.5:cloud"
    extraction_timeout: int = 120
    confidence_threshold: float = 0.7
    
    # Validation
    validate_german_invoice: bool = True
    require_tax_id: bool = True
    require_invoice_number: bool = True
    
    # Export
    export_format: str = "json"  # json, csv, xml, hana, api
    export_on_success: bool = True
    export_on_validation_fail: bool = False
    
    # Database
    hana: HANAConfig = field(default_factory=HANAConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./idp_pipeline.log"
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        return cls(
            input_dir=Path(os.getenv("INPUT_DIR", "./input")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./output")),
            processed_dir=Path(os.getenv("PROCESSED_DIR", "./data/processed")),
            failed_dir=Path(os.getenv("FAILED_DIR", "./data/failed")),
            batch_size=int(os.getenv("BATCH_SIZE", "10")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
            ocr_enabled=os.getenv("OCR_ENABLED", "true").lower() == "true",
            ocr_languages=os.getenv("OCR_LANGUAGES", "deu+eng"),
            extraction_model=os.getenv("EXTRACTION_MODEL", "minimax-m2.5:cloud"),
            extraction_timeout=int(os.getenv("EXTRACTION_TIMEOUT", "120")),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
            validate_german_invoice=os.getenv("VALIDATE_GERMAN_INVOICE", "true").lower() == "true",
            require_tax_id=os.getenv("REQUIRE_TAX_ID", "true").lower() == "true",
            require_invoice_number=os.getenv("REQUIRE_INVOICE_NUMBER", "true").lower() == "true",
            export_format=os.getenv("EXPORT_FORMAT", "json"),
            export_on_success=os.getenv("EXPORT_ON_SUCCESS", "true").lower() == "true",
            export_on_validation_fail=os.getenv("EXPORT_ON_VALIDATION_FAIL", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "./idp_pipeline.log"),
            hana=HANAConfig.from_env(),
            api=APIConfig.from_env(),
        )
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        for dir_path in [self.output_dir, self.processed_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "processed_dir": str(self.processed_dir),
            "batch_size": self.batch_size,
            "extraction_model": self.extraction_model,
            "confidence_threshold": self.confidence_threshold,
            "export_format": self.export_format,
            "hana_host": self.hana.host,
            "api_url": self.api.base_url,
        }


# Global config instance
_config: Optional[PipelineConfig] = None


def get_config() -> PipelineConfig:
    """Get global pipeline configuration."""
    global _config
    if _config is None:
        _config = PipelineConfig.from_env()
        _config.ensure_directories()
    return _config


def load_config_from_file(config_path: str) -> PipelineConfig:
    """Load configuration from JSON file."""
    global _config
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # Update environment variables from config
    for key, value in config_data.items():
        env_key = key.upper()
        if isinstance(value, dict):
            # Nested config (hana, api)
            for sub_key, sub_value in value.items():
                env_var = f"{env_key}_{sub_key.upper()}"
                os.environ[env_var] = str(sub_value)
        else:
            os.environ[env_key] = str(value)
    
    _config = PipelineConfig.from_env()
    _config.ensure_directories()
    return _config
