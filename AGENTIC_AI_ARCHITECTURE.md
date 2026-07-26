# Agentic AI Platform — Production-Grade Architecture
## Vendor-Neutral · White-Labeled · Plug-and-Play

> **Document scope:** Complete system design for a production-grade Agentic AI platform.
> Every layer is specified with enough detail to drive implementation.
> The architecture is deliberately provider-agnostic at every interface boundary.

---

## Table of Contents

1. [Architectural Principles](#1-architectural-principles)
2. [System Topology Overview](#2-system-topology-overview)
3. [Layer 0 — Core Abstractions & Plugin Contract](#3-layer-0--core-abstractions--plugin-contract)
4. [Layer 1 — API Gateway & Edge](#4-layer-1--api-gateway--edge)
5. [Layer 2 — Authentication & Authorization](#5-layer-2--authentication--authorization)
6. [Layer 3 — Agent Runtime Engine](#6-layer-3--agent-runtime-engine)
7. [Layer 4 — Orchestration & Multi-Agent Coordination](#7-layer-4--orchestration--multi-agent-coordination)
8. [Layer 5 — LLM Abstraction & Model Routing](#8-layer-5--llm-abstraction--model-routing)
9. [Layer 6 — Tool Registry & Execution Sandbox](#9-layer-6--tool-registry--execution-sandbox)
10. [Layer 7 — Memory & Context Management](#10-layer-7--memory--context-management)
11. [Layer 8 — RAG & Knowledge Layer](#11-layer-8--rag--knowledge-layer)
12. [Layer 9 — Security & Threat Defense](#12-layer-9--security--threat-defense)
13. [Layer 10 — PII, Privacy & Data Governance](#13-layer-10--pii-privacy--data-governance)
14. [Layer 11 — Hallucination Control & Output Quality](#14-layer-11--hallucination-control--output-quality)
15. [Layer 12 — Cost Management & FinOps](#15-layer-12--cost-management--finops)
16. [Layer 13 — Observability, Monitoring & Alerting](#16-layer-13--observability-monitoring--alerting)
17. [Layer 14 — Audit, Compliance & Explainability](#17-layer-14--audit-compliance--explainability)
18. [Layer 15 — Data Pipelines & Feedback Loops](#18-layer-15--data-pipelines--feedback-loops)
19. [Layer 16 — Infrastructure & Deployment](#19-layer-16--infrastructure--deployment)
20. [Layer 17 — Multi-Tenancy & White-Labeling](#20-layer-17--multi-tenancy--white-labeling)
21. [Layer 18 — Developer Experience & SDK](#21-layer-18--developer-experience--sdk)
22. [Cross-Cutting Concerns](#22-cross-cutting-concerns)
23. [Data Flow — End-to-End Trace](#23-data-flow--end-to-end-trace)
24. [Failure Modes & Resilience Patterns](#24-failure-modes--resilience-patterns)
25. [Implementation Roadmap](#25-implementation-roadmap)

---

## 1. Architectural Principles

| Principle | What It Means in Practice |
|---|---|
| **Vendor Neutrality** | Every external provider (LLM, vector DB, auth) is accessed through an abstract interface. Swapping providers requires only config, not code. |
| **Plugin-First** | Every layer exposes a well-typed extension point. New capabilities are added by registering plugins, not modifying core. |
| **Zero-Trust** | Every service call is authenticated and authorized, even intra-cluster. No implicit trust based on network position. |
| **Observable by Default** | Traces, metrics, and structured logs are emitted automatically at every boundary. No instrumentation is opt-in. |
| **Immutable Audit** | Every agent action and every LLM call is recorded in an append-only store. Records cannot be mutated post-write. |
| **Fail Safe** | Default behavior on any error is to halt and surface, never to silently degrade or hallucinate forward. |
| **Cost First** | Token budget is a first-class constraint enforced before execution, not reported after. |
| **Privacy by Design** | PII is detected, classified, and masked before it leaves the trust boundary, in both directions. |

---

## 2. System Topology Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENTS  (Web, Mobile, CLI, Webhooks, Scheduled Jobs)                      │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ HTTPS / WebSocket / gRPC
┌────────────────────────────▼────────────────────────────────────────────────┐
│  LAYER 1 — API GATEWAY & EDGE                                               │
│  Rate Limiting · TLS Termination · DDoS Shield · Request Routing            │
│  Canary Routing · IP Allowlisting · WAF                                     │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────────┐
│  LAYER 2 — AUTH SERVICE                                                     │
│  AuthN (JWT/API-Key/OAuth2/OIDC) · AuthZ (RBAC+ABAC) · Agent Identity      │
│  Tenant Isolation · Session Management · Key Rotation                       │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ Verified Request + Claims
┌────────────────────────────▼────────────────────────────────────────────────┐
│  LAYER 9 — SECURITY GUARD (inline, pre-agent)                               │
│  Prompt Injection Detection · Content Policy · Secret Scanning              │
│  Input Sanitization · PII Pre-Masking                                       │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ Cleared Request
┌────────────────────────────▼────────────────────────────────────────────────┐
│  LAYER 3 — AGENT RUNTIME ENGINE                                             │
│  Task Planner · Step Executor · State Machine · Retry/Rollback              │
│  Agent Context · Tool Call Dispatcher                                       │
└───────┬──────────────────────────────────────┬───────────────────────────────┘
        │                                       │
┌───────▼───────────┐             ┌─────────────▼──────────────────────────────┐
│  LAYER 4          │             │  LAYER 5 — LLM ABSTRACTION                 │
│  ORCHESTRATOR     │             │  Provider Router · Model Selector           │
│  Multi-Agent DAG  │             │  Token Budget Enforcer · Retry w/ backoff  │
│  Supervisor/Worker│             │  Response Validator · Cost Ledger           │
└───────┬───────────┘             └─────────────┬──────────────────────────────┘
        │                                       │
┌───────▼───────────┐             ┌─────────────▼──────────────────────────────┐
│  LAYER 6          │             │  EXTERNAL LLM PROVIDERS                    │
│  TOOL REGISTRY    │             │  (OpenAI / Anthropic / Gemini / Mistral /  │
│  Sandbox Exec     │             │   Azure OAI / Bedrock / local Ollama)      │
│  Tool AuthZ       │             └────────────────────────────────────────────┘
└───────┬───────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────────────┐
│  LAYER 7 — MEMORY & CONTEXT                                                  │
│  Working Memory · Episodic Memory · Semantic Memory                          │
│  Context Window Packer · Summarizer · Retriever                              │
└───────┬──────────────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────────────────┐
│  LAYER 8 — RAG / KNOWLEDGE                                                   │
│  Ingestion Pipeline · Chunker · Embedder · Vector Store                      │
│  Hybrid Search (vector + BM25) · Reranker · Citation Builder                 │
└──────────────────────────────────────────────────────────────────────────────┘

        (All layers emit to the Observability Plane)

┌──────────────────────────────────────────────────────────────────────────────┐
│  CROSS-CUTTING PLANES                                                        │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │ Observability   │  │ Audit & Compliance│  │ Cost & FinOps            │   │
│  │ OTEL Traces     │  │ Immutable Log     │  │ Token Ledger             │   │
│  │ Metrics         │  │ Policy Engine     │  │ Budget Enforcer          │   │
│  │ Structured Logs │  │ Explainability    │  │ Anomaly Detector         │   │
│  └─────────────────┘  └──────────────────┘  └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer 0 — Core Abstractions & Plugin Contract

This layer defines the type system that every other layer implements against. No layer imports a concrete provider directly — only interfaces from here.

### 3.1 Universal Plugin Interface

Defined as Python Abstract Base Classes (the platform core is Python). TypeScript SDK plugins mirror this contract via interface files generated from the Python ABCs.

```python
# core/interfaces/plugin.py
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Any

class PluginHook(str, Enum):
    PRE_REQUEST           = "PRE_REQUEST"
    POST_REQUEST          = "POST_REQUEST"
    PRE_LLM_CALL          = "PRE_LLM_CALL"
    POST_LLM_CALL         = "POST_LLM_CALL"
    PRE_TOOL_EXEC         = "PRE_TOOL_EXEC"
    POST_TOOL_EXEC        = "POST_TOOL_EXEC"
    PRE_RESPONSE          = "PRE_RESPONSE"
    POST_RESPONSE         = "POST_RESPONSE"
    ON_ERROR              = "ON_ERROR"
    ON_COST_THRESHOLD     = "ON_COST_THRESHOLD"
    ON_PII_DETECTED       = "ON_PII_DETECTED"
    ON_HALLUCINATION      = "ON_HALLUCINATION"

@dataclass
class HealthStatus:
    healthy: bool
    message: str
    details: dict[str, Any] | None = None

class Plugin(ABC):
    """Base class for all platform plugins. Every plugin must implement this."""

    @property
    @abstractmethod
    def id(self) -> str: ...          # globally unique, e.g. "my-org.cost-reporter"

    @property
    @abstractmethod
    def version(self) -> str: ...     # semver string, e.g. "1.2.0"

    @property
    @abstractmethod
    def hooks(self) -> list[PluginHook]: ...   # which lifecycle points this binds to

    @abstractmethod
    async def init(self, config: dict[str, Any]) -> None: ...

    @abstractmethod
    async def teardown(self) -> None: ...

    @abstractmethod
    def health_check(self) -> HealthStatus: ...
```

### 3.2 Core Domain Types

All types carry a `schema_version` field from day 1. When a type evolves, consumers check the version and apply a migration shim. This prevents silent incompatibilities between old queue messages and new consumers.

```
// Every execution unit
type AgentRun = {
  schema_version: int       // increment on any breaking field change
  runId:       UUID
  tenantId:    UUID
  agentId:     UUID
  sessionId:   UUID
  userId:      UUID
  traceId:     UUID           // OTEL propagated
  budget:      TokenBudget
  startTime:   ISO8601
  status:      RunStatus      // PENDING | RUNNING | PAUSED | DONE | FAILED
  steps:       AgentStep[]
  context:     RunContext
}

// Every LLM call
type LLMCall = {
  callId:          UUID
  runId:           UUID
  provider:        ProviderID      // opaque string, resolved by router
  model:           ModelID
  promptTokens:    int
  completionTokens: int
  costUSD:         Decimal
  latencyMs:       int
  requestHash:     SHA256          // for caching and dedup
  messages:        Message[]       // post-PII-masking
  response:        LLMResponse
  hallucinationScore: float        // 0.0-1.0
  cached:          bool
}

// Every tool invocation
type ToolCall = {
  callId:     UUID
  runId:      UUID
  toolId:     string
  input:      JSON               // sanitized
  output:     JSON               // sanitized
  durationMs: int
  sandbox:    SandboxID
  allowed:    bool               // post-authz check
  riskScore:  float
}
```

### 3.3 Configuration Schema (vendor-neutral)

All configuration is expressed as a versioned schema. Environment variables, secrets manager, or config files are all equivalent sources.

```yaml
# agentic-platform.config.yaml
version: "1.0"

llm:
  router: "cost-aware"          # cost-aware | latency-first | capability-match | round-robin
  providers:
    - id: "openai"
      adapter: "@adapters/openai"
      priority: 1
    - id: "anthropic"
      adapter: "@adapters/anthropic"
      priority: 2
    - id: "bedrock"
      adapter: "@adapters/bedrock"
      priority: 3

vector_store:
  adapter: "@adapters/qdrant"   # qdrant | pinecone | weaviate | pgvector | chroma

auth:
  adapter: "@adapters/keycloak" # keycloak | auth0 | cognito | okta | custom-jwt

audit_store:
  adapter: "@adapters/postgres" # postgres | dynamodb | bigquery | s3-parquet

secret_store:
  adapter: "@adapters/vault"    # vault | aws-ssm | gcp-secret-manager | azure-keyvault

telemetry:
  exporter: "otlp"              # otlp | jaeger | datadog | grafana
  endpoint: "${OTEL_ENDPOINT}"
```

---

## 4. Layer 1 — API Gateway & Edge

### 4.1 Responsibilities

- TLS termination (TLS 1.3 minimum, HSTS enforced)
- DDoS protection (rate limiting per IP, per tenant, per API key)
- Web Application Firewall (OWASP rule sets + custom AI-specific rules)
- Request routing to correct tenant shard
- Canary/blue-green routing for agent version rollouts
- Request ID injection (becomes the root OTEL trace ID)
- WebSocket management for streaming responses
- gRPC-HTTP transcoding for internal services

### 4.2 Rate Limiting Strategy

Three-tier rate limiting, each independently configurable:

```
Tier 1 — IP-level      :  1000 req/min (burst: 200/s)
Tier 2 — API-key-level :  configured per plan (Free: 60/min, Pro: 600/min, Enterprise: custom)
Tier 3 — Agent-level   :  max concurrent runs per agent definition
```

Token bucket algorithm with Redis-backed state for distributed enforcement.
Sliding window counters per 1-second, 1-minute, 1-hour, 1-day windows.

### 4.3 WAF Rules (AI-Specific Layer)

Beyond OWASP Top 10, the WAF adds:

| Rule | Trigger | Action |
|---|---|---|
| Oversized payload | request body > 100KB | Block + 413 |
| Recursive embedding | nested JSON depth > 10 | Block |
| Unicode abuse | unusual Unicode categories in prompt field | Flag + sanitize |
| Null byte injection | `\x00` in any string field | Block |
| Script injection | `<script>`, `javascript:` in prompt | Block |

### 4.4 Edge Response Headers (Security)

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: no-store
X-Request-ID: {trace_id}
```

---

## 5. Layer 2 — Authentication & Authorization

### 5.1 Authentication Methods (all simultaneously supported)

| Method | Use Case | Token Lifetime |
|---|---|---|
| API Key (HMAC-SHA256) | Server-to-server, CI/CD | Until rotated |
| JWT (RS256/ES256) | User sessions, SPAs | 15 min access / 7 day refresh |
| OAuth2 Client Credentials | Machine-to-machine | Configurable |
| OIDC (SSO) | Enterprise, workforce | Session-bound |
| mTLS | Internal service-to-service | Certificate lifetime |
| Webhook Signatures | Inbound webhooks (HMAC-SHA256) | Per-request |

**Agent Identity** — each deployed agent instance gets its own cryptographic identity (rotating key pair), separate from the human user's identity. Every tool call is signed with the agent's private key.

### 5.2 API Key Management

```
Key structure: {prefix}_{tenant_short}_{random_32bytes_base58}
Example:       aai_acme_3xR7mKp2...

Key record:
  keyId:          UUID (public, non-secret — returned to user at creation)
  keyHash:        HMAC-SHA256(key, server_secret)  -- stored, never the key itself
  tenantId:       UUID
  createdBy:      UUID
  scopes:         string[]
  rateLimit:      RateLimitPolicy
  ipAllowlist:    CIDR[]
  expiresAt:      ISO8601 | null
  lastUsedAt:     ISO8601
  rotationPolicy: RotationPolicy
```

**Why HMAC-SHA256, not bcrypt:**
API keys are 32 random bytes (256 bits of entropy). Brute force is computationally infeasible regardless of hash speed. bcrypt is designed for *low-entropy* passwords (short, human-memorable). Using bcrypt at cost=12 adds 200-400ms per verification — catastrophic at API gateway throughput. HMAC-SHA256 is the correct choice for high-entropy tokens (used by GitHub, Stripe, and all major API platforms).

Key verification process:
1. Compute `HMAC-SHA256(presented_key, server_secret)` — constant-time
2. Compare to stored `keyHash` — constant-time comparison (no timing leak)
3. Cache result in Redis: `key:{keyId} → {principal_claims}` with 60s TTL
4. Subsequent requests within 60s: Redis lookup only (no DB hit, near-zero latency)
5. Cache miss or TTL expired: re-verify from DB + refresh cache

### 5.3 Authorization Model (RBAC + ABAC combined)

**RBAC** handles structural permissions (roles → permissions).
**ABAC** handles dynamic, context-aware decisions (run-time attributes).

```
Principal (User | ServiceAccount | Agent)
    └── has Roles (tenant-scoped)
           └── Role has Permissions
                    └── Permission = {resource, action, conditions}

ABAC conditions evaluated at runtime:
  - request.tenant_id == resource.tenant_id
  - request.time BETWEEN policy.allowed_hours
  - resource.classification IN principal.cleared_classifications
  - agent.tool_id IN principal.allowed_tools
  - run.cost_usd < principal.max_run_cost
```

Policy Decision Point (PDP) is a dedicated service, not inline code.
Policy Information Point (PIP) pulls attributes from user store + resource store.
Policies are written in OPA (Open Policy Agent) Rego — vendor neutral.

**Sample OPA policy:**

```rego
package agentic.authz

default allow := false

allow if {
    valid_token
    has_required_scope
    within_cost_budget
    not is_pii_restricted_resource
}

valid_token if {
    input.token.tenant_id == input.resource.tenant_id
}

has_required_scope if {
    input.action in input.token.scopes
}

within_cost_budget if {
    input.token.remaining_budget_usd > input.run.estimated_cost_usd
}

is_pii_restricted_resource if {
    input.resource.classification == "PII-HIGH"
    not input.token.pii_authorized
}
```

### 5.4 Agent-to-Agent Authorization

When Agent A spawns Agent B (multi-agent), Agent B receives a **derived, scoped token**:
- Inherits subset of parent agent's permissions (never more)
- Includes a `parent_run_id` claim for full lineage
- Has a shorter TTL (max: parent run TTL)
- Cannot spawn further agents unless explicitly granted

### 5.5 Session Management

```
Session record:
  sessionId:    UUID
  tenantId:     UUID
  userId:       UUID
  createdAt:    ISO8601
  lastActiveAt: ISO8601
  expiresAt:    ISO8601
  ipFingerprint: SHA256(ip+useragent)
  deviceId:     UUID
  mfaVerified:  bool
  scopes:       string[]
  anomalyScore: float   -- updated continuously by auth anomaly detector
```

Sessions are stored in Redis with TTL-based expiry.
Session fixation prevention: rotate session ID on privilege elevation.
Concurrent session limits enforced per tenant policy.

### 5.6 Secret Management (Platform-Internal)

All secrets (LLM API keys, DB passwords, signing keys) flow exclusively through the secret store adapter:

```
SecretStore interface:
  get(path: string, version?: int): Promise<Secret>
  set(path: string, value: string, metadata: SecretMetadata): Promise<void>
  rotate(path: string): Promise<Secret>
  audit(path: string): Promise<AccessLog[]>

Rotation policy:
  LLM API keys:    every 30 days, zero-downtime (dual-active window)
  Signing keys:    every 90 days, RS256 JWKS endpoint auto-updated
  DB credentials:  every 7 days via dynamic secrets (Vault)
  Webhook secrets: per-endpoint, rotated on demand
```

---

## 6. Layer 3 — Agent Runtime Engine

### 6.1 Agent Definition Schema

```yaml
# agent.yaml — everything needed to define an agent
id: "invoice-processor-v2"
version: "2.1.0"
display_name: "Invoice Processor"

model:
  primary:   "gpt-4o"      # resolved by model router
  fallback:  "claude-3-5-sonnet"
  temperature: 0.2
  max_tokens:  4096

system_prompt:
  template: |
    You are an invoice processing specialist for {{tenant.company_name}}.
    You extract structured data from invoices.
    Rules:
    - Never invent data not present in the document
    - Always cite the source field location
    - Flag ambiguous fields rather than guessing
  variables:
    - tenant.company_name

tools:
  - id: "file_read"
    max_file_size_mb: 10
    allowed_types: ["pdf", "png", "jpg", "csv"]
  - id: "structured_output"
  - id: "web_search"
    allowed_domains: ["^.*\\.gov$", "^.*\\.reuters\\.com$"]

memory:
  working_memory_tokens: 8000
  episodic_memory: true
  semantic_memory: true
  max_history_turns: 20

budget:
  max_tokens_per_run:    50000
  max_cost_usd_per_run:  0.50
  max_tool_calls:        30
  max_wall_time_seconds: 120

guardrails:
  hallucination_threshold: 0.3   # abort if score exceeds
  pii_action:              "mask"
  content_policy:          "strict"

output:
  schema: "InvoiceOutput"        # JSON Schema reference
  enforce_schema: true
  citations_required: true
```

### 6.2 Agent State Machine

```
                    ┌─────────┐
                    │ CREATED │
                    └────┬────┘
                         │ init()
                    ┌────▼────┐
                    │PLANNING │  ← Task decomposition, tool selection
                    └────┬────┘
                         │ plan approved (or auto-approved)
                    ┌────▼────┐
            ┌──────►│EXECUTING│◄──────────┐
            │       └────┬────┘           │
            │            │                │
        (tool      ┌─────┴──────┐    (retry
         result)   │            │     ok)
            │   TOOL_WAIT  LLM_WAIT
            │      │            │
            └──────┘            │ response
                                │
                    ┌───────────▼─────────┐
                    │    VALIDATING       │  ← schema, hallucination, PII
                    └───────────┬─────────┘
                                │
                    ┌───────────▼─────────┐
              ┌─────┤   CHECKPOINTING     │  ← persist state
              │     └───────────┬─────────┘
              │                 │
         (more steps)    (complete)
              │                 │
              └─────────►  ┌────▼────┐
                           │  DONE   │
                           └─────────┘

Error paths → FAILED (with structured error + full context snapshot)
Human approval needed → PAUSED (async, timeout configurable)
Timeout (max_wall_time_seconds hit) → TIMEOUT (see cleanup sequence below)
```

### 6.2a Agent Timeout — Cleanup Sequence

When `max_wall_time_seconds` is exceeded, a structured cleanup runs. Never kill abruptly.

```
TIMEOUT CLEANUP SEQUENCE:

1. Set run status → CANCELLING (prevents new steps from starting)
2. In-flight LLM call:
   a. If streaming: close stream, record partial response in step output
   b. If waiting: wait max 5s for response, then cancel connection
   c. Partial tokens consumed → still charged to cost ledger
3. In-flight tool call:
   a. Send SIGTERM to sandbox process/container
   b. Wait 3s grace period
   c. If not exited: SIGKILL
   d. Ephemeral sandbox filesystem: destroy
4. Release distributed lock held by this run (see Section 22.5)
5. Write final checkpoint (all completed steps + partial step)
6. Set run status → TIMEOUT
7. Emit AGENT_RUN_TIMEOUT audit event
8. Return structured error to client:
   {
     "error": {
       "code": "AAI-5001",
       "type": "RUN_TIMEOUT",
       "message": "Run exceeded maximum wall time of 120s",
       "completed_steps": 3,
       "partial_output": { ... },    // output from steps that completed
       "resumable": false            // TIMEOUT runs are not resumable
     }
   }
9. Partial results option: if agent has output_on_timeout: true,
   return the output of the last successfully completed step
```

### 6.3 Step Execution Engine

Each step in a plan is executed as:

```
1. Pre-step hook (plugins)
2. Resolve tool or LLM call
3. Enforce budget check (abort if over)
4. Execute with timeout wrapper
5. Capture output + metadata
6. Post-step validation
7. Write step record to audit log (immediate, synchronous)
8. Emit span to trace (OTEL)
9. Update run state
10. Post-step hook (plugins)
```

Retry policy per step type:
```
LLM call:       exponential backoff, max 3 retries, jitter ±200ms
Tool call:      per-tool retry config (default: 2 retries)
Network errors: 5 retries with circuit breaker
Rate limits:    queue + retry after Retry-After header
```

### 6.4 Human-in-the-Loop (HITL)

High-risk actions require human approval before execution:

```
HITL trigger conditions (configurable per agent):
  - Tool has risk_level: HIGH
  - Estimated cost > threshold
  - Action is irreversible (delete, publish, send)
  - Confidence score < threshold
  - Novel action pattern (no prior approval in episodic memory)

HITL flow:
  1. Agent pauses at CHECKPOINTING
  2. Approval request pushed to configured channel (webhook / email / Slack / in-app)
  3. Approval token has TTL (default: 24h)
  4. On approval: resume from checkpoint with approver identity recorded
  5. On rejection: agent receives rejection reason, can replan
  6. On timeout: agent fails with HITL_TIMEOUT, full state preserved
```

---

## 7. Layer 4 — Orchestration & Multi-Agent Coordination

### 7.1 Orchestration Patterns Supported

| Pattern | Description | When to Use |
|---|---|---|
| Sequential | Steps run one after another | Simple linear workflows |
| Parallel Fan-Out | Multiple agents run concurrently | Independent subtasks |
| Map-Reduce | Fan-out then aggregate | Batch processing |
| Supervisor-Worker | Supervisor decomposes, delegates to specialist workers | Complex domain tasks |
| Hierarchical | Nested orchestrators | Enterprise workflows |
| Event-Driven | Agents triggered by events/webhooks | Real-time pipelines |
| Debate/Critique | Multiple agents debate then consensus | High-stakes decisions |

### 7.2 DAG Execution Engine

Workflows are expressed as DAGs (Directed Acyclic Graphs):

```
Workflow definition:
  nodes:
    - id: "extract"
      agent: "pdf-extractor-v1"
      inputs: {file: "$input.file"}

    - id: "validate"
      agent: "data-validator-v1"
      inputs: {data: "$nodes.extract.output"}
      depends_on: ["extract"]

    - id: "enrich-a"
      agent: "crm-enricher-v1"
      depends_on: ["validate"]
      run_if: "$nodes.validate.output.has_customer_id == true"

    - id: "enrich-b"
      agent: "web-enricher-v1"
      depends_on: ["validate"]

    - id: "merge"
      agent: "merger-v1"
      depends_on: ["enrich-a", "enrich-b"]
      wait_for: "all"   # or "any" or "n_of:1"

Execution:
  - Topological sort determines execution order
  - Independent nodes execute in parallel (bounded by concurrency limit)
  - Each edge carries typed, validated data
  - Workflow state persisted at each node completion (resumable)
  - Conditional branches short-circuit cleanly
```

### 7.3 Agent Communication Protocol

Agents communicate via a message bus (abstracted — Kafka / RabbitMQ / SQS / NATS):

```
AgentMessage:
  messageId:    UUID
  correlationId: UUID        # ties request to response
  workflowRunId: UUID
  fromAgent:    AgentID
  toAgent:      AgentID | "broadcast"
  type:         REQUEST | RESPONSE | ERROR | HEARTBEAT | CANCEL
  payload:      JSON         # typed by message schema registry
  sentAt:       ISO8601
  expiresAt:    ISO8601
  signature:    HMAC-SHA256  # signed with sending agent's key
  traceContext: OTELContext   # propagated for distributed tracing
```

### 7.4 Consensus Mechanism (Debate Pattern)

For high-stakes decisions (financial, medical, legal):

```
1. Orchestrator sends same problem to N agents (different models/temperatures)
2. Each agent produces an answer + reasoning
3. Critic agent evaluates all answers for consistency
4. If consensus (>= 2/3 agreement): proceed with consensus answer
5. If divergent:
   a. Escalate to HITL if configured
   b. Or: run a tiebreaker agent with all N answers as context
6. Final answer cites which agents agreed, which dissented, why
```

---

## 8. Layer 5 — LLM Abstraction & Model Routing

### 8.1 Provider Adapter Interface

```
interface LLMProvider {
  id:             string
  capabilities:   ModelCapability[]    // TEXT, VISION, CODE, FUNCTION_CALL, LONG_CONTEXT
  maxContextTokens: int
  costPer1kInputTokens:  Decimal
  costPer1kOutputTokens: Decimal

  complete(request: CompletionRequest): Promise<CompletionResponse>
  stream(request: CompletionRequest):   AsyncIterator<CompletionChunk>
  embed(request: EmbedRequest):         Promise<EmbedResponse>
  countTokens(text: string):            int
}

// Adapters implemented for:
// OpenAI (gpt-4o, gpt-4-turbo, gpt-3.5-turbo)
// Anthropic (claude-3-5-sonnet, claude-3-haiku, claude-opus-4)
// Google (gemini-1.5-pro, gemini-flash)
// Mistral (mistral-large, mistral-7b)
// Cohere (command-r+)
// AWS Bedrock (any underlying model)
// Azure OpenAI (same interface, different endpoint)
// Ollama (local, for dev/cost-sensitive)
// vLLM (self-hosted)
```

### 8.2 Model Router

Routes each LLM call to the optimal provider based on configured strategy:

```
Routing Strategies:

COST_AWARE:
  - Score models by: (quality_score / cost_per_token)
  - Select highest ratio that meets minimum quality bar
  - Quality bar set by agent's task_complexity

CAPABILITY_MATCH:
  - Filter to models supporting required capabilities
  - Prefer highest capability match
  - Example: vision task → only vision-capable models

LATENCY_FIRST:
  - Sort by p50 latency (measured, not vendor-claimed)
  - Use for user-facing real-time interactions

ROUND_ROBIN:
  - Distribute load across providers for resilience
  - Useful for high-volume batch jobs

A/B_ROUTING:
  - Send percentage of traffic to experimental model
  - Collect quality metrics for comparison
```

### 8.3 Semantic Cache

Before hitting any LLM provider, check cache:

```
Cache key: SHA256(
  model_id +
  messages_canonical_form +
  temperature +
  tools_hash
)

Cache lookup:
  1. Exact match (hash) → return immediately, zero cost
  2. Semantic similarity match:
     a. Embed the incoming prompt
     b. Search vector cache for nearest neighbors (threshold: 0.95 cosine)
     c. If match found and temperature=0: return cached response
  3. Miss → call provider → store in cache

Cache store: Redis (hot, < 1h TTL) + vector DB (warm, up to 7d TTL)
Cache hit rate target: > 30% for repetitive workloads
Cache invalidation: explicit (on agent redeploy) + TTL-based
```

### 8.4 Token Budget Enforcement

Enforced in three places. **Race condition prevention is critical** — in multi-agent parallel execution, naive read-then-check allows multiple concurrent calls to all pass the budget check simultaneously, each consuming up to the full remaining budget.

```
ATOMIC Pre-call check (HARD) — uses Redis atomic increment:

  # Redis Lua script (executes atomically, no TOCTOU race)
  local current = redis.call('GET', budget_key) or 0
  local estimated = tonumber(ARGV[1])   -- estimated tokens for this call
  local max = tonumber(ARGV[2])         -- max_tokens_per_run
  if tonumber(current) + estimated > max then
    return -1   -- REJECT
  end
  redis.call('INCRBY', budget_key, estimated)
  redis.call('EXPIRE', budget_key, 86400)
  return 1      -- APPROVED (reservation made)

  On REJECT: raise BUDGET_EXCEEDED, do not call LLM.
  On APPROVE: reservation is held. Reconcile after call.

Post-call reconciliation:
  actual_used = response.prompt_tokens + response.completion_tokens
  delta = actual_used - estimated
  redis.call('INCRBY', budget_key, delta)    -- adjust for over/under estimate
  cost_ledger.record(callId, actual_cost)    -- async write to DB

Soft warning at 80% consumed:
  emit BUDGET_WARNING event
  plugin hook: ON_COST_THRESHOLD fired
  agent may choose to summarize context to reduce future usage
```

### 8.5 Tokenizer Abstraction (Per Model)

Token counting MUST use the correct tokenizer for each model. `tiktoken` only covers OpenAI models. Using the wrong tokenizer leads to incorrect budget enforcement.

```python
# core/interfaces/tokenizer.py
class TokenizerAdapter(ABC):
    @abstractmethod
    def count(self, text: str) -> int: ...

    @abstractmethod
    def count_messages(self, messages: list[dict]) -> int: ...

# Implementations:
# adapters/tokenizer/tiktoken_adapter.py   → OpenAI, GPT-4o, GPT-3.5
# adapters/tokenizer/sentencepiece.py      → Llama, Mistral, Gemma, Phi
# adapters/tokenizer/hf_tokenizer.py       → Any HuggingFace model (AutoTokenizer)
# adapters/tokenizer/estimate.py           → Fallback: 4 chars ≈ 1 token estimate

# Registry maps model_id → tokenizer_adapter
TOKENIZER_REGISTRY = {
    "gpt-4o":                  TiktokenAdapter("cl100k_base"),
    "gpt-4o-mini":             TiktokenAdapter("cl100k_base"),
    "ollama/llama3.1:8b":      SentencePieceAdapter("llama3"),
    "ollama/mistral:7b":       SentencePieceAdapter("mistral"),
    "ollama/phi3:medium":      SentencePieceAdapter("phi3"),
    "bedrock/anthropic.*":     TiktokenAdapter("cl100k_base"),  # approximation
    "__default__":             EstimateAdapter(),               # safe fallback
}
```

### 8.6 Streaming Protocol Decision

```
Protocol   Use Case                           Reason
────────────────────────────────────────────────────────────────
SSE        Run event streaming to client      Unidirectional, works through
           (step complete, token stream,      all HTTP proxies, simpler
           cost updates)                      client implementation

WebSocket  Interactive HITL sessions          Bidirectional needed:
           where user sends approval          server pushes approval request,
           mid-stream                         client sends approval decision

gRPC       Internal service-to-service        Efficient binary framing,
           communication only                 not exposed to external clients
```

**SSE is the default for all public API streaming.** WebSocket is only opened when an agent run explicitly enters HITL_WAIT state and requires bidirectional communication.

### 8.7 PII on Streaming Output — Solved Design

Streaming token-by-token and PII masking are in conflict. Solution: **sliding window buffer**.

```
PII Streaming Strategy:

1. LLM streams tokens into a server-side buffer
2. Buffer flushes to client when:
   a. Buffer contains a "safe" delimiter (sentence end, newline, paragraph)
   b. AND no PII entity spans the flush boundary
3. PII scanner runs on buffer using sliding window:
   - Window size: 200 chars (enough to detect any PII pattern)
   - Overlap: 50 chars (prevents split-entity misses)
4. On PII detected within window:
   a. Replace entity with [MASKED:TYPE]
   b. Flush up to start of entity
   c. Flush masked replacement
   d. Continue streaming from after entity
5. On stream end: flush remainder, final PII scan pass

Tradeoffs accepted:
  - Latency added: 50-100ms vs raw streaming (buffer accumulation)
  - This is a deliberate product decision: safety over raw speed
  - Configurable: PII_STREAM_BUFFER_MS per agent definition

For agents where PII is guaranteed absent (e.g., code generation only):
  - pii_scan_output: false in agent definition
  - Zero buffer, raw token streaming
```

### 8.8 Prompt Construction & Injection Defense

```
PromptBuilder:
  1. Load system prompt template
  2. Resolve template variables (only from allowlisted sources)
  3. Apply tool definitions
  4. Pack conversation history (respecting context window)
  5. Inject retrieved context (RAG)
  6. Apply PII masking pass
  7. Validate final prompt against injection patterns
  8. Count tokens (abort if over model limit)
  9. Hash for cache lookup

Template variable resolution:
  ALLOWED: tenant config, user profile fields (whitelisted), KB lookups
  NEVER: raw user input directly into system prompt position
  ALWAYS: user input goes into user message position, clearly delimited
```

### 8.9 Response Validation

Every LLM response is validated before being acted upon:

```
1. Schema validation (if output schema defined)
   - JSON parse
   - JSON Schema validation
   - Semantic type checks
   - On failure: retry with schema re-enforcement in prompt (max 2 retries)

2. Hallucination scoring (see Layer 11)

3. Content policy check
   - Toxicity, bias, restricted content
   - Custom domain policies

4. PII scan on output (see Layer 10)

5. Refusal detection
   - Detect when model refused to follow instruction
   - Route to different provider if refusal pattern detected

6. Citation validation
   - If citations_required: verify every factual claim has a source reference
```

---

## 9. Layer 6 — Tool Registry & Execution Sandbox

### 9.1 Tool Definition Schema

```yaml
# tool definition — registered once, used by any agent
id: "web_search"
version: "1.2.0"
description: "Search the web for current information"
category: "information_retrieval"

input_schema:
  type: object
  properties:
    query:
      type: string
      maxLength: 512
      sanitize: true          # strip special chars, normalize unicode
    max_results:
      type: integer
      default: 5
      maximum: 20
    allowed_domains:
      type: array
      items: {type: string, format: regex}

output_schema:
  type: object
  properties:
    results:
      type: array
      items:
        type: object
        properties:
          url:     {type: string, format: uri}
          title:   {type: string}
          snippet: {type: string}
          retrieved_at: {type: string, format: datetime}

authorization:
  required_scopes:  ["tools:web_search"]
  risk_level:       MEDIUM        # LOW | MEDIUM | HIGH | CRITICAL
  requires_hitl:    false

execution:
  timeout_seconds:  30
  retry_count:      2
  sandbox:          "network_isolated"   # none | network_isolated | full_sandbox

rate_limits:
  per_run:          50
  per_minute:       10
  per_day_per_tenant: 10000

audit:
  log_inputs:   true
  log_outputs:  true
  pii_scan:     both      # inputs | outputs | both | none
```

### 9.2 Tool Registry

```
ToolRegistry:
  register(tool: ToolDefinition): void
  get(toolId: string, version?: semver): ToolDefinition
  list(filter: ToolFilter): ToolDefinition[]
  authorize(toolId: string, principal: Principal): AuthzDecision
  getAdapter(toolId: string): ToolAdapter
  validateInput(toolId: string, input: JSON): ValidationResult
  validateOutput(toolId: string, output: JSON): ValidationResult

Tool categories (built-in):
  Core:       file_read, file_write, structured_output, http_request
  Search:     web_search, kb_search, database_query
  Code:       code_exec, shell_exec (sandboxed)
  Data:       csv_parse, json_transform, pdf_extract
  External:   email_send, slack_post, calendar_read
  AI:         image_analyze, audio_transcribe, document_classify
```

### 9.3 Sandbox Execution

All tool execution happens inside isolated environments:

```
Sandbox types by risk level:

NONE (LOW risk):
  - In-process execution
  - No I/O, pure computation
  - Example: JSON transform, text manipulation

NETWORK_ISOLATED (MEDIUM risk):
  - Separate process
  - No outbound network except allowlisted domains
  - Filesystem access: read-only, scoped directory
  - CPU limit: 1 core, Memory: 256MB, Time: 30s

FULL_SANDBOX (HIGH risk):
  - Separate container (gVisor or similar)
  - Network: egress through controlled proxy only
  - Filesystem: ephemeral, destroyed after run
  - No access to host resources
  - Seccomp profile applied
  - No privilege escalation

CRITICAL risk:
  - Requires HITL approval before execution
  - Executed in dedicated VM (not container)
  - Full forensic recording of all syscalls
  - Results reviewed by policy engine before returned to agent
```

### 9.4 Tool Call Security

```
Before execution:
  1. AuthZ check (does this agent have permission for this tool?)
  2. Input schema validation
  3. Input sanitization (SQL injection, path traversal, command injection)
  4. PII scan on inputs
  5. Rate limit check

During execution:
  1. Timeout wrapper
  2. Resource limits enforced
  3. Syscall monitoring (in high-risk sandboxes)

After execution:
  1. Output schema validation
  2. PII scan on outputs
  3. Content policy check on outputs
  4. Sensitive data detection (credentials, keys in outputs)
  5. Audit log write (synchronous)
  6. Metrics emission
```

### 9.5 Dangerous Tool Interception

Some tools require special handling:

| Tool | Risk | Mitigation |
|---|---|---|
| code_exec | Arbitrary execution | Full sandbox, no network, resource limits, static analysis pre-run |
| shell_exec | Same as above | Disabled by default, CRITICAL risk level |
| http_request | SSRF | Block private IP ranges (10/8, 172.16/12, 192.168/16, 169.254/16), allowlist domains |
| file_write | Data exfiltration | Scoped to run temp dir, virus scan on content |
| email_send | Spam/phishing | Rate limited, recipient allowlist, content scan |
| db_query | SQL injection | Parameterized queries enforced, read-only by default |

---

## 10. Layer 7 — Memory & Context Management

### 10.1 Memory Architecture (Three Tiers)

```
┌─────────────────────────────────────────────────────────┐
│ WORKING MEMORY (in-flight, per run)                     │
│  • Current conversation turns                           │
│  • Active tool results                                  │
│  • Current plan and step state                         │
│  • Storage: in-memory (Redis-backed for HA)            │
│  • Lifetime: run duration                              │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ on run complete
┌─────────────────────────────────────────────────────────┐
│ EPISODIC MEMORY (per user/agent, session-scoped)        │
│  • Past run summaries                                   │
│  • User preferences observed                           │
│  • Successful/failed patterns                          │
│  • Storage: PostgreSQL + vector embeddings             │
│  • Lifetime: configurable (default: 90 days)          │
│  • Retrieval: recency + relevance weighted             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ curated, high-value facts
┌─────────────────────────────────────────────────────────┐
│ SEMANTIC MEMORY (per agent, shared across users)        │
│  • Domain knowledge, curated facts                     │
│  • Entity relationships                                │
│  • Agent's "learned" expertise                         │
│  • Storage: vector DB + knowledge graph               │
│  • Lifetime: until explicitly invalidated              │
│  • Retrieval: semantic similarity                      │
└─────────────────────────────────────────────────────────┘
```

### 10.2 Context Window Management

```
Context Window Packer (token budget aware):

Priority order (highest → lowest):
  1. System prompt (always included)
  2. Most recent N turns (always included)
  3. Retrieved episodic memories (relevant to current task)
  4. Retrieved semantic memories (domain knowledge)
  5. Injected RAG context
  6. Older conversation history (summarized if needed)
  7. Auxiliary context

Algorithm:
  available = model.maxContextTokens - output_token_reserve
  pack(SYSTEM_PROMPT)               → always
  pack(RECENT_N_TURNS, n=6)         → always
  remaining = available - used_so_far
  add MEMORIES by relevance_score until remaining < memory_budget
  add RAG_CONTEXT until remaining < 0 (truncate last chunk gracefully)
  if still over: run summarizer on oldest history, replace with summary

Summarizer:
  - Runs on a cheap/fast model (not the primary model)
  - Produces: key facts, decisions made, entities mentioned
  - Stored back as a memory entry
  - Token savings target: 70% compression ratio
```

### 10.3 Memory Privacy

- Episodic memories are tenant + user scoped (never cross tenants)
- Semantic memories are agent scoped (optionally shared across users of same tenant)
- Memory entries inherit PII classification of their source run
- PII-HIGH memories are auto-expired after 30 days
- Users can invoke "right to be forgotten" → purge all episodic memories for their user ID

---

## 11. Layer 8 — RAG & Knowledge Layer

### 11.1 Ingestion Pipeline

```
Document → Ingestion Pipeline → Vector Store

Pipeline stages:
  1. FORMAT DETECTION
     - Detect: PDF, DOCX, PPTX, HTML, MD, CSV, JSON, image
     - Route to appropriate parser

  2. EXTRACTION
     - PDF: PyMuPDF or LlamaParse (configurable)
     - HTML: BeautifulSoup + Readability
     - Tables: structure-aware table extractor
     - Images: OCR + vision model captioning

  3. PRE-PROCESSING
     - Language detection
     - Boilerplate removal (headers/footers)
     - Normalization (whitespace, encoding)
     - PII scan + classification
     - If PII-HIGH: apply masking before storage

  4. CHUNKING (configurable strategy)
     - Fixed-size: 512 tokens, 10% overlap (simple, fast)
     - Semantic: sentence-boundary aware, coherence-scored
     - Hierarchical: parent-child chunks (retrieve child, embed parent context)
     - Document-structure-aware: heading-based sections

  5. METADATA EXTRACTION
     - Title, author, date, source URL
     - Section headings, page numbers
     - Custom metadata (tenant-defined)
     - Content classification

  6. EMBEDDING
     - Pluggable embedding model (default: text-embedding-3-small or equiv)
     - Batch embedding for efficiency
     - Dimension: 1536 (OpenAI) or 384/768/1024 (local models)
     - Multi-vector: different embeddings for different retrieval strategies

  7. INDEXING
     - Write to vector store (adapter pattern)
     - Write to BM25 index (for keyword search)
     - Store raw chunk text in object store (for faithfulness check)
     - Update knowledge graph (entities + relationships)

  8. VERIFICATION
     - Re-retrieve sample chunks, verify embeddings are meaningful
     - Log ingestion metrics (chunks created, tokens, cost, time)
```

### 11.2 Retrieval Pipeline

```
Query → Retrieval → Reranking → Context Assembly

1. QUERY ANALYSIS
   - Intent classification
   - Entity extraction from query
   - Query expansion (HyDE: generate hypothetical answer, embed that)
   - Multi-query generation (3-5 reformulations, retrieve for each)

2. MULTI-STRATEGY RETRIEVAL (run in parallel)
   a. Dense retrieval: embed query → ANN search in vector store
   b. Sparse retrieval: BM25 keyword search
   c. Graph retrieval: entity-based traversal in knowledge graph
   d. Time-filtered: recency-boosted for time-sensitive queries

3. FUSION & DEDUPLICATION
   - Reciprocal Rank Fusion (RRF) across all retrieval strategies
   - Remove duplicate chunks (similarity > 0.98)
   - Limit to top K candidates (K = 20-50)

4. RERANKING
   - Cross-encoder reranker (e.g., ms-marco-MiniLM or Cohere Rerank)
   - Scores each candidate for relevance to query
   - Select top N (N = 5-10) for context injection

5. CONTEXT ASSEMBLY
   - Order by relevance
   - Include source citations (document, page, section)
   - Truncate to fit token budget
   - Format citations in structured form for validation

6. FAITHFULNESS GUARDRAIL (post-response)
   - After LLM response: verify each claim can be traced to a retrieved chunk
   - Unverifiable claims flagged (see Layer 11)
```

### 11.3 Vector Store Adapter Interface

```
interface VectorStore {
  upsert(vectors: Vector[], namespace: string): Promise<void>
  query(embedding: float[], topK: int, filter: MetadataFilter): Promise<SearchResult[]>
  delete(ids: string[], namespace: string): Promise<void>
  namespaceStats(namespace: string): Promise<Stats>
}

// Adapters: Qdrant · Pinecone · Weaviate · pgvector · Chroma · Milvus
// Namespace = tenant_id + agent_id + kb_id (full isolation)
```

### 11.4 Embedding Dimension Migration Strategy

When switching embedding models (e.g., moving from OpenAI text-embedding-3-small at 1536d to a local model at 768d, or upgrading to a higher-dimension model), a naive swap breaks all existing vectors. Migration procedure:

```
Phase 1 — Dual-write (zero downtime):
  1. Register new embedding model in config alongside old model
  2. Configure vector store to maintain two collections per namespace:
       {namespace}__v1  → old model, 1536d
       {namespace}__v2  → new model, 768d
  3. New ingestion writes to BOTH collections
  4. Retrieval reads from v1 only (stable queries)

Phase 2 — Backfill (async, offline):
  5. Background job re-embeds all existing chunks using new model
     Rate: 1,000 chunks/min (CPU-bound; do not saturate GPU queue)
     Checkpoint every 10,000 chunks to allow pause/resume
     Verify: sample 1% of chunks, compare retrieval quality
  6. Track backfill progress: backfill_progress_{kb_id} in Redis

Phase 3 — Cutover:
  7. When backfill_progress = 100%, switch retrieval to v2 collection
     (config change only — no code deploy needed)
  8. Run dual-retrieval smoke test (compare top-5 results for N=100 queries)
  9. Monitor retrieval quality metrics for 48h
  10. If quality unchanged or improved: delete v1 collection + stop dual-write

Rollback: switch retrieval back to v1 collection (single config value change)

Key constraints:
  - Dimension mismatch is hard: v1 and v2 vectors are not comparable
  - Never query across dimensions — always use model-matched collection
  - Store embedding model name + dimension in chunk metadata for auditability
  - Knowledge base schema version tracks which embedding model was used
```

### 11.5 Knowledge Graph — Technology Decision

Knowledge graph is optional and scoped to semantic memory enrichment (entity-relationship extraction). It is NOT a primary query path — dense + sparse retrieval handles the majority of RAG queries.

```
Scope:
  USE for: entity extraction, relationship-aware retrieval, schema-guided question answering
  DO NOT use for: primary retrieval (too slow), real-time data (not designed for it)

Default implementation: Apache AGE (PostgreSQL extension)
  - Runs inside existing PostgreSQL cluster (no new infrastructure)
  - Cypher query language
  - Tenant-isolated via graph label prefix: tenant_{id}_entity
  - Good fit for moderate-scale graphs (< 10M nodes per tenant)

Alternative if graph scale exceeds PostgreSQL capacity:
  - Neo4j (self-hosted) or Neo4j Aura (managed)
  - Swap via GraphStoreAdapter ABC (same interface)

GraphStoreAdapter interface:
  upsert_entities(entities: list[Entity], tenant_id: str) -> None
  upsert_relationships(rels: list[Relationship], tenant_id: str) -> None
  query_neighbors(entity_id: str, depth: int, tenant_id: str) -> list[Entity]
  delete_tenant(tenant_id: str) -> None

When to skip knowledge graph entirely:
  - If no agents require multi-hop entity reasoning: set enable_knowledge_graph: false
  - Dense retrieval + reranker handles 95% of factual Q&A use cases adequately
  - Knowledge graph adds ingestion latency (~200ms per document for NER + relation extraction)
```

---

## 12. Layer 9 — Security & Threat Defense

### 12.1 Prompt Injection Defense

Prompt injection is the OWASP #1 risk for LLM applications. Multi-layer defense:

```
LAYER A — Structural Defense (pre-LLM):
  - User input always in "user" role, never system role
  - Clear delimiters between system, user, and retrieved content
    Example: """USER INPUT START""" ... """USER INPUT END"""
  - Template variables escaped before injection
  - Length limits per input position

LAYER B — Pattern Detection (pre-LLM):
  - Regex patterns: "ignore previous", "disregard instructions",
    "you are now", "new persona", "DAN mode", "developer mode"
  - Adversarial suffix detection (known attack patterns)
  - Unicode normalization (catch zero-width space, homograph attacks)
  - Scoring: flag > threshold, block > hard threshold

LAYER C — Semantic Detection (pre-LLM):
  - Classifier model (fine-tuned for injection detection)
  - Embed input, compare to injection pattern clusters
  - Any similarity > 0.7 to injection pattern → flag

LAYER D — Response Monitoring (post-LLM):
  - Detect if agent is deviating from its task definition
  - Flag unexpected tool calls not in the plan
  - Flag responses that reference system prompt content (exfiltration)
  - Flag responses in unexpected languages/formats

LAYER E — Architectural (always active):
  - Tool calls are validated against agent's tool allowlist (never open-ended)
  - External content (RAG, web) marked as untrusted in prompt
  - Separate context positions for trusted vs untrusted content
```

### 12.2 Output Sanitization

```
All agent outputs pass through output sanitizer before delivery:

  1. Strip any remaining PII per masking policy
  2. HTML escape if output is rendered in browser
  3. Detect and redact API keys, secrets, credentials in output
     - Regex patterns for common secret formats
     - Entropy analysis for high-entropy strings
  4. Strip any instructions or jinja/template syntax
  5. Validate against output schema
  6. Content safety classification (toxicity, hate, self-harm)
     - Threshold-based: warn | redact | block
```

### 12.3 Secret Scanning in I/O

```
Secret patterns detected (before LLM and in output):

  AWS Access Key:      AKIA[0-9A-Z]{16}
  AWS Secret Key:      [0-9a-zA-Z/+]{40}
  OpenAI API Key:      sk-[a-zA-Z0-9]{48}
  Anthropic API Key:   sk-ant-[a-zA-Z0-9-]{95}
  GitHub Token:        (ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}
  Private Key PEM:     -----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----
  JWT:                 [A-Za-z0-9+/]+\.[A-Za-z0-9+/]+\.[A-Za-z0-9+/]+
  Generic High Entropy: >4.5 entropy strings > 20 chars
  Credit Card:         [0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}
  SSN:                 [0-9]{3}-[0-9]{2}-[0-9]{4}

On detection:
  - Replace with [REDACTED:SECRET_TYPE]
  - Emit SECURITY_EVENT to audit log
  - Alert security team (configurable threshold)
  - Abort run if in system prompt position (exfiltration attempt)
```

### 12.4 Supply Chain Security (Tool and Plugin)

```
Plugin verification:
  - All plugins must be signed (code signing certificate)
  - Signature verified at load time
  - Hash pinned in platform config
  - SBOM (Software Bill of Materials) required for each plugin
  - CVE scanning on plugin dependencies (automated, blocks install if critical CVE)
  - No plugins from unknown publishers without explicit allowlist

Tool adapter verification:
  - Same signing requirement as plugins
  - Tool network calls go through audited proxy
  - No direct outbound except through registered adapters
```

### 12.5 Network Security

```
Internal service communication:
  - All internal calls: mTLS (service mesh, e.g., Istio/Linkerd)
  - Service accounts per service (not shared credentials)
  - Zero trust: every internal call authenticated + authorized

Outbound (tool calls to external APIs):
  - All outbound through egress proxy
  - Domain allowlist enforced at proxy level
  - TLS certificate validation (no insecure)
  - Request/response logged at proxy level (for audit)
  - No direct outbound from agent execution environment

Data at rest:
  - All databases encrypted (AES-256)
  - Encryption keys in secret store (not alongside data)
  - Vector store: namespace-level encryption

Data in transit:
  - TLS 1.3 everywhere
  - Certificate pinning for critical external dependencies
  - HSTS enforced
```

---

## 13. Layer 10 — PII, Privacy & Data Governance

### 13.1 PII Detection Engine

```
Detection methods (multi-layer):

REGEX (fast, exact):
  - Name patterns (proper noun heuristics)
  - Email: RFC 5322 pattern
  - Phone: E.164 + local formats
  - SSN, TIN, passport numbers
  - Credit card (Luhn check)
  - IP addresses (v4 and v6)
  - Dates of birth
  - Bank account numbers (IBAN, routing)
  - Medical record numbers

NLP-BASED (slower, higher recall):
  - NER model (fine-tuned on PII datasets)
  - Detects contextual PII (e.g., "my patient John Smith" → person entity)
  - Multi-language support
  - Confidence scores per detected entity

CONTEXT-AWARE:
  - PII detected in context of a sensitive field is weighted higher
  - Example: "age: 42" alone vs "patient age: 42" in medical context

Classification tiers:
  PII-LOW:     First name only, generic city
  PII-MEDIUM:  Full name, email, phone, IP address
  PII-HIGH:    SSN, passport, financial, medical, biometric
  PII-CRITICAL: Combined identifiers that enable re-identification
```

### 13.2 PII Actions

Per-tenant, per-agent configurable:

```
PASSTHROUGH:   No modification (must be explicitly configured for justified reason)
MASK:          Replace with [MASKED:TYPE] — default for PII-MEDIUM
PSEUDONYMIZE:  Replace with consistent token within a session (reversible, keyed)
ANONYMIZE:     Replace with category label (irreversible)
ENCRYPT:       Encrypt in place (authorized users can decrypt)
BLOCK:         Reject the entire request if PII detected

Policy matrix example:
  Source\PII-Level   LOW         MEDIUM        HIGH          CRITICAL
  User Input         PASSTHROUGH MASK          PSEUDONYMIZE  BLOCK
  LLM Output         PASSTHROUGH MASK          ANONYMIZE     ANONYMIZE
  Tool Input         MASK        MASK          ANONYMIZE     BLOCK
  Tool Output        PASSTHROUGH MASK          PSEUDONYMIZE  ENCRYPT
  Logs               PASSTHROUGH PSEUDONYMIZE  ANONYMIZE     ANONYMIZE
  Audit Trail        PASSTHROUGH PSEUDONYMIZE  PSEUDONYMIZE  PSEUDONYMIZE
```

### 13.3 Data Residency & Sovereignty

```
Tenant-level data residency configuration:
  data_residency:
    regions: ["us-east-1", "eu-west-1"]
    cross_region_allowed: false
    llm_provider_regions: ["us", "eu"]   # only use providers with data centers here

Enforcement:
  - LLM router filters providers by declared data residency
  - Vector store namespaced to region
  - Audit logs written to regional store
  - Data never leaves configured regions (verified by egress proxy)
  - Contractual: providers that don't offer regional isolation are not routed to
```

### 13.4 Compliance Frameworks

| Framework | Controls Implemented |
|---|---|
| GDPR | Right to erasure, data portability, purpose limitation, DPA records, breach notification hooks |
| CCPA | Right to know, right to delete, opt-out of sale, privacy notice |
| HIPAA | PHI detection, audit controls, encryption at rest/transit, BAA hooks, minimum necessary |
| SOC 2 Type II | Access controls, change management, monitoring, incident response |
| ISO 27001 | Risk assessment, asset management, control framework |
| PCI DSS | CHD detection, masking, audit logging, access control |

Data retention policies (configurable, defaults):
```
Run logs:           90 days (compressed)
Audit logs:         7 years (immutable, replicated)
PII-HIGH content:   30 days (then purged from all stores)
Episodic memory:    90 days (unless user extends)
Embeddings:         Until document deleted + 7 days
Billing records:    7 years
```

### 13.5 Right to Erasure (GDPR Article 17)

```
Erasure request flow:
  1. Request received (API endpoint + user identity verified)
  2. Enqueue erasure job for user_id across all stores:
     - Working memory: immediate
     - Episodic memory: delete all entries for user_id
     - Audit logs: pseudonymize user_id (cannot delete for legal hold)
     - Vector store: delete chunks tagged with user_id
     - Run logs: anonymize user references
     - LLM call cache: purge entries for user sessions
  3. Cascade to any connected downstream systems via erasure webhooks
  4. Completion confirmed within 30 days
  5. Erasure receipt issued (audit-able)
```

---

## 14. Layer 11 — Hallucination Control & Output Quality

### 14.1 Hallucination Detection — Multi-Signal Approach

```
Signal 1 — Self-consistency (expensive — conditional triggers only):
  - Run same prompt N=3 times at temperature=0.7 using the CHEAPEST available model
  - Compare outputs for factual consistency
  - High variance in named entities/numbers → high hallucination risk
  - Cost: 3x cheap model cost (e.g., 3 × haiku calls, not 3 × opus calls)

  TRIGGER CONDITIONS (not run by default — must meet at least one):
    a. Agent definition sets hallucination_check: strict
    b. Task is classified as HIGH_STAKES (financial, medical, legal domain)
    c. Prior faithfulness score for this run already > 0.4
    d. No RAG context available (nothing to cross-check against)
    e. Explicit agent config: self_consistency: true

  DO NOT trigger for: code generation, creative tasks, data extraction with schema,
  any agent where temperature: 0.0 is already set (deterministic = no variance)

Signal 2 — RAG faithfulness:
  - For every factual claim in output, search retrieved context
  - Faithfulness score = claims_supported / total_claims
  - Unsupported claims = potential hallucination
  - Tool: NLI (Natural Language Inference) model as claim verifier

Signal 3 — Uncertainty quantification:
  - Monitor model's token probabilities (where API exposes logprobs)
  - Low confidence tokens on key entities flag potential hallucination
  - Entropy of next token distribution as uncertainty proxy

Signal 4 — External verification (optional, high-stakes):
  - For claimed facts (dates, numbers, names): web search verification
  - Compare claim against retrieved evidence
  - Cost: 1 web search per factual claim (use selectively)

Signal 5 — Knowledge boundary detection:
  - Classify question type: factual vs opinion vs reasoning
  - For factual questions: require citation or flag as unverified
  - Detect when model reasons about topics outside training data scope

Composite hallucination score: weighted average of available signals
  score 0.0 - 0.3: Low risk — proceed
  score 0.3 - 0.6: Medium risk — attach confidence warning to output
  score 0.6 - 0.8: High risk — trigger verification pipeline or HITL
  score 0.8 - 1.0: Abort — return error with explanation, do not surface output
```

### 14.2 Structural Quality Controls

```
Output schema enforcement:
  - Define expected output structure in JSON Schema
  - Parse and validate every response
  - If parse fails: retry with explicit format instructions (max 2 retries)
  - If still fails: return structured error (never raw malformed output)

Citation enforcement:
  - If citations_required: every factual claim must have [Source: X] reference
  - Verify cited sources were actually in retrieved context
  - Strip fabricated citations (claims to cite source not in context)
  - Return claims without valid citations as unverified

Numeric validation:
  - Numbers extracted from output validated against source documents
  - Arithmetic checked where verifiable (totals, dates, ages)
  - Suspicious numbers (e.g., sum doesn't add up) flagged

Temporal validation:
  - Dates checked for plausibility (not in future if historical query)
  - Event sequences checked for chronological consistency
```

### 14.3 Model-Level Controls

```
Temperature discipline:
  - Factual extraction tasks: temperature 0.0-0.2
  - Analysis tasks: temperature 0.2-0.5
  - Creative tasks: temperature 0.5-1.0
  - Default: 0.2 (conservative)

Grounding instructions in system prompt:
  - "Only state facts supported by the provided context"
  - "If unsure, say 'I don't have enough information' rather than guessing"
  - "Quote the source text when making factual claims"
  - "Never invent names, numbers, or dates"

Chain-of-thought enforcement:
  - For complex reasoning: require step-by-step reasoning before answer
  - Reasoning logged separately for audit
  - Reasoning quality scored (coherence, completeness)

Stop sequences:
  - Configure model to stop before common hallucination triggers
  - E.g., stop before generating references it can't verify
```

---

## 15. Layer 12 — Cost Management & FinOps

### 15.1 Cost Tracking

Every token consumed is tracked in real time:

```
CostLedger:
  record(entry: CostEntry): void
  
CostEntry:
  entryId:        UUID
  timestamp:      ISO8601
  tenantId:       UUID
  agentId:        UUID
  runId:          UUID
  callId:         UUID
  provider:       ProviderID
  model:          ModelID
  promptTokens:   int
  completionTokens: int
  cachedTokens:   int           # tokens served from cache (cost = 0)
  unitCostUSD:    Decimal       # per 1k tokens
  totalCostUSD:   Decimal
  feature:        string        # what agent feature triggered this
  cached:         bool

Aggregation views (materialized, refreshed every 60s):
  - Cost by tenant/day/agent/model
  - Cost by feature
  - Cost trend (7d, 30d)
  - Cache savings (how much caching saved)
  - Top cost consumers
```

### 15.2 Budget Enforcement Hierarchy

```
Level 1 — Platform budget (ops team sets):
  global_daily_budget_usd:  10000
  global_alert_threshold:   0.8

Level 2 — Tenant budget (per tenant):
  monthly_budget_usd:       500
  daily_budget_usd:         50
  burst_allowed:            false

Level 3 — Agent budget (per agent definition):
  max_cost_usd_per_run:     0.50
  max_tokens_per_run:       50000
  max_llm_calls_per_run:    20

Level 4 — User budget (per end user):
  max_cost_usd_per_day:     5.00
  max_runs_per_day:         100

Enforcement is HARD at levels 1, 3, 4 (abort run).
SOFT at level 2 (alert + optional throttle).
```

### 15.3 Cost Optimization Strategies

```
CACHING:
  - Semantic cache (see Layer 5): 30%+ cache hit rate target
  - Exact cache for repetitive prompts
  - Prompt caching (Anthropic extended context cache): 90% discount on cached tokens

MODEL ROUTING (cost-optimized):
  - Classify task complexity before routing
  - Simple extraction → cheap/fast model (gpt-4o-mini, haiku)
  - Complex reasoning → expensive model
  - Expected savings: 40-60% vs always-use-best-model

CONTEXT COMPRESSION:
  - Summarize long conversations before passing to LLM
  - Remove redundant tool results from context
  - Use retrieval instead of injecting full documents
  - Target: keep prompt tokens under 50% of context window unless necessary

TOKEN COUNTING PRE-FLIGHT:
  - Count tokens BEFORE calling LLM (using tiktoken or equivalent)
  - Abort if over budget (zero cost)
  - Compress context automatically if approaching limit

BATCH PROCESSING:
  - Non-urgent tasks queued and processed in batch (off-peak)
  - Batch API pricing where available (OpenAI Batch: 50% discount)
  - Priority queues: real-time vs background

PROGRESSIVE ELABORATION:
  - Start with cheap model for initial attempt
  - Escalate to expensive model only on failure or insufficient quality
  - Reduces average cost while preserving quality on complex tasks
```

### 15.4 Cost Anomaly Detection

```
Anomaly signals:
  - Sudden spike: cost > 3x p95 for that agent in rolling 24h
  - Rate acceleration: cost growth rate > 200% vs prior period
  - Single run: cost > 10x agent average
  - User: cost > 5x that user's average

On anomaly:
  - Alert operations team (severity based on magnitude)
  - Optionally: throttle the offending agent/user
  - Log anomaly for investigation
  - If > hard threshold: automatically suspend with notification
```

### 15.5 Showback & Chargeback

```
Tenant-facing cost visibility:
  - Real-time cost dashboard (streaming updates)
  - Per-agent, per-run cost breakdown
  - Cost attribution by feature/workflow
  - Projected monthly cost based on current usage
  - Cost optimization recommendations (generated by cost analyzer agent)

Internal chargeback (for enterprise customers):
  - Cost allocated to business units (BU ID passed in request header)
  - BU-level reports
  - Budget alerts per BU
```

---

## 16. Layer 13 — Observability, Monitoring & Alerting

### 16.1 The Three Pillars — All Agent-Aware

#### Distributed Tracing (OTEL)

Every agent run generates a root trace span. Child spans for each:

```
Trace hierarchy:
  run:{runId}
    ├── auth:{callId}
    ├── security_scan:{scanId}
    ├── planning:{planId}
    ├── step:{stepId}
    │     ├── llm_call:{callId}
    │     │     ├── token_count
    │     │     ├── cache_lookup
    │     │     └── provider_call
    │     └── tool_call:{callId}
    │           ├── authz_check
    │           ├── sandbox_setup
    │           ├── execution
    │           └── output_validation
    ├── hallucination_check:{checkId}
    ├── pii_scan:{scanId}
    └── output_validation:{validationId}

OTEL attributes (all spans):
  tenant.id, agent.id, run.id, user.id
  model.id, model.provider, model.version
  cost.usd, cost.tokens_prompt, cost.tokens_completion
  cache.hit, cache.type
  hallucination.score
  pii.detected, pii.types_detected
  security.injection_score
  latency.llm_ms, latency.total_ms
  error.code, error.type
```

#### Metrics (Prometheus-compatible)

```
Agent Runtime Metrics:
  aai_run_total{tenant, agent, status}                    Counter
  aai_run_duration_ms{tenant, agent}                      Histogram (p50/p90/p99)
  aai_run_concurrent{tenant, agent}                       Gauge
  aai_steps_per_run{agent}                                Histogram

LLM Metrics:
  aai_llm_calls_total{provider, model, cached}            Counter
  aai_llm_tokens_prompt{provider, model}                  Counter
  aai_llm_tokens_completion{provider, model}              Counter
  aai_llm_cost_usd{provider, model, tenant}               Counter
  aai_llm_latency_ms{provider, model}                     Histogram
  aai_llm_errors{provider, model, error_type}             Counter
  aai_llm_cache_hit_rate{provider, model}                 Gauge
  aai_llm_hallucination_score{agent}                      Histogram

Tool Metrics:
  aai_tool_calls_total{tool, status}                      Counter
  aai_tool_duration_ms{tool}                              Histogram
  aai_tool_errors{tool, error_type}                       Counter
  aai_tool_blocked{tool, reason}                          Counter

Security Metrics:
  aai_injection_detected{severity}                        Counter
  aai_pii_detected{type, action}                          Counter
  aai_secret_detected{type}                               Counter
  aai_authz_denied{resource, action}                      Counter

Quality Metrics:
  aai_hallucination_detected{agent, severity}             Counter
  aai_schema_validation_failed{agent}                     Counter
  aai_output_blocked{agent, reason}                       Counter
  aai_hitl_triggered{agent, reason}                       Counter
  aai_user_satisfaction_score{agent}                      Histogram  (from feedback)

Cost Metrics:
  aai_cost_usd_total{tenant, agent}                       Counter
  aai_budget_utilization{tenant, agent}                   Gauge
  aai_cost_savings_usd{type}                              Counter    (caching, routing)
  aai_budget_exceeded{tenant, agent}                      Counter
```

#### Structured Logging

```json
{
  "timestamp": "2026-06-19T10:23:45.123Z",
  "level": "INFO",
  "service": "agent-runtime",
  "trace_id": "abc123",
  "span_id": "def456",
  "run_id": "run_789",
  "tenant_id": "t_acme",
  "agent_id": "invoice-processor-v2",
  "user_id": "u_hashed_or_pseudonym",
  "event": "llm_call_complete",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet",
  "prompt_tokens": 1243,
  "completion_tokens": 389,
  "cost_usd": 0.0089,
  "latency_ms": 1234,
  "cached": false,
  "hallucination_score": 0.12,
  "pii_in_output": false,
  "step_id": "step_3",
  "step_name": "extract_line_items"
}
```

All logs: structured JSON, no PII in log fields (pseudonymized IDs only).

### 16.2 Dashboards

```
Operational Dashboard:
  - Run success rate (target: > 99%)
  - P99 run latency
  - Active concurrent runs
  - Error rate by type
  - Provider health (latency, error rate per provider)
  - Queue depth (pending runs)

Quality Dashboard:
  - Hallucination score distribution
  - Output validation failure rate
  - HITL trigger rate and approval time
  - User satisfaction scores
  - Schema violation rate

Security Dashboard:
  - Injection attempt rate (blocked + flagged)
  - PII detection events by type
  - Secret detection alerts
  - AuthZ denial rate
  - Anomalous access patterns

Cost Dashboard:
  - Real-time spend rate ($/hr)
  - Spend by tenant/agent/model
  - Cache savings
  - Budget utilization per tenant
  - Cost trend vs forecast
  - Top N most expensive runs today

Tenant Dashboard (self-service):
  - Their own runs, costs, quality metrics
  - No cross-tenant visibility
```

### 16.3 Alerting

```
Alert severity levels:
  P0 (page immediately):
    - Platform error rate > 5% (5-min window)
    - Security breach detected (secret exfiltration, injection success)
    - Platform cost > 150% of daily budget
    - Data residency violation

  P1 (alert in 15 min):
    - Provider down, no fallback available
    - Any tenant budget exceeded
    - Auth service degraded
    - Hallucination rate > 10% for any agent

  P2 (alert within 1 hour):
    - P99 latency > 30s
    - Cache hit rate drops > 20% from baseline
    - HITL queue > 50 pending approvals
    - Any single user consuming > 50% of tenant budget

  P3 (daily digest):
    - Quality metrics trend down
    - New PII patterns detected
    - Cost optimization opportunities
```

### 16.4 Agent-Specific Metrics (LLMOps)

Beyond generic infrastructure metrics:

```
Per-agent over rolling 7 days:
  - Task completion rate (did agent accomplish the goal?)
  - Average steps to completion
  - Tool call success rate per tool
  - Replanning frequency (how often did agent change plan mid-run?)
  - Average hallucination score
  - User-rated output quality (1-5)
  - Cost per successful completion
  - Time-to-first-token
  - Token efficiency (output quality per token spent)

Drift detection:
  - Compare current week metrics to baseline (first 2 weeks after deploy)
  - Alert if metrics drift > 2 standard deviations
  - Triggers automated canary rollback if quality metrics degrade
```

---

## 17. Layer 14 — Audit, Compliance & Explainability

### 17.1 Immutable Audit Trail

```
AuditEvent types:
  AGENT_RUN_STARTED, AGENT_RUN_COMPLETED, AGENT_RUN_FAILED
  LLM_CALL_MADE, LLM_CALL_CACHED
  TOOL_CALL_AUTHORIZED, TOOL_CALL_BLOCKED, TOOL_CALL_COMPLETED
  HUMAN_APPROVAL_REQUESTED, HUMAN_APPROVAL_GRANTED, HUMAN_APPROVAL_DENIED
  PII_DETECTED, PII_MASKED, PII_BLOCKED
  INJECTION_DETECTED, SECRET_DETECTED
  AUTHZ_GRANTED, AUTHZ_DENIED
  COST_THRESHOLD_EXCEEDED, BUDGET_EXCEEDED
  USER_DATA_ERASURE_REQUESTED, USER_DATA_ERASURE_COMPLETED
  CONFIG_CHANGED, PLUGIN_LOADED, PLUGIN_REMOVED
  ADMIN_ACTION

AuditEvent record:
  eventId:      UUID
  eventType:    AuditEventType
  timestamp:    ISO8601 (nanosecond precision)
  sequenceNum:  int64 (monotonic, per tenant)
  tenantId:     UUID
  principalId:  UUID (user or agent)
  runId:        UUID | null
  resourceType: string
  resourceId:   string
  action:       string
  outcome:      SUCCESS | FAILURE | BLOCKED
  details:      JSON (event-specific)
  hash:         SHA256(prev_hash + event_data)  // chain integrity
  signature:    RSA-sign(hash, audit_signing_key)

Storage:
  - Append-only (database insert only, no update/delete)
  - Replicated to 3 availability zones
  - Archived to object store (S3/GCS/Azure Blob) after 90 days
  - Integrity verified daily (hash chain check)
  - Legal hold: 7 years minimum
```

### 17.2 Explainability

For every completed agent run, users can request an explanation:

```
RunExplanation:
  runId:          UUID
  task:           string             // original user request
  plan:           PlanStep[]         // what the agent planned to do
  steps_taken:    StepExplanation[]  // what actually happened, in plain language
  tools_used:     ToolUsage[]        // which tools, why, what result
  sources_cited:  Citation[]         // which documents/URLs informed the answer
  alternatives_considered: string[] // other paths considered (if chain-of-thought logged)
  confidence:     float              // aggregate confidence score
  limitations:    string[]           // what the agent couldn't determine
  cost_breakdown: CostBreakdown      // how much each step cost

Generated by:
  - Raw step data from audit trail
  - Summarized by a fast model for human-readable narrative
  - Always grounded in actual audit events (not generated from scratch)
```

### 17.3 Policy Engine (Centralized)

```
Policy types:
  Content policies:    What output types are allowed/blocked
  Data policies:       How PII is handled, retention periods
  Access policies:     Who can do what (OPA Rego)
  Cost policies:       Spending limits and throttles
  Quality policies:    Hallucination thresholds, required citations
  Compliance policies: GDPR, HIPAA, PCI controls

Policy management:
  - Policies stored as versioned documents
  - Every change: git-style diff, reviewed and approved
  - Policy versions linked to audit records at time of event
  - Rollback: any prior policy version can be restored
  - Testing: policy can be tested in dry-run mode (evaluate but don't enforce)
  - Tenant override: tenants can make policies more restrictive, never less
```

---

## 18. Layer 15 — Data Pipelines & Feedback Loops

### 18.1 Continuous Learning Pipeline

```
Data sources → Processing → Model/Agent Improvement

Sources:
  1. Run outcomes (success/failure, user ratings)
  2. HITL decisions (what humans approved/rejected)
  3. Hallucination detections and corrections
  4. Tool call success rates
  5. Cost vs quality data

Processing:
  1. Daily job: extract all run data for past 24h
  2. Compute quality signals per run
  3. Label: (run_config, outcome) pairs
  4. Privacy: strip all PII, pseudonymize users
  5. Write to feature store

Outputs:
  a. Agent configuration optimization:
     - Recommend temperature adjustments
     - Identify underperforming tools
     - Suggest system prompt improvements

  b. Model routing optimization:
     - Update cost/quality model per provider
     - Tune routing thresholds

  c. RAG quality improvement:
     - Identify chunks that were retrieved but not used (low relevance)
     - Identify queries with low faithfulness (needs better chunking)
     - Feed into re-chunking/re-embedding jobs

  d. Hallucination pattern library:
     - Build corpus of known hallucination patterns
     - Improve detection classifier
```

### 18.2 Human Feedback Collection

```
Feedback channels:
  1. Explicit: thumbs up/down, 1-5 rating, free text comment
  2. Implicit: run re-submitted immediately (dissatisfied), 
               downstream action taken (satisfied)
  3. HITL decisions: approval/rejection of agent actions

Feedback storage:
  feedbackId:   UUID
  runId:        UUID
  stepId:       UUID | null
  userId:       UUID
  channel:      EXPLICIT | IMPLICIT | HITL
  score:        int | null      // 1-5
  sentiment:    POSITIVE | NEGATIVE | NEUTRAL
  comment:      string | null   // PII scrubbed
  timestamp:    ISO8601

Feedback loop:
  - Aggregate weekly
  - Identify agents with consistently low scores
  - Trigger review workflow for those agents
  - A/B test proposed improvements vs control
```

### 18.3 Drift Detection Pipeline

```
Daily comparison: current metrics vs baseline (30-day rolling average)

Monitored signals:
  - Task completion rate
  - Average hallucination score
  - User satisfaction score
  - Tool call success rate
  - Cost per successful completion

Drift triggers:
  - Statistical: > 2 SD from baseline, or > 15% relative change
  - Trend: consistent downward trend over 5 days

On drift detected:
  1. Alert agent owner + platform team
  2. Investigate: was there a model update? Data shift? New user population?
  3. Options: rollback agent version, retune config, update RAG knowledge base
  4. Track remediation in incident record
```

---

## 19. Layer 16 — Infrastructure & Deployment

### 19.1 Container & Orchestration

```
Container strategy:
  - All services containerized (Docker)
  - Base images: distroless or minimal (no shell in production)
  - Image scanning: CVE scan on every build (block if critical CVE)
  - Non-root user inside all containers
  - Read-only root filesystem
  - Resource limits mandatory (CPU + memory)

Kubernetes (or equivalent):
  - Namespaces: one per service, one per tenant tier
  - NetworkPolicy: deny-all + explicit allow rules
  - PodSecurityPolicy: restricted profile
  - Pod identity: Workload Identity (not static secrets in env)
  - Horizontal Pod Autoscaler on all stateless services
  - PodDisruptionBudget: minimum 2 pods for all critical services

Agent execution:
  - Each agent run: ephemeral pod (or serverless function)
  - Launched on demand, destroyed after run
  - No shared state between runs at pod level
  - Resource limits scoped to agent definition
  - Run pod: network policy prevents pod-to-pod communication
```

### 19.2 Service Decomposition

```
Core services (independently deployable):

  api-gateway          → Nginx/Kong/Envoy (stateless, scale horizontally)
  auth-service         → AuthN/AuthZ, token validation
  agent-runner         → Agent lifecycle, step execution (stateless)
  orchestrator         → Multi-agent DAG execution
  llm-proxy            → LLM abstraction, routing, caching
  tool-executor        → Tool dispatch, sandbox management
  memory-service       → Memory read/write, context packing
  rag-service          → Retrieval, ingestion
  security-guard       → Injection detection, content policy
  pii-service          → PII detection, masking
  hallucination-check  → Quality scoring
  cost-service         → Ledger, budget enforcement
  audit-service        → Immutable event recording
  policy-engine        → OPA-based policy decisions
  notification-service → HITL, alerts, webhooks
  config-service       → Centralized config, feature flags
  telemetry-collector  → OTEL collector (sidecar pattern)
```

### 19.3 Deployment Pipeline (CI/CD)

```
Every commit:
  1. Unit tests + integration tests
  2. Security scan: SAST, dependency CVE, secret scan
  3. Container build + CVE scan
  4. Contract tests (API compatibility)

Every merge to main:
  5. Build production image
  6. Deploy to staging
  7. Run end-to-end tests (including quality tests)
  8. Run load tests (< 30 min)
  9. Run chaos tests (random service kill)
  10. Security integration test (injection attack suite)

Production deploy (blue/green):
  11. Deploy new version as "green" (0% traffic)
  12. Smoke test green
  13. Canary: shift 1% → 5% → 20% → 50% → 100% (10 min between steps)
  14. Auto-rollback triggers:
      - Error rate > 2x baseline
      - P99 latency > 150% baseline
      - Hallucination score > 20% above baseline
  15. Full rollout if all metrics healthy

Agent version rollout (separate pipeline):
  - Agent definitions versioned independently of service code
  - A/B routing per agent version
  - Quality gate: new version must match or beat prior version on quality metrics
  - Gradual rollout with auto-rollback
```

### 19.4 High Availability

```
RPO (Recovery Point Objective): 1 minute (streaming replication)
RTO (Recovery Time Objective): < 5 minutes (automated failover)

Strategies:
  - Multi-AZ deployment for all stateful services
  - Active-active for stateless services
  - Active-passive with automatic failover for databases
  - Global load balancing across regions (for global tenants)
  - Circuit breakers: auto-open on provider failure (retry elsewhere)
  - Graceful degradation: if RAG fails, agent runs without RAG context (logged)
  - Queue-based decoupling: agents enqueue runs, runner processes when able
```

### 19.5 Disaster Recovery

```
Backup strategy:
  - Databases: continuous streaming replication + daily snapshots
  - Vector stores: daily exports to object store
  - Audit logs: real-time replication to secondary region
  - Configs: GitOps (git IS the backup)

Recovery procedures (automated, not manual):
  - Database failover: automatic (Patroni or cloud-native)
  - Service recovery: K8s self-heals via pod restart
  - Data recovery: automated restore from last snapshot
  - Full region failure: activate secondary region (RTO: 15 min)

DR test: quarterly full DR drill (automated, uses shadow environment)
```

---

## 20. Layer 17 — Multi-Tenancy & White-Labeling

### 20.1 Tenant Isolation Model

```
Data isolation:
  - Database: row-level tenant_id filter (RLS enforced at DB level)
  - Vector store: separate namespace per tenant
  - Cache: key prefix with tenant_id
  - Audit logs: partitioned by tenant_id
  - Object store: separate bucket or prefix per tenant
  - No data ever returned without tenant_id filter applied

Compute isolation tiers:
  SHARED (default):
    - Shared compute pool, per-tenant rate limits enforced via Redis token bucket
    - Tenant data isolated at application layer: every query carries tenant_id, DB RLS enforces it
    - Pods are shared; data is not — a pod processes one request at a time with request-scoped context
    - No cross-tenant data leakage risk: connection-level DB variable (SET app.tenant_id) reset per request
    - Cost-efficient, appropriate for SMB tenants; noisy-neighbor risk mitigated by rate limits

  DEDICATED (premium):
    - Dedicated agent runner pool
    - Reserved capacity, guaranteed SLA
    - No noisy neighbor issues

  ISOLATED (enterprise):
    - Separate Kubernetes namespace
    - Dedicated database instances
    - VPC peering / private link
    - Custom data residency

Network isolation:
  - API gateway enforces tenant_id from auth token (cannot be spoofed)
  - Internal services: tenant_id carried in every request header
  - NetworkPolicy: pods cannot communicate across tenant namespaces
```

### 20.2 White-Labeling

```
Brand customization per tenant (stored in tenant config):

  Visual:
    logo_url:           CDN URL for tenant logo
    primary_color:      hex color
    secondary_color:    hex color
    font_family:        web-safe font name
    favicon_url:        CDN URL

  Text:
    product_name:       "AcmeCorp AI Assistant"
    company_name:       "AcmeCorp"
    support_email:      "ai-support@acme.com"
    terms_url:          URL to tenant's terms
    privacy_url:        URL to tenant's privacy policy

  Domain:
    custom_domain:      "ai.acme.com" (CNAME to platform)
    api_base_url:       "api.ai.acme.com"
    ssl_cert:           auto-provisioned via Let's Encrypt / ACME protocol

  Agent personas:
    agent_name:         "Alex"  (instead of platform default)
    agent_avatar_url:   CDN URL
    greeting_message:   custom

  LLM provider override (BYOLLM):
    - Enterprise tenants can bring their own LLM API keys
    - Keys stored encrypted in Vault under tenant's namespace, wrapped with tenant's KMS key (AWS CMK / Azure Key Vault / GCP CMEK)
    - Platform never logs the raw key; only the Vault secret path is stored in the DB
    - At runtime, LLM proxy fetches the key from Vault, uses it in memory, and discards it after the response
    - BYOLLM cost does not appear in platform billing (tenant billed directly by the provider)

Platform attribution:
    hide_platform_branding: true  (available on enterprise plan)
    no_platform_watermark:  true
```

### 20.3 Tenant Onboarding

```
Automated onboarding flow:
  1. Create tenant record (UUID generated)
  2. Provision isolated namespaces (DB schema, vector namespace, cache prefix)
  3. Generate initial admin API key (rotated after first login)
  4. Apply default policies (can be customized post-onboarding)
  5. Set up tenant-level budget (from plan)
  6. Configure data residency (from plan + tenant selection)
  7. Provision white-label config (if applicable)
  8. Send welcome email with onboarding guide
  9. Create audit record: TENANT_PROVISIONED

Onboarding time: < 60 seconds (fully automated)
```

---

## 21. Layer 18 — Developer Experience & SDK

### 21.1 SDK Design (vendor-neutral client)

```typescript
// TypeScript SDK (also available: Python, Go, Java, .NET)

import { AgentClient } from "@agentic-platform/sdk";

const client = new AgentClient({
  baseUrl:  process.env.AGENT_API_URL,
  apiKey:   process.env.AGENT_API_KEY,
  tenantId: process.env.TENANT_ID,
});

// Run an agent
const run = await client.agents.run("invoice-processor-v2", {
  input: { file: "path/to/invoice.pdf" },
  budget: { maxCostUsd: 0.25 },
  stream: true,
});

// Stream events
for await (const event of run.events()) {
  switch (event.type) {
    case "step_complete":
      console.log("Step done:", event.step.name, event.step.output);
      break;
    case "tool_call":
      console.log("Tool called:", event.tool.id, event.tool.input);
      break;
    case "hitl_required":
      const decision = await askUser(event.approval_request);
      await run.approve(event.approval_id, decision);
      break;
    case "done":
      console.log("Result:", event.output);
      break;
  }
}

// Explain a run
const explanation = await client.runs.explain(run.runId);

// Feedback
await client.runs.feedback(run.runId, { score: 5, comment: "Perfect" });
```

### 21.2 Admin API

```
Agent Management:
  POST   /v1/agents                    Create agent definition
  GET    /v1/agents/{id}               Get agent definition
  PUT    /v1/agents/{id}               Update agent definition (new version)
  DELETE /v1/agents/{id}               Deprecate agent
  GET    /v1/agents/{id}/versions      List versions
  POST   /v1/agents/{id}/deploy        Deploy specific version with rollout config

Run Management:
  POST   /v1/runs                      Start a run
  GET    /v1/runs/{id}                 Get run status
  GET    /v1/runs/{id}/events          Stream run events
  POST   /v1/runs/{id}/cancel          Cancel a run
  GET    /v1/runs/{id}/explain         Get explanation
  POST   /v1/runs/{id}/feedback        Submit feedback
  GET    /v1/runs/{id}/cost            Get cost breakdown

Tool Management:
  POST   /v1/tools                     Register a tool
  GET    /v1/tools/{id}                Get tool definition
  PUT    /v1/tools/{id}                Update tool definition
  GET    /v1/tools                     List available tools

Knowledge Base:
  POST   /v1/kb                        Create knowledge base
  POST   /v1/kb/{id}/ingest            Ingest documents
  GET    /v1/kb/{id}/status            Ingestion status
  DELETE /v1/kb/{id}/documents/{docId} Delete document

Observability:
  GET    /v1/metrics                   Prometheus metrics endpoint
  GET    /v1/runs?from=&to=&status=    Query runs
  GET    /v1/audit?from=&to=           Query audit log

Cost & Budget:
  GET    /v1/cost/summary              Cost summary
  GET    /v1/cost/runs                 Cost per run
  PUT    /v1/budget                    Update budget config
  GET    /v1/budget/status             Current budget utilization

Compliance:
  POST   /v1/privacy/erasure           Submit erasure request
  GET    /v1/privacy/erasure/{id}      Check erasure status
  GET    /v1/audit/export              Export audit log (GDPR/SOC2)
```

### 21.3 Webhook Events

```
Webhook delivery:
  - HMAC-SHA256 signature header: X-Agentic-Signature
  - Retry on failure: 5 attempts (1s, 5s, 30s, 5m, 30m)
  - Dead letter: failed deliveries logged, available for replay

Event types:
  run.started, run.step_complete, run.tool_called,
  run.hitl_required, run.complete, run.failed,
  cost.threshold_reached, cost.budget_exceeded,
  security.injection_detected, security.pii_detected,
  agent.deployed, agent.rollback
```

### 21.4 Local Development

```
Local dev setup:
  1. docker compose up   → starts all platform services locally
  2. npm run dev         → starts local hot-reload agent runner
  3. Platform configured for:
     - Fake auth (no actual auth check in dev mode)
     - Local Ollama as LLM backend (zero API cost)
     - Local Qdrant as vector store
     - Local Redis for cache
     - SQLite for audit log

Dev features:
  - Agent debugger: step-through execution with state inspection
  - Prompt playground: test prompts without full run overhead
  - Tool mock: mock tool responses for deterministic tests
  - Cost estimator: estimate cost before running
  - Injection tester: run injection attack suite against your agent

Testing utilities:
  - AgentTestHarness: set up isolated agent with mock tools
  - run scenarios against test inputs
  - Assert on output schema, cost, steps taken, tools called
  - Golden test: compare output against stored expected output
```

---

## 22. Cross-Cutting Concerns

### 22.0 Scale Targets

The architecture is designed to meet these targets. All design decisions must be validated against them.

```
Tier              Metric                      Target
──────────────────────────────────────────────────────────────────────
Throughput        Agent run starts/sec         500 rps (peak)
                  LLM calls/sec (proxied)      2,000 rps
                  Tool executions/sec          5,000 rps
                  Ingest documents/day         1,000,000

Concurrency       Simultaneous agent runs      10,000
                  Concurrent HITL waits        50,000
                  Active WebSocket connections  100,000

Latency (p99)     Auth check                  < 10ms
                  Time-to-first-token (TTFT)  < 2s (real-time agents)
                  Full run (simple, no tools) < 5s
                  Full run (with tools, RAG)  < 30s

Storage           Tenants                     10,000
                  Agents per tenant           1,000
                  Documents in knowledge base 100,000,000 chunks
                  Audit events/day            500,000,000

Reliability       Platform availability       99.9% (three 9s)
                  Data durability             99.999999999% (eleven 9s)
                  RPO                         1 minute
                  RTO                         5 minutes
```

### 22.1 Database Schema (Core Tables)

```sql
-- ── TENANTS ─────────────────────────────────────────────────────────
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_version  INT NOT NULL DEFAULT 1,
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,         -- used in API key prefix
    plan            TEXT NOT NULL DEFAULT 'free', -- free | pro | enterprise
    status          TEXT NOT NULL DEFAULT 'active',
    data_residency  TEXT[] NOT NULL DEFAULT '{"us"}',
    config          JSONB NOT NULL DEFAULT '{}',  -- white-label, feature flags
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── API KEYS ────────────────────────────────────────────────────────
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    key_hash        TEXT NOT NULL UNIQUE,          -- HMAC-SHA256, hex-encoded
    key_prefix      TEXT NOT NULL,                 -- first 8 chars, for display
    name            TEXT NOT NULL,
    scopes          TEXT[] NOT NULL DEFAULT '{}',
    ip_allowlist    CIDR[] NOT NULL DEFAULT '{}',
    rate_limit      JSONB NOT NULL DEFAULT '{}',
    expires_at      TIMESTAMPTZ,
    last_used_at    TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id) WHERE revoked_at IS NULL;

-- ── AGENTS ──────────────────────────────────────────────────────────
CREATE TABLE agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    agent_ref       TEXT NOT NULL,                 -- human-readable id
    version         TEXT NOT NULL,                 -- semver
    status          TEXT NOT NULL DEFAULT 'draft', -- draft | deployed | deprecated
    definition      JSONB NOT NULL,                -- full agent.yaml as JSON
    deployed_at     TIMESTAMPTZ,
    created_by      UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, agent_ref, version)
);
CREATE INDEX idx_agents_tenant_ref ON agents(tenant_id, agent_ref) WHERE status='deployed';

-- ── AGENT RUNS ──────────────────────────────────────────────────────
CREATE TABLE agent_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_version  INT NOT NULL DEFAULT 1,
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    agent_id        UUID NOT NULL REFERENCES agents(id),
    user_id         UUID NOT NULL,
    session_id      UUID,
    workflow_run_id UUID,                          -- set if part of multi-agent DAG
    parent_run_id   UUID REFERENCES agent_runs(id),
    status          TEXT NOT NULL DEFAULT 'pending',
    input           JSONB NOT NULL,
    output          JSONB,
    error           JSONB,
    plan            JSONB,
    budget_config   JSONB NOT NULL,
    tokens_used     INT NOT NULL DEFAULT 0,
    cost_usd        DECIMAL(12,8) NOT NULL DEFAULT 0,
    trace_id        TEXT NOT NULL,                 -- OTEL root trace
    idempotency_key TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(idempotency_key) WHERE idempotency_key IS NOT NULL
);
CREATE INDEX idx_runs_tenant_status ON agent_runs(tenant_id, status, created_at DESC);
CREATE INDEX idx_runs_user ON agent_runs(user_id, created_at DESC);
CREATE INDEX idx_runs_trace ON agent_runs(trace_id);

-- ── RUN STEPS ───────────────────────────────────────────────────────
CREATE TABLE run_steps (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL REFERENCES agent_runs(id),
    step_index      INT NOT NULL,
    step_type       TEXT NOT NULL,                 -- llm_call | tool_call | hitl_wait
    step_name       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    input           JSONB NOT NULL DEFAULT '{}',
    output          JSONB,
    error           JSONB,
    tokens_used     INT,
    cost_usd        DECIMAL(12,8),
    latency_ms      INT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    UNIQUE(run_id, step_index)
);
CREATE INDEX idx_steps_run ON run_steps(run_id, step_index);

-- ── COST LEDGER ─────────────────────────────────────────────────────
CREATE TABLE cost_ledger (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    run_id          UUID NOT NULL REFERENCES agent_runs(id),
    step_id         UUID REFERENCES run_steps(id),
    provider        TEXT NOT NULL,
    model           TEXT NOT NULL,
    prompt_tokens   INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    cached_tokens   INT NOT NULL DEFAULT 0,
    cost_usd        DECIMAL(12,8) NOT NULL,
    cached          BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (recorded_at);           -- monthly partitions

-- ── AUDIT LOG (append-only) ─────────────────────────────────────────
CREATE TABLE audit_events (
    id              UUID DEFAULT gen_random_uuid(),
    seq_num         BIGINT GENERATED ALWAYS AS IDENTITY,  -- monotonic per tenant
    tenant_id       UUID NOT NULL,
    event_type      TEXT NOT NULL,
    principal_id    UUID,
    run_id          UUID,
    resource_type   TEXT,
    resource_id     TEXT,
    action          TEXT,
    outcome         TEXT NOT NULL,             -- SUCCESS | FAILURE | BLOCKED
    details         JSONB NOT NULL DEFAULT '{}',
    event_hash      TEXT NOT NULL,             -- SHA256(prev_hash + event_data)
    signature       TEXT NOT NULL,             -- RSA signature of event_hash
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, seq_num)
) PARTITION BY RANGE (occurred_at);

-- Revoke DELETE and UPDATE on audit_events from application user
-- Only audit_service_user has INSERT permission
REVOKE UPDATE, DELETE ON audit_events FROM app_user;

-- ── MEMORY ──────────────────────────────────────────────────────────
CREATE TABLE episodic_memory (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    user_id         UUID NOT NULL,
    agent_id        UUID NOT NULL REFERENCES agents(id),
    run_id          UUID,
    content         TEXT NOT NULL,             -- PII-scrubbed summary
    embedding_id    TEXT,                      -- reference to vector in Qdrant
    pii_level       TEXT NOT NULL DEFAULT 'LOW',
    relevance_score FLOAT,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_memory_user_agent ON episodic_memory(tenant_id, user_id, agent_id)
    WHERE expires_at > NOW();

-- ── HITL APPROVALS ──────────────────────────────────────────────────
CREATE TABLE hitl_approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id          UUID NOT NULL REFERENCES agent_runs(id),
    step_id         UUID NOT NULL REFERENCES run_steps(id),
    request         JSONB NOT NULL,            -- what the agent wants to do
    status          TEXT NOT NULL DEFAULT 'pending',
    decision        TEXT,                      -- approved | rejected
    reason          TEXT,
    approver_id     UUID,
    token           TEXT NOT NULL UNIQUE,      -- secure token for approval link
    expires_at      TIMESTAMPTZ NOT NULL,
    decided_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 22.2 Service Discovery & Internal Networking

All internal service-to-service calls use Kubernetes DNS. No service registry needed — K8s DNS is the registry.

```
Naming convention:
  http://{service-name}.{namespace}.svc.cluster.local:{port}

Internal URLs:
  http://llm-proxy.platform.svc.cluster.local:8000
  http://rag-service.platform.svc.cluster.local:8000
  http://pii-service.platform.svc.cluster.local:8000
  http://memory-service.platform.svc.cluster.local:8000
  http://cost-service.platform.svc.cluster.local:8000
  http://audit-service.platform.svc.cluster.local:8000
  http://auth-service.platform.svc.cluster.local:8000
  http://tool-executor.platform.svc.cluster.local:8000
  http://security-guard.platform.svc.cluster.local:8000

Service-to-service auth: mTLS via Linkerd (automatic, zero config in app code)
Service-to-service identity: Kubernetes ServiceAccount + SPIFFE/SPIRE
```

### 22.3 Distributed Locking

Required in these specific scenarios:

```
Scenario 1 — Idempotency key (prevent duplicate runs):
  Lock key:    lock:idempotency:{idempotency_key}
  TTL:         30s
  Pattern:     SET NX PX 30000 → only one request wins
               Loser gets 409 Conflict immediately

Scenario 2 — Tenant budget check (prevent concurrent overspend):
  Handled by Redis atomic INCR (Lua script) — no explicit lock needed
  See Section 8.4

Scenario 3 — DAG node execution (prevent duplicate execution):
  Lock key:    lock:dag:{workflow_run_id}:{node_id}
  TTL:         node.timeout_seconds * 2
  Pattern:     Acquire before executing, release on completion

Scenario 4 — Agent definition deploy (prevent concurrent deploys):
  Lock key:    lock:deploy:{tenant_id}:{agent_ref}
  TTL:         60s
  Pattern:     Acquire before deploy, release on completion or error

All locks:
  Implementation: Redis SET key value NX PX {ttl_ms}
  Lock value: unique token (UUID) — only holder can release
  Release: Lua script: if GET key == token then DEL key end
  Watchdog: locks renewed every TTL/3 for long-running operations
  No Redlock: single Redis node is sufficient (we already HA Redis)
```

### 22.4 Dead Letter Queue Strategy

Every queue consumer has a DLQ for messages that cannot be processed.

```
Per-topic DLQ configuration:

Topic: aai.runs (agent run dispatch)
  Max retries:    3 (1s, 5s, 30s backoff)
  DLQ topic:      aai.runs.dlq
  DLQ action:     Alert ops, mark run FAILED in DB, notify user
  Manual replay:  Admin API: POST /v1/admin/dlq/runs/{messageId}/replay

Topic: aai.audit-events
  Max retries:    10 (exponential, up to 10 min)
  DLQ topic:      aai.audit.dlq
  DLQ action:     P0 alert — audit integrity at risk. Buffer locally.
  Auto-replay:    YES — replay automatically when audit service recovers
  NEVER DROP:     Audit events must not be lost. Buffer in Redis if DLQ also fails.

Topic: aai.cost-ledger
  Max retries:    5
  DLQ topic:      aai.cost.dlq
  DLQ action:     Alert ops, best-effort reconciliation from run records
  Manual replay:  YES — replay when cost service recovers

Topic: aai.notifications (HITL, webhooks)
  Max retries:    5 (webhook: 5 attempts per delivery, separate from queue retries)
  DLQ topic:      aai.notifications.dlq
  DLQ action:     Alert tenant, mark delivery FAILED, available for manual replay

DLQ monitoring:
  Alert: DLQ depth > 0 for aai.audit.dlq → P0
  Alert: DLQ depth > 100 for any other topic → P1
  Dashboard: DLQ depth per topic (real-time)
```

### 22.5 Graceful Shutdown

Every service handles SIGTERM before Kubernetes pod termination.

```
Graceful shutdown sequence (all services):

1. SIGTERM received → set service health to DRAINING (K8s removes from load balancer)
2. Stop accepting new connections / requests
3. Set readiness probe to UNHEALTHY (K8s stops routing new traffic)
4. Wait for in-flight requests to complete (drain timeout: 30s)
5. Close all outbound connections (DB pool, Redis, NATS)
6. Flush OTEL spans and metrics
7. Release any distributed locks held
8. Log: "Service shutdown complete"
9. Exit 0

Kubernetes PreStop hook:
  lifecycle:
    preStop:
      exec:
        command: ["sleep", "5"]   # give K8s 5s to remove from endpoints

Termination grace period: 60s (must be > drain timeout + preStop sleep)

Agent runner additional steps (between steps 3 and 4):
  - Stop accepting new run assignments from queue
  - Mark all in-progress run steps as INTERRUPTED
  - Write checkpoint for each in-progress run
  - Runs auto-resume when new runner pod picks them up from queue

Run resumption after crash (non-graceful):
  - Watchdog job runs every 30s: finds runs RUNNING > 5min with no heartbeat
  - Marks those runs as INTERRUPTED
  - Re-queues them for pickup by available runner
  - Runner loads last checkpoint and continues from last completed step
```

### 22.6 Database Connection Pooling (PgBouncer)

Required to prevent connection exhaustion across 18 services, each with their own pool.

```
Problem:
  18 services × 3 pods each × 10 connections per pool
  = 540 connections minimum at rest
  PostgreSQL max_connections typically 200-400
  → Exceeds limit → connection errors under normal operation

Solution: PgBouncer as connection pooler

Deployment: PgBouncer as a sidecar to PostgreSQL (or dedicated service)

Configuration:
  pool_mode:           transaction     # best for microservices (connection released after each txn)
  max_client_conn:     5000            # connections from all services
  default_pool_size:   20             # connections to actual PostgreSQL per DB user
  min_pool_size:       5
  reserve_pool_size:   10
  max_db_connections:  200            # hard cap to PostgreSQL

Service connection config (each service):
  pool_size: 5          # reduced from 10 since PgBouncer multiplexes
  max_overflow: 10
  connect to: pgbouncer:5432 (not postgres:5432 directly)
```

### 22.7 API Versioning & Pagination

```
Versioning:
  All public APIs: /v1/ prefix
  Breaking change (field removal, type change, semantic change): new /v2/ prefix
  Non-breaking change (field addition, new endpoint): same version
  Deprecation notice: 6 months before removing old version
  Both versions run simultaneously during transition period
  Deprecation header on old version: Deprecation: true, Sunset: {date}

Cursor-based pagination (all list endpoints):
  Request:  GET /v1/runs?limit=50&cursor=eyJpZCI6IjEyMyJ9
  Response: {
    "data": [...],
    "pagination": {
      "cursor":      "eyJpZCI6IjQ1NiJ9",   // opaque, base64 encoded
      "has_more":    true,
      "total_count": null                   // omitted (expensive to compute)
    }
  }

  Cursor encodes: {id, created_at} of last item (stable sort key)
  Default limit: 20, max limit: 100
  Applied to: /v1/runs, /v1/audit, /v1/tools, /v1/agents, /v1/kb/{id}/documents

Rate limit response headers (all 429 responses):
  X-RateLimit-Limit:      60          # limit for this tier
  X-RateLimit-Remaining:  0           # requests remaining in window
  X-RateLimit-Reset:      1719000000  # unix timestamp when window resets
  Retry-After:            30          # seconds until retry is safe

CORS (configurable per tenant for white-labeled deployments):
  Default allowed origins: [tenant.custom_domain, platform.domain]
  Tenant override: CORS_ALLOWED_ORIGINS in tenant config
  Preflight cache: Access-Control-Max-Age: 86400
```

### 22.8 Health Check Contract (per service)

Every service exposes two distinct probes. K8s treats them differently: failing liveness → pod restart; failing readiness → pod removed from LB without restart.

```
Liveness Probe (GET /internal/health/live):
  Purpose:  "Is this process alive and not deadlocked?"
  Checks:   - Event loop / thread pool is responsive (timeout < 1s)
            - No internal deadlock detected
  Does NOT check: database, Redis, external dependencies
  Response: 200 {"status":"alive"} or 503 {"status":"deadlocked"}
  Failure:  kubelet kills pod; restartPolicy applies
  Timeout:  2s | Failure threshold: 3 | Period: 10s | Initial delay: 5s

Readiness Probe (GET /internal/health/ready):
  Purpose:  "Can this pod safely receive traffic?"
  Checks:   Service-specific dependency checklist:

  ┌─────────────────────┬──────────────────────────────────────────┐
  │  Service            │  Readiness Dependencies                  │
  ├─────────────────────┼──────────────────────────────────────────┤
  │  agent-api          │  PostgreSQL ping, Redis ping, Vault reachable │
  │  orchestrator       │  NATS connected, Redis ping              │
  │  llm-proxy          │  ≥1 upstream provider healthy (circuit CLOSED/HALF-OPEN) │
  │  tool-executor      │  gVisor runtime available, tool registry reachable │
  │  memory-service     │  PostgreSQL ping, vector store ping      │
  │  auth-service       │  PostgreSQL ping, JWKS endpoint reachable │
  │  cost-service       │  PostgreSQL ping, Redis ping             │
  │  pii-service        │  Presidio analyzer loaded (model warm)   │
  └─────────────────────┴──────────────────────────────────────────┘

  Response:
    200 {"status":"ready", "checks": {"postgres":"ok", "redis":"ok", "vault":"ok"}}
    503 {"status":"not_ready", "checks": {"postgres":"ok", "redis":"timeout"}}
  Timeout:  3s | Failure threshold: 2 | Period: 15s | Initial delay: 10s

Startup Probe (overrides liveness during slow startup):
  GET /internal/health/live
  Timeout: 5s | Failure threshold: 30 | Period: 5s
  Purpose: Give time-consuming startup (e.g., Presidio model load) up to 150s before liveness kicks in

Metrics endpoint (always on, separate port):
  GET :9090/metrics  → Prometheus text format
  Not behind auth; NetworkPolicy restricts access to monitoring namespace only
```

### 22.9 Testing Strategy

```
Unit Tests (per service, run on every commit):
  Framework:    pytest (Python) / Vitest (TypeScript)
  Target:       > 80% line coverage on business logic
  Speed:        < 30s full suite per service
  Mocking:      All external adapters mocked (no real DB/Redis/LLM in unit tests)
  Key areas:    State machine transitions, budget enforcement, PII detection,
                injection pattern matching, schema validation

Integration Tests (per service, run on PR):
  Framework:    pytest with testcontainers (spins up real Postgres, Redis, NATS)
  Target:       All adapter implementations (Qdrant, pgvector, NATS, Redis)
  LLM calls:    Use Ollama with a tiny model (llama3.2:1b) — real call, low cost
  Speed:        < 5 min per service

Contract Tests (cross-service, run on PR):
  Framework:    Pact (consumer-driven contract testing)
  Purpose:      Prevent llm-proxy API changes from breaking agent-runner silently
  Coverage:     Every service-to-service API call has a contract test
  Enforcement:  PR blocked if contract test fails

End-to-End Tests (full stack, run on merge to main):
  Environment:  Dedicated test environment (all services running)
  Scenarios:    10 golden-path scenarios covering all major flows
  LLM:          Ollama (real, deterministic with seed)
  Speed:        < 20 min

Security Tests (run weekly + on security-related PRs):
  Injection suite:   100+ known injection payloads tested against security-guard
  PII test vectors:  Synthetic PII in 10 languages tested through full pipeline
  Auth bypass:       Known JWT attack patterns, API key brute force simulation
  SSRF:              SSRF payloads against http_request tool
  Tool:              OWASP ZAP (automated) + manual review quarterly

Load Tests (run on merge to main, non-blocking):
  Tool:         k6 or Locust
  Scenarios:    Ramp to 500 rps over 10 min, hold 5 min, ramp down
  Pass criteria: p99 < 2s at 500 rps, error rate < 0.1%
  Frequency:    Every merge to main (non-blocking), daily in staging

Performance Benchmarks (tracked over time):
  p50/p99 latency per endpoint
  Token throughput (tokens/sec through llm-proxy)
  Memory usage per service at load
  Alert if any benchmark regresses > 20% vs prior week
```

### 22.10 Feature Flags

```
Feature flags govern:
  - New capabilities (before full rollout)
  - A/B tests on agent behavior
  - Emergency kill switches (disable a feature in seconds)
  - Tenant-specific enables (beta access)

Flag types:
  Boolean:       on/off
  Percentage:    e.g., 10% of runs get new model router
  Tenant-list:   only enabled for specific tenants
  User-list:     only enabled for specific users

Evaluation:
  - Evaluated per-request (not cached, for consistency)
  - Available as context variable in all plugin hooks
  - Changes take effect within 30 seconds (no deploy needed)
```

### 22.11 Configuration Management

```
Config precedence (highest to lowest):
  1. Run-level override (passed in API request)
  2. Agent definition config
  3. Tenant-level config
  4. Platform defaults

Config hot reload:
  - Most config reloaded without restart
  - Exceptions: network bindings, TLS certs (require restart)
  - Config change generates AUDIT event

Secrets never in config files:
  - Config references secret paths (e.g., "vault://secret/llm/openai-key")
  - Secret store resolves at runtime
  - Secrets cached in memory for 5 min (reduce secret store load)
```

### 22.12 Error Handling Philosophy

```
Every error:
  1. Has a unique error code (e.g., AAI-4001: BUDGET_EXCEEDED)
  2. Is logged with full context (run_id, step_id, correlation_id)
  3. Is traced (OTEL span marked as error with attributes)
  4. Never exposes internal stack traces to external callers
  5. Returns structured JSON error response
  6. Is classified: TRANSIENT (retry) vs PERMANENT (don't retry)

Error response format:
  {
    "error": {
      "code":       "AAI-4001",
      "type":       "BUDGET_EXCEEDED",
      "message":    "Run exceeded maximum cost of $0.50",
      "requestId":  "req_abc123",
      "runId":      "run_xyz789",
      "retryable":  false,
      "details": {
        "budget_usd":  0.50,
        "consumed_usd": 0.52,
        "step":        "enrich_customer_data"
      }
    }
  }
```

### 22.13 Idempotency

```
All run-creating API calls support idempotency:
  Header: Idempotency-Key: <client-generated UUID>

Behavior:
  - First request: processed normally, result stored keyed by Idempotency-Key
  - Duplicate request (same key, within 24h): return stored result immediately
  - After 24h: key expired, new request treated as new

Critical for:
  - Webhook retry safety
  - Client retry on network failure
  - Mobile clients on flaky connections
```

---

## 23. Data Flow — End-to-End Trace

Tracing a single user request through the full system:

```
01. User submits: POST /v1/runs {agent:"invoice-processor", input:{file:"inv.pdf"}}

02. API GATEWAY:
    - TLS termination
    - Rate limit check (pass)
    - WAF scan (pass)
    - Inject X-Request-ID → becomes OTEL trace root
    - Route to auth-service

03. AUTH SERVICE:
    - Validate API key: compute HMAC-SHA256(key, server_secret), check Redis cache (60s TTL), fall back to DB lookup
    - Extract tenant_id, user_id, scopes from key record
    - Generate short-lived internal JWT (15 min, signed with internal key)
    - Return 200 + claims to gateway

04. SECURITY GUARD (pre-agent):
    - Scan input.file metadata for injection patterns
    - PII scan on any text fields in request body
    - Content policy check
    - All pass → forward to agent runtime

05. AGENT RUNTIME:
    - Validate agent exists and is deployed for this tenant
    - Check user has scope "agents:invoice-processor:run"
    - OPA policy evaluation: cost budget, PII authorization
    - Create AgentRun record (PENDING), write to DB
    - Emit run.started event
    - Enqueue run to runner pool

06. AGENT RUNNER picks up run:
    - Load agent definition (cache-first)
    - Initialize working memory
    - Load episodic memory: retrieve relevant past invoice runs for this user
    - Build plan:
        Step 1: extract text from PDF (tool: pdf_extract)
        Step 2: identify invoice fields (LLM call)
        Step 3: validate extracted data (tool: schema_validator)
        Step 4: enrich vendor info (tool: web_search, conditional)
        Step 5: generate structured output (LLM call)

07. STEP 1 — Tool: pdf_extract
    - AuthZ check: agent has "tools:pdf_extract" scope? Yes.
    - Risk level: LOW → no sandbox needed
    - Execute: extract text, table data, metadata from PDF
    - PII scan on output (found: vendor name, amount — PII-LOW, passthrough)
    - Write tool call audit record
    - Emit tool_call span

08. STEP 2 — LLM call: identify invoice fields
    - Build prompt:
        System: agent system prompt (with tenant name injected)
        Context: extracted PDF text (PII-masked: amounts pseudonymized for logging)
        User: "Identify all invoice fields from this document..."
    - Token count: 2,341 tokens
    - Budget check: 2,341 + 4,096 (max_response) < remaining 50,000 → pass
    - Cache lookup: SHA256(prompt) → MISS
    - Model router: task_complexity=MEDIUM, cost-aware → selects claude-3-5-haiku
    - LLM call to Anthropic API (via LLM proxy)
    - Response received: 847 tokens, latency: 1,240ms, cost: $0.0031
    - Schema validation: response matches InvoiceFields schema → pass
    - Hallucination check: faithfulness score 0.94 (well above threshold 0.7) → pass
    - PII scan on output → amounts detected (PII-LOW, passthrough)
    - Cache write (TTL: 1h)
    - Write LLM call audit record
    - Cost ledger: +$0.0031

09. STEP 3 — Tool: schema_validator
    (similar flow, omitted for brevity)

10. STEP 4 — Tool: web_search (conditional)
    - Condition: invoice.vendor_id NOT IN known_vendors
    - Condition evaluates true → step executes
    - AuthZ: scope "tools:web_search" → granted
    - Risk: MEDIUM → network_isolated sandbox
    - Input sanitization: query built from vendor name (sanitized, not raw user input)
    - Allowed domains: ["^.*\\.reuters\\.com$", "^.*\\.companies\\.gov\\.uk$"]
    - Execute in sandbox: outbound only to allowlisted domains
    - Result: vendor info retrieved
    - PII scan output: no PII → passthrough
    - Write audit record

11. STEP 5 — LLM call: generate structured output
    (similar to step 8, temperature 0.0 for determinism)
    - Output schema enforced: InvoiceOutput JSON Schema
    - Response validated against schema → pass
    - Citation check: all amounts traced to source PDF fields → pass
    - Hallucination score: 0.08 → pass
    - Final output assembled

12. AGENT RUNTIME — post-execution:
    - Summarize run for episodic memory (async, cheap model)
    - Update run record: DONE
    - Emit run.complete event
    - Final cost: $0.0089 (under $0.50 budget)

13. RESPONSE:
    - Output passes security guard (output scan: no secrets, no injected content)
    - PII in output: amounts (passthrough per policy)
    - Response returned to client
    - Streaming: events were pushed in real-time throughout steps 7-12

14. OBSERVABILITY (throughout):
    - Single root trace with all child spans
    - 23 metrics data points emitted
    - 8 structured log entries
    - 6 audit events written
    - Total run: 4.2 seconds, $0.0089

Total wall time: 4.2 seconds
Total cost: $0.0089
Audit events: 6 immutable records
Trace spans: 14 spans across 4 services
```

---

## 24. Failure Modes & Resilience Patterns

### 24.1 Provider Failures

| Scenario | Detection | Recovery |
|---|---|---|
| LLM provider returns 429 | Rate limit header | Queue + retry after Retry-After |
| LLM provider returns 5xx | HTTP status + timeout | Fallback to next provider in priority list |
| LLM provider network timeout | Socket timeout | Same as 5xx |
| All providers down | Circuit breaker open for all | Return graceful error to user, queue for retry |
| Provider quality degradation | Hallucination score spike | Route away from provider until quality recovers |

### 24.2 Circuit Breaker Configuration

```
Per provider circuit breaker:
  threshold:    5 failures in 60 seconds → open
  half-open:    1 probe request after 30s cool-down
  metrics:      error rate + p99 latency

States:
  CLOSED (normal): requests pass through
  OPEN (failing):  requests fail fast, fallback provider used
  HALF-OPEN:       single probe, close if succeeds, reopen if fails
```

### 24.3 Graceful Degradation

```
If RAG service fails:
  → Agent runs without retrieved context
  → Response flagged with "no_context_retrieval" in metadata
  → Hallucination score threshold tightened (compensate for no grounding)

If PII service fails:
  → BLOCK the request (fail safe, not fail open)
  → Alert operations team
  → Log incident

If cost service fails:
  → Use last known budget state (cached, max 60s old)
  → If cache also stale: apply conservative estimate (assume 80% budget consumed)
  → Alert operations team

If audit service fails:
  → Buffer audit events in local queue (Redis)
  → Retry until audit service recovers
  → Do NOT drop audit events (circuit breaker does not apply here)
  → Alert immediately if buffer fills past threshold

If auth service fails:
  → Serve from cache (JWT validation is local + cached public keys)
  → New key issuance blocked until auth service recovers
  → Alert immediately
```

### 24.4 Incident Response Runbooks

| Scenario | Detection | Immediate Action | Escalation |
|----------|-----------|-----------------|------------|
| All LLM providers down | Circuit breakers all OPEN; error rate 100% | Activate static fallback response; page on-call | P0 — notify all tenants within 15 min |
| Database primary down | Healthcheck failures; write errors | Promote replica to primary (automated PG Patroni failover < 30s) | P1 — monitor failover completion |
| Redis unavailable | Cache miss floods DB; budget enforcement degraded | Apply conservative budget (reject all runs > $0.10); alert ops | P1 — restore Redis or switch to in-memory fallback |
| Secret store unreachable | Service startup failures; 500s on secret refresh | Services use cached secrets (TTL: 60s); alert; prepare manual key rotation | P1 |
| NATS cluster down | Message queue backlogs; async tasks stalled | Drain in-flight HTTP requests; hold new runs; alert | P1 |
| Prompt injection attack (confirmed) | Injection detection alert spike | Rate-limit offending tenant to 0; quarantine affected runs | P1 — security team |
| Data breach suspected | Anomaly in audit log; cross-tenant query attempt | Isolate affected service; preserve evidence; page security lead | P0 — GDPR 72h clock starts |
| Cost anomaly (spend spike) | Cost anomaly alert threshold | Auto-throttle tenant; alert tenant admin | P2 |

Full P0/P1/P2/P3 runbooks with step-by-step forensics procedures are in `SECURITY_ARCHITECTURE.md` Section 9.

---

## 25. Implementation Roadmap

Phased implementation — each phase delivers working end-to-end value:

### Phase 1 — Foundation (Weeks 1-4)
- Layer 0: Core abstractions, plugin interfaces, type system
- Layer 1: API Gateway (basic rate limiting, TLS)
- Layer 2: Authentication (API keys, JWT)
- Layer 3: Agent Runtime (state machine, basic step executor)
- Layer 5: LLM Abstraction (2-3 provider adapters)
- Layer 13: Basic observability (traces, metrics, structured logs)
- **Deliverable**: Single-agent, single-provider runs with full observability

### Phase 2 — Security & Quality (Weeks 5-8)
- Layer 2: Full Authorization (RBAC, OPA policies)
- Layer 6: Tool Registry (core tools + sandboxed execution)
- Layer 9: Security Guard (injection detection, output sanitization)
- Layer 10: PII detection and masking
- Layer 11: Basic hallucination detection (self-consistency + faithfulness)
- Layer 14: Immutable audit trail
- **Deliverable**: Production-safe single-agent runs

### Phase 3 — Intelligence & Cost (Weeks 9-12)
- Layer 5: Model routing (cost-aware, capability-match)
- Layer 5: Semantic cache
- Layer 7: Memory system (all three tiers)
- Layer 8: RAG pipeline (ingestion + retrieval)
- Layer 12: Cost tracking + budget enforcement
- **Deliverable**: RAG-enabled agents with cost control

### Phase 4 — Scale & Multi-Agent (Weeks 13-16)
- Layer 4: Multi-agent orchestration (DAG engine)
- Layer 4: Agent-to-agent communication
- Layer 11: Advanced hallucination detection (NLI verification)
- Layer 12: FinOps dashboard + anomaly detection
- Layer 13: Advanced dashboards, drift detection
- **Deliverable**: Complex multi-agent workflows

### Phase 5 — Enterprise & White-Label (Weeks 17-20)
- Layer 17: Full multi-tenancy isolation
- Layer 17: White-labeling (custom domains, branding)
- Layer 10: Full compliance controls (GDPR erasure, data residency)
- Layer 14: Compliance reporting exports
- Layer 18: Full SDK + developer portal
- **Deliverable**: Enterprise-ready, white-labeled platform

### Phase 6 — Continuous Learning (Weeks 21-24)
- Layer 15: Feedback collection + analysis pipeline
- Layer 15: Drift detection + automated alerting
- Layer 15: A/B testing infrastructure for agent versions
- Cost optimization automation
- **Deliverable**: Self-improving platform

---

## Summary: Component Count

| Category | Count |
|---|---|
| Core services | 18 |
| Plugin hooks | 10 |
| LLM provider adapters | 9 |
| Vector store adapters | 6 |
| Auth adapters | 5 |
| Secret store adapters | 4 |
| Built-in tools | 12 |
| Metrics | 30+ |
| Audit event types | 20 |
| OPA policy types | 6 |

---

*Architecture Version: 1.1 | Status: Design Complete + All Issues Resolved | Next: Phase 1 Implementation*  
*Companion documents: SYSTEM_DESIGN.md · SEQUENCE_DIAGRAMS.md · SECURITY_ARCHITECTURE.md*
