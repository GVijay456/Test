"""AAI-XXXX error code registry.

Ranges:
  AAI-1xxx  Auth / identity
  AAI-2xxx  Agent / run lifecycle
  AAI-3xxx  LLM / model
  AAI-4xxx  Tool / plugin
  AAI-5xxx  Memory / RAG
  AAI-6xxx  Config / tenant
  AAI-9xxx  Internal / infrastructure
"""
from enum import StrEnum


class ErrorCode(StrEnum):
    # Auth
    AUTH_INVALID_API_KEY       = "AAI-1001"
    AUTH_API_KEY_EXPIRED       = "AAI-1002"
    AUTH_JWT_INVALID           = "AAI-1010"
    AUTH_JWT_EXPIRED           = "AAI-1011"
    AUTH_JWT_WRONG_AUDIENCE    = "AAI-1012"
    AUTH_MTLS_CERT_INVALID     = "AAI-1020"
    AUTH_IP_BLOCKED            = "AAI-1030"
    AUTH_RATE_LIMITED          = "AAI-1040"

    # AuthZ
    AUTHZ_FORBIDDEN            = "AAI-1050"
    AUTHZ_POLICY_DENIED        = "AAI-1051"

    # Agent / run lifecycle
    RUN_NOT_FOUND              = "AAI-2001"
    RUN_ALREADY_EXISTS         = "AAI-2002"   # idempotency key collision
    RUN_CANCELLED              = "AAI-2003"
    RUN_TIMEOUT                = "AAI-2004"
    RUN_MAX_STEPS_EXCEEDED     = "AAI-2010"
    RUN_BUDGET_EXCEEDED        = "AAI-2020"

    # LLM / model
    LLM_PROVIDER_ERROR         = "AAI-3001"
    LLM_CONTEXT_OVERFLOW       = "AAI-3002"
    LLM_RATE_LIMITED           = "AAI-3003"
    LLM_CIRCUIT_OPEN           = "AAI-3004"
    LLM_SCHEMA_VIOLATION       = "AAI-3010"
    LLM_PROMPT_INJECTION       = "AAI-3020"
    LLM_HALLUCINATION_DETECTED = "AAI-3030"

    # Tool / plugin
    TOOL_NOT_FOUND             = "AAI-4001"
    TOOL_EXECUTION_ERROR       = "AAI-4002"
    TOOL_TIMEOUT               = "AAI-4003"
    TOOL_SCHEMA_VIOLATION      = "AAI-4010"
    PLUGIN_UNTRUSTED           = "AAI-4020"
    PLUGIN_MANIFEST_INVALID    = "AAI-4021"

    # Memory / RAG
    MEMORY_STORE_ERROR         = "AAI-5001"
    MEMORY_RETRIEVAL_ERROR     = "AAI-5002"
    EMBEDDING_ERROR            = "AAI-5010"

    # Config / tenant
    TENANT_NOT_FOUND           = "AAI-6001"
    TENANT_SUSPENDED           = "AAI-6002"
    CONFIG_INVALID             = "AAI-6010"
    FEATURE_NOT_ENABLED        = "AAI-6020"

    # Internal / infra
    INTERNAL_ERROR             = "AAI-9001"
    DATABASE_ERROR             = "AAI-9010"
    CACHE_ERROR                = "AAI-9011"
    MESSAGE_BUS_ERROR          = "AAI-9012"
    VAULT_ERROR                = "AAI-9020"
