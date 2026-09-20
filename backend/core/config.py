import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Project metadata
    PROJECT_NAME: str = "Contract Agentic Society (CAS)"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Gemini API Settings (SOLE LLM Provider)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT_SECONDS: float = 45.0

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cas_db"
    DATABASE_POOL_SIZE: int = 10

    # Optional Redis for caching / queuing
    REDIS_URL: Optional[str] = None

    # Fastn Organization and Real Workflows
    FASTN_ORG_ID: str = "personal_867cccac2ec39658a401"
    
    # Real Fastn Webhook Triggers
    FASTN_INTAKE_WEBHOOK_URL: str = (
        "https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/1211f7a1-39c5-44da-9b3c-718fff44ad7d"
    )
    FASTN_RISK_WEBHOOK_URL: str = (
        "https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/f31003e6-61ae-41c0-bef9-1647dd093d66"
    )
    FASTN_INBOUND_APPROVAL_WEBHOOK_URL: str = (
        "https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/a23aaf8f-ecb4-4bc6-9281-f9f110f06919"
    )
    FASTN_INBOUND_NEGOTIATION_WEBHOOK_URL: str = (
        "https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/7c668bc4-6ddc-4904-8b8f-74554a14c145"
    )

    # 10 Fastn Workflows (5 Deployed Core + 5 Domain Escalation & Archive)
    FASTN_INTAKE_WORKFLOW_ID: str = "wf_0c61baf31b93"
    FASTN_RISK_WORKFLOW_ID: str = "wf_7330f03b75f6"
    FASTN_APPROVAL_WORKFLOW_ID: str = "wf_5ccc14b11936"
    FASTN_OBLIGATION_WORKFLOW_ID: str = "wf_2783a17803cc"
    FASTN_RENEWAL_WORKFLOW_ID: str = "wf_ef794f8dd239"
    FASTN_COMPLIANCE_WORKFLOW_ID: str = "wf_compliance_escalation"
    FASTN_NEGOTIATION_WORKFLOW_ID: str = "wf_negotiation_update"
    FASTN_DEADLINE_WORKFLOW_ID: str = "wf_deadline_escalation"
    FASTN_DISPUTE_WORKFLOW_ID: str = "wf_dispute_escalation"
    FASTN_DECISION_ARCHIVE_WORKFLOW_ID: str = "wf_decision_archive"

    # Security & Guardrails
    MAX_CONTRACT_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    AUDIT_LOG_RETENTION_DAYS: int = 90


settings = Settings()
