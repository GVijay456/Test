"""Tests for config loader."""
import os
import tempfile

import yaml

from aai_core.config import PlatformConfig, load_config


class TestLoadConfig:
    def test_defaults(self):
        cfg = load_config()
        assert cfg.environment == "local"
        assert cfg.vector_store_backend == "qdrant"
        assert cfg.message_bus_backend == "nats"
        assert cfg.secret_store_backend == "vault"

    def test_yaml_override(self):
        data = {"environment": "staging", "vector_store_backend": "pgvector"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(data, f)
            path = f.name

        cfg = load_config(path)
        assert cfg.environment == "staging"
        assert cfg.vector_store_backend == "pgvector"

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv("AAI_ENVIRONMENT", "production")
        cfg = load_config()
        assert cfg.environment == "production"

    def test_nonexistent_file_uses_defaults(self):
        cfg = load_config("/nonexistent/path/config.yaml")
        assert cfg.environment == "local"
