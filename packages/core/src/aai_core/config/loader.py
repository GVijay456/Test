"""Platform configuration — YAML file + env var overrides via Pydantic Settings."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_DB_")

    url: str = "postgresql+asyncpg://aai:aai@localhost:5432/aai"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_REDIS_")

    url: str = "redis://localhost:6379/0"
    max_connections: int = 50


class VaultConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_VAULT_")

    addr: str = "http://localhost:8200"
    # Auth method: "token" | "kubernetes" | "aws"
    auth_method: str = "token"
    token: SecretStr | None = None
    role: str | None = None                 # for kubernetes auth
    mount_path: str = "secret"


class NATSConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_NATS_")

    url: str = "nats://localhost:4222"
    stream_name: str = "AAI_EVENTS"
    consumer_group: str = "aai-workers"


class QdrantConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_QDRANT_")

    url: str = "http://localhost:6333"
    api_key: SecretStr | None = None


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_LLM_")

    # Default provider: "litellm" | "ollama" | "vllm"
    provider: str = "litellm"
    default_model: str = "gpt-4o-mini"
    litellm_proxy_url: str | None = None
    ollama_url: str = "http://localhost:11434"


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_AUTH_")

    # API key HMAC signing secret — must be set in production
    api_key_secret: SecretStr = SecretStr("dev-secret-change-me")
    api_key_cache_ttl: int = 60             # seconds

    # JWT / OIDC
    jwks_url: str | None = None
    jwt_issuer: str | None = None
    jwt_audience: str = "aai-platform"

    # Internal service JWT
    internal_jwt_secret: SecretStr = SecretStr("internal-dev-secret-change-me")
    internal_jwt_ttl: int = 300             # 5 minutes


class ObservabilityConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AAI_OTEL_")

    endpoint: str = "http://localhost:4317"
    service_name: str = "aai-platform"
    # "grpc" | "http"
    exporter: str = "grpc"
    log_level: str = "INFO"


class PlatformConfig(BaseSettings):
    """Top-level platform configuration.

    Loaded from YAML, then overridden by AAI_* env vars.
    Change adapters by setting the provider fields — no code changes needed.
    """
    model_config = SettingsConfigDict(env_prefix="AAI_", extra="ignore")

    environment: str = "local"
    debug: bool = False

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    vault: VaultConfig = Field(default_factory=VaultConfig)
    nats: NATSConfig = Field(default_factory=NATSConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)

    # Swappable adapter selection — change here to switch implementations
    secret_store_backend: str = "vault"         # "vault" | "aws-sm" | "azure-kv" | "gcp-sm"
    vector_store_backend: str = "qdrant"        # "qdrant" | "pgvector" | "pinecone"
    message_bus_backend: str = "nats"           # "nats" | "kafka" | "sqs"
    auth_provider_backend: str = "keycloak"     # "keycloak" | "auth0" | "cognito" | "azure-ad"


def load_config(path: str | Path | None = None) -> PlatformConfig:
    """Load config from YAML file (optional) then apply env var overrides."""
    overrides: dict[str, Any] = {}

    config_path = path or os.environ.get("AAI_CONFIG_FILE")
    if config_path and Path(str(config_path)).exists():
        with open(config_path) as f:
            overrides = yaml.safe_load(f) or {}

    return PlatformConfig(**overrides)
