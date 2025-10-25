"""Model storage and loading"""

import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from ..config import settings


def get_model_path(version: str = "v1") -> Path:
    """Get path to model file"""
    return Path(settings.model_path) / f"model_{version}.joblib"


def save_model(model: Any, version: str, metrics: dict[str, float]) -> None:
    """Save trained model"""
    model_path = get_model_path(version)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    # Save model
    joblib.dump(model, model_path)

    # Save metrics
    metrics_path = model_path.with_suffix(".json")
    import json

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)


def load_model(version: str = "v1") -> Any:
    """Load trained model"""
    model_path = get_model_path(version)
    if not model_path.exists():
        # Return default model if none exists
        return RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42,
        )
    return joblib.load(model_path)


def predict_duration(context: dict[str, Any], config: dict[str, Any]) -> float:
    """Predict build duration given context and config"""
    model = load_model(settings.model_version)

    # Build feature vector
    features = {**context, **config}

    # Convert categorical to numeric (simple encoding for demo)
    feature_vector = [
        features.get("cpu_req", 4),
        features.get("mem_req_gb", 8),
        features.get("concurrency", 4),
        features.get("max_rss_gb", 4),
        features.get("io_read_gb", 1),
        features.get("io_write_gb", 0.5),
        features.get("cache_hit_ratio", 0.5),
        features.get("num_steps", 10),
        features.get("avg_step_duration_s", 30),
    ]

    # Predict
    try:
        X = np.array([feature_vector])
        pred = model.predict(X)[0]
        return float(pred)
    except Exception:
        # Fallback: simple heuristic
        return features.get("avg_step_duration_s", 30) * features.get("num_steps", 10)
