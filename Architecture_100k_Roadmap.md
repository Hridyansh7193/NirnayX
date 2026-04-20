# Architectural Roadmap: NirnayX 100k

## 📉 Migration & Portability Strategy

### 1. The Expand-Contract Migration Pattern
To support 100,000 users without downtime:
- **Phase 1**: Add new version of the column/table.
- **Phase 2**: Backend writes to BOTH old and new locations.
- **Phase 3**: Backfill old data to new format in small chunks (1000 rows at a time).
- **Phase 4**: Switch reads to New location.
- **Phase 5**: Delete old location.

### 2. Standardized Decision Export (SDE)
Create a utility today that exports a case and its full deliberation history into a **Flat JSON Manifest**. This ensures portability and allows for cold-storage (moving old cases to S3 while keeping them readable).

---

## 🛠️ The "De-Locking" Design Checklist

| Component | Current Implementation | "De-Locked" Alternative | Lock-in Level |
| :--- | :--- | :--- | :--- |
| **AI Provider** | Hardcoded OpenAI/Mock | **Model-Agnostic Adapter** | High -> Low |
| **Audit Log** | Main DB Table | **Events-as-Ledger (Kafka)** | Med -> Low |
| **RL State** | Postgres Tables | **Standard Tensors (ONNX)** | Med -> Low |
| **Auth** | JWT / DB User | **OIDC (Okta/Auth0)** | Med -> Low |

---

## 🚀 Infrastructure Shifting Plan

### Stage 1: (Current) Monolithic Worker
- One Celery worker handles everything.
- **Limit**: CPU saturation at ~500 concurrent evaluations.

### Stage 2: (10k Users) Sharded Workers
- Workers split by Domain (Legal-Worker, HR-Worker).
- **Benefit**: Isolate failure. If HR agents are slow, Legal decisions stay fast.

### Stage 3: (100k Users) Distributed Event Mesh
- Decisions move through a pipeline of micro-services.
- **Benefit**: Horizontal scale. You can run 100 "Ethics Agents" containers independently of the "Risk Analyst" containers.
