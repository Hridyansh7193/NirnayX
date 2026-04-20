# Cloud Cost Strategy: NirnayX Platform

## 💰 Resource Allocation & Spend

### 1. Compute (FastAPI & Celery)
- **100 DAU**: Single t3.medium instance.
- **10k DAU**: Auto-scaling group of 5-10 c6g.large instances.
- **Optimization**: Use **ARM64 (Graviton)** instances to save ~20% on compute cost.

### 2. Database (RDS PostgreSQL)
- **Driver**: High IOPS due to Audit Logging.
- **Optimization**: Batch audit logs in Redis and write to DB once per minute instead of once per action. This can reduce IOPS costs by up to 80%.

### 3. AI Inference (The "Decider" Cost)
- **Tier 1 (Classify/Extract)**: Model: `GPT-4o-mini` or `Llama-3-8B`. Cost: Near Zero.
- **Tier 2 (Persona Deliberation)**: Model: `Claude 3.5 Sonnet`. Cost: High.
- **Optimization**: 
  - **Compressed Personas**: Use Vector Embeddings for "Reasoning Priors" instead of raw text prompts.
  - **Prompt Caching**: Active headers to avoid re-billing for unchanged system prompts.

---

## 📉 Cost Optimization Roadmap

| Feature | Savings | Implementation Effort |
| :--- | :--- | :--- |
| **Audit Log Archiving** | 30% (Storage) | Low |
| **Hierarchical LLM Routing** | 50% (Inference) | Medium |
| **Redis Result Caching** | 20% (Inference) | Low |
| **Spot Instance Workers** | 60% (Compute) | Medium |

---

## ⚠️ Financial Guardrails (Pro-Active Alerts)
1. **Decision Budget per Org**: Set a hard-cap on how many decisions a company can run per month.
2. **Token Response Limit**: Set `max_tokens` for Juror Agents to 1,000 to prevent expensive "infinite reasoning" loops.
3. **IOPS Burst Alert**: Monitor DB writes specifically to detect bot activity or malicious case cloning.
