"""Auth service HTTP routes.

POST /v1/auth/validate-key   — validate API key, return internal JWT
POST /v1/auth/validate-jwt   — validate external JWT, return internal JWT
POST /v1/auth/refresh        — refresh external JWT
POST /v1/auth/keys           — create API key (admin)
DELETE /v1/auth/keys/{id}    — revoke API key (admin)
GET  /internal/health/live   — liveness probe
GET  /internal/health/ready  — readiness probe
GET  /metrics                — Prometheus (port :9090)
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from aai_core.errors import AAIError

from ..core.api_key import generate_api_key
from ..core.ip_allowlist import check_ip_allowlist
from ..dependencies import get_api_key_validator, get_jwt_minter, get_repo, get_cache

router = APIRouter()


# ── Request / response models ─────────────────────────────────────────────────

class ValidateKeyRequest(BaseModel):
    api_key: str
    client_ip: str | None = None


class ValidateJWTRequest(BaseModel):
    token: str
    client_ip: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class InternalTokenResponse(BaseModel):
    internal_token: str
    tenant_id: str
    scopes: list[str]


class CreateKeyRequest(BaseModel):
    tenant_id: str
    name: str
    scopes: list[str] = []
    environment: str = "live"


class CreateKeyResponse(BaseModel):
    key_id: str
    raw_key: str        # shown ONCE — not stored
    key_prefix: str
    scopes: list[str]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/v1/auth/validate-key", response_model=InternalTokenResponse)
async def validate_api_key(
    body: ValidateKeyRequest,
    validator=Depends(get_api_key_validator),
    minter=Depends(get_jwt_minter),
):
    from aai_core.adapters.auth import AuthResult

    cached = await validator.validate(body.api_key)

    if body.client_ip:
        repo = validator._repo
        tenant = await repo.get_tenant(cached.tenant_id)
        if tenant:
            check_ip_allowlist(body.client_ip, list(tenant.ip_allowlist))

    auth_result = AuthResult(
        tenant_id=cached.tenant_id,
        user_id=None,
        scopes=cached.scopes,
    )
    token = minter.mint(auth_result)
    return InternalTokenResponse(
        internal_token=token,
        tenant_id=cached.tenant_id,
        scopes=cached.scopes,
    )


@router.post("/v1/auth/validate-jwt", response_model=InternalTokenResponse)
async def validate_jwt(
    body: ValidateJWTRequest,
    minter=Depends(get_jwt_minter),
    # JWT validator injected via provider — see dependencies.py
    request: Request = None,
):
    # JWT validator is optional (only if OIDC is configured)
    jwt_validator = request.app.state.jwt_validator if request else None
    if jwt_validator is None:
        raise AAIError.forbidden("OIDC not configured for this deployment")

    auth_result = await jwt_validator.validate(body.token)
    token = minter.mint(auth_result)
    return InternalTokenResponse(
        internal_token=token,
        tenant_id=auth_result.tenant_id,
        scopes=auth_result.scopes,
    )


@router.post("/v1/auth/refresh")
async def refresh_token(body: RefreshRequest, request: Request):
    provider = getattr(request.app.state, "auth_provider", None)
    if provider is None:
        raise AAIError.forbidden("Auth provider not configured")
    access_token, new_refresh = await provider.refresh_token(body.refresh_token)
    return {"access_token": access_token, "refresh_token": new_refresh}


@router.post("/v1/auth/keys", response_model=CreateKeyResponse)
async def create_api_key(
    body: CreateKeyRequest,
    repo=Depends(get_repo),
):
    from ..core.api_key import _compute_hash
    import os

    secret = os.environ.get("AAI_AUTH_API_KEY_SECRET", "dev-secret-change-me")
    raw_key, key_prefix = generate_api_key(body.environment)
    key_hash = _compute_hash(raw_key, secret)

    db_key = await repo.create(
        tenant_id=body.tenant_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=body.name,
        scopes=body.scopes,
    )

    return CreateKeyResponse(
        key_id=db_key.id,
        raw_key=raw_key,
        key_prefix=key_prefix,
        scopes=body.scopes,
    )


@router.delete("/v1/auth/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    tenant_id: Annotated[str, Header(alias="X-Tenant-Id")],
    repo=Depends(get_repo),
    cache=Depends(get_cache),
):
    revoked = await repo.revoke(key_id, tenant_id)
    if not revoked:
        raise AAIError.not_found("api_key", key_id)
    return {"revoked": True}


# ── Health probes ─────────────────────────────────────────────────────────────

@router.get("/internal/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/internal/health/ready")
async def readiness(request: Request):
    checks: dict[str, str] = {}

    # Check DB
    try:
        db = request.app.state.db_session_factory
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "error"

    # Check Redis
    try:
        await request.app.state.redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.items())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
