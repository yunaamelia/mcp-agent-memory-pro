"""
ML Importance Predictor
Predicts memory importance using machine learning
"""

import json
import sqlite3
from datetime import UTC
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class ImportancePredictor:
    """ML-based importance prediction"""

    def __init__(self, db_connection: sqlite3.Connection, model_dir: Path):
        self.conn = db_connection
        self.model_dir = model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.scaler = None
        self.feature_names = [
            "content_length",
            "has_project",
            "has_file_path",
            "tag_count",
            "entity_count",
            "access_count",
            "age_days",
            "is_code",
            "is_note",
            "source_score",
        ]

        self._load_or_train_model()

    def _load_or_train_model(self):
        """Load existing model or train new one"""

        model_path = self.model_dir / "importance_model.joblib"
        scaler_path = self.model_dir / "importance_scaler.joblib"

        if model_path.exists() and scaler_path.exists():
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
        else:
            self._train_model()

    def _train_model(self):
        """Train ML model on existing data"""

        # Get training data
        cursor = self.conn.execute("""
            SELECT
                id, type, source, content, timestamp, access_count,
                created_at, project, file_path, tags, entities,
                importance_score
            FROM memories
            WHERE importance_score IS NOT NULL
              AND importance_score > 0
              AND archived = 0
            LIMIT 1000
        """)

        memories = [dict(row) for row in cursor.fetchall()]

        if len(memories) < 50:
            # Not enough data, use simple model
            self.model = RandomForestRegressor(n_estimators=10, random_state=42)
            self.scaler = StandardScaler()

            # Create dummy training data
            X = np.random.rand(50, len(self.feature_names))
            y = np.random.rand(50)

            self.scaler.fit(X)
            self.model.fit(X, y)
        else:
            # Extract features
            X = []
            y = []

            for memory in memories:
                features = self._extract_features(memory)
                X.append(features)
                y.append(memory["importance_score"])

            X = np.array(X)
            y = np.array(y)

            # Train model
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            self.model = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
            )

            self.model.fit(X_scaled, y)

        # Save model
        joblib.dump(self.model, self.model_dir / "importance_model.joblib")
        joblib.dump(self.scaler, self.model_dir / "importance_scaler.joblib")

    def predict_importance(self, memory: dict[str, Any]) -> float:
        """Predict importance for a memory"""

        features = self._extract_features(memory)
        features_scaled = self.scaler.transform([features])

        prediction = self.model.predict(features_scaled)[0]

        # Clip to valid range
        return max(0.0, min(1.0, float(prediction)))

    def batch_predict(self, memory_ids: list[str]) -> dict[str, float]:
        """Predict importance for multiple memories"""

        predictions = {}

        for memory_id in memory_ids:
            cursor = self.conn.execute(
                """
                SELECT * FROM memories WHERE id = ?
            """,
                (memory_id,),
            )

            row = cursor.fetchone()
            if row:
                memory = dict(row)
                predictions[memory_id] = self.predict_importance(memory)

        return predictions

    def _extract_features(self, memory: dict[str, Any]) -> list[float]:
        """Extract features from memory"""

        from datetime import datetime

        features = []

        # Content length
        features.append(len(memory.get("content", "")))

        # Has project
        features.append(1.0 if memory.get("project") else 0.0)

        # Has file path
        # Handle cases where file_path might not be in the dictionary if retrieved via partial select
        features.append(1.0 if memory.get("file_path") else 0.0)

        # Tag count
        tags = memory.get("tags", "[]")
        try:
            tag_list = json.loads(tags) if isinstance(tags, str) else tags
            features.append(len(tag_list) if isinstance(tag_list, list) else 0)
        except Exception:
            features.append(0)

        # Entity count
        entities = memory.get("entities", "[]")
        try:
            entity_list = json.loads(entities) if isinstance(entities, str) else entities
            features.append(len(entity_list) if isinstance(entity_list, list) else 0)
        except Exception:
            features.append(0)

        # Access count
        features.append(memory.get("access_count", 0))

        # Age in days
        timestamp = memory.get("timestamp", 0)
        age_ms = datetime.now(UTC).timestamp() * 1000 - timestamp
        age_days = age_ms / (24 * 60 * 60 * 1000)
        features.append(age_days)

        # Is code
        features.append(1.0 if memory.get("type") == "code" else 0.0)

        # Is note
        features.append(1.0 if memory.get("type") == "note" else 0.0)

        # Source score
        source_scores = {"manual": 0.8, "ide": 0.7, "terminal": 0.6}
        features.append(source_scores.get(memory.get("source", ""), 0.5))

        return features

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance from model"""

        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            return {
                name: float(importance)
                for name, importance in zip(self.feature_names, importances, strict=False)
            }

        return {}
