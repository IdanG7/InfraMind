"""Optimization engine"""

from typing import Any
import random

from ..config import settings
from .model_store import predict_duration

# Parameter bounds
BOUNDS = {
    "concurrency": (1, 16),
    "cpu_req": (1, 16),
    "mem_req_gb": (2, 64),
    "cache_size_gb": (1, 30),
}


def clamp(v: float, lo: float, hi: float) -> float:
    """Clamp value to bounds"""
    return max(lo, min(hi, v))


def candidate_configs(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate candidate configurations"""
    # Get last successful config or defaults
    base = context.get(
        "last_success",
        {
            "concurrency": 4,
            "cpu_req": 4,
            "mem_req_gb": 8,
            "cache_size_gb": 10,
        },
    )

    candidates = []

    # Grid search around base
    deltas = [-2, -1, 0, 1, 2]
    for dc in deltas:
        for dcpu in [-1, 0, 1]:
            for dmem in [-2, 0, 2]:
                cfg = {
                    "concurrency": int(
                        clamp(
                            base.get("concurrency", 4) + dc,
                            *BOUNDS["concurrency"],
                        )
                    ),
                    "cpu_req": int(
                        clamp(
                            base.get("cpu_req", 4) + dcpu,
                            *BOUNDS["cpu_req"],
                        )
                    ),
                    "mem_req_gb": int(
                        clamp(
                            base.get("mem_req_gb", 8) + dmem,
                            *BOUNDS["mem_req_gb"],
                        )
                    ),
                    "cache": {
                        "ccache": True,
                        "size_gb": base.get("cache_size_gb", 10),
                    },
                }

                # Deduplicate
                if cfg not in candidates:
                    candidates.append(cfg)

    # Add some exploration
    if random.random() < settings.exploration_rate:
        candidates.append(
            {
                "concurrency": random.randint(*BOUNDS["concurrency"]),
                "cpu_req": random.randint(1, BOUNDS["cpu_req"][1]),
                "mem_req_gb": random.choice([4, 8, 16, 32]),
                "cache": {"ccache": True, "size_gb": 10},
            }
        )

    return candidates[:20]  # Limit candidates


def apply_safety_guards(
    config: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Apply safety constraints to config"""
    # Ensure memory is above RSS p95 * multiplier
    rss_p95_bytes = context.get("max_rss_bytes", 0)
    min_mem_gb = max(
        BOUNDS["mem_req_gb"][0],
        int((rss_p95_bytes * settings.safe_multiplier) / (1024**3)),
    )

    if config["mem_req_gb"] < min_mem_gb:
        config["mem_req_gb"] = min_mem_gb

    # Ensure CPU >= concurrency / 4 (avoid starvation)
    if config["cpu_req"] < config["concurrency"] / 4:
        config["cpu_req"] = max(1, config["concurrency"] // 4)

    return config


def suggest(
    context: dict[str, Any], constraints: dict[str, Any]
) -> tuple[dict[str, Any], str, float]:
    """
    Generate optimization suggestions

    Returns: (suggestions, rationale, confidence)
    """
    # Generate candidates
    candidates = candidate_configs(context)

    # Apply constraints if provided
    if constraints:
        max_concurrency = constraints.get("max_concurrency")
        min_ram_gb = constraints.get("min_ram_gb")

        if max_concurrency:
            for cfg in candidates:
                cfg["concurrency"] = min(cfg["concurrency"], max_concurrency)

        if min_ram_gb:
            for cfg in candidates:
                cfg["mem_req_gb"] = max(cfg["mem_req_gb"], min_ram_gb)

    # Score each candidate
    best_cfg = None
    best_pred = float("inf")
    predictions = []

    for cfg in candidates:
        # Apply safety guards
        safe_cfg = apply_safety_guards(cfg.copy(), context)

        # Predict duration
        pred = predict_duration(context, safe_cfg)
        predictions.append((safe_cfg, pred))

        if pred < best_pred:
            best_pred = pred
            best_cfg = safe_cfg

    # Fallback if no candidates
    if best_cfg is None:
        best_cfg = {
            "concurrency": 4,
            "cpu_req": 4,
            "mem_req_gb": 8,
            "cache": {"ccache": True, "size_gb": 10},
        }
        best_pred = context.get("avg_step_duration_s", 30) * context.get("num_steps", 10)

    # Build rationale
    rationale = (
        f"Selected config with predicted duration={best_pred:.1f}s "
        f"(current baseline: {context.get('duration_s', 'unknown')}s). "
        f"Evaluated {len(predictions)} candidates. "
        f"Safety: mem >= {context.get('max_rss_gb', 0):.1f}GB * {settings.safe_multiplier}."
    )

    # Compute confidence based on prediction variance
    pred_values = [p[1] for p in predictions]
    confidence = 0.7 if len(pred_values) > 5 else 0.5

    return best_cfg, rationale, confidence
