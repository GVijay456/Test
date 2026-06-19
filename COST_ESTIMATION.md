# Cost Estimation — Agentic AI Platform

> All prices are 2025–2026 estimates. Verify current rates before budgeting.  
> AWS us-east-1 on-demand pricing used as baseline. Azure/GCP within ±15%.  
> Reserved instances / committed-use discounts reduce compute by 30–60%.

---

## TL;DR — Monthly Cost by Scale

| Tier | Runs/month | Concurrent | Infrastructure | LLM APIs | Total/month |
|------|-----------|------------|---------------|---------|-------------|
| Local dev | — | 1 | $0 (Docker) | $20–50 | **$20–50** |
| Staging | ~1k | 10 | $1,300 | $50 | **$1,350** |
| Startup | 50k | 50 | $3,500 | $1,000–3,000 | **$4,500–6,500** |
| Growth | 500k | 500 | $10,500 | $5,000–15,000 | **$15,500–25,500** |
| Scale | 5M | 5,000 | $55,000 | $15,000–60,000 | **$70,000–115,000** |

> LLM API range = cheapest (self-hosted / mini models) to premium (GPT-4o / Claude Sonnet)

---

## 1. Infrastructure Cost Breakdown

### 1.1 Local Development (Zero infrastructure cost)

```
docker-compose up -d
```

All services run on your laptop. Only cost is your own API key usage while testing.
- Estimate: $20–50/month in LLM API calls during development
- Requirement: 16GB RAM minimum, 32GB recommended

---

### 1.2 Staging Environment (~$1,300/month)

| Component | Instance | Count | Monthly |
|-----------|----------|-------|---------|
| EKS control plane | — | 1 | $73 |
| Application nodes | m5.xlarge (4vCPU/16GB) | 3 | $420 |
| PostgreSQL (RDS) | db.r6g.large (2vCPU/16GB) | 1 | $175 |
| Redis (ElastiCache) | cache.r7g.large (2vCPU/13GB) | 1 | $121 |
| NATS JetStream | m5.large (2vCPU/8GB) | 2 | $140 |
| Qdrant vector store | m5.xlarge | 2 | $280 |
| Monitoring stack | m5.large | 1 | $70 |
| Load balancer | ALB | 1 | $20 |
| **Total** | | | **~$1,300** |

---

### 1.3 Production — Startup (50k runs/month, ~$3,500/month infra)

| Component | Instance | Count | Monthly |
|-----------|----------|-------|---------|
| EKS control plane | — | 1 | $73 |
| Application nodes | m5.2xlarge (8vCPU/32GB) | 6 | $1,680 |
| PII service (Presidio model ~2GB) | m5.2xlarge | 1 | $280 |
| PostgreSQL primary + replica | db.r6g.xlarge (4vCPU/32GB), Multi-AZ | 1 pair | $700 |
| Redis | cache.r7g.xlarge (4vCPU/26GB) | 1 | $243 |
| NATS JetStream | m5.large | 3 | $210 |
| Qdrant | m5.xlarge | 3 | $420 |
| Vault | m5.large | 2 | $140 |
| Monitoring (Grafana + Tempo + Loki) | m5.xlarge | 1 | $140 |
| Load balancer, NAT gateway | ALB + NAT | — | $60 |
| S3 storage (100GB) | — | — | $2 |
| Data transfer (~100GB out) | — | — | $9 |
| **Total** | | | **~$3,960** |

Rounded budget: **$4,000–4,500/month** (includes headroom for spikes)

---

### 1.4 Production — Growth (500k runs/month, ~$10,500/month infra)

| Component | Instance | Count | Monthly |
|-----------|----------|-------|---------|
| EKS control plane | — | 1 | $73 |
| Application nodes | m5.2xlarge | 12 | $3,360 |
| PII service (dedicated, CPU-optimized) | m5.4xlarge (16vCPU/64GB) | 2 | $1,120 |
| PostgreSQL (Multi-AZ) | db.r6g.2xlarge (8vCPU/64GB) | 1 pair | $1,400 |
| Redis cluster | cache.r7g.2xlarge (8vCPU/52GB) | 2 nodes | $970 |
| NATS JetStream | m5.2xlarge | 3 | $840 |
| Qdrant cluster | m5.2xlarge | 5 | $1,400 |
| Vault cluster | m5.large | 3 | $210 |
| Monitoring | m5.2xlarge | 2 | $560 |
| Load balancer, NAT, data transfer | — | — | $350 |
| S3 (1TB) | — | — | $23 |
| **Total** | | | **~$10,310** |

Rounded budget: **$11,000–12,000/month** (with headroom)

---

### 1.5 Production — Scale (5M runs/month, ~$55,000/month infra)

| Component | Instance | Count | Monthly |
|-----------|----------|-------|---------|
| EKS control plane (3 clusters: prod, DR, regional) | — | 3 | $220 |
| Application nodes | m5.4xlarge (16vCPU/64GB) | 40 | $22,400 |
| PII service (dedicated) | m5.4xlarge | 10 | $5,600 |
| PostgreSQL (Aurora, 3 read replicas) | db.r6g.4xlarge | 4 | $8,000 |
| Redis cluster | cache.r7g.2xlarge | 10 | $4,850 |
| NATS JetStream | m5.4xlarge | 5 | $2,800 |
| Qdrant cluster | m5.4xlarge | 10 | $5,600 |
| Vault | m5.xlarge | 5 | $700 |
| Monitoring + SIEM | m5.4xlarge | 4 | $2,240 |
| CDN (CloudFront) | — | — | $200 |
| Load balancers, NAT, transfer (~10TB out) | — | — | $1,600 |
| S3 (10TB) | — | — | $230 |
| **Total** | | | **~$54,440** |

Rounded budget: **$55,000–60,000/month**

---

## 2. LLM API Costs

### 2.1 Cost Per Agent Run

A typical agent run = **3 LLM calls** × (4,000 input + 800 output tokens) = 12,000 input + 2,400 output tokens

| LLM Provider | Model | Input $/1M | Output $/1M | Cost per run | Notes |
|-------------|-------|-----------|------------|-------------|-------|
| OpenAI | GPT-4o | $2.50 | $10.00 | **$0.054** | Best quality, priciest |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 | **$0.0032** | Great value for simple tasks |
| OpenAI | o3-mini | $1.10 | $4.40 | **$0.024** | Reasoning tasks |
| Anthropic | Claude Sonnet 4.6 | $3.00 | $15.00 | **$0.072** | Excellent for agents |
| Anthropic | Claude Haiku 4.5 | $0.25 | $1.25 | **$0.006** | Very fast, cheap |
| AWS Bedrock | Llama 3.1 70B | $2.65 | $2.65 | **$0.038** | Open weights, managed |
| AWS Bedrock | Llama 3.1 8B | $0.22 | $0.22 | **$0.0032** | Cheap, decent quality |
| Groq | Llama 3.1 70B | $0.59 | $0.79 | **$0.009** | Very fast inference |
| Together AI | Llama 3.1 70B | $0.88 | $0.88 | **$0.013** | Good price/performance |
| Google Vertex | Gemini 1.5 Pro | $1.25 | $5.00 | **$0.027** | Long context (1M tokens) |
| Self-hosted | Llama 3.1 8B (1x A10G) | — | — | **$0.002** | At 400k runs/month throughput |
| Self-hosted | Llama 3.1 70B (2x A100) | — | — | **$0.030** | At 200k runs/month throughput |

### 2.2 Monthly LLM API Cost at Scale

| Scale | Runs/month | All GPT-4o | 50/50 mix (GPT-4o + mini) | 80% mini + 20% GPT-4o | All self-hosted (8B) |
|-------|-----------|-----------|--------------------------|----------------------|-------------------|
| Startup | 50k | $2,700 | $1,400 | $600 | $100 (GPU included) |
| Growth | 500k | $27,000 | $14,000 | $6,000 | $885 (GPU) + $1,100 API |
| Scale | 5M | $270,000 | $140,000 | $60,000 | $8,850 (10x GPU) |

> Smart routing (route simple tasks to mini models, complex to GPT-4o) typically achieves 70–80% cost reduction with minimal quality loss.

### 2.3 Embedding Costs (for RAG)

| Provider | Model | Price/1M tokens | Cost per 1k docs (1MB avg) |
|----------|-------|----------------|--------------------------|
| OpenAI | text-embedding-3-small | $0.02 | **$1.00** |
| OpenAI | text-embedding-3-large | $0.13 | **$6.50** |
| AWS Bedrock | Titan Embed G1 | $0.10 | **$5.00** |
| Cohere | embed-v3 | $0.10 | **$5.00** |
| Self-hosted | BGE-M3 / Nomic-Embed (CPU) | ~$0 | **$0** (pay for EC2) |

Embedding happens once at ingest. Query embedding is negligible (< 1k tokens per query).

---

## 3. Self-Hosted Model GPU Costs

### 3.1 Model Size vs GPU Requirements

| Model | Parameters | Precision | VRAM needed | Minimum GPU | Recommended GPU |
|-------|-----------|----------|------------|------------|----------------|
| Llama 3.2 1B / Phi-3-mini | 1–3B | fp16 | 2–6GB | T4 (16GB) | T4 |
| Llama 3.1 8B / Mistral 7B | 7–8B | fp16 | 14–16GB | T4 | A10G (24GB) |
| Llama 3.1 8B | 8B | 4-bit quant | 5GB | T4 | T4 |
| Llama 3.1 70B | 70B | 4-bit quant | 38GB | A100 40GB | A100 80GB |
| Llama 3.1 70B | 70B | fp16 | 140GB | 2x A100 80GB | 2x A100 80GB |
| Llama 3.1 405B | 405B | 4-bit quant | 210GB | 3x A100 80GB | H100 cluster |

### 3.2 GPU Instance Pricing (AWS, on-demand)

| Instance | GPU | VRAM | vCPU | RAM | $/hour | $/month | Good for |
|----------|-----|------|------|-----|--------|---------|---------|
| g4dn.xlarge | 1x T4 | 16GB | 4 | 16GB | $0.526 | $384 | Dev, 3B models |
| g4dn.2xlarge | 1x T4 | 16GB | 8 | 32GB | $0.752 | $549 | 8B 4-bit |
| g5.xlarge | 1x A10G | 24GB | 4 | 16GB | $1.006 | $734 | 8B fp16 |
| g5.2xlarge | 1x A10G | 24GB | 8 | 32GB | $1.212 | $885 | 8B fp16 (recommended) |
| g5.12xlarge | 4x A10G | 96GB | 48 | 192GB | $5.672 | $4,141 | 70B 4-bit |
| p3.2xlarge | 1x V100 | 16GB | 8 | 61GB | $3.060 | $2,234 | 8B fp16 (older) |
| p4d.24xlarge | 8x A100 40GB | 320GB | 96 | 1.1TB | $32.77 | $23,922 | 70B fp16, 405B 4-bit |
| p4de.24xlarge | 8x A100 80GB | 640GB | 96 | 1.1TB | $40.96 | $29,901 | 405B fp16 |
| p5.48xlarge | 8x H100 80GB | 640GB | 192 | 2TB | $98.32 | $71,777 | Largest models |

### 3.3 Alternative GPU Providers (significantly cheaper than AWS)

| Provider | GPU | $/hour | $/month | Notes |
|----------|-----|--------|---------|-------|
| Lambda Labs | A10 (24GB) | $0.75 | $547 | Reliable, good for inference |
| Lambda Labs | A100 40GB | $1.29 | $941 | Best non-cloud price |
| Lambda Labs | H100 80GB | $2.49 | $1,817 | Excellent H100 price |
| CoreWeave | A100 80GB | $2.23 | $1,628 | Good reliability |
| RunPod (on-demand) | A10G | $0.54 | $394 | Good for variable load |
| RunPod (spot) | A10G | $0.30 | $219 | 30% interruption risk |
| Vast.ai (spot) | A10G | $0.20–0.40 | $150–290 | Cheapest, variable availability |
| Together AI | — | Per token | — | Managed Llama inference, $0.88/1M |
| Fireworks AI | — | Per token | — | Fast inference, ~$0.50/1M |
| Replicate | — | Per second | — | Good for bursty workloads |

> For production self-hosted inference, Lambda Labs or CoreWeave offer the best price-reliability ratio. Vast.ai is great for dev/fine-tuning.

### 3.4 Self-Hosted Throughput Estimates (using vLLM)

| Model | GPU | Throughput | Cost/month | Cost per 1k runs | Break-even vs API |
|-------|-----|-----------|-----------|-----------------|------------------|
| Llama 3.1 8B | 1x A10G (Lambda) | ~200 req/min | $547 | $0.0019 | > 50k runs/month vs Bedrock |
| Llama 3.1 8B | 1x A10G (AWS) | ~200 req/min | $885 | $0.0031 | > 80k runs/month vs Bedrock |
| Llama 3.1 70B 4-bit | g5.12xlarge | ~30 req/min | $4,141 | $0.095 | > 110k runs vs Bedrock 70B |
| Llama 3.1 70B fp16 | 2x A100 (Lambda) | ~20 req/min | $1,882 | $0.065 | > 50k runs vs Bedrock 70B |

> Rule of thumb: self-hosted pays off at > 50k–100k runs/month for 8B models. For 70B models, managed APIs (Groq, Together) are often cheaper than self-hosted at medium scale.

---

## 4. Model Development / Fine-Tuning Costs

### 4.1 Do You Need to Fine-Tune?

| Use Case | Recommendation | Reason |
|----------|---------------|--------|
| General agent tasks | No fine-tuning needed | GPT-4o / Llama 3.1 70B are sufficient |
| Domain-specific terminology | RAG is cheaper and faster | Add documents to knowledge base |
| Specific output format | Prompt engineering first | System prompt + few-shot examples |
| Consistent persona/tone | Prompt engineering | Few-shot examples in system prompt |
| Outperform base model on a narrow task | Fine-tune | e.g., contract clause extraction, medical coding |
| Cut costs on high-volume narrow task | Fine-tune small model | e.g., 8B model for classification |
| Custom tool calling style | Fine-tune | If base model tool calling is inconsistent |

**Recommendation for this platform:** Start without fine-tuning. Add RAG + good system prompts first. Fine-tune only when you have > 1,000 labeled examples of what the model gets wrong.

### 4.2 Fine-Tuning Cost Breakdown

#### Supervised Fine-Tuning (SFT) — Most Common

| Model | Dataset size | GPU | Hours | Cost (Lambda) | Cost (AWS) |
|-------|-------------|-----|-------|--------------|-----------|
| Llama 3.1 8B | 1k examples | 1x A10G | 1h | $0.75 | $1.21 |
| Llama 3.1 8B | 10k examples | 1x A10G | 4h | $3.00 | $4.85 |
| Llama 3.1 8B | 100k examples | 1x A10G | 24h | $18 | $29 |
| Llama 3.1 70B | 10k examples | 8x A100 40GB | 8h | $82 | $262 |
| Llama 3.1 70B | 100k examples | 8x A100 40GB | 48h | $495 | $1,573 |

> LoRA / QLoRA fine-tuning — reduces memory by 4–8x, minimal quality loss.  
> Budget 5–20 training runs for hyperparameter search. Total: $100–500 for an 8B model.

#### RLHF / DPO (Preference Alignment)

| Stage | Cost estimate | Notes |
|-------|-------------|-------|
| Data collection (human feedback) | $0.05–0.15 per label | Via Scale AI, Labelbox, or your users |
| 1,000 preference pairs | $50–150 | Minimum viable dataset |
| 10,000 preference pairs | $500–1,500 | Good quality alignment |
| DPO training (Llama 3.1 8B, 10k pairs) | $5–20 | Single training run |
| Full RLHF pipeline | $500–5,000 | Multiple rounds + reward model training |

#### Managed Fine-Tuning Services (no GPU setup needed)

| Service | Model | Price | Notes |
|---------|-------|-------|-------|
| OpenAI | GPT-4o-mini | $25/1M tokens trained | Easy, expensive at scale |
| Together AI | Llama 3.1 8B | $0.50–3/GPU-hour | Self-serve, good tooling |
| AWS Bedrock | Llama 3.1 8B/70B | Per token | Easiest for AWS shops |
| Replicate | Any model | Per second | Good for experimentation |

**Recommended path:**  
1. Start with Together AI or Replicate for experiments ($10–50/run)  
2. Move to Lambda Labs or CoreWeave for production fine-tuning ($50–500/run)  
3. Self-host training only if you're doing > 1 fine-tuning run/week

---

## 5. Real Cost Scenarios

### Scenario A — B2B SaaS startup, Year 1

**Setup:** 20 enterprise customers, 5k–10k agent runs/month each, total 100k runs/month.  
**Model strategy:** 60% Claude Haiku (simple tasks), 30% Sonnet (complex reasoning), 10% GPT-4o (coding).

| Item | Monthly cost |
|------|-------------|
| Infrastructure (startup tier) | $4,000 |
| LLM APIs (blended ~$0.012/run) | $1,200 |
| Embedding (RAG queries) | $50 |
| Object storage (document ingestion) | $25 |
| Monitoring / logging | $100 |
| **Total** | **$5,375/month** |

Revenue needed to break even at 30% GM: **$18,000/month ARR** (~$900 per customer/month)

---

### Scenario B — Internal platform team, Fortune 500

**Setup:** 500 internal users, 1k runs/user/month = 500k runs/month.  
**Model strategy:** 70% Llama 3.1 8B self-hosted (A10G), 30% GPT-4o for complex tasks.

| Item | Monthly cost |
|------|-------------|
| Infrastructure (growth tier) | $11,000 |
| GPU hosting for Llama 8B (2x g5.2xlarge) | $1,770 |
| GPT-4o API (150k runs × $0.054) | $8,100 |
| Llama 8B self-hosted (350k runs, $0.003) | ~$0 (GPU included above) |
| Embedding, storage, transfer | $300 |
| **Total** | **$21,170/month** |

Cost per employee per month: **$42** — comparable to GitHub Copilot pricing.

---

### Scenario C — Multi-tenant platform, 5M runs/month at scale

**Setup:** 500 SMB tenants, mix of models, auto-routing by cost tier.  
**Model strategy:** 50% Groq Llama 70B ($0.009/run), 30% Haiku ($0.006/run), 20% self-hosted 8B ($0.002/run).

| Item | Monthly cost |
|------|-------------|
| Infrastructure (scale tier) | $57,000 |
| Groq API (2.5M runs × $0.009) | $22,500 |
| Claude Haiku API (1.5M runs × $0.006) | $9,000 |
| Self-hosted Llama 8B (1M runs, 5x g5.2xlarge) | $4,425 |
| RAG embedding (100M docs/month) | $2,000 |
| Storage, transfer, monitoring | $3,000 |
| **Total** | **$97,925/month** |

At $0.05/run platform charge to tenants: **$250,000/month revenue**, ~$150k gross profit.

---

## 6. Cost by Cloud Provider

### Infrastructure Cost Comparison (Growth tier, 500k runs/month)

| Item | AWS | Azure | GCP |
|------|-----|-------|-----|
| Kubernetes (managed) | $73 (EKS) | $0 (AKS free) | $73 (GKE) |
| Compute (12x 8vCPU/32GB) | $3,360 | $3,480 | $3,200 |
| PostgreSQL (managed) | $1,400 (RDS) | $1,200 (Flexible Server) | $1,100 (Cloud SQL) |
| Redis (managed) | $970 (ElastiCache) | $900 (Azure Cache) | $850 (Memorystore) |
| Object storage | $23 (S3) | $20 (Blob) | $18 (GCS) |
| Load balancer | $50 | $45 | $40 |
| Data transfer out | $90 | $85 | $85 |
| **Total** | **~$5,970** | **~$5,730** | **~$5,370** |

GCP is marginally cheapest (~10%) for this profile. Azure offers AKS at no control-plane cost. AWS has the broadest managed service ecosystem.

### LLM APIs — Cloud Provider Native Models

| Cloud | Model | Price | Quality tier |
|-------|-------|-------|-------------|
| AWS Bedrock | Llama 3.1 8B | $0.22/1M | Budget |
| AWS Bedrock | Llama 3.1 70B | $2.65/1M | Mid |
| AWS Bedrock | Claude Sonnet | $3.00/1M | Premium |
| Azure OpenAI | GPT-4o-mini | $0.15/1M | Budget |
| Azure OpenAI | GPT-4o | $2.50/1M | Premium |
| GCP Vertex AI | Gemini 1.5 Flash | $0.075/1M | Budget |
| GCP Vertex AI | Gemini 1.5 Pro | $1.25/1M | Mid-premium |

---

## 7. Cost Optimization Strategies

### Immediate (no code change)

| Strategy | Savings | How |
|----------|---------|-----|
| Use smaller models for simple tasks | 60–80% | Route classification/extraction to Haiku/mini |
| Enable semantic cache | 20–40% | Repeated similar queries served from Redis |
| Reserved instances | 30–60% | Commit 1–3 years for predictable workloads |
| Spot instances for non-critical workers | 60–70% | Tool executors, batch embedding — fault tolerant |
| Use Groq/Together for Llama inference | 40–60% vs self-hosted | Skip GPU management overhead |

### Phase 3 Implementation (in-platform)

| Strategy | Savings | Mechanism |
|----------|---------|----------|
| Prompt compression | 20–30% on tokens | Remove redundant context before sending to LLM |
| Self-hosted 8B for high-volume | 50–80% vs cloud API | Break-even at ~50k runs/month |
| Tiered model routing | 40–60% | Cost-aware router: cheap → expensive only if needed |
| Batch embedding | 30–40% on embedding cost | Embed in bulk during off-peak, not per-request |
| Cache warming | 15–25% on cache miss | Pre-embed common queries in off-peak hours |

### Reserved Instance Savings (AWS)

| Commitment | Discount vs on-demand |
|-----------|----------------------|
| 1-year, no upfront | 30–35% |
| 1-year, partial upfront | 35–42% |
| 3-year, all upfront | 55–65% |

At growth scale: $10,500 → ~$6,000/month infrastructure cost with 3-year reserved.

---

## 8. One-Time Setup Costs

| Item | Estimate | Notes |
|------|---------|-------|
| Architecture design (this phase) | Done | Current work |
| Development (Phases 1–6, 24 weeks) | $200k–600k | Depends on team size/location |
| Fine-tuning initial models | $500–5,000 | Optional — only if base models insufficient |
| Security audit / pen test | $10k–30k | Recommended before enterprise launch |
| SOC 2 Type II audit | $20k–50k | Required for enterprise sales |
| Infrastructure setup (Terraform, CI/CD) | 2–4 weeks of eng time | Included in Phase 1 |

### Development Team Estimate (6-month build, Phase 1–4)

| Role | Count | Monthly cost | 6-month total |
|------|-------|-------------|--------------|
| Backend engineer (Python/AI) | 2 | $12k–18k | $144k–216k |
| Backend engineer (TypeScript/API) | 1 | $10k–15k | $60k–90k |
| DevOps / Platform engineer | 1 | $12k–16k | $72k–96k |
| AI/ML engineer | 1 | $14k–20k | $84k–120k |
| **Total (5 engineers, 6 months)** | | | **$360k–522k** |

> Offshore/nearshore teams can reduce this by 40–60% with appropriate coordination overhead.

---

## 9. Summary Recommendation by Stage

| Stage | Model strategy | Infrastructure | Est. monthly total |
|-------|--------------|---------------|-------------------|
| **MVP (first 3 months)** | Claude Haiku + GPT-4o-mini API | Docker locally + $1,300 staging | **$2,000–3,000** |
| **Pilot (months 4–6)** | Haiku/mini for 80%, Sonnet/GPT-4o for 20% | Startup tier ($4,000) | **$5,000–7,000** |
| **Growth (months 7–18)** | Add self-hosted Llama 8B + smart routing | Growth tier ($11,000) | **$15,000–25,000** |
| **Scale (18+ months)** | Self-hosted 70B + Groq + premium for top tier | Scale tier ($55,000) | **$70,000–115,000** |

**Key insight:** LLM API costs dominate at all scales. The single biggest lever is **routing cheap tasks to cheap models** — this alone can cut 60–80% of LLM spend with minimal quality impact.

---

*Prices as of 2025–2026. All figures are estimates — validate against current provider pricing pages before budgeting.*  
*See also: PLAN.md for implementation timeline, SYSTEM_DESIGN.md for component swappability.*
