"""
Configuration management
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    db_path: str = Field(default="data/compliance.db", env="DB_PATH")
    db_password: Optional[str] = Field(default=None, env="DB_PASSWORD")
    
    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Encryption
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    encryption_password: Optional[str] = Field(default=None, env="ENCRYPTION_PASSWORD")
    
    # Application
    app_name: str = "JDK Compliance Scanner"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Scanning
    default_thread_count: int = Field(default=5, env="DEFAULT_THREAD_COUNT")
    default_scan_mode: str = Field(default="Parallel", env="DEFAULT_SCAN_MODE")
    
    # Reporting
    report_template_dir: str = Field(
        default="core/reporting/templates",
        env="REPORT_TEMPLATE_DIR"
    )
    
    # Email (optional)
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file (like ADMIN_PASSWORD)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def set_settings(settings: Settings):
    """Set application settings"""
    global _settings
    _settings = settings

