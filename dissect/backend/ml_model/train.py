import json
import os
import random
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

from backend.config import settings

# -----------------------------
# 1. Generate Synthetic Dataset
# -----------------------------

def generate_dataset(n_samples=500):
    X = []
    y = []

    for _ in range(n_samples):
        confidence = random.uniform(0, 1)
        complexity = random.uniform(0, 1)
        depth = random.uniform(0, 1)

        # Simulated "true risk"
        risk_score = (
            0.5 * confidence +
            0.3 * depth +
            0.2 * complexity
        )

        # Add slight noise
        risk_score += random.uniform(-0.05, 0.05)

        X.append([confidence, complexity, depth])
        y.append(min(max(risk_score, 0), 1))

    return np.array(X), np.array(y)


# -----------------------------
# 2. Train Model
# -----------------------------

def train_model():
    print("[+] Generating dataset...")
    X, y = generate_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1
    )

    print("[+] Training XGBoost model...")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)

    print(f"[✓] Training complete | MSE: {mse:.4f}")

    return model


# -----------------------------
# 3. Extract Feature Importance
# -----------------------------

def extract_weights(model):
    """
    Convert model feature importance into weights
    """
    importances = model.feature_importances_

    # Normalize
    total = sum(importances)
    if total == 0:
        return {
            "confidence": 0.5,
            "complexity": 0.2,
            "depth": 0.3
        }

    weights = {
        "confidence": float(importances[0] / total),
        "complexity": float(importances[1] / total),
        "depth": float(importances[2] / total)
    }

    return weights


# -----------------------------
# 4. Save Model Weights
# -----------------------------

def save_weights(weights):
    os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)

    with open(settings.MODEL_PATH, "w") as f:
        json.dump(weights, f, indent=4)

    print(f"[✓] Weights saved to {settings.MODEL_PATH}")


# -----------------------------
# MAIN EXECUTION
# -----------------------------

if __name__ == "__main__":
    model = train_model()
    weights = extract_weights(model)
    save_weights(weights)

    print("\nFinal Learned Weights:")
    print(json.dumps(weights, indent=4))