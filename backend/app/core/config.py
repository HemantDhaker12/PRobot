from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_ENV: str = Field(default="development", description="Application environment (development/production)")
    LOG_LEVEL: str = Field(default="INFO", description="Global logging level")

    # Database Settings
    POSTGRES_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/probot",
        description="PostgreSQL Database Connection URL",
    )

    # Vector Store Settings
    CHROMA_PATH: str = Field(
        default="./chroma_db",
        description="Path to store local ChromaDB data",
    )

    # Redis Settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for Celery and caching",
    )

    # GitHub Settings
    GITHUB_TOKEN: str = Field(
        default="",
        description="GitHub Personal Access Token for API requests",
    )
    GITHUB_WEBHOOK_SECRET: str = Field(
        default="",
        description="Secret key to verify GitHub webhook payloads",
    )

    # LLM Settings
    GROQ_API_KEY: str = Field(
        default="",
        description="Groq API key for Llama LLM access",
    )

    # Pydantic settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global settings instance
settings = Settings()


import os
import sys
import logging
from pathlib import Path


def check_env_source(key: str) -> str:
    if key in os.environ:
        return "system environment"
    if Path(".env").exists():
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.strip().startswith(key):
                        return ".env file"
        except Exception:
            pass
    return "default/unknown"


def validate_and_log_settings() -> None:
    placeholders = {
        "your_github_token_here",
        "your_webhook_secret_here",
        "your_groq_api_key_here",
    }

    # Check if running under pytest, alembic, or other CLI tools
    is_testing = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
    
    # Try to safely check sys.argv[0] for celery/uvicorn
    sys_argv_0 = sys.argv[0] if sys.argv else ""
    is_operational_service = any(name in sys_argv_0 for name in ("uvicorn", "celery"))
    
    # We only enforce strict exit for operational services (API/worker)
    bypass_exit = not is_operational_service or is_testing

    has_dotenv = Path(".env").exists()

    diag_lines = [
        "--- Environment Diagnostics ---",
        f"Dotenv (.env) file found on disk: {has_dotenv}"
    ]

    detected_placeholders = []

    for key, val in [
        ("GITHUB_WEBHOOK_SECRET", settings.GITHUB_WEBHOOK_SECRET),
        ("GITHUB_TOKEN", settings.GITHUB_TOKEN),
        ("GROQ_API_KEY", settings.GROQ_API_KEY),
    ]:
        val_len = len(val) if val else 0
        source = check_env_source(key)
        is_placeholder = val in placeholders
        if is_placeholder:
            detected_placeholders.append(key)

        diag_lines.append(
            f"Setting: {key} | Length: {val_len} | Loaded from: {source} | Placeholder detected: {is_placeholder}"
        )
    diag_lines.append("--------------------------------")

    for line in diag_lines:
        print(line, file=sys.stdout)
        logging.info(line)

    if detected_placeholders:
        for key in detected_placeholders:
            err_msg = f"Invalid configuration: {key} is still using placeholder value."
            print(f"CRITICAL ERROR: {err_msg}", file=sys.stderr)
            logging.critical(err_msg)
        if not bypass_exit:
            print("CRITICAL: Failing application startup due to invalid configuration placeholders.", file=sys.stderr)
            sys.exit(1)
        else:
            print("WARNING: Bypassing startup exit in non-operational/testing environment.", file=sys.stderr)


# Run validation immediately on import
validate_and_log_settings()

