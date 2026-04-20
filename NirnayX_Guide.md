# NirnayX: Project Walkthrough & Guide

Welcome to **NirnayX**, your AI-powered, reinforcement learning-based jury simulation engine! Based on your PRD, this project acts as a multi-perspective decision intelligence system. Instead of relying on a single AI response, NirnayX recruits a "jury" of different AI personas to debate and evaluate complex cases.

This guide will explain exactly what was built, how it works, and how to navigate the codebase.

---

## 1. What Did We Build?

We built a complete, full-stack application mirroring the requirements of the PRD ranging from the fast backend engine to a dynamic frontend dashboard.

*   **Backend:** Python with FastAPI. It handles all the core logic, Agent frameworks, RL algorithms, and API endpoints.
*   **Frontend:** Next.js (App Router) with Tailwind CSS. We implemented a visually rich, premium glassmorphism dashboard.
*   **Storage (In-Memory Prototype):** For this prototype stage, the database uses rapid in-memory stores initialized inside the application so you don't need any complex external setups to test it immediately.

---

## 2. Architecture & Components

The application follows the microservices-style layout detailed in your PRD:

### I. Case Ingestion Service (`backend/app/services/ingestion.py`)
When you submit a new case (e.g., "Expand to Southeast Asia"), the ingestion service steps in to:
1.  **Auto-Classify Domain:** It searches for keywords to automatically categorize the case (e.g., HR, Legal, Business).
2.  **Extract Details:** It parses the text to find key entities (dates, monetary values, organizations) and explicit constraints.

### II. Juror Agent Framework (`backend/app/services/agents.py`)
This is the core of NirnayX. We implemented **5 distinct AI Archetypes**:
1.  **Risk Analyst** (Conservative, focuses on downside and failure modes)
2.  **Growth Advocate** (Optimistic, focuses on scalability and value creation)
3.  **Financial Modeler** (Data-driven, looks at ROI and economics)
4.  **Ethical Reviewer** (Justice-oriented, checks fairness and compliance)
5.  **Devil's Advocate** (Contrarian, challenges all assumptions)

*How it works: Each agent evaluates the ingested case independently ("blind deliberation"). They produce a verdict (`approve`, `reject`, `escalate`), a confidence score (0-100), and a structured reasoning chain explaining their stance.*

### III. Aggregation & Verdict Engine (`backend/app/services/aggregation.py`)
Once all agents submit their verdicts, this engine compiles them.
*   It supports different modes (e.g., Weighted Voting, Supermajority).
*   It aggregates the final score based on the Agent's verdict, their confidence, and their current ML weight.
*   If consensus drops below a predefined threshold (e.g., 60%), it automatically flags the case for **Mandatory Human Review**.

### IV. Reinforcement Learning Engine (`backend/app/services/rl_engine.py`)
NirnayX is designed to adapt. Once a case is closed and a decision is played out, humans can provide **Outcome Feedback** (1 to 5 stars).
*   The RL Engine uses a policy gradient technique. If an agent voted to "approve" and the real-world outcome was 5-stars, that agent's weight goes up. If the outcome was a disaster (1-star), their weight goes down.
*   **Bias Guardrail:** The system ensures no single agent can have more than 35% of the total decision weight, avoiding an AI dictatorship.

### V. Explainability Layer (`backend/app/services/explainability.py`)
Black-box AI is useless for enterprise decisions. This layer generates a full human-readable Verdict Report detailing exactly *why* a decision was made, breaking down the contributing factors, dissenting agents, and audit logs.

---

## 3. How to Use the System

Everything is glued together by the **Next.js Dashboard** which lives at `http://localhost:3000`.

### A. The Dashboard Overview
When you first open the app, you see high-level statistics like Total Verdicts, Average Confidence, and real-time Agent Performance metrics.

### B. Creating a Case
Navigate to **New Case** on the sidebar.
1. Enter a Title (e.g., "Q4 Hiring Freeze").
2. Enter a description containing details, budgets, or constraints.
3. Submit it for Evaluation.
4. The backend spawns the agents and immediately shows you the compiled verdict screen!

### C. Reading the Verdict
On the results screen, you will see:
*   The massive **Final Verdict** tag.
*   **Rings** showing Confidence and Consensus.
*   A grid of the agents with individual reasoning. So if the Risk Analyst disagreed with the Growth Advocate, you can see exactly why.

### D. Submitting Feedback
Scroll to the bottom of any evaluated case to submit **Outcome Feedback**. Entering star ratings simulates real-world learning and invokes the RL engine to calibrate your AI jury for subsequent cases!

---

## 4. Technical File Structure

If you wish to explore or modify the code, here is where everything lives inside the `NirnayX/` folder on your Desktop:

*   **`backend/app/main.py`** - FastAPI entry point.
*   **`backend/app/models/`** - SQLAlchemy ORM definitions for scaling to PostgreSQL.
*   **`backend/app/schemas/`** - Pydantic models for strict API validation.
*   **`backend/app/services/`** - The "Brain" (Agents, RL, Ingestion).
*   **`backend/app/routers/`** - API endpoints mapped to HTTP requests.
*   **`frontend/src/app/page.js`** - The entire Interactive Next.js Dashboard.
*   **`frontend/src/app/globals.css`** - Modern styling configurations, variables, and dark themes.

NirnayX is fully constructed. If you wish to test it right now interactively, open a web browser and navigate to `http://localhost:3000`!
