"""AI-driven proof tactic planner using PyTorch neural policy networks."""
from __future__ import annotations

import inspect

from ...ast import EPi, Expr
from ...environment import Environment
from ...errors import ProofError, PyTorchIntegrationError
from ...framework import ProofScript
from ...kernel import Goal
from ...utils.logging import get_logger
from ..tactic import TacticArg, TacticPlan
from .model import TacticPredictor, TacticVocabulary

try:
    import torch
except ImportError as err:
    msg = (
        "PyTorch is required for this module. "
        "Install with: pip install 'poussins[pytorch]'"
    )
    raise PyTorchIntegrationError(msg) from err


class _SearchScript(ProofScript):
    """Internal ProofScript used by AITacticPlanner for state exploration."""

    def __init__(self, statement: Expr, env: Environment) -> None:
        super().__init__(statement, env)
        self.logger = get_logger(__name__)

    def qed(self) -> None:
        """No-op for search script."""
        pass


class AITacticPlanner:
    """AI planner that utilizes a trained PyTorch model to synthesize TacticPlans."""

    def __init__(  # noqa: PLR0913
        self,
        model: TacticPredictor,
        vocabulary: TacticVocabulary,
        env: Environment | None = None,
        max_depth: int = 15,
        top_k: int = 4,
        device: str = "cpu",
    ) -> None:
        """Initialize planner with model, vocabulary, and search parameters."""
        self.model = model.to(device)
        self.vocabulary = vocabulary
        self.env = env if env is not None else Environment.standard()
        self.max_depth = max_depth
        self.top_k = top_k
        self.device = device

    def _goal_to_tensor(self, goal: Goal) -> tuple[torch.Tensor, list[str]]:
        """Encode goal statement and local context into input_ids tensor."""
        tokens: list[str] = [TacticVocabulary.goal_symbol]
        tokens.extend(TacticVocabulary.tokenize(str(goal.statement)))

        ordered_hyp_names: list[str] = []
        if goal.local_context:
            for name, typ in goal.local_context.items():
                ordered_hyp_names.append(name)
                tokens.append(TacticVocabulary.hyp_symbol)
                tokens.extend(TacticVocabulary.tokenize(f"{name} : {typ}"))

        input_ids = self.vocabulary.encode(tokens, max_len=128)
        tensor = torch.tensor([input_ids], dtype=torch.long, device=self.device)
        return tensor, ordered_hyp_names

    def suggest_tactics(
        self,
        goal: Goal,
        top_k: int | None = None,
    ) -> list[tuple[str, float]]:
        """Return top-k candidate tactic names and confidence scores for a goal."""
        k = top_k if top_k is not None else self.top_k
        tensor, _ = self._goal_to_tensor(goal)
        top_indices = self.model.predict_top_k(tensor, top_k=k)

        suggestions: list[tuple[str, float]] = []
        for tactic_id, prob in top_indices:
            tactic_name = self.vocabulary.id_to_tactic.get(tactic_id)
            if tactic_name:
                suggestions.append((tactic_name, prob))
        return suggestions

    def _generate_candidate_actions(
        self,
        script: _SearchScript,
        goal: Goal,
        tactic_name: str,
        ordered_hyp_names: list[str],
        arg_logits: torch.Tensor,
    ) -> list[dict[str, TacticArg]]:
        """Construct plausible keyword arguments for any tactic via introspection."""
        if not hasattr(script, tactic_name):
            return []

        tactic_fn = getattr(script, tactic_name)
        try:
            sig = inspect.signature(tactic_fn)
            params = [
                p for p in sig.parameters.values() if p.name not in ("self",)
            ]
        except (ValueError, TypeError):
            params = []

        actions: list[dict[str, TacticArg]] = []

        # Case 1: Tactic takes no required arguments (or has all defaults)
        if not params or all(p.default is not inspect.Parameter.empty for p in params):
            actions.append({})

        # Extract sorted hypothesis names by neural arg ranking
        scored_hyps = ordered_hyp_names
        if ordered_hyp_names:
            arg_probs = torch.softmax(arg_logits[0], dim=-1)
            scored = []
            for idx, hyp_name in enumerate(ordered_hyp_names):
                score = (
                    float(arg_probs[idx].item())
                    if idx < len(arg_probs)
                    else 0.0
                )
                scored.append((hyp_name, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            scored_hyps = [name for name, _ in scored]

        # Case 2: Inspect parameter patterns
        param_names = {p.name for p in params}

        if "name" in param_names and len(params) == 1:
            if isinstance(goal.statement, EPi) and goal.statement.var != "_":
                actions.append({"name": goal.statement.var})
            else:
                actions.append({"name": f"h{len(ordered_hyp_names)}"})

        elif "names" in param_names and len(params) == 1:
            names: list[str] = []
            curr: Expr = goal.statement
            idx = len(ordered_hyp_names)
            while isinstance(curr, EPi):
                if curr.var != "_":
                    names.append(curr.var)
                else:
                    names.append(f"h{idx}")
                    idx += 1
                curr = curr.body
            if names:
                actions.append({"names": names})
            else:
                actions.append({"names": [f"h{len(ordered_hyp_names)}"]})

        elif "expr_or_name" in param_names:
            for hyp_name in scored_hyps:
                actions.append({"expr_or_name": hyp_name})

        elif "hyp_name" in param_names:
            for hyp_name in scored_hyps:
                actions.append({"hyp_name": hyp_name})

        elif "hypothesis_name" in param_names:
            for hyp_name in scored_hyps:
                actions.append({"hypothesis_name": hyp_name})

        return actions

    def plan(
        self,
        statement: Expr,
        env: Environment | None = None,
    ) -> list[TacticPlan]:
        """Synthesize a complete sequence of TacticPlans for statement.

        Raises:
            PyTorchIntegrationError: If no valid proof plan can be discovered.

        """
        active_env = env if env is not None else self.env
        script = _SearchScript(statement, active_env)

        plan_result = self._search(script, depth=0)
        if plan_result is None:
            msg = f"AITacticPlanner failed to find a tactic plan for '{statement}'."
            raise PyTorchIntegrationError(msg)
        return plan_result

    def _search(
        self,
        script: _SearchScript,
        depth: int,
    ) -> list[TacticPlan] | None:
        """Perform recursive backtracking search over proof states."""
        if script.is_closed:
            return []

        if depth >= self.max_depth:
            return None

        current_goal = script.current_state.current_goal
        if current_goal is None:
            return []

        tensor, ordered_hyps = self._goal_to_tensor(current_goal)
        self.model.eval()
        with torch.no_grad():
            tactic_logits, arg_logits = self.model(tensor)
            probs = torch.softmax(tactic_logits[0], dim=-1)
            _, top_indices = torch.topk(probs, min(self.top_k, self.model.num_tactics))

        for idx_tensor in top_indices:
            tactic_idx = int(idx_tensor.item())
            tactic_name = self.vocabulary.id_to_tactic.get(tactic_idx)
            if not tactic_name or not hasattr(script, tactic_name):
                continue

            candidates = self._generate_candidate_actions(
                script, current_goal, tactic_name, ordered_hyps, arg_logits
            )

            for kwargs in candidates:
                tactic_fn = getattr(script, tactic_name)
                try:
                    tactic_fn(**kwargs)
                except (ProofError, TypeError, ValueError):
                    # Tactic failed or invalidated the goal, try next candidate
                    continue

                sub_plan = self._search(script, depth + 1)
                if sub_plan is not None:
                    return [(tactic_name, kwargs), *sub_plan]

                script.undo()

        return None
