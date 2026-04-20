# Production Architecture Spec: NirnayX @ 10,000 DAU

## 1. High-Scale Normalized Schema

### Operations Schema
| Table | Description | Partitioning Key |
| :--- | :--- | :--- |
| `cases` | Header information, status, and domain mapping. | `domain_id` |
| `case_context` | Large text payloads (description, extracted facts). Separate from header for shallow list performance. | N/A |
| `agent_jury_evals` | The "Blind" reasoning. | `case_id` (Hash) |
| `verdicts_final` | Aggregated consensus scores and threshold flags. | `created_at` |
| `rl_skill_snapshots` | Versioned agent weights per domain. Key for reproducible simulations. | `domain_key` |

### Compliance & Ledger Schema (Immutable)
| Table | Description | Stability Rule |
| :--- | :--- | :--- |
| `audit_ledger` | Every action. Uses `jsonb` for payload flexibility. | Partitioned by `range(created_at)`. |
| `audit_signatures` | Cryptographic hashes of ledger blocks to ensure tamper-evidence. | Non-updatable. |

---

## 2. Bottlenecks & Weaknesses

### ⚠️ Risk: The "Feedback Avalanche"
When a user submits feedback on a year-old case, the RL engine must update the "current" weight. If the system is normalized, a naive `UPDATE weights SET score = x` will block new evaluations.
*   **Solution**: Use a **Snapshotted State**. Agents read weight from `v_latest_weights`, while RL writes to `weight_history`.

### ⚠️ Risk: Read Latency on Dashboard
A dashboard showing "Avg Confidence" or "Agent Bias" across 1,000,000 cases will be slow if it performs `AVG()` on the live `evaluations` table.
*   **Solution**: **Materialized Views** refreshed every 10 minutes, or a separate **Elasticsearch/ClickHouse** instance for analytics.

### ⚠️ Risk: Write Amplification
Inserting one `case` creates:
- 1 Case record
- 5 Agent records
- 1 Verdict record
- 8 Audit records
- 10 Entity records
**Total: 25 Writes per single decision.**
*   **Solution**: **Batch Inserts**. Push "Processing" events to a worker (Celery/Arq) to handle the 24 supplementary writes outside the user's request-response cycle.

---

## 3. Stability Optimizations

### I. Multi-Tenancy Strategy
Instead of a simple `user_id`, implement **`organization_id`** indexed at the top level of every table. This allows for horizontal sharding (moving one big org to a separate DB cluster) without re-architecting the code.

### II. The "Lead-Free" RL Loop
Implement a **Weight Buffer**. The system should not update the "Main" weight for every single feedback. Instead, buffer feedback and run a **Daily Gravity Update**. This prevents oscillation in the AI's "personality" and drastically reduces write pressure.

### III. Ingestion Pre-Process
Move NLP/Entity extraction to a **Pre-Commit Hook**. Don't write the case until the entities are extracted. This ensures the DB never contains "Broken/Unstructured" cases that the agents can't process.

### IV. Indexing Suggestions
*   `CREATE INDEX idx_eval_case_agent ON agent_jury_evals (case_id, agent_id);` (Covering index for fast report generation).
*   `CREATE INDEX idx_verdict_needs_review ON verdicts_final (requires_human_review) WHERE requires_human_review = true;` (Minimize scan size for human-review queues).
