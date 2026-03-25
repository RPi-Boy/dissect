"""
model.py — Heuristic ML Risk Scorer.

Provides rapid, deterministic risk scoring based on static features.
If scikit-learn is missing (due to environment constraints), it safely
falls back to a rule-based weighted heuristic.
"""

import logging
from .feature_extractor import extract_features
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    # Attempt to use a real ML model if dependencies exist
    from sklearn.ensemble import RandomForestRegressor
    import numpy as np
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not available. Using fallback rule-based model.")


class RiskScorer:
    """Provides a 1-10 risk score based on codebase features."""

    def __init__(self):
        self._model = None
        if HAS_SKLEARN:
            # In a real scenario, we'd load model.pkl. Here we use an untrained
            # random forest with heavily weighted synthetic rules.
            self._model = RandomForestRegressor(n_estimators=10, random_state=42)
            # Dummy training data to bias the model
            X = np.array([
                [1.0, 10.0, 0.0, 0.0, 2.0],  # low risk
                [10.0, 100.0, 50.0, 2.0, 15.0], # high risk
            ])
            y = np.array([1.5, 9.5])
            self._model.fit(X, y)

    def predict(self, features: dict[str, float]) -> float:
        """Predict the risk score given the features."""
        if HAS_SKLEARN and self._model:
            X_input = np.array([[
                features.get("log_loc", 0),
                features.get("file_count", 0),
                features.get("keyword_density", 0),
                features.get("risky_files", 0),
                features.get("max_complexity", 0)
            ]])
            score = self._model.predict(X_input)[0]
            # Ensure bounds 1-10
            return max(1.0, min(10.0, round(score, 1)))
        
        # Fallback Rule-Based Scoring (if scikit-learn is failing in the env)
        score = 1.0
        
        # Scale complexity impact
        score += features.get("max_complexity", 0) * 0.2
        
        # Keyword density strongly influences risk
        score += features.get("keyword_density", 0) * 0.5
        
        # Immediate red flags
        score += features.get("risky_files", 0) * 2.5
        
        # Large codebases have inherently higher attack surface
        score += features.get("log_loc", 0) * 0.2
        
        return max(1.0, min(10.0, round(score, 1)))


scorer = RiskScorer()

def get_rapid_risk_score(repo_path: Path) -> dict[str, float]:
    """Extract features and generate an instant risk score.

    Args:
        repo_path: The checked out repository path.
        
    Returns:
        Dict with "score" and the raw features.
    """
    logger.info("Computing rapid ML risk score for %s", repo_path)
    features = extract_features(repo_path)
    score = scorer.predict(features)
    logger.info("Computed rapid score: %.1f/10", score)
    
    return {
        "score": score,
        "features": features
    }
