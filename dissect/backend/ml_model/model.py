import json
import os
from backend.config import settings

class RiskModel:
    def __init__(self):
        self.weights = {
            "confidence": 0.5,
            "complexity": 0.2,
            "depth": 0.3
        }

        self.model_loaded = False

        if os.path.exists(settings.MODEL_PATH):
            try:
                with open(settings.MODEL_PATH, "r") as f:
                    self.weights = json.load(f)
                    self.model_loaded = True
            except:
                pass

    def predict(self, features: dict):
        score = 0

        for key, weight in self.weights.items():
            score += features.get(key, 0) * weight

        return score