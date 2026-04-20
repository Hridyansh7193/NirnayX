# Graph Report - C:\Users\hridy\Desktop\NirnayX  (2026-04-20)

## Corpus Check
- 36 files · ~21,946 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 299 nodes · 426 edges · 24 communities detected
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 84 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]

## God Nodes (most connected - your core abstractions)
1. `Base` - 33 edges
2. `fetchAPI()` - 22 edges
3. `create_audit_entry()` - 9 edges
4. `RLEngine` - 9 edges
5. `submit_case()` - 8 edges
6. `register()` - 7 edges
7. `submit_feedback()` - 7 edges
8. `CaseResponse` - 7 edges
9. `aggregate_verdicts()` - 7 edges
10. `structure_case()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `User Model — System users with role-based access control (RBAC).` --uses--> `Base`  [INFERRED]
  C:\Users\hridy\Desktop\NirnayX\backend\app\models\user.py → C:\Users\hridy\Desktop\NirnayX\backend\app\database.py
- `Agent Model — Juror agent profiles and their per-case evaluations.` --uses--> `Base`  [INFERRED]
  C:\Users\hridy\Desktop\NirnayX\backend\app\models\agent.py → C:\Users\hridy\Desktop\NirnayX\backend\app\database.py
- `A juror agent archetype definition.     Each agent has a reasoning persona, a ba` --uses--> `Base`  [INFERRED]
  C:\Users\hridy\Desktop\NirnayX\backend\app\models\agent.py → C:\Users\hridy\Desktop\NirnayX\backend\app\database.py
- `A single agent's evaluation of a specific case.     Contains the agent's verdict` --uses--> `Base`  [INFERRED]
  C:\Users\hridy\Desktop\NirnayX\backend\app\models\agent.py → C:\Users\hridy\Desktop\NirnayX\backend\app\database.py
- `Audit Log Model — Immutable, append-only audit trail for all system actions.` --uses--> `Base`  [INFERRED]
  C:\Users\hridy\Desktop\NirnayX\backend\app\models\audit.py → C:\Users\hridy\Desktop\NirnayX\backend\app\database.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (32): AgentEvaluation, AgentProfile, Agent Model — Juror agent profiles and their per-case evaluations., A juror agent archetype definition.     Each agent has a reasoning persona, a ba, A single agent's evaluation of a specific case.     Contains the agent's verdict, AuditLog, Audit Log Model — Immutable, append-only audit trail for all system actions., Tamper-evident, append-only audit log for all NirnayX actions.     Retention: 7 (+24 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (39): clone_case(), create_case(), get_all_cases_db(), get_all_evaluations_db(), get_all_verdicts_db(), get_audit_logs(), get_case(), get_case_evaluations() (+31 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (38): create_access_token(), get_me(), login(), Get current user profile (demo mode returns demo user)., Create a JWT access token., Register a new user account., Authenticate and receive an access token., register() (+30 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (26): _agent_evaluate(), _analyze_case_signals(), evaluate_case(), _generate_concerns(), _generate_deterministic_seed(), _generate_rationale(), _generate_supporting_factors(), get_agent() (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.17
Nodes (22): cloneCase(), createCase(), fetchAPI(), getAgents(), getAuditLogs(), getBiasReport(), getCase(), getCaseEvaluations() (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (14): get_feedback_db(), list_feedback(), Submit outcome feedback for a closed case.     This triggers the RL engine to up, List all feedback entries., Expose feedback DB for dashboard., submit_feedback(), Reinforcement Learning Engine — Weight updates, reward propagation, and policy m, NirnayX Reinforcement Learning Engine.      Manages agent weight updates, reward (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (17): create_domain(), get_domain(), list_domains(), Domains Router — Domain profile management., Create a new domain profile., Create default domain profiles., List all domain profiles., Get a specific domain profile by key. (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (13): decode_token(), get_current_user(), hash_password(), Authentication Utilities — JWT token creation and password hashing., Hash a password using bcrypt., Create a demo user for testing., Verify a password against its hash., Decode and validate a JWT token. (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (0): 

### Community 9 - "Community 9"
Cohesion: 0.23
Nodes (11): aggregate_verdicts(), _confidence_weighted_average(), _empty_verdict(), Aggregation & Verdict Engine — Synthesizes all agent outputs into a final weight, FR-04.1: Final Score = Σ (Agent Weight × Confidence × Decision Value)     Verdic, Aggregate using confidence-weighted average of decision values., Aggregate all agent evaluations into a final verdict.      FR-04.1: Final Score, Require supermajority (67%+) agreement for approve/reject.     Otherwise escalat (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.23
Nodes (11): classify_domain(), extract_constraints(), extract_entities(), extract_key_facts(), Case Ingestion Service — Parses, classifies, and structures incoming cases. Impl, Extract key factual statements from the case description., Extract constraints and requirements from the case description., Full case ingestion pipeline: classify, extract entities, facts, and constraints (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (5): BaseSettings, Config, NirnayX Configuration Module Centralized settings management using Pydantic Base, Application configuration loaded from environment variables., Settings

### Community 12 - "Community 12"
Cohesion: 0.33
Nodes (5): get_db(), init_db(), NirnayX Database Module Async SQLAlchemy engine and session management., Dependency that provides a database session., Initialize database tables.

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (3): NirnayX — Reinforcement Learning-Based Jury Decision Platform Main FastAPI Appli, Root endpoint with API information., root()

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **87 isolated node(s):** `Config`, `NirnayX Configuration Module Centralized settings management using Pydantic Base`, `Application configuration loaded from environment variables.`, `NirnayX Database Module Async SQLAlchemy engine and session management.`, `Base class for all SQLAlchemy models.` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (2 nodes): `layout.js`, `RootLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `extract_docx.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `eslint.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `next.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `postcss.config.mjs`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `submit_case()` connect `Community 1` to `Community 9`, `Community 2`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._
- **Why does `Base` connect `Community 0` to `Community 12`, `Community 6`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._
- **Why does `submit_feedback()` connect `Community 5` to `Community 1`, `Community 2`, `Community 6`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `Base` (e.g. with `AgentProfile` and `AgentEvaluation`) actually correct?**
  _`Base` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `str` (e.g. with `_seed_demo_user()` and `register()`) actually correct?**
  _`str` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `NirnayX Configuration Module Centralized settings management using Pydantic Base`, `Application configuration loaded from environment variables.` to the rest of the system?**
  _87 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._