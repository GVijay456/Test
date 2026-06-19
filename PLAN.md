# Agentic AI Platform — Master Plan

> Update this file as work progresses. Check off tasks as done.  
> Branch: `claude/agentic-ai-architecture-xfs7j6`

---

## Overall Status

| Phase | What | Status |
|-------|------|--------|
| 0 — Design & Docs | Architecture + system design + diagrams + security | ✅ Complete |
| 1 — Foundation | Core abstractions, auth, agent runtime, LLM abstraction, observability | ⬜ Not started |
| 2 — Security & Quality | AuthZ, tool sandbox, PII, injection defense, audit trail | ⬜ Not started |
| 3 — Intelligence & Cost | Memory, RAG, model routing, semantic cache, cost enforcement | ⬜ Not started |
| 4 — Scale & Multi-Agent | DAG orchestration, HITL, FinOps dashboard, advanced hallucination | ⬜ Not started |
| 5 — Enterprise | Multi-tenancy isolation, white-labeling, GDPR, SDK | ⬜ Not started |
| 6 — Continuous Learning | Feedback pipeline, drift detection, A/B testing | ⬜ Not started |

---

## Phase 0 — Design & Documentation ✅

### Documents Completed
- [x] `AGENTIC_AI_ARCHITECTURE.md` — 18-layer architecture, full PostgreSQL DDL, adapter interfaces, all cross-cutting concerns (v1.1)
- [x] `SYSTEM_DESIGN.md` — Tech stack, monorepo structure, open-source model catalog, cloud configs, docker-compose
- [x] `SEQUENCE_DIAGRAMS.md` — 18 Mermaid sequence diagrams covering all key flows
- [x] `SECURITY_ARCHITECTURE.md` — STRIDE threat model, zero-trust diagram, 6 auth flows, prompt injection defense, secret lifecycle, incident runbooks, pen test checklist

### Key Decisions Locked
- Language split: Python (AI core services) + TypeScript (API gateway SDK)
- LLM abstraction: LiteLLM (covers OpenAI, Anthropic, Bedrock, Azure, Ollama, vLLM, HF TGI)
- Auth: Keycloak default → swappable via config (Auth0, Cognito, Azure AD)
- Vector store: Qdrant default → swappable (pgvector, Pinecone, OpenSearch, Weaviate)
- Secret store: HashiCorp Vault → swappable (AWS SM, Azure Key Vault, GCP SM)
- Message bus: NATS JetStream → swappable (Kafka, SQS, Service Bus, Pub/Sub)
- API key hashing: HMAC-SHA256 + Redis 60s cache (not bcrypt)
- Streaming: SSE default; WebSocket only for HITL bidirectional sessions
- DB connection pooling: PgBouncer in transaction mode
- Policy engine: OPA Rego for RBAC + ABAC
- Observability: OpenTelemetry (vendor-neutral) → Grafana stack (Tempo + Loki + Prometheus)

---

## Phase 1 — Foundation (Weeks 1–4) ⬜

**Deliverable:** Single-agent run with one LLM provider, full observability, end-to-end working.

### Monorepo Skeleton
- [ ] Create monorepo structure (`services/`, `packages/`, `infra/`, `config/`)
- [ ] Set up Python workspace (`uv` workspaces, shared `pyproject.toml`)
- [ ] Set up TypeScript workspace (pnpm workspaces, shared `tsconfig`)
- [ ] CI pipeline skeleton (GitHub Actions: lint + test on every PR)
- [ ] `docker-compose.yml` — local dev stack (postgres, redis, nats, vault, qdrant)

### Layer 0 — Core Abstractions (`packages/core`)
- [ ] Domain types with `schema_version` field (AgentRun, RunStep, Tool, Agent, Tenant)
- [ ] Plugin ABC (`Plugin`, `PluginHook`, `HealthStatus`)
- [ ] Adapter ABCs: `LLMProvider`, `VectorStore`, `SecretStore`, `MessageBus`, `AuthProvider`
- [ ] Configuration loader (YAML → Pydantic model, env var override)
- [ ] Tokenizer abstraction + registry (tiktoken for OpenAI, SentencePiece for Llama/Mistral, EstimateAdapter fallback)
- [ ] Error code registry (`AAI-XXXX` codes)

### Layer 1 — API Gateway (`services/gateway`)
- [ ] Kong config or FastAPI proxy with TLS termination
- [ ] Pre-auth rate limiting (100 rps / IP, configurable)
- [ ] WAF rules (AI-specific injection patterns)
- [ ] Request ID injection → OTEL trace root
- [ ] Security response headers (HSTS, CSP, X-Frame-Options)

### Layer 2 — Authentication (`services/auth`)
- [ ] API key validation: HMAC-SHA256 + Redis 60s cache + DB fallback
- [ ] JWT/OIDC validation: JWKS fetch + cache + exp/iss/aud check
- [ ] Internal JWT minting (short-lived, 5 min, signed)
- [ ] Keycloak adapter (first auth provider)
- [ ] IP allowlist check per tenant

### Layer 3 — Agent API + Runtime (`services/agent-api`, `services/orchestrator`)
- [ ] `POST /v1/runs` endpoint (idempotency key, tenant validation)
- [ ] Agent run state machine (PENDING → RUNNING → DONE/FAILED/CANCELLED)
- [ ] Basic step executor (sequential steps, no DAG yet)
- [ ] SSE streaming endpoint (`GET /v1/runs/{id}/stream`)
- [ ] Run checkpoint write (before each step)
- [ ] Graceful shutdown with SIGTERM handler + run resume on restart
- [ ] DB schema migration (Alembic): tenants, api_keys, agents, agent_runs, run_steps
- [ ] PgBouncer config (transaction mode)

### Layer 5 — LLM Abstraction (`services/llm-proxy`)
- [ ] LiteLLM proxy wrapper
- [ ] OpenAI adapter (first provider)
- [ ] Ollama adapter (first open-source provider)
- [ ] Schema validation on LLM responses
- [ ] Basic circuit breaker (per provider, CLOSED/OPEN/HALF-OPEN)
- [ ] Token count estimation (tokenizer registry)

### Layer 13 — Observability (`services/otel-collector`)
- [ ] OpenTelemetry SDK instrumentation in all services
- [ ] Trace propagation across service calls
- [ ] Structured JSON logging (request_id, run_id, tenant_id in every log line)
- [ ] Prometheus metrics: request rate, latency p50/p99, error rate
- [ ] Grafana dashboards: service health, run status, LLM call latency
- [ ] Health probe endpoints: `/internal/health/live` and `/internal/health/ready` per service

### Phase 1 Exit Criteria
- [ ] `curl` a run from outside, it executes on Ollama, returns SSE stream
- [ ] Kill the orchestrator pod mid-run, new pod resumes the run
- [ ] OTEL trace visible end-to-end in Grafana Tempo
- [ ] All unit tests pass, integration test with real Ollama passes

---

## Phase 2 — Security & Quality (Weeks 5–8) ⬜

**Deliverable:** Production-safe agent runs — all guardrails active.

### Layer 2 — Authorization (`services/auth` + OPA)
- [ ] OPA deployment + Rego policy bundle
- [ ] RBAC policies: scopes checked on every operation
- [ ] ABAC policies: PII tier, budget tier, tool risk level
- [ ] OPA policy tests (Rego unit tests)

### Layer 6 — Tool Registry + Sandbox (`services/tool-registry`, `services/tool-executor`)
- [ ] Tool manifest format (id, version, risk_level, permissions, schema)
- [ ] Tool registry API (register, list, get)
- [ ] gVisor (runsc) sandbox for code execution tools
- [ ] Tool input validation (JSON schema)
- [ ] Tool output PII scan before returning to agent
- [ ] Audit event per tool call
- [ ] Built-in tools: http_request, web_search, code_exec, file_read, pdf_extract, json_transform

### Layer 9 — Security Guard (`services/security-guard`)
- [ ] Pre-request injection pattern scan (regex library, 1000+ patterns)
- [ ] Semantic injection classifier (DistilBERT fine-tuned, CPU, p99 < 50ms)
- [ ] SSRF validator for any URL in request/tool output
- [ ] Output scan (secrets regex: API keys, tokens, private keys)
- [ ] Blocked request audit event

### Layer 10 — PII Detection (`services/pii-service`)
- [ ] Microsoft Presidio integration
- [ ] PII scan on request body, LLM output, tool output
- [ ] Sliding window buffer for streaming output masking (200 char window)
- [ ] PII classification tiers: HIGH/MEDIUM/LOW
- [ ] PII audit event (entity type + count, not the PII itself)

### Layer 14 — Audit Trail (`services/audit`)
- [ ] Append-only audit_events table (REVOKE UPDATE/DELETE at DB level)
- [ ] All 20 audit event types implemented
- [ ] Async write via NATS (never blocks request path)
- [ ] Tenant-scoped audit query API (`GET /v1/audit?from=&to=`)
- [ ] Audit export (CSV/JSON for compliance)

### Phase 2 Exit Criteria
- [ ] Prompt injection test suite (100 payloads) — all detected or blocked
- [ ] PII test vectors (SSN, CC, email in 5 languages) — all masked in output
- [ ] SQL injection probes on all query params — all return 400
- [ ] Audit log immutability: SQL UPDATE on audit_events returns permission denied
- [ ] Tool sandbox escape attempt — contained by gVisor

---

## Phase 3 — Intelligence & Cost (Weeks 9–12) ⬜

**Deliverable:** RAG-enabled agents with cost control and memory.

### Layer 5 — Model Routing + Cache (`services/llm-proxy` additions)
- [ ] Cost-aware routing (cheapest capable model for task)
- [ ] Capability-match routing (vision → vision model, code → code model)
- [ ] Semantic cache (Redis + vector similarity, threshold: 0.98)
- [ ] Remaining provider adapters: Anthropic, AWS Bedrock, Azure OAI, vLLM, HF TGI
- [ ] BYOLLM support: tenant key stored in Vault, fetched at runtime

### Layer 7 — Memory (`services/memory`)
- [ ] Episodic memory: store + retrieve by run_id + user_id
- [ ] Semantic memory: agent-scoped facts, entity relationships
- [ ] Context window packer (priority-based token budget)
- [ ] Memory summarizer (cheap model, 70% compression target)
- [ ] Memory privacy: tenant + user scoped isolation
- [ ] PII-HIGH memory auto-expiry (30 days)

### Layer 8 — RAG Pipeline (`services/rag`)
- [ ] Document ingestion: PDF, DOCX, HTML, MD, CSV, JSON
- [ ] Chunking strategies: fixed-size, semantic, hierarchical
- [ ] Embedding with pluggable model (default: text-embedding-3-small)
- [ ] Vector store write (Qdrant adapter, tenant-namespaced)
- [ ] BM25 index write (keyword search)
- [ ] Multi-strategy retrieval: dense + sparse + RRF fusion
- [ ] Cross-encoder reranker (ms-marco-MiniLM)
- [ ] Citation validation (faithfulness guardrail post-response)
- [ ] Embedding dimension migration procedure (dual-write → backfill → cutover)

### Layer 12 — Cost Tracking (`services/cost`)
- [ ] Atomic token reservation (Redis Lua script, check+reserve)
- [ ] Post-call reconciliation (adjust reservation to actual)
- [ ] Cost ledger table (partitioned by month)
- [ ] Per-tenant budget enforcement (daily/monthly/per-run limits)
- [ ] Cost anomaly detection (3x p95 baseline = alert)
- [ ] Auto-throttle on budget soft limit (95%)

### Phase 3 Exit Criteria
- [ ] Ingest a 100-page PDF, query it, get cited answer with faithfulness score
- [ ] 5 parallel agent steps all within budget (no race condition via Lua script)
- [ ] Semantic cache hit rate > 30% in load test (repeated similar queries)
- [ ] Budget exceeded → run stops, cost_usd in response matches ledger

---

## Phase 4 — Scale & Multi-Agent (Weeks 13–16) ⬜

**Deliverable:** Complex multi-agent DAG workflows at scale.

### Layer 4 — Multi-Agent Orchestration (`services/orchestrator`)
- [ ] DAG engine: topological sort, level-based parallel execution
- [ ] Agent-to-agent communication (supervisor spawns workers)
- [ ] Scoped token derivation (worker gets subset of supervisor scopes)
- [ ] Dependency resolution (node N starts when all dependencies complete)
- [ ] DAG failure handling (partial failure = cancel dependents, keep independent)

### Layer 4 — HITL Approval (`services/hitl`)
- [ ] Risk level tagging on tools (LOW/MEDIUM/HIGH/CRITICAL)
- [ ] HITL trigger config per agent (which risk levels require approval)
- [ ] Approval request: email + Slack + webhook notification
- [ ] WebSocket endpoint for real-time approval UI (`WS /v1/hitl/{id}/stream`)
- [ ] Approval timeout (configurable, default 24h → auto-FAIL)
- [ ] Signed approval token (approver identity in audit log)

### Layer 11 — Hallucination Detection (`services/hallucination`)
- [ ] Faithfulness check (claim verifiable against retrieved context?)
- [ ] NLI entailment classifier (DeBERTa-based, optional)
- [ ] Self-consistency trigger (conditional: HITL, medical, financial domains)
- [ ] Hallucination score in run metadata
- [ ] Configurable threshold per agent (flag vs block)

### Layer 12 — FinOps Dashboard
- [ ] Per-tenant cost breakdown by model, tool, date
- [ ] Cost trend charts (Grafana panels)
- [ ] Budget utilization alerts (Prometheus alert rules)
- [ ] Cost export API (CSV/JSON)

### Phase 4 Exit Criteria
- [ ] 5-agent DAG completes with parallel fan-out; results merged correctly
- [ ] Kill one worker mid-run; DAG resumes from checkpoint
- [ ] HITL approval timeout fires, run marked FAILED with reason
- [ ] Load test: 500 rps, 10,000 concurrent runs, p99 < 2s, error < 0.1%

---

## Phase 5 — Enterprise & White-Label (Weeks 17–20) ⬜

**Deliverable:** Enterprise-ready, white-labeled platform.

### Layer 17 — Multi-Tenancy (`services/tenant`)
- [ ] Tenant onboarding API (< 60s automated provisioning)
- [ ] SHARED / DEDICATED / ISOLATED compute tiers
- [ ] Row-Level Security validation tests (cross-tenant query = empty, not error)
- [ ] Tenant suspension and deletion
- [ ] Data residency enforcement (EU / US / APAC region routing)

### Layer 17 — White-Labeling
- [ ] Tenant brand config (logo, colors, fonts, product name)
- [ ] Custom domain support (CNAME + auto-TLS via ACME)
- [ ] Custom agent personas (name, avatar, greeting)
- [ ] Hide platform branding (enterprise plan flag)

### Layer 10 — GDPR & Compliance
- [ ] Right to erasure endpoint (`POST /v1/privacy/erasure`)
- [ ] Parallel erasure: Redis, DB (pseudonymize), vector store, object store
- [ ] Erasure receipt in audit log
- [ ] Data portability export (`GET /v1/exports/gdpr`)
- [ ] Compliance report generator (SOC 2 evidence export)

### Layer 18 — Developer SDK (`packages/sdk-typescript`, `packages/sdk-python`)
- [ ] TypeScript SDK: typed client, streaming support, retry logic
- [ ] Python SDK: async client, tool decorator, agent builder
- [ ] SDK docs (auto-generated from OpenAPI spec)
- [ ] Developer portal (API reference, quickstart, examples)
- [ ] Webhook SDK helper (signature verification)

### Phase 5 Exit Criteria
- [ ] Tenant onboarding: < 60s end-to-end automated
- [ ] GDPR erasure: all user data gone within 24h, receipt in audit log
- [ ] Custom domain serving HTTPS with valid cert (Let's Encrypt)
- [ ] SDK quickstart: working agent in < 10 lines of code

---

## Phase 6 — Continuous Learning (Weeks 21–24) ⬜

**Deliverable:** Self-improving platform.

### Layer 15 — Feedback & Learning (`services/feedback`)
- [ ] Thumbs up/down feedback API per run
- [ ] Free-text feedback collection
- [ ] Feedback → training data pipeline (RLHF annotations)
- [ ] A/B testing infrastructure (agent version A vs B, traffic split)
- [ ] Statistical significance calculator for A/B results

### Drift Detection
- [ ] Output quality drift detection (rolling hallucination score baseline)
- [ ] Latency drift alert (p99 > 2x rolling average)
- [ ] Cost drift alert (per-run cost trending up)
- [ ] Model performance degradation alert

### Cost Optimization
- [ ] Prompt compression (remove redundant context, target 30% token reduction)
- [ ] Cache warming (pre-embed common queries)
- [ ] Model downgrade automation (route to cheaper model when quality threshold met)

### Phase 6 Exit Criteria
- [ ] A/B test shows statistically significant quality difference between agent versions
- [ ] Drift alert fires when hallucination score degrades > 20% baseline
- [ ] Prompt compression reduces token usage by > 20% on test corpus

---

## Component Swappability Reference

| Component | Default | Swap options | How to swap |
|-----------|---------|--------------|-------------|
| LLM provider | Ollama (local) | OpenAI, Anthropic, Bedrock, Azure, vLLM, HF TGI | `config/llm.yaml: provider:` |
| Vector store | Qdrant | pgvector, Pinecone, OpenSearch, Weaviate | `config/rag.yaml: vector_store:` |
| Auth | Keycloak | Auth0, Cognito, Azure AD, Firebase | `config/auth.yaml: provider:` |
| Secret store | Vault | AWS SM, Azure Key Vault, GCP SM | `config/secrets.yaml: backend:` |
| Message bus | NATS JetStream | Kafka, AWS SQS, Azure Service Bus, GCP Pub/Sub | `config/messaging.yaml: bus:` |
| Embedding model | text-embedding-3-small | Local models (384d/768d/1024d), Cohere | `config/rag.yaml: embedding_model:` |
| Observability | Grafana stack | Datadog, New Relic, Honeycomb, Dynatrace | `config/observability.yaml: exporter:` |
| Object store | MinIO (local) | S3, GCS, Azure Blob | `config/storage.yaml: backend:` |
| Reranker | ms-marco-MiniLM | Cohere Rerank, BGE, Jina | `config/rag.yaml: reranker:` |
| Graph store | Apache AGE | Neo4j, Amazon Neptune | `config/rag.yaml: graph_store:` |

---

## Open Questions / Decisions Needed

- [ ] Which cloud first for production deploy? (AWS / Azure / GCP)
- [ ] Kubernetes distribution? (EKS / AKS / GKE / self-hosted k3s)
- [ ] Service mesh? (Istio / Linkerd / Cilium — or skip for Phase 1)
- [ ] Ollama GPU instance sizing for self-hosted models
- [ ] Which embedding model for production? (cloud vs local tradeoff)
- [ ] Knowledge graph: enable for Phase 3 or defer to Phase 5?
- [ ] SDK: TypeScript first or Python first?

---

## Reference Docs

| Doc | Purpose |
|-----|---------|
| `AGENTIC_AI_ARCHITECTURE.md` | 18-layer deep architecture, all design decisions |
| `SYSTEM_DESIGN.md` | Tech stack, monorepo layout, cloud configs, adapter code |
| `SEQUENCE_DIAGRAMS.md` | 18 Mermaid flow diagrams for all key paths |
| `SECURITY_ARCHITECTURE.md` | STRIDE model, threat controls, incident runbooks, pen test checklist |
| `PLAN.md` | This file — progress tracking |
