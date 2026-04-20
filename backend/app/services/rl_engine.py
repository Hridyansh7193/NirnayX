"""
Reinforcement Learning Engine — Weight updates, reward propagation, and policy management.
Implements FR-03.1 through FR-03.7.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from app.config import settings


class RLEngine:
    """
    NirnayX Reinforcement Learning Engine.

    Manages agent weight updates, reward signal processing, and policy versioning.
    Uses a simplified policy gradient approach where agent weights are adjusted
    based on feedback quality signals.
    """

    def __init__(self):
        self.learning_rate = settings.RL_LEARNING_RATE
        self.min_feedback_cycles = settings.RL_MIN_FEEDBACK_CYCLES
        self.reward_history: List[Dict[str, Any]] = []
        self.weight_history: List[Dict[str, Any]] = []
        self.policy_version: int = 0
        self._checkpoints: Dict[int, Dict[str, float]] = {}

    def compute_reward_signal(
        self,
        outcome_rating: int,
        outcome_accuracy: Optional[float] = None,
        agent_evaluations: Optional[List[Dict]] = None,
    ) -> float:
        """
        Compute the reward signal from user feedback.
        FR-03.2: Reward signal definable per domain with outcome accuracy and user satisfaction.

        Args:
            outcome_rating: User satisfaction rating (1-5)
            outcome_accuracy: Optional accuracy metric (0-1)
            agent_evaluations: Optional list of agent evaluation results

        Returns:
            Normalized reward signal in range [-1, 1]
        """
        # Normalize rating to [-1, 1]
        rating_reward = (outcome_rating - 3) / 2.0  # 1→-1, 3→0, 5→1

        if outcome_accuracy is not None:
            # Blend rating and accuracy (60% accuracy, 40% satisfaction)
            accuracy_reward = (outcome_accuracy * 2) - 1  # 0→-1, 0.5→0, 1→1
            reward = 0.6 * accuracy_reward + 0.4 * rating_reward
        else:
            reward = rating_reward

        return round(float(np.clip(reward, -1.0, 1.0)), 4)

    def update_weights(
        self,
        current_weights: Dict[str, float],
        agent_evaluations: List[Dict[str, Any]],
        reward_signal: float,
        domain: str = "general",
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Update agent weights based on reward signal.
        FR-03.4: Agent weights must update after each feedback cycle.
        FR-03.6: RL training must be domain-isolated.

        Uses a simplified policy gradient:
        w_new = w_old + lr * reward * (confidence / 100) * agreement_bonus

        Where agreement_bonus is positive if the agent's verdict aligned with
        the reward direction, negative otherwise.

        Returns:
            Tuple of (updated_weights, update_details)
        """
        updated_weights = {}
        update_details = {
            "domain": domain,
            "reward_signal": reward_signal,
            "policy_version": self.policy_version,
            "per_agent_updates": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        for evaluation in agent_evaluations:
            archetype = evaluation.get("archetype", "unknown")
            current_w = current_weights.get(archetype, 1.0)
            confidence = evaluation.get("confidence_score", 50.0) / 100.0
            decision_value = evaluation.get("decision_value", 0.5)

            # Agreement bonus: how well did this agent's verdict align with outcome?
            # Positive reward + approve verdict → positive bonus
            # Negative reward + reject verdict → positive bonus
            verdict = evaluation.get("verdict", "escalate")
            if verdict == "approve":
                agreement = decision_value
            elif verdict == "reject":
                agreement = 1.0 - decision_value
            else:
                agreement = 0.5  # Neutral for escalate

            # Compute weight update
            # Reward aligns with agreement → increase weight
            # Reward contradicts agreement → decrease weight
            delta = self.learning_rate * reward_signal * confidence * (agreement - 0.5) * 2

            new_weight = float(np.clip(current_w + delta, 0.1, 3.0))  # Clamp weights
            updated_weights[archetype] = round(new_weight, 4)

            update_details["per_agent_updates"].append({
                "archetype": archetype,
                "old_weight": round(current_w, 4),
                "new_weight": round(new_weight, 4),
                "delta": round(delta, 6),
                "confidence": round(confidence, 4),
                "agreement": round(agreement, 4),
            })

        # Normalize weights so they sum to agent count (prevents drift)
        weight_sum = sum(updated_weights.values())
        target_sum = len(updated_weights)
        if weight_sum > 0:
            scale_factor = target_sum / weight_sum
            updated_weights = {k: round(v * scale_factor, 4) for k, v in updated_weights.items()}

        # Update version and history
        self.policy_version += 1
        update_details["new_policy_version"] = self.policy_version

        self.reward_history.append({
            "cycle": self.policy_version,
            "reward": reward_signal,
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
        })

        self.weight_history.append({
            "policy_version": self.policy_version,
            "weights": updated_weights.copy(),
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return updated_weights, update_details

    def create_checkpoint(self, weights: Dict[str, float]) -> int:
        """
        FR-03.5: Policy update history must be versioned and rollback-capable.
        """
        self._checkpoints[self.policy_version] = weights.copy()
        return self.policy_version

    def rollback_to_checkpoint(self, version: int) -> Optional[Dict[str, float]]:
        """Rollback weights to a previous checkpoint."""
        if version in self._checkpoints:
            return self._checkpoints[version].copy()
        return None

    def get_telemetry(self) -> Dict[str, Any]:
        """
        FR-03.7: Expose RL telemetry data.
        Returns reward curves, convergence metrics, and weight history.
        """
        convergence = "not_started"
        if len(self.reward_history) >= self.min_feedback_cycles:
            recent_rewards = [r["reward"] for r in self.reward_history[-10:]]
            avg_reward = np.mean(recent_rewards)
            if avg_reward > 0.3:
                convergence = "converging_positive"
            elif abs(avg_reward) < 0.1:
                convergence = "stable"
            else:
                convergence = "improving"
        elif len(self.reward_history) > 0:
            convergence = "learning"

        return {
            "total_feedback_cycles": len(self.reward_history),
            "policy_version": self.policy_version,
            "reward_curve": self.reward_history[-50:],
            "agent_weight_history": self.weight_history[-20:],
            "convergence_status": convergence,
            "checkpoints_available": list(self._checkpoints.keys()),
            "last_update": self.reward_history[-1]["timestamp"] if self.reward_history else None,
        }

    def get_bias_report(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Generate a bias audit report.
        Ensures no single agent contributes > 35% of total weight.
        """
        total_weight = sum(weights.values())
        max_allowed_ratio = 0.35
        violations = []

        agent_contributions = {}
        for agent, weight in weights.items():
            ratio = weight / total_weight if total_weight > 0 else 0
            agent_contributions[agent] = {
                "weight": round(weight, 4),
                "weight_ratio": round(ratio, 4),
                "exceeds_limit": ratio > max_allowed_ratio,
            }
            if ratio > max_allowed_ratio:
                violations.append(agent)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_contributions": agent_contributions,
            "max_allowed_ratio": max_allowed_ratio,
            "violations": violations,
            "bias_check_passed": len(violations) == 0,
            "recommendation": "Agent weights are balanced." if not violations
                else f"WARNING: Agents {violations} exceed the 35% weight limit. Consider rebalancing.",
        }


# Global RL engine instance
rl_engine = RLEngine()
