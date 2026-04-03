# Copyright (c) 2025 mufthakherul — see LICENSE.txt
"""Policy-pack loading and evaluation utilities.

Implements offline policy-pack enforcement for enterprise-style report
evaluation (Sprint 10 roadmap track).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import jsonschema


class PolicyPackError(Exception):
    """Raised when policy-pack parsing/validation/evaluation fails."""


class _SafeExprEvaluator:
    """Very small safe expression evaluator for policy conditions."""

    def __init__(self, context: dict[str, Any]):
        self._context = context

    def evaluate(self, expression: str) -> bool:
        if not expression or len(expression) > 300:
            raise PolicyPackError("Policy rule condition is empty or too long")

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise PolicyPackError(f"Invalid policy condition syntax: {exc}") from exc

        value = self._eval_node(tree.body)
        return bool(value)

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            if node.id not in self._context:
                raise PolicyPackError(f"Unknown symbol in policy condition: {node.id}")
            return self._context[node.id]

        if isinstance(node, ast.Attribute):
            base = self._eval_node(node.value)
            if isinstance(base, dict):
                if node.attr not in base:
                    raise PolicyPackError(
                        f"Unknown attribute in policy condition: {node.attr}"
                    )
                return base[node.attr]
            if hasattr(base, node.attr):
                return getattr(base, node.attr)
            raise PolicyPackError(f"Unsupported attribute access: {node.attr}")

        if isinstance(node, ast.BoolOp):
            values = [bool(self._eval_node(v)) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise PolicyPackError("Unsupported boolean operator")

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.Not):
                return not bool(operand)
            if isinstance(node.op, ast.USub):
                return -float(operand)
            raise PolicyPackError("Unsupported unary operator")

        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            raise PolicyPackError("Unsupported binary operator")

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                if isinstance(op, ast.Lt):
                    matched = left < right
                elif isinstance(op, ast.LtE):
                    matched = left <= right
                elif isinstance(op, ast.Gt):
                    matched = left > right
                elif isinstance(op, ast.GtE):
                    matched = left >= right
                elif isinstance(op, ast.Eq):
                    matched = left == right
                elif isinstance(op, ast.NotEq):
                    matched = left != right
                elif isinstance(op, ast.In):
                    matched = left in right
                elif isinstance(op, ast.NotIn):
                    matched = left not in right
                else:
                    raise PolicyPackError("Unsupported comparison operator")

                if not matched:
                    return False
                left = right
            return True

        raise PolicyPackError(f"Unsupported expression node: {type(node).__name__}")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _policy_schema_path() -> Path:
    return _project_root() / "schemas" / "policy-pack-schema-1.0.0.json"


def load_policy_pack(path: Path) -> dict[str, Any]:
    """Load and schema-validate a policy pack JSON file."""
    if not path.exists() or not path.is_file():
        raise PolicyPackError(f"Policy pack not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyPackError(f"Invalid policy pack JSON: {exc}") from exc

    schema = json.loads(_policy_schema_path().read_text(encoding="utf-8"))
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as exc:
        raise PolicyPackError(f"Policy pack schema validation failed: {exc.message}")

    return payload


def evaluate_policy_pack(
    policy_pack: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate policy rules and return a deterministic policy result payload."""
    evaluator = _SafeExprEvaluator(context)

    severity_weights = {
        "warn": {"info": -1, "warning": -3, "critical": -7},
        "recommend": {"info": 0, "warning": -1, "critical": -2},
        "fail": {"info": -5, "warning": -10, "critical": -20},
    }

    triggered_rules: list[dict[str, Any]] = []
    score_delta = 0
    fail_count = 0
    warn_count = 0
    recommend_count = 0

    for rule in policy_pack.get("rules", []):
        condition = str(rule.get("condition", "")).strip()
        if not evaluator.evaluate(condition):
            continue

        action = str(rule.get("action", "warn"))
        severity = str(rule.get("severity", "warning"))
        message = str(rule.get("message") or rule.get("title") or "Policy matched")

        score_delta += severity_weights.get(action, severity_weights["warn"]).get(
            severity,
            -1,
        )

        if action == "fail":
            fail_count += 1
        elif action == "recommend":
            recommend_count += 1
        else:
            warn_count += 1

        triggered_rules.append(
            {
                "id": rule.get("id"),
                "title": rule.get("title"),
                "severity": severity,
                "action": action,
                "message": message,
                "condition": condition,
            }
        )

    if fail_count > 0:
        status = "fail"
    elif warn_count > 0:
        status = "warn"
    elif recommend_count > 0:
        status = "recommend"
    else:
        status = "pass"

    return {
        "pack_id": policy_pack.get("pack_id"),
        "display_name": policy_pack.get("display_name"),
        "target_profile": policy_pack.get("target_profile"),
        "rules_evaluated": len(policy_pack.get("rules", [])),
        "rules_triggered": len(triggered_rules),
        "status": status,
        "score_delta": score_delta,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "recommend_count": recommend_count,
        "triggered_rules": triggered_rules,
    }
