# Agentic AI Platform — System Design Document
## Companion to AGENTIC_AI_ARCHITECTURE.md

> **Purpose:** Concrete technology decisions, open-source model catalog, cloud provider
> swappability matrix, repository structure, and local development setup.
> Read alongside `AGENTIC_AI_ARCHITECTURE.md` which covers the 18-layer design.

---

## Table of Contents

1. [Technology Stack Decisions](#1-technology-stack-decisions)
2. [Open Source Model Catalog & Connections](#2-open-source-model-catalog--connections)
3. [Complete Swappability Matrix](#3-complete-swappability-matrix)
4. [Cloud Provider Mapping — AWS / Azure / GCP](#4-cloud-provider-mapping--aws--azure--gcp)
5. [Adapter Implementation Pattern](#5-adapter-implementation-pattern)
6. [Monorepo Structure](#6-monorepo-structure)
7. [Configuration Schema (Complete)](#7-configuration-schema-complete)
8. [Local Development Stack](#8-local-development-stack)
9. [Environment Progression (Dev → Staging → Prod)](#9-environment-progression-dev--staging--prod)
10. [Service Communication Map](#10-service-communication-map)
11. [Data Store Ownership](#11-data-store-ownership)
12. [Dependency Graph](#12-dependency-graph)
13. [Implementation Sequence](#13-implementation-sequence)

---

## 1. Technology Stack Decisions

### Why Two Languages

The platform uses **Python** for AI-core services and **TypeScript** for API-surface services. This is not a compromise — it is the optimal split based on where each ecosystem is strongest.

```
┌─────────────────────────────────────────────────────────────────────┐
│  PYTHON DOMAIN                    │  TYPESCRIPT DOMAIN              │
│  (AI ecosystem, async I/O)        │  (API contracts, SDK, DX)       │
│                                   │                                 │
│  agent-runner                     │  api-gateway (config-only)      │
│  llm-proxy                        │  notification-service           │
│  rag-service                      │  config-service                 │
│  tool-executor                    │  client-sdk                     │
│  memory-service                   │  admin-portal                   │
│  pii-service                      │  webhook-service                │
│  hallucination-checker            │                                 │
│  security-guard                   │                                 │
│  cost-service                     │                                 │
│  audit-service                    │                                 │
│  auth-service                     │                                 │
│  orchestrator                     │                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Python Services — Stack

| Concern | Library | Why |
|---|---|---|
| Web framework | FastAPI 0.111+ | Async-native, auto OpenAPI, streaming, fastest Python framework |
| ASGI server | Uvicorn + Gunicorn | Production-ready, multi-worker |
| Data validation | Pydantic v2 | Runtime type enforcement, JSON Schema generation, Rust-speed |
| LLM abstraction | LiteLLM 1.x | Single interface to 100+ LLM providers, zero vendor lock-in |
| RAG framework | LlamaIndex 0.10+ | Production-grade ingestion, retrieval, reranking |
| PII detection | Microsoft Presidio | NLP-based, multi-language, extensible entity recognizers |
| NLP / NER | spaCy 3.x | Fast NER pipeline for PII and entity extraction |
| Embeddings | sentence-transformers | Local embedding models, no API cost |
| Task queue | Celery 5.x + Redis | Battle-tested, reliable, supports priorities |
| ORM | SQLAlchemy 2.0 (async) | Async-first, supports all SQL databases |
| DB migrations | Alembic | Works with SQLAlchemy, supports all SQL databases |
| HTTP client | httpx | Async, supports HTTP/2, connection pooling |
| Secrets | python-dotenv (dev) / SDK per provider | Adapter pattern for secret stores |
| Observability | OpenTelemetry SDK | Vendor-neutral, all exporters |
| Testing | pytest + pytest-asyncio + httpx | Industry standard for async FastAPI |
| Linting | ruff | 10-100x faster than flake8/black combined |
| Type checking | mypy / pyright | Catches runtime errors at build time |
| Containerize | Docker (distroless python base) | Minimal attack surface |

### TypeScript Services — Stack

| Concern | Library | Why |
|---|---|---|
| Framework | NestJS 10+ | Decorator DI, modular, excellent for plugin architecture |
| Runtime | Node.js 22 LTS | LTS stability, native ESM, excellent async |
| Validation | Zod 3.x | Runtime + compile-time, matches Pydantic's role |
| ORM | Prisma 5.x | Type-safe queries, excellent migrations |
| HTTP client | ky / got | Modern, promise-based, interceptors |
| SDK bundler | tsup | ESM + CJS dual output, tree-shaking |
| Testing | Vitest | Faster than Jest, native ESM |
| Linting | ESLint + Prettier | Standard |

### Infrastructure (No Custom Code)

| Component | Technology | Version |
|---|---|---|
| API Gateway | Kong CE or Traefik v3 | Config-driven, no code |
| Policy engine | Open Policy Agent (OPA) | Rego policies |
| Service mesh | Linkerd v2 (or Istio) | mTLS, observability |
| Container runtime | Docker + containerd | |
| Orchestration | Kubernetes 1.30+ | |
| CI/CD | GitHub Actions / GitLab CI | |
| GitOps | ArgoCD | |
| Secrets (default) | HashiCorp Vault OSS | Swappable |
| Auth (default) | Keycloak 24+ | Swappable |

---

## 2. Open Source Model Catalog & Connections

All open-source models connect through **LiteLLM**, which provides a unified interface. The agent code never changes — only the config.

### 2.1 Model Categories

```
Category          Models                              Best For
──────────────────────────────────────────────────────────────────────
General Purpose   Llama 3.1 (8B, 70B, 405B)          Most tasks
                  Mistral 7B / Mixtral 8x7B           Fast, multilingual
                  Qwen 2.5 (7B, 72B)                  Multilingual, coding
                  Gemma 2 (2B, 9B, 27B)               Lightweight, Google
                  Phi-3 / Phi-3.5 (Mini, Medium)      Small but capable

Coding            DeepSeek Coder V2                   Code generation
                  CodeLlama (7B, 13B, 34B)            Code completion
                  Starcoder2                          Multi-language code

Long Context      Llama 3.1 405B (128K)               Document processing
                  Mistral NeMo (128K)                 Long docs

Embeddings        nomic-embed-text (local)            RAG, semantic search
                  mxbai-embed-large                   High quality embeddings
                  all-MiniLM-L6-v2                    Fast, lightweight
                  bge-m3                              Multilingual embeddings

Vision            Llava 1.6 (7B, 13B, 34B)           Image understanding
                  Llama 3.2 Vision (11B, 90B)         Latest vision model
                  moondream2                          Lightweight vision

Function Calling  Llama 3.1 (all sizes)              Tool use / agents
                  Mistral 7B Instruct                Tool use
                  Hermes-2-Pro                       Excellent tool calling

Reasoning         DeepSeek-R1 (1.5B to 70B)          Chain-of-thought
                  QwQ-32B                            Math, reasoning
```

### 2.2 Connection Methods

#### Method A — Ollama (Recommended for Dev + Small-Scale Prod)

```bash
# Install and run Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.1:8b
ollama pull llama3.1:70b
ollama pull nomic-embed-text
ollama pull llava:13b
ollama pull phi3:medium

# Ollama exposes OpenAI-compatible API at localhost:11434
```

```yaml
# Config
llm:
  providers:
    - id: ollama-llama
      adapter: litellm
      base_url: http://ollama:11434
      model: ollama/llama3.1:8b
      api_key: ollama            # Ollama ignores the key but LiteLLM requires it

    - id: ollama-embed
      adapter: litellm
      base_url: http://ollama:11434
      model: ollama/nomic-embed-text
```

```python
# In code — identical to any other provider
response = await llm_client.complete(
    model="ollama/llama3.1:8b",
    messages=[{"role": "user", "content": "Extract invoice fields..."}]
)
```

#### Method B — vLLM (High-Throughput Production Self-Hosting)

```bash
# Run vLLM server (requires GPU)
docker run --runtime nvidia --gpus all \
  -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Meta-Llama-3.1-70B-Instruct \
  --tensor-parallel-size 4 \
  --max-model-len 32768 \
  --api-key your-secret-key

# vLLM exposes OpenAI-compatible API
```

```yaml
# Config
llm:
  providers:
    - id: vllm-llama
      adapter: litellm
      base_url: http://vllm-service:8000/v1
      model: openai/meta-llama/Meta-Llama-3.1-70B-Instruct
      api_key: ${secrets.VLLM_KEY}
      extra_headers:
        X-Custom-Header: value
```

#### Method C — HuggingFace TGI (Text Generation Inference)

```bash
# Run TGI server
docker run --gpus all \
  -p 8080:80 \
  -v /models:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id mistralai/Mistral-7B-Instruct-v0.3 \
  --max-input-length 8000 \
  --max-total-tokens 16000
```

```yaml
# Config
llm:
  providers:
    - id: tgi-mistral
      adapter: litellm
      base_url: http://tgi-service:8080
      model: huggingface/mistralai/Mistral-7B-Instruct-v0.3
```

#### Method D — HuggingFace Inference API (Managed, No GPU needed)

```yaml
# Config
llm:
  providers:
    - id: hf-api
      adapter: litellm
      model: huggingface/meta-llama/Llama-3.1-70B-Instruct
      api_key: ${secrets.HF_TOKEN}
      # Uses HF Inference API — no infrastructure needed
```

#### Method E — AWS Bedrock (Managed, Open Source Models on AWS)

```yaml
# Config — no API key needed, uses IAM role
llm:
  providers:
    - id: bedrock-llama
      adapter: litellm
      model: bedrock/meta.llama3-1-70b-instruct-v1:0
      aws_region: us-east-1
      # IAM role must have: bedrock:InvokeModel permission

    - id: bedrock-mistral
      adapter: litellm
      model: bedrock/mistral.mistral-large-2402-v1:0
      aws_region: us-east-1

    - id: bedrock-claude
      adapter: litellm
      model: bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
      aws_region: us-east-1
```

#### Method F — Azure AI (Llama, Phi, Mistral on Azure)

```yaml
# Config
llm:
  providers:
    - id: azure-llama
      adapter: litellm
      base_url: ${secrets.AZURE_AI_ENDPOINT}
      model: azure_ai/Meta-Llama-3.1-70B-Instruct
      api_key: ${secrets.AZURE_AI_KEY}

    - id: azure-phi
      adapter: litellm
      base_url: ${secrets.AZURE_AI_ENDPOINT}
      model: azure_ai/Phi-3-medium-128k-instruct
      api_key: ${secrets.AZURE_AI_KEY}
```

#### Method G — GCP Vertex AI Model Garden

```yaml
# Config — uses GCP service account
llm:
  providers:
    - id: vertex-llama
      adapter: litellm
      model: vertex_ai/meta/llama3-405b-instruct-maas
      vertex_project: my-gcp-project
      vertex_location: us-central1

    - id: vertex-gemma
      adapter: litellm
      model: vertex_ai/google/gemma-2-27b-it
      vertex_project: my-gcp-project
      vertex_location: us-central1
```

### 2.3 Embedding Model Connections

```yaml
embeddings:
  # Option A: Local via Ollama (free, private)
  - id: local-nomic
    adapter: litellm
    model: ollama/nomic-embed-text
    base_url: http://ollama:11434
    dimensions: 768

  # Option B: Local via sentence-transformers (Python, no server needed)
  - id: local-minilm
    adapter: sentence-transformers
    model: all-MiniLM-L6-v2
    dimensions: 384

  # Option C: OpenAI (high quality, paid)
  - id: openai-embed
    adapter: litellm
    model: text-embedding-3-small
    api_key: ${secrets.OPENAI_KEY}
    dimensions: 1536

  # Option D: AWS Bedrock Titan Embeddings
  - id: bedrock-embed
    adapter: litellm
    model: bedrock/amazon.titan-embed-text-v2:0
    aws_region: us-east-1
    dimensions: 1024

  # Option E: Azure OpenAI Embeddings
  - id: azure-embed
    adapter: litellm
    model: azure/text-embedding-3-small
    base_url: ${secrets.AZURE_OAI_ENDPOINT}
    api_key: ${secrets.AZURE_OAI_KEY}
    dimensions: 1536

  # Option F: Cohere Embed (multilingual)
  - id: cohere-embed
    adapter: litellm
    model: embed-multilingual-v3.0
    api_key: ${secrets.COHERE_KEY}
    dimensions: 1024
```

### 2.4 Model Selection Guide

```
For your use case, pick:

Real-time chat (< 2s response):
  → Llama 3.1 8B (Ollama/vLLM) or GPT-4o-mini or Claude Haiku
  → Small, fast, cheap

Complex reasoning / multi-step:
  → Llama 3.1 70B or GPT-4o or Claude 3.5 Sonnet
  → Better accuracy, worth the cost

Document processing (long):
  → Llama 3.1 405B (128K context) or Gemini 1.5 Pro (1M context)
  → Long context window needed

Code generation:
  → DeepSeek Coder V2 (OSS) or GPT-4o or Claude 3.5 Sonnet
  → Code-specific training

Vision / image:
  → Llama 3.2 Vision (OSS) or GPT-4o or Claude 3.5 Sonnet
  → Multimodal capability

Privacy-critical (can't leave your infra):
  → Any Ollama/vLLM model on your own hardware
  → Data never leaves your environment

Cost-zero dev / testing:
  → Ollama with any 7-8B model locally
  → Absolutely free
```

---

## 3. Complete Swappability Matrix

Every platform component has a **default** (works out of the box) and **alternatives** (swap via config).

```
COMPONENT           DEFAULT (Local/OSS)    ALTERNATIVES
═══════════════════════════════════════════════════════════════════════════════

LLM Provider        Ollama                 OpenAI, Anthropic, Gemini, Mistral,
                                           AWS Bedrock, Azure OpenAI,
                                           GCP Vertex, HuggingFace, vLLM, TGI

Embedding Model     nomic-embed (Ollama)   OpenAI Ada-3, Cohere, AWS Titan,
                                           Azure OpenAI, sentence-transformers

Vector Store        Qdrant                 Pinecone, Weaviate, Chroma,
                                           pgvector (Postgres), Milvus,
                                           AWS OpenSearch, Azure AI Search,
                                           GCP Vertex Vector Search

Relational DB       PostgreSQL             MySQL, MariaDB,
                                           AWS RDS, Azure PostgreSQL,
                                           GCP Cloud SQL, CockroachDB

Auth / Identity     Keycloak               Auth0, Okta, AWS Cognito,
                                           Azure AD / Entra ID,
                                           Firebase Auth, Supabase Auth,
                                           Custom JWT

Secret Store        HashiCorp Vault OSS    AWS Secrets Manager / SSM,
                                           Azure Key Vault,
                                           GCP Secret Manager,
                                           Doppler, Infisical

Cache               Redis (OSS)            AWS ElastiCache, AWS MemoryDB,
                                           Azure Cache for Redis,
                                           GCP Memorystore, Valkey, Dragonfly

Message Queue       NATS JetStream         Apache Kafka, RabbitMQ,
                                           AWS SQS + SNS, AWS MSK (Kafka),
                                           Azure Service Bus, Azure Event Hub,
                                           GCP Pub/Sub, GCP Dataflow

Object Storage      MinIO                  AWS S3, Azure Blob Storage,
                                           GCP Cloud Storage, Cloudflare R2,
                                           Backblaze B2

Search (BM25)       Elasticsearch OSS      OpenSearch (AWS), Typesense,
                                           Meilisearch, Solr,
                                           AWS OpenSearch Service,
                                           Azure AI Search

Email               SMTP / Mailhog(dev)    AWS SES, SendGrid, Postmark,
                                           Mailgun, Azure Communication

Observability       Grafana Stack          Datadog, New Relic, Dynatrace,
(Traces)            (Tempo)                AWS X-Ray, Azure App Insights,
                                           GCP Cloud Trace, Honeycomb, Lightstep

Observability       Prometheus             Datadog, CloudWatch, Azure Monitor,
(Metrics)           + Grafana              GCP Cloud Monitoring, InfluxDB

Observability       Loki                   Datadog, Splunk, ELK Stack,
(Logs)              + Grafana              AWS CloudWatch Logs, Azure Log Analytics

API Gateway         Kong CE / Traefik      AWS API Gateway, Azure APIM,
                                           GCP Cloud Endpoints, Apigee,
                                           Nginx, Caddy

CDN / Edge          Caddy (local)          AWS CloudFront, Azure CDN,
                                           GCP Cloud CDN, Cloudflare

Container Reg.      Docker Hub / local     AWS ECR, Azure ACR, GCP Artifact
                                           Registry, GitHub Container Registry

Kubernetes          Local k3s / Kind       AWS EKS, Azure AKS, GCP GKE,
                                           OpenShift, Rancher, Civo

Workflow/DAG        Built-in DAG engine    Apache Airflow, Prefect, Temporal,
                                           AWS Step Functions, Azure Durable Func

Policy Engine       OPA (Open Policy       Built-in RBAC only (simpler),
                    Agent)                 AWS IAM + Cedar, Azure ABAC
```

---

## 4. Cloud Provider Mapping — AWS / Azure / GCP

### 4.1 AWS Deployment

```
Platform Service          AWS Native                 Notes
──────────────────────────────────────────────────────────────────────
LLM (commercial)          Bedrock                    Claude, Titan, Llama, Mistral
LLM (OSS self-hosted)     EC2 (G/P instances) + vLLM GPU instances
Vector Store              OpenSearch k-NN            Or pgvector on RDS
Relational DB             RDS PostgreSQL             Multi-AZ, automated backups
Cache                     ElastiCache Redis          Cluster mode
Message Queue             SQS + SNS                  Or MSK (managed Kafka)
Object Storage            S3                         Lifecycle policies
Auth                      Cognito                    Or Keycloak on EC2
Secret Store              Secrets Manager + SSM      Dynamic secrets
API Gateway               API Gateway v2             Or ALB + Kong on EKS
Kubernetes                EKS (Fargate or EC2)       Managed control plane
Container Registry        ECR                        Image scanning built-in
Observability Traces      X-Ray + ADOT               OTEL compatible
Observability Metrics     CloudWatch + Container Ins. Or Prometheus on EKS
Observability Logs        CloudWatch Logs            Or OpenSearch
CDN                       CloudFront                 WAF integrated
DNS                       Route 53                   Health checks + failover
Certificate Mgr           ACM                        Auto-renew TLS
Service Mesh              App Mesh or Istio on EKS   mTLS
Storage (files)           EFS                        Shared filesystem
Config                    AppConfig + Parameter Store Hot reload
```

```yaml
# AWS production config
llm:
  providers:
    - id: bedrock-primary
      adapter: litellm
      model: bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
      aws_region: us-east-1
    - id: bedrock-llama
      adapter: litellm
      model: bedrock/meta.llama3-1-70b-instruct-v1:0
      aws_region: us-east-1

vector_store:
  adapter: opensearch
  endpoint: ${secrets.OPENSEARCH_ENDPOINT}
  index_prefix: aai
  aws_region: us-east-1
  # Uses IAM role — no credentials in config

database:
  adapter: postgresql
  url: ${secrets.RDS_URL}
  pool_size: 20

cache:
  adapter: redis
  url: ${secrets.ELASTICACHE_URL}
  tls: true

queue:
  adapter: sqs
  region: us-east-1
  queue_url: ${secrets.SQS_QUEUE_URL}
  # Uses IAM role — no credentials

storage:
  adapter: s3
  bucket: ${secrets.S3_BUCKET}
  region: us-east-1
  # Uses IAM role

auth:
  adapter: cognito
  user_pool_id: ${secrets.COGNITO_USER_POOL_ID}
  client_id: ${secrets.COGNITO_CLIENT_ID}
  region: us-east-1

secrets:
  adapter: aws-secrets-manager
  region: us-east-1
  prefix: /aai/prod/
  # Uses IAM role

telemetry:
  adapter: otlp
  endpoint: http://adot-collector:4317   # ADOT → CloudWatch + X-Ray
```

### 4.2 Azure Deployment

```
Platform Service          Azure Native               Notes
──────────────────────────────────────────────────────────────────────
LLM (commercial)          Azure OpenAI               GPT-4o, GPT-3.5
LLM (OSS)                 Azure AI Studio            Llama, Phi, Mistral
Vector Store              Azure AI Search            Vector + keyword hybrid
Relational DB             Azure PostgreSQL Flex       HA, automatic backups
Cache                     Azure Cache for Redis       Or Azure Managed Redis
Message Queue             Azure Service Bus          Topics + subscriptions
Object Storage            Azure Blob Storage          Lifecycle management
Auth                      Azure AD / Entra ID        SSO, B2C for consumers
Secret Store              Azure Key Vault             Managed HSM available
API Gateway               Azure APIM                 Policies, rate limiting
Kubernetes                AKS                        Managed, AAD integrated
Container Registry        Azure Container Registry    Geo-replication
Observability Traces      App Insights               OTEL compatible
Observability Metrics     Azure Monitor              Alerts, dashboards
Observability Logs        Log Analytics Workspace    KQL queries
CDN                       Azure Front Door           WAF + CDN combined
DNS                       Azure DNS                  Private zones
Certificate Mgr           App Service Certificates   Or Let's Encrypt
Service Mesh              Open Service Mesh / Istio  mTLS
Config                    Azure App Configuration    Feature flags + config
```

```yaml
# Azure production config
llm:
  providers:
    - id: azure-oai-primary
      adapter: litellm
      base_url: ${secrets.AZURE_OAI_ENDPOINT}
      model: azure/gpt-4o
      api_key: ${secrets.AZURE_OAI_KEY}
      api_version: "2024-08-01-preview"

    - id: azure-llama
      adapter: litellm
      base_url: ${secrets.AZURE_AI_ENDPOINT}
      model: azure_ai/Meta-Llama-3.1-70B-Instruct
      api_key: ${secrets.AZURE_AI_KEY}

vector_store:
  adapter: azure-ai-search
  endpoint: ${secrets.AZURE_SEARCH_ENDPOINT}
  api_key: ${secrets.AZURE_SEARCH_KEY}  # Or managed identity
  index_prefix: aai

database:
  adapter: postgresql
  url: ${secrets.AZURE_PG_URL}
  ssl_mode: require

cache:
  adapter: redis
  url: ${secrets.AZURE_REDIS_URL}
  tls: true
  ssl_cert_reqs: required

queue:
  adapter: azure-service-bus
  connection_string: ${secrets.ASB_CONNECTION_STRING}
  topic_name: aai-runs

storage:
  adapter: azure-blob
  connection_string: ${secrets.AZURE_STORAGE_CONNECTION}
  container_name: aai-artifacts

auth:
  adapter: azure-ad
  tenant_id: ${secrets.AZURE_TENANT_ID}
  client_id: ${secrets.AZURE_CLIENT_ID}
  authority: https://login.microsoftonline.com/${secrets.AZURE_TENANT_ID}

secrets:
  adapter: azure-keyvault
  vault_url: ${secrets.AZURE_KEYVAULT_URL}
  # Uses managed identity — no credentials

telemetry:
  adapter: otlp
  endpoint: ${secrets.APPINSIGHTS_OTLP_ENDPOINT}
  headers:
    x-otlp-api-key: ${secrets.APPINSIGHTS_KEY}
```

### 4.3 GCP Deployment

```
Platform Service          GCP Native                 Notes
──────────────────────────────────────────────────────────────────────
LLM (commercial)          Vertex AI (Gemini)         Gemini 1.5 Pro/Flash
LLM (OSS)                 Vertex AI Model Garden     Llama, Gemma, Mistral
Vector Store              AlloyDB pgvector           Or Vertex Vector Search
Relational DB             Cloud SQL PostgreSQL       HA, read replicas
Cache                     Memorystore (Redis)        Managed Redis
Message Queue             Pub/Sub                    At-least-once delivery
Object Storage            Cloud Storage (GCS)        Lifecycle management
Auth                      Identity Platform          Firebase Auth for consumers
Secret Store              Secret Manager             Automatic rotation
API Gateway               Cloud Endpoints / Apigee   OpenAPI based
Kubernetes                GKE Autopilot              Fully managed nodes
Container Registry        Artifact Registry          Vulnerability scanning
Observability Traces      Cloud Trace                OTEL compatible
Observability Metrics     Cloud Monitoring           Alerts, SLOs
Observability Logs        Cloud Logging              Log-based metrics
CDN                       Cloud CDN + Cloud Armor    WAF integrated
DNS                       Cloud DNS                  Private zones
Certificate Mgr           Certificate Manager        Auto-renew
Service Mesh              Traffic Director / Istio   mTLS
Config                    Firebase Remote Config     Or Cloud Run env vars
```

```yaml
# GCP production config
llm:
  providers:
    - id: vertex-gemini
      adapter: litellm
      model: vertex_ai/gemini-1.5-pro-002
      vertex_project: ${secrets.GCP_PROJECT}
      vertex_location: us-central1

    - id: vertex-llama
      adapter: litellm
      model: vertex_ai/meta/llama3-70b-instruct-maas
      vertex_project: ${secrets.GCP_PROJECT}
      vertex_location: us-central1

vector_store:
  adapter: pgvector          # AlloyDB with pgvector extension
  url: ${secrets.ALLOYDB_URL}

database:
  adapter: postgresql
  url: ${secrets.CLOUDSQL_URL}
  # Cloud SQL Proxy handles auth

cache:
  adapter: redis
  url: ${secrets.MEMORYSTORE_URL}
  tls: true

queue:
  adapter: pubsub
  project_id: ${secrets.GCP_PROJECT}
  topic_id: aai-runs
  subscription_id: aai-runs-sub

storage:
  adapter: gcs
  bucket: ${secrets.GCS_BUCKET}
  project: ${secrets.GCP_PROJECT}

auth:
  adapter: firebase
  project_id: ${secrets.GCP_PROJECT}
  # Uses Application Default Credentials

secrets:
  adapter: gcp-secret-manager
  project_id: ${secrets.GCP_PROJECT}
  prefix: aai-prod-

telemetry:
  adapter: otlp
  endpoint: https://cloudtrace.googleapis.com
  # Uses Application Default Credentials
```

---

## 5. Adapter Implementation Pattern

This is how every swappable component is built. One interface, many implementations.

### 5.1 The Pattern (VectorStore Example)

```python
# core/interfaces/vector_store.py  ← The contract (never changes)
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class SearchResult:
    id: str
    score: float
    payload: dict[str, Any]
    content: str

class VectorStoreAdapter(ABC):

    @abstractmethod
    async def upsert(
        self,
        vectors: list[dict],
        namespace: str
    ) -> None: ...

    @abstractmethod
    async def query(
        self,
        embedding: list[float],
        top_k: int,
        namespace: str,
        filter: dict | None = None
    ) -> list[SearchResult]: ...

    @abstractmethod
    async def delete(self, ids: list[str], namespace: str) -> None: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

```python
# adapters/vector/qdrant.py  ← Default local implementation
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, Filter, SearchRequest
from core.interfaces.vector_store import VectorStoreAdapter, SearchResult

class QdrantAdapter(VectorStoreAdapter):
    def __init__(self, url: str, api_key: str | None = None):
        self.client = AsyncQdrantClient(url=url, api_key=api_key)

    async def upsert(self, vectors: list[dict], namespace: str) -> None:
        points = [
            PointStruct(id=v["id"], vector=v["embedding"], payload=v["metadata"])
            for v in vectors
        ]
        await self.client.upsert(collection_name=namespace, points=points)

    async def query(self, embedding, top_k, namespace, filter=None):
        results = await self.client.search(
            collection_name=namespace,
            query_vector=embedding,
            limit=top_k,
            query_filter=Filter(**filter) if filter else None,
            with_payload=True
        )
        return [
            SearchResult(
                id=str(r.id),
                score=r.score,
                payload=r.payload,
                content=r.payload.get("content", "")
            )
            for r in results
        ]

    async def delete(self, ids: list[str], namespace: str) -> None:
        await self.client.delete(collection_name=namespace, points_selector=ids)

    async def health_check(self) -> bool:
        info = await self.client.get_collections()
        return info is not None
```

```python
# adapters/vector/pgvector.py  ← AWS RDS / Azure PostgreSQL / GCP AlloyDB
import asyncpg
from core.interfaces.vector_store import VectorStoreAdapter, SearchResult

class PgVectorAdapter(VectorStoreAdapter):
    def __init__(self, connection_string: str):
        self.dsn = connection_string
        self.pool = None

    async def upsert(self, vectors: list[dict], namespace: str) -> None:
        async with self.pool.acquire() as conn:
            for v in vectors:
                await conn.execute(
                    f"""
                    INSERT INTO {namespace}_vectors (id, embedding, content, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                    SET embedding=$2, content=$3, metadata=$4
                    """,
                    v["id"], v["embedding"], v["content"], v["metadata"]
                )

    async def query(self, embedding, top_k, namespace, filter=None):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, 1 - (embedding <=> $1::vector) as score,
                       content, metadata
                FROM {namespace}_vectors
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                embedding, top_k
            )
        return [
            SearchResult(id=r["id"], score=r["score"],
                        content=r["content"], payload=r["metadata"])
            for r in rows
        ]

    async def delete(self, ids: list[str], namespace: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {namespace}_vectors WHERE id = ANY($1)", ids
            )

    async def health_check(self) -> bool:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT 1") == 1
```

```python
# adapters/vector/opensearch.py  ← AWS OpenSearch Service
from opensearchpy import AsyncOpenSearch
from core.interfaces.vector_store import VectorStoreAdapter, SearchResult

class OpenSearchAdapter(VectorStoreAdapter):
    def __init__(self, endpoint: str, region: str):
        self.client = AsyncOpenSearch(hosts=[endpoint], use_ssl=True)
        self.region = region

    async def query(self, embedding, top_k, namespace, filter=None):
        body = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": embedding,
                        "k": top_k
                    }
                }
            }
        }
        response = await self.client.search(index=namespace, body=body)
        return [
            SearchResult(
                id=hit["_id"],
                score=hit["_score"],
                content=hit["_source"].get("content", ""),
                payload=hit["_source"]
            )
            for hit in response["hits"]["hits"]
        ]
```

```python
# core/registry/adapter_registry.py  ← Loads adapter from config
from core.interfaces.vector_store import VectorStoreAdapter
from core.config import PlatformConfig

class AdapterRegistry:
    _vector_store: VectorStoreAdapter | None = None

    @classmethod
    def get_vector_store(cls) -> VectorStoreAdapter:
        if cls._vector_store:
            return cls._vector_store

        config = PlatformConfig.get()
        adapter_name = config.vector_store.adapter

        match adapter_name:
            case "qdrant":
                from adapters.vector.qdrant import QdrantAdapter
                cls._vector_store = QdrantAdapter(
                    url=config.vector_store.url,
                    api_key=config.vector_store.api_key
                )
            case "pgvector":
                from adapters.vector.pgvector import PgVectorAdapter
                cls._vector_store = PgVectorAdapter(
                    connection_string=config.vector_store.url
                )
            case "opensearch":
                from adapters.vector.opensearch import OpenSearchAdapter
                cls._vector_store = OpenSearchAdapter(
                    endpoint=config.vector_store.url,
                    region=config.vector_store.region
                )
            case "pinecone":
                from adapters.vector.pinecone import PineconeAdapter
                cls._vector_store = PineconeAdapter(
                    api_key=config.vector_store.api_key,
                    environment=config.vector_store.environment
                )
            case _:
                raise ValueError(f"Unknown vector store adapter: {adapter_name}")

        return cls._vector_store

# Usage — same everywhere, adapter loaded transparently:
# vector_store = AdapterRegistry.get_vector_store()
# results = await vector_store.query(embedding, top_k=10, namespace="tenant_abc")
```

The same pattern repeats for: LLM, Auth, SecretStore, Cache, Queue, Storage, Database, Email, Observability.

---

## 6. Monorepo Structure

```
agentic-platform/
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint, test, build on PR
│       ├── security-scan.yml         # CVE + SAST on every push
│       └── deploy.yml                # Deploy on merge to main
│
├── infra/
│   ├── docker-compose.yml            # Full local stack
│   ├── docker-compose.override.yml   # Dev overrides (hot reload, debug ports)
│   ├── k8s/
│   │   ├── base/                     # Kustomize base manifests
│   │   │   ├── agent-runner/
│   │   │   ├── llm-proxy/
│   │   │   ├── rag-service/
│   │   │   └── ...each service/
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── helm/                     # Helm charts (alternative to Kustomize)
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── aws/                  # AWS-specific modules
│   │   │   ├── azure/                # Azure-specific modules
│   │   │   └── gcp/                  # GCP-specific modules
│   │   └── environments/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   ├── kong/
│   │   └── kong.yml                  # Kong declarative config
│   └── opa/
│       └── policies/                 # OPA Rego policy files
│
├── services/                         # Python microservices
│   │
│   ├── shared/                       # Shared Python code (published as internal package)
│   │   ├── core/
│   │   │   ├── interfaces/           # All abstract adapter interfaces
│   │   │   │   ├── vector_store.py
│   │   │   │   ├── llm_provider.py
│   │   │   │   ├── secret_store.py
│   │   │   │   ├── cache.py
│   │   │   │   ├── queue.py
│   │   │   │   ├── storage.py
│   │   │   │   └── auth_provider.py
│   │   │   ├── models/               # Shared domain types (AgentRun, LLMCall, etc.)
│   │   │   ├── config.py             # Config loader (reads platform config file)
│   │   │   └── registry.py           # AdapterRegistry
│   │   ├── adapters/
│   │   │   ├── vector/
│   │   │   │   ├── qdrant.py
│   │   │   │   ├── pgvector.py
│   │   │   │   ├── opensearch.py
│   │   │   │   ├── pinecone.py
│   │   │   │   ├── weaviate.py
│   │   │   │   └── azure_ai_search.py
│   │   │   ├── llm/
│   │   │   │   └── litellm.py        # LiteLLM wraps all LLM providers
│   │   │   ├── auth/
│   │   │   │   ├── keycloak.py
│   │   │   │   ├── auth0.py
│   │   │   │   ├── cognito.py
│   │   │   │   ├── azure_ad.py
│   │   │   │   └── firebase.py
│   │   │   ├── secrets/
│   │   │   │   ├── vault.py
│   │   │   │   ├── aws_secrets.py
│   │   │   │   ├── azure_keyvault.py
│   │   │   │   └── gcp_secret_manager.py
│   │   │   ├── cache/
│   │   │   │   └── redis.py          # Works for Redis, ElastiCache, Azure Cache
│   │   │   ├── queue/
│   │   │   │   ├── nats.py
│   │   │   │   ├── kafka.py
│   │   │   │   ├── sqs.py
│   │   │   │   ├── azure_service_bus.py
│   │   │   │   └── pubsub.py
│   │   │   └── storage/
│   │   │       ├── minio.py          # Works for MinIO and S3 (S3-compatible)
│   │   │       ├── s3.py
│   │   │       ├── azure_blob.py
│   │   │       └── gcs.py
│   │   └── pyproject.toml
│   │
│   ├── agent-runner/                 # Core agent execution engine
│   │   ├── app/
│   │   │   ├── main.py               # FastAPI app
│   │   │   ├── routers/
│   │   │   │   ├── runs.py           # POST /runs, GET /runs/{id}
│   │   │   │   └── health.py
│   │   │   ├── services/
│   │   │   │   ├── run_manager.py    # AgentRun lifecycle
│   │   │   │   ├── planner.py        # Task decomposition
│   │   │   │   ├── step_executor.py  # Step execution + retry
│   │   │   │   └── state_machine.py  # Run state transitions
│   │   │   ├── workers/
│   │   │   │   └── run_worker.py     # Celery worker for async runs
│   │   │   └── models/
│   │   │       └── schemas.py        # Pydantic request/response models
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── llm-proxy/                    # LLM abstraction, routing, caching
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   └── completions.py    # POST /v1/chat/completions (OpenAI-compatible)
│   │   │   ├── services/
│   │   │   │   ├── router.py         # Model routing logic
│   │   │   │   ├── cache.py          # Semantic cache
│   │   │   │   ├── budget.py         # Token budget enforcement
│   │   │   │   └── validator.py      # Response validation
│   │   │   └── providers/            # LiteLLM wrappers per provider config
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── rag-service/                  # RAG ingestion + retrieval
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── ingest.py         # POST /kb/{id}/ingest
│   │   │   │   └── retrieve.py       # POST /retrieve
│   │   │   ├── services/
│   │   │   │   ├── ingestion/
│   │   │   │   │   ├── parser.py     # Format detection + extraction
│   │   │   │   │   ├── chunker.py    # Chunking strategies
│   │   │   │   │   └── embedder.py   # Embedding models
│   │   │   │   └── retrieval/
│   │   │   │       ├── dense.py      # Vector similarity search
│   │   │   │       ├── sparse.py     # BM25 keyword search
│   │   │   │       ├── fusion.py     # RRF fusion
│   │   │   │       └── reranker.py   # Cross-encoder reranking
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── auth-service/                 # AuthN + AuthZ
│   ├── security-guard/               # Injection, content policy
│   ├── pii-service/                  # PII detection + masking
│   ├── hallucination-checker/        # Quality scoring
│   ├── memory-service/               # Three-tier memory
│   ├── tool-executor/                # Tool registry + sandboxed execution
│   ├── orchestrator/                 # Multi-agent DAG execution
│   ├── cost-service/                 # Ledger + budget + FinOps
│   └── audit-service/                # Immutable audit trail
│
├── packages/                         # TypeScript packages
│   │
│   ├── sdk/                          # Client SDK (@agentic-platform/sdk)
│   │   ├── src/
│   │   │   ├── client.ts             # AgentClient class
│   │   │   ├── types.ts              # All TypeScript types (generated from Python schemas)
│   │   │   ├── streaming.ts          # SSE + WebSocket handling
│   │   │   └── index.ts
│   │   ├── tests/
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── notification-service/         # NestJS: HITL, webhooks, alerts
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   └── config-service/              # NestJS: config management, feature flags
│       ├── src/
│       ├── Dockerfile
│       └── package.json
│
├── config/
│   ├── platform.dev.yaml             # Dev config (Ollama, local DBs)
│   ├── platform.staging.yaml         # Staging config (cloud services)
│   ├── platform.prod.yaml            # Prod config (full cloud, no secrets)
│   └── platform.schema.json          # JSON Schema for config validation
│
├── scripts/
│   ├── setup-dev.sh                  # One-command dev setup
│   ├── generate-types.sh             # Generate TS types from Python Pydantic models
│   └── seed-dev-data.sh              # Seed dev environment
│
├── docs/
│   ├── AGENTIC_AI_ARCHITECTURE.md    # 18-layer architecture (this repo)
│   ├── SYSTEM_DESIGN.md              # This document
│   ├── api/                          # Auto-generated OpenAPI docs
│   └── runbooks/                     # Operational runbooks
│
├── Makefile                          # Common commands
└── README.md
```

---

## 7. Configuration Schema (Complete)

The single platform config file, fully documented:

```yaml
# config/platform.dev.yaml
version: "1.0"
environment: "development"        # development | staging | production

# ─── LLM ──────────────────────────────────────────────────────────────
llm:
  router: "cost-aware"            # cost-aware | latency-first | capability-match | round-robin
  default_provider: "ollama"

  providers:
    - id: "ollama"
      adapter: "litellm"
      base_url: "http://ollama:11434"
      model: "ollama/llama3.1:8b"
      api_key: "ollama"
      capabilities: ["text", "function_calling"]
      max_context_tokens: 128000
      cost_per_1k_input: 0.0      # Free — local model
      cost_per_1k_output: 0.0
      priority: 1

    - id: "ollama-vision"
      adapter: "litellm"
      base_url: "http://ollama:11434"
      model: "ollama/llava:13b"
      api_key: "ollama"
      capabilities: ["text", "vision"]
      cost_per_1k_input: 0.0
      cost_per_1k_output: 0.0
      priority: 1

    # Fallback to OpenAI when Ollama can't handle (e.g., capability gap)
    - id: "openai"
      adapter: "litellm"
      api_key: "${secrets.OPENAI_KEY}"
      model: "gpt-4o"
      capabilities: ["text", "vision", "function_calling", "json_mode"]
      max_context_tokens: 128000
      cost_per_1k_input: 0.0025
      cost_per_1k_output: 0.010
      priority: 2

  cache:
    enabled: true
    exact_ttl_seconds: 3600       # Exact match cache TTL
    semantic_ttl_seconds: 86400   # Semantic match cache TTL
    semantic_threshold: 0.95      # Cosine similarity threshold for semantic cache

# ─── EMBEDDINGS ───────────────────────────────────────────────────────
embeddings:
  default_provider: "ollama-embed"
  providers:
    - id: "ollama-embed"
      adapter: "litellm"
      base_url: "http://ollama:11434"
      model: "ollama/nomic-embed-text"
      dimensions: 768
      cost_per_1k: 0.0

# ─── VECTOR STORE ─────────────────────────────────────────────────────
vector_store:
  adapter: "qdrant"
  url: "http://qdrant:6333"
  api_key: null                   # null = no auth (dev mode)
  collection_prefix: "aai"

# ─── DATABASE ─────────────────────────────────────────────────────────
database:
  adapter: "postgresql"
  url: "${secrets.DATABASE_URL}"  # postgresql+asyncpg://user:pass@postgres:5432/aai
  pool_size: 10
  max_overflow: 20
  echo: false                     # Set true to log all SQL (dev only)

# ─── CACHE ────────────────────────────────────────────────────────────
cache:
  adapter: "redis"
  url: "redis://redis:6379/0"
  default_ttl_seconds: 3600

# ─── QUEUE ────────────────────────────────────────────────────────────
queue:
  adapter: "nats"
  url: "nats://nats:4222"
  subjects:
    runs: "aai.runs"
    events: "aai.events"
    notifications: "aai.notifications"

# ─── STORAGE ──────────────────────────────────────────────────────────
storage:
  adapter: "minio"               # S3-compatible, works with s3 adapter too
  endpoint: "http://minio:9000"
  access_key: "${secrets.MINIO_ACCESS_KEY}"
  secret_key: "${secrets.MINIO_SECRET_KEY}"
  bucket: "aai-artifacts"
  region: "us-east-1"            # MinIO ignores this but S3 needs it

# ─── AUTH ─────────────────────────────────────────────────────────────
auth:
  adapter: "keycloak"
  issuer_url: "http://keycloak:8080/realms/aai"
  client_id: "aai-platform"
  client_secret: "${secrets.KEYCLOAK_CLIENT_SECRET}"
  api_key_header: "X-API-Key"
  jwt_algorithm: "RS256"
  token_ttl_minutes: 15
  refresh_ttl_days: 7

# ─── SECRET STORE ─────────────────────────────────────────────────────
secrets:
  adapter: "env"                 # env (dev) | vault | aws | azure | gcp
  # In dev: reads from .env file
  # In prod: change to "vault" + add vault config

# ─── SECURITY ─────────────────────────────────────────────────────────
security:
  injection_detection:
    enabled: true
    block_threshold: 0.8         # Score above this = block request
    flag_threshold: 0.5          # Score above this = log warning
  content_policy:
    adapter: "built-in"          # built-in | openai-moderation | custom
    level: "standard"            # permissive | standard | strict
  output_sanitization:
    enabled: true
    secret_detection: true
    html_escape: true

# ─── PII ──────────────────────────────────────────────────────────────
pii:
  enabled: true
  detection:
    engine: "presidio"           # presidio | regex-only | custom
    languages: ["en", "es", "fr", "de"]
    confidence_threshold: 0.7
  default_actions:
    LOW: "passthrough"
    MEDIUM: "mask"
    HIGH: "pseudonymize"
    CRITICAL: "block"

# ─── HALLUCINATION CONTROL ────────────────────────────────────────────
hallucination:
  enabled: true
  thresholds:
    warn: 0.3
    block: 0.7
  signals:
    self_consistency: true       # Run N samples, check variance
    self_consistency_n: 3        # Number of samples (cost = 3x for this signal)
    faithfulness: true           # Check claims against retrieved context
    logprobs: false              # Requires provider to support logprobs
    external_verify: false       # Web search verification (expensive, opt-in)

# ─── COST ─────────────────────────────────────────────────────────────
cost:
  tracking_enabled: true
  default_budgets:
    max_cost_usd_per_run: 1.00
    max_tokens_per_run: 100000
    max_tool_calls_per_run: 50
    max_wall_time_seconds: 300
  anomaly_detection:
    enabled: true
    spike_multiplier: 3.0        # Alert if cost > 3x p95

# ─── OBSERVABILITY ────────────────────────────────────────────────────
telemetry:
  adapter: "otlp"
  endpoint: "http://otel-collector:4317"
  service_name: "agentic-platform"
  environment: "${environment}"
  sample_rate: 1.0               # 1.0 = 100% (reduce in high-volume prod)
  metrics_interval_seconds: 15

logging:
  level: "INFO"                  # DEBUG | INFO | WARNING | ERROR
  format: "json"                 # json | text (text for dev readability)

# ─── MULTI-TENANCY ────────────────────────────────────────────────────
tenancy:
  mode: "multi"                  # single | multi
  default_isolation: "shared"    # shared | dedicated | isolated

# ─── FEATURE FLAGS ────────────────────────────────────────────────────
features:
  multi_agent_orchestration: true
  hitl_approvals: true
  rag_enabled: true
  semantic_cache: true
  hallucination_check: true
  pii_detection: true
  cost_tracking: true
  audit_log: true
  white_labeling: false          # Enable in production
```

---

## 8. Local Development Stack

### 8.1 docker-compose.yml — Complete Local Stack

```yaml
version: "3.9"

services:

  # ── AI / LLM ──────────────────────────────────────────────────
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]   # Remove if no GPU — CPU still works, just slower
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s

  ollama-init:                       # Pulls required models on first start
    image: ollama/ollama:latest
    depends_on: [ollama]
    command: >
      sh -c "
        ollama pull llama3.1:8b &&
        ollama pull nomic-embed-text &&
        ollama pull llava:13b
      "
    environment:
      - OLLAMA_HOST=http://ollama:11434

  # ── DATABASES ─────────────────────────────────────────────────
  postgres:
    image: pgvector/pgvector:pg16    # PostgreSQL with pgvector extension
    environment:
      POSTGRES_USER: aai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpassword}
      POSTGRES_DB: aai
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aai"]
      interval: 5s

  qdrant:
    image: qdrant/qdrant:v1.9.0
    ports: ["6333:6333", "6334:6334"]
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s

  # ── CACHE & QUEUE ─────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  nats:
    image: nats:2.10-alpine
    ports: ["4222:4222", "8222:8222"]
    command: "-js -m 8222"           # Enable JetStream + monitoring
    healthcheck:
      test: ["CMD", "nats-server", "--ping"]
      interval: 10s

  # ── STORAGE ───────────────────────────────────────────────────
  minio:
    image: minio/minio:latest
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s

  # ── AUTH ──────────────────────────────────────────────────────
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/aai
      KC_DB_USERNAME: aai
      KC_DB_PASSWORD: ${POSTGRES_PASSWORD:-devpassword}
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD:-admin}
    command: start-dev --import-realm
    ports: ["8080:8080"]
    volumes:
      - ./infra/keycloak/realm-export.json:/opt/keycloak/data/import/realm.json
    depends_on:
      postgres: {condition: service_healthy}

  # ── API GATEWAY ───────────────────────────────────────────────
  kong:
    image: kong:3.7
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
    ports: ["8000:8000", "8443:8443"]
    volumes:
      - ./infra/kong/kong.dev.yml:/kong.yml
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s

  # ── OBSERVABILITY ─────────────────────────────────────────────
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports: ["4317:4317", "4318:4318", "8888:8888"]
    volumes:
      - ./infra/otel/collector.yml:/etc/otel-collector-config.yml
    command: --config /etc/otel-collector-config.yml

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infra/grafana/datasources:/etc/grafana/provisioning/datasources

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    volumes:
      - loki_data:/loki

  tempo:
    image: grafana/tempo:latest
    ports: ["3200:3200", "4317:4317"]
    volumes:
      - tempo_data:/var/tempo

  # ── PLATFORM SERVICES ─────────────────────────────────────────
  agent-runner:
    build: ./services/agent-runner
    environment:
      - PLATFORM_CONFIG=/config/platform.dev.yaml
      - DATABASE_URL=postgresql+asyncpg://aai:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/aai
    ports: ["8001:8000"]
    volumes:
      - ./config:/config
      - ./services/shared:/app/shared   # Hot reload shared code
    depends_on:
      postgres: {condition: service_healthy}
      redis: {condition: service_healthy}
      nats: {condition: service_healthy}
    develop:
      watch:
        - action: sync
          path: ./services/agent-runner
          target: /app

  llm-proxy:
    build: ./services/llm-proxy
    environment:
      - PLATFORM_CONFIG=/config/platform.dev.yaml
    ports: ["8002:8000"]
    volumes: ["./config:/config"]
    depends_on: [redis, ollama]

  rag-service:
    build: ./services/rag-service
    environment:
      - PLATFORM_CONFIG=/config/platform.dev.yaml
    ports: ["8003:8000"]
    volumes: ["./config:/config"]
    depends_on: [qdrant, postgres]

  # (other services follow same pattern)

  # ── DEV TOOLS ─────────────────────────────────────────────────
  mailhog:
    image: mailhog/mailhog:latest    # Fake SMTP for dev — see emails in browser
    ports: ["1025:1025", "8025:8025"]

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
  minio_data:
  ollama_models:
  prometheus_data:
  grafana_data:
  loki_data:
  tempo_data:
```

### 8.2 One-Command Dev Setup

```bash
# scripts/setup-dev.sh

#!/bin/bash
set -e

echo "Setting up Agentic AI Platform dev environment..."

# 1. Copy env template
cp .env.example .env

# 2. Start all infrastructure
docker compose up -d postgres redis qdrant nats minio keycloak \
                     ollama otel-collector prometheus grafana loki tempo \
                     mailhog

# 3. Wait for DB
echo "Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U aai; do sleep 1; done

# 4. Run DB migrations
docker compose run --rm agent-runner alembic upgrade head

# 5. Seed dev data (agents, tenants, API keys)
docker compose run --rm agent-runner python scripts/seed.py

# 6. Pull Ollama models (takes a few minutes on first run)
echo "Pulling LLM models (this takes a few minutes on first run)..."
docker compose run --rm ollama-init

# 7. Start platform services
docker compose up -d agent-runner llm-proxy rag-service \
                     auth-service security-guard pii-service \
                     cost-service audit-service kong

echo ""
echo "✓ Platform ready!"
echo ""
echo "  API Gateway:     http://localhost:8000"
echo "  Grafana:         http://localhost:3001  (admin/admin)"
echo "  Keycloak:        http://localhost:8080  (admin/admin)"
echo "  MinIO Console:   http://localhost:9001  (minioadmin/minioadmin)"
echo "  Mailhog:         http://localhost:8025"
echo "  Qdrant UI:       http://localhost:6333/dashboard"
echo ""
echo "  SDK quickstart:"
echo "    cd packages/sdk && npm install && npm run example"
```

---

## 9. Environment Progression (Dev → Staging → Prod)

```
                DEV                 STAGING              PRODUCTION
                (local Docker)      (cloud, small)       (cloud, full)
────────────────────────────────────────────────────────────────────────────
LLM             Ollama (local)      Bedrock/Azure(real)  Bedrock/Azure + vLLM
Embeddings      nomic (Ollama)      Same as prod         OpenAI Ada / Titan
Vector DB       Qdrant (Docker)     Qdrant (managed)     OpenSearch / pgvector
Database        Postgres (Docker)   RDS/CloudSQL (dev)   RDS/CloudSQL (prod, HA)
Cache           Redis (Docker)      ElastiCache (small)  ElastiCache (cluster)
Queue           NATS (Docker)       NATS managed         SQS / Service Bus
Storage         MinIO (Docker)      S3/Blob (real)       S3/Blob (real)
Auth            Keycloak (Docker)   Keycloak (managed)   Cognito / Azure AD
Secrets         .env file           Vault OSS            AWS Secrets Manager
Observability   Grafana stack       Grafana Cloud        Datadog / CloudWatch
API Gateway     Kong (Docker)       Kong (managed)       Kong Enterprise / APIM
TLS             Self-signed         Let's Encrypt        ACM / Managed Certs
HA              None                1 replica each       Multi-AZ, autoscale
Cost            $0                  ~$200/mo             Per usage
```

---

## 10. Service Communication Map

```
External Client
      │ HTTPS
      ▼
  Kong Gateway ──────────────────────────────────────────┐
      │                                                   │ (auth check)
      │ internal mTLS (Linkerd)                           ▼
      ▼                                           Auth Service
  Agent Runner ──────────────────────────────────────────┘
      │
      ├──► Security Guard       (pre-execution, sync)
      ├──► PII Service          (pre-execution, sync)
      ├──► LLM Proxy ──────────► [LLM Provider] (external HTTPS)
      │         └──► Cache (Redis)
      ├──► Tool Executor ──────► [External Tools] (sandboxed HTTPS)
      ├──► Memory Service ─────► PostgreSQL
      │         └──────────────► Qdrant (semantic memory)
      ├──► RAG Service ────────► Qdrant
      │         └──────────────► Elasticsearch (BM25)
      ├──► Hallucination Check  (post-LLM, sync)
      ├──► Cost Service         (async via NATS)
      └──► Audit Service        (async via NATS, guaranteed delivery)

Orchestrator (multi-agent)
      │
      ├──► Agent Runner (1..N workers via NATS queue)
      └──► Notification Service (HITL via NATS)

All services emit to:
      └──► OTEL Collector ────► Grafana Tempo (traces)
                          ────► Prometheus   (metrics)
                          ────► Loki         (logs)
```

---

## 11. Data Store Ownership

Each store is owned by one service. Other services request data via the owning service's API.

```
Store                   Owner Service           Consumers
──────────────────────────────────────────────────────────────────────────
PostgreSQL (runs)       agent-runner            orchestrator, cost-service
PostgreSQL (audit)      audit-service           (read-only export API)
PostgreSQL (users)      auth-service            agent-runner (via API)
PostgreSQL (agents)     agent-runner            all services (via API)
PostgreSQL (cost)       cost-service            agent-runner (budget check)
Qdrant (vectors)        rag-service             agent-runner (via rag API)
Qdrant (memory)         memory-service          agent-runner (via memory API)
Redis (cache)           llm-proxy               (exclusive owner)
Redis (sessions)        auth-service            (exclusive owner)
Redis (rate limits)     kong / auth-service     (exclusive owner)
NATS                    shared bus              all services publish/subscribe
MinIO / S3              rag-service             tool-executor (temp files)
```

---

## 12. Dependency Graph

Build and deploy order (each level can be parallelized within):

```
Level 0 (infrastructure, no code):
  PostgreSQL, Redis, Qdrant, NATS, MinIO, Keycloak, Kong, Ollama

Level 1 (core platform, no inter-service deps):
  shared library (Python package, published to internal PyPI)
  audit-service (only needs PostgreSQL)
  cost-service  (only needs PostgreSQL + NATS)

Level 2 (auth-gated services):
  auth-service  (needs: Keycloak + PostgreSQL)
  config-service (needs: PostgreSQL)

Level 3 (AI services, need LLM + auth):
  llm-proxy         (needs: Redis + Ollama/LLM provider)
  pii-service       (needs: nothing external, CPU-only)
  security-guard    (needs: nothing external, CPU-only)
  hallucination-checker (needs: llm-proxy)

Level 4 (agent-adjacent):
  memory-service    (needs: PostgreSQL + Qdrant)
  rag-service       (needs: Qdrant + llm-proxy + PostgreSQL)
  tool-executor     (needs: PostgreSQL + storage)

Level 5 (core runtime):
  agent-runner      (needs: all Level 1-4 services)

Level 6 (orchestration):
  orchestrator      (needs: agent-runner + NATS)
  notification-service (needs: NATS + email)
```

---

## 13. Implementation Sequence

Building in this order gives you a working system at the end of each phase with no dead ends.

```
PHASE 1 — Skeleton that runs (Week 1-2)
  ├── Monorepo setup (Makefile, linting, base Dockerfiles)
  ├── shared library: interfaces + config loader + adapter registry
  ├── docker-compose.yml: all infra services
  ├── agent-runner: basic run lifecycle (no tools, no LLM yet)
  ├── llm-proxy: LiteLLM wrapper, Ollama only
  └── Proof: POST /runs → agent calls Ollama → returns response

PHASE 2 — Secure (Week 3-4)
  ├── auth-service: API key + JWT validation
  ├── security-guard: injection detection (regex + basic classifier)
  ├── audit-service: immutable event log
  ├── Kong gateway: TLS + rate limiting + auth enforcement
  └── Proof: full auth flow, all calls logged to audit trail

PHASE 3 — Smart (Week 5-7)
  ├── rag-service: ingest + retrieve pipeline
  ├── memory-service: working + episodic memory
  ├── tool-executor: tool registry + first 5 built-in tools
  ├── llm-proxy: model routing + semantic cache
  └── Proof: agent uses RAG context + memory across sessions

PHASE 4 — Safe (Week 8-9)
  ├── pii-service: Presidio integration, all masking actions
  ├── hallucination-checker: faithfulness + self-consistency
  ├── cost-service: token ledger + budget enforcement
  └── Proof: PII is masked, hallucinations blocked, budget enforced

PHASE 5 — Scale (Week 10-12)
  ├── orchestrator: multi-agent DAG engine
  ├── notification-service: HITL + webhooks
  ├── SDK (TypeScript): client library published
  ├── Cloud adapters: AWS set (Bedrock, RDS, S3, SQS, Cognito, etc.)
  └── Proof: multi-agent workflow, SDK works, one-line swap to AWS

PHASE 6 — Enterprise (Week 13-16)
  ├── Multi-tenancy: full isolation enforcement
  ├── White-labeling: custom domain + brand config
  ├── Cloud adapters: Azure + GCP sets
  ├── Compliance: GDPR erasure, audit export, data residency
  └── Proof: two tenants isolated, deploy on Azure, all controls pass
```

---

*System Design Version: 1.0 | Companion: AGENTIC_AI_ARCHITECTURE.md*
