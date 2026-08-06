"""
Configuration settings for Order Extraction Agent
"""

from typing import Dict, Any
from pathlib import Path
import os


class Config:
    """Application configuration"""
    
    # Ollama Settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))
    
    # PDF Processing
    PDF_CHUNK_SIZE = int(os.getenv("PDF_CHUNK_SIZE", "2000"))
    PDF_CHUNK_OVERLAP = int(os.getenv("PDF_CHUNK_OVERLAP", "200"))
    PDF_MAX_SIZE_MB = float(os.getenv("PDF_MAX_SIZE_MB", "10.0"))
    
    # Confidence Thresholds
    HIGH_CONFIDENCE = 0.8
    MEDIUM_CONFIDENCE = 0.5
    LOW_CONFIDENCE = 0.3
    
    # Required Fields
    CRITICAL_FIELDS = [
        "customer_name",
        "items"
    ]
    
    IMPORTANT_FIELDS = [
        "customer_email",
        "customer_phone",
        "shipping_address",
        "total_amount"
    ]
    
    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/orders.db")
    ENABLE_DATABASE = os.getenv("ENABLE_DATABASE", "false").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/agent.log")
    
    # Streamlit
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # Processing
    ENABLE_STREAMING = True
    SHOW_INTERMEDIATE_STEPS = True
    
    @classmethod
    def get_llm_config(cls) -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            "base_url": cls.OLLAMA_BASE_URL,
            "model": cls.DEFAULT_MODEL,
            "temperature": cls.LLM_TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS
        }
    
    @classmethod
    def get_pdf_config(cls) -> Dict[str, Any]:
        """Get PDF processing configuration"""
        return {
            "chunk_size": cls.PDF_CHUNK_SIZE,
            "chunk_overlap": cls.PDF_CHUNK_OVERLAP,
            "max_size_mb": cls.PDF_MAX_SIZE_MB
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check Ollama URL
        if not cls.OLLAMA_BASE_URL.startswith("http"):
            errors.append("OLLAMA_BASE_URL must start with http:// or https://")
        
        # Check temperature range
        if not 0 <= cls.LLM_TEMPERATURE <= 1:
            errors.append("LLM_TEMPERATURE must be between 0 and 1")
        
        # Check thresholds
        if not (0 <= cls.LOW_CONFIDENCE < cls.MEDIUM_CONFIDENCE < cls.HIGH_CONFIDENCE <= 1):
            errors.append("Confidence thresholds must be in ascending order and between 0 and 1")
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True


# Environment-specific configurations

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG_MODE = True
    LOG_LEVEL = "DEBUG"
    SHOW_INTERMEDIATE_STEPS = True


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG_MODE = False
    LOG_LEVEL = "WARNING"
    SHOW_INTERMEDIATE_STEPS = False
    ENABLE_DATABASE = True


class TestingConfig(Config):
    """Testing environment configuration"""
    DEFAULT_MODEL = "llama3.2:1b"  # Faster for testing
    DATABASE_PATH = ":memory:"  # In-memory database
    LOG_LEVEL = "DEBUG"


# Select configuration based on environment
ENV = os.getenv("APP_ENV", "development").lower()

if ENV == "production":
    config = ProductionConfig()
elif ENV == "testing":
    config = TestingConfig()
else:
    config = DevelopmentConfig()


# Validate configuration on import
if not config.validate():
    raise ValueError("Invalid configuration. Please check settings.")
