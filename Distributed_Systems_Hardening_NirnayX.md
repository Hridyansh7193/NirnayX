# Distributed Systems Spec: NirnayX Resiliency

## 🌊 Traffic Spike Management

### 1. Backpressure Implementation
- **Mechanism**: The FastAPI `submit_case` endpoint checks the Redis queue length before accepting a task.
- **Rule**: If `redis_queue_length > 5000`, the API returns `429 Cloud Overload`. This protects the system from "Cascade Failure."

### 2. Circuit Breaker for LLM API
- **Tool**: Use a library like `resilience4j` or a custom logic.
- **Rule**: If 5% of LLM calls fail in a 1-minute window, **Trip the Circuit**. 
- **Action**: Stop processing NEW deliberation tasks but continue processing EXISTING ones until the API stabilizes.

---

## 💾 Data Consistency (Jury -> Ledger)

### 3. The "State Machine" Pattern
Cases must move through strict phases:
1. `SUBMITTED`
2. `QUEUED` (Worker picked it up)
3. `DELIBERATING` (Agents are talking)
4. `FINALIZING` (Aggregation in progress)
5. `VERDICT_READY` (Audit log written AND verdict stored)

**Rule**: Any failure in phase 5 must rollback BOTH the verdict and the audit log to prevent "Ghost Decisions."

---

## 🛠️ Worker Strategy: "Domain Sharding"

To prevent a single domain (like a "Legal" surge) from killing the system:
- **Default Queue**: Standard business cases.
- **Critical Queue**: Healthcare/High-Stakes cases.
- **Reserved Workers**: Always keep 20% of workers reserved for the `Critical Queue` to ensure life-saving or high-priority decisions are never stuck behind a mass-submission of low-priority business cases.
