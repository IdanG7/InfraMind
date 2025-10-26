"""Model training"""

from datetime import datetime
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from ..models.orm import Model, Pipeline, Run
from ..storage.postgres import SessionLocal
from .features import build_feature_matrix
from .model_store import save_model
from ..storage.redis import set_active_model_version


def prepare_data(
    pipeline_name: str | None = None, limit: int = 500
) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare training data"""
    session = SessionLocal()

    try:
        query = session.query(Run).filter(Run.status == "success")

        if pipeline_name:
            pipeline = session.query(Pipeline).filter(Pipeline.name == pipeline_name).first()
            if pipeline:
                query = query.filter(Run.pipeline_id == pipeline.id)

        runs = query.order_by(Run.started_at.desc()).limit(limit).all()

        if not runs:
            print("No runs found for training")
            return pd.DataFrame(), pd.Series()

        X, y = build_feature_matrix(runs, session)

        # Convert to DataFrame
        df = pd.DataFrame(X)

        # Encode categorical features
        categorical_cols = ["image", "branch", "node"]
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].astype("category").cat.codes

        return df, pd.Series(y)

    finally:
        session.close()


def train_model(
    pipeline_name: str | None = None,
    n_estimators: int = 100,
    max_depth: int = 15,
) -> dict[str, Any]:
    """Train optimization model"""
    print(f"Preparing data for {pipeline_name or 'all pipelines'}...")
    X, y = prepare_data(pipeline_name)

    if X.empty or len(y) < 10:
        print("Insufficient data for training")
        return {"error": "insufficient_data"}

    print(f"Training on {len(X)} samples...")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "mae": float(mae),
        "r2": float(r2),
        "n_samples": len(X),
        "n_features": len(X.columns),
    }

    print(f"Model trained: MAE={mae:.2f}s, R²={r2:.3f}")

    # Save model
    version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    save_model(model, version, metrics)

    # Update active version
    set_active_model_version(version)

    # Store metadata in database
    session = SessionLocal()
    try:
        model_record = Model(
            version=version,
            algo="RandomForest",
            metrics=metrics,
        )
        session.add(model_record)
        session.commit()
    finally:
        session.close()

    print(f"Model {version} saved and activated")

    return {
        "version": version,
        "metrics": metrics,
    }


if __name__ == "__main__":
    # CLI for training
    import sys

    pipeline = sys.argv[1] if len(sys.argv) > 1 else None
    result = train_model(pipeline)
    print(result)
