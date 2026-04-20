# NirnayX Unified Architecture Specification
**Author:** Principal Systems Architect
**Target Scale:** 100k+ DAU (Multi-Tenant Enterprise)

---

## 1. 🔧 CONTRADICTION RESOLUTION (MANDATORY)

#### Issue A: Immutable Audit Log vs Rollback Contradiction
*   **Problem:** The system requires a tamper-evident, append-only log. However, distributed transactions occasionally drop mid-flight, and naive systems use "DELETE" to roll back partial state. 
*   **Decision:** **Compensating Event (Event Sourcing) Pattern.** Let the database be the ultimate source of truth, enforcing append-only via DB-level constraints.
*   **Fix:** The Audit Log acts as a Write-Ahead Log (WAL). Before an action executes, log `DELIBERATION_STARTED`. If the transaction succeeds, log `DELIBERATION_COMPLETED`. If the transaction rolls back, log a compensating event: `DELIBERATION_FAILED_ROLLED_BACK`. No `UPDATE` or `DELETE` commands are *ever* issued to the `audit_logs` table.

#### Issue B: 500ms RL Update SLA vs Daily Batch
*   **Problem:** Real-time (500ms) RL updates for 100k DAUs create catastrophic database locks, write-amplification (updating 5 agents per feedback), and mathematical instability in the Policy Gradient.
*   **Decision:** **Daily Batch (Gravity Update).** Abandon the 500ms SLA. It is architecturally lethal and mathematically unsound for RL.
*   **Fix:** Feedback submissions are appended to a high-throughput event stream (e.g., Kafka or Redis Streams) acknowledging receipt to the user in <50ms. A nightly cron-job consumes this buffer, calculates the gradient using batch optimization, and writes a new immutable `RL_Policy_Snapshot`.

#### Issue C: Batch Write Failure → Undefined State
*   **Problem:** If writing 5 evaluations, 1 verdict, and updating case status fails midway, the database is left in a "Ghost State" where agents deliberated but the case is stuck.
*   **Decision:** **Strong Consistency via Postgres Unit of Work.**
*   **Fix:** The Celery worker holding the deliberation result aggregates everything in memory. It initiates **one** database transaction. It writes the evaluations, the verdict, updates the case to `VERDICT_READY`, and writes the audit log. If any step fails, the transaction rolls back, reverting the DB state to `DELIBERATING` instantly. The Celery task then safely retries.

#### Issue D: Token Limit (1000) breaks reasoning chains
*   **Problem:** A hard 1000-token cap truncates high-stakes legal/healthcare reasoning, silently breaking the aggregation logic.
*   **Decision:** **Domain-Aware Dynamic Quotas.**
*   **Fix:** Drop the global token cap. Enforce `max_tokens` at the `DomainProfile` level. 
    *   `Healthcare/Legal`: 4000 tokens per agent.
    *   `Business/HR`: 1500 tokens per agent. 
    *   Agent outputs must be forced into strict **JSON Schema structure**, heavily favoring dense bullet points over sprawling narrative prose.

#### Issue E: NeMo Guardrails dependency not in stack
*   **Problem:** PRD assumes heavy Python/C++ NeMo infra, but we are optimizing for a lightweight FastAPI stack. It breaks deployment simplicity.
*   **Decision:** **Drop NeMo. Implement an LLM-as-a-Judge Router.**
*   **Fix:** Deploy a fast, cheap pre-flight model (Llama-3-8B or GPT-4o-mini). Cases must pass a synchronous `SanitizeInput()` prompt layer that outputs `{"is_safe": true/false}`. If false, the case is rejected instantly with a 400 error.

---

## 2. 🧱 FINAL SYSTEM DESIGN (CLEAN VERSION)

*   **State Machine (Strictly Enforced):**
    `DRAFT` → `INGESTING` → `QUEUED` → `DELIBERATING` → `FINALIZING` → `VERDICT_READY` → `CLOSED`
*   **Data Consistency Model:** 
    *   *Operational Truth (Cases, Verdicts):* **Strong Consistency** (ACID Postgres Transactions).
    *   *AI Analytics & RL Policy:* **Eventual Consistency** (Batch-processed overnight).
*   **Audit Logging Model:** Write-Ahead Log (WAL) pattern. Append-only table with permissions physically stripped at the DB level (`REVOKE UPDATE, DELETE ON audit_logs FROM app_user;`).

---

## 3. 🗄️ DATA CONSISTENCY & FAILURE HANDLING

*   **Partial Failures:** Handled by the Celery retry mechanism with exponential backoff + jitter. If the LLM API drops on agent 4/5, the entire deliberation block is aborted and re-queued. LLM calls are stateless and safe to retry.
*   **Idempotency Strategy:** The Celery Task ID is deterministically derived from the `case_id` and `case_version`. If a message is delivered twice, the worker checks `SELECT status FROM cases WHERE id = X FOR UPDATE`. If `status >= VERDICT_READY`, the worker drops the task instantly (Exactly-Once processing semantics via DB locks).
*   **Ghost States Prevention:** The `FOR UPDATE` row lock guarantees a case cannot be processed by two workers simultaneously. 

---

## 4. 🧠 RL SYSTEM CORRECTION

*   **Final RL Update Mechanism:** Epoch-based batch processing.
*   **Feedback Validation (Anti-Gaming):**
    *   *Sybil Protection:* Ignore feedback from users with a variance of `0` (giving everything 5 stars or 1 star).
    *   *Weight Clamping:* Agent weights are hard-clamped between `0.05` and `MaxDomainWeight (e.g., 0.35)`. An agent can never "die" (weight 0) or become a dictator (weight > 0.51).
*   **Divergence Safeguards:** Moving Average constraint. A nightly batch update is bounded by a `max_shift` of `5%`. If the calculated gradient demands a `15%` shift, it caps at `5%` to prevent sudden catastrophic personality changes.

---

## 5. 🔐 SECURITY FIXES (CONCRETE)

*   **Row-Level Security (RLS in Postgres):**
    Multi-tenant data leaks are mathematically prevented at the database layer.
    ```sql
    ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_policy ON cases 
    USING (organization_id = current_setting('app.current_org_id')::uuid);
    ```
    FastAPI passes the org ID to Postgres via `db.execute(text("SET LOCAL app.current_org_id = :org"), {"org": user_org_id})` at the start of every request.
*   **Agent Isolation Guarantees:** Agents are evaluated using `asyncio.gather` on stateless HTTP calls to the LLM provider. They share absolutely no memory context. 

---

## 6. ⚙️ INFRASTRUCTURE CORRECTIONS

*   **Redis Dual-Use Issue:** Running Celery (eviction tolerant) and Caching (eviction hostile) on the same Redis cluster is a ticking time bomb.
    *   *Fix:* Stand up 2 isolated containers: `redis-queue:7` (maxmemory policy noeviction) and `redis-cache:7` (maxmemory policy allkeys-lru).
*   **Worker → Event Mesh Migration (Evolution Plan):**
    *   *v1 (Now):* Celery + Redis. Maxes out at ~5,000 concurrent cases.
    *   *v2 (Scale):* Swap Celery for **Apache Kafka** / **Redpanda**. Introduce discrete K8s deployments mapping to Kafka topics (`topic.legal_deliberation`, `topic.audit_log`).
    *   *v3 (Global):* Move DB from Postgres to distributed CockroachDB. 

---

## 7. 💰 COST-SAFE ARCHITECTURE

*   **Cost Guardrails (Hard Caps):** Every tenant has a `monthly_token_budget` cached in Redis. Middleware checks this cache on `POST /cases/submit`. If exceeded, `402 Payment Required`.
*   **Domain-Aware LLM Routing:**
    *   Routing/Extraction Phase: Evaluated by `Llama-3-8B` (~$0.20 / 1M tokens).
    *   Core Deliberation Phase: Evaluated by `Claude-3.5-Sonnet` (~$3.00 / 1M tokens).

---

## 8. 🧪 MISSING SYSTEMS (NEW ADDITIONS)

*   **Hallucination Detection Layer (The Cross-Examiner):** 
    After the 5 agents output their reasoning, a specialized, deterministic semantic-check agent compares the citations in the reasoning block strictly against the `key_facts` JSON. Any evaluation citing non-existent facts has its confidence artificially set to `0.0`.
*   **Model Drift Monitoring:** 
    Calculate the **Jensen-Shannon Divergence** of each agent's verdict distribution on a 30-day rolling window. Alerts trigger if an agent historically voting 40% `Approve` suddenly drifts to 80% `Approve` across the network.
*   **Observability Metrics (Datadog/Prometheus):**
    1.  `queue_latency_seconds` (Alert if > 30s)
    2.  `llm_token_generation_rate` (Alert if anomalous drop implies provider outage)
    3.  `db_transaction_duration_ms` (Alert if > 500ms)
