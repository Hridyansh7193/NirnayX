# Security Hardening: NirnayX Platform

## 🛡️ Phase 1: Authentication & Authorization

### 1.1 Secure JWT Configuration
- **Issue**: Standard HS256 secrets are prone to brute-force if not rotated.
- **Fix**: 
  - Switch to **EdDSA or RS256** signatures.
  - Implement **Refresh Tokens** stored in `HttpOnly` cookies.
  - Set Short TTL for access tokens (15 minutes).

### 1.2 Granular RBAC (Role-Based Access Control)
- **Roles**: `User`, `Reviewer`, `Admin`, `Auditor`.
- **Implementation**: FastAPI dependencies (`check_role("reviewer")`) on sensitive endpoints like `/override` and `/rl/telemetry`.

---

## 🏗️ Phase 2: AI & ML Integrity (Guardrails)

### 2.1 Prompt Injection Sanitization
- **Risk**: Manipulation of Juror Agents through malicious case descriptions.
- **Strategy**:
  - Use a **Pre-Evaluation Filter** (e.g., NeMo Guardrails) to detect adversarial intent.
  - Define "System Constraints" at the API provider level (e.g., OpenAI/Anthropic "System Message" purity).

### 2.2 Blind Deliberation Isolation
- **Fix**: Ensure the Celery worker fetches each agent's evaluation in a separate, isolated task. No agent's output should be visible to another during the deliberation phase.

---

## 📊 Phase 3: Infrastructure & Data Protection

### 3.1 Rate Limiting (Redis)
- **Target**: `POST /api/v1/cases/submit` and `/clone`.
- **Logic**: 
  - Max 5 submissions per minute per user.
  - Max 100 simulations per organization per day.

### 3.2 Immutability of the Audit Ledger
- **DB Permission Script**:
  ```sql
  -- Run as superuser to lock down the audit table
  REVOKE UPDATE, DELETE ON audit_log FROM nirnayx_app_user;
  GRANT SELECT, INSERT ON audit_log TO nirnayx_app_user;
  ```

### 3.3 Data Masking in Logs
- **Fix**: Implement a utility to mask PII (Emails, Names, etc.) in the `details` JSONB field of the Audit Log before it hits the database.
