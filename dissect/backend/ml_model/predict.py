from backend.ml_model.model import RiskModel
from backend.ml_model.feature_extractor import extract_features
from backend.ml_model.rules_engine import apply_rules
from backend.constants import *

model = RiskModel()

def predict_risk(llm_result: dict, graph: dict):
    # Step 1: Extract features
    features = extract_features(llm_result, graph)

    # Step 2: ML Score
    ml_score = model.predict(features)

    # Step 3: Rule-based adjustment
    rule_score = apply_rules(features, graph)

    final_score = (ml_score * 0.7) + (rule_score * 0.3)

    # Step 4: Convert to risk level
    if final_score > 0.8:
        return RISK_CRITICAL
    elif final_score > 0.6:
        return RISK_HIGH
    elif final_score > 0.4:
        return RISK_MEDIUM
    else:
        return RISK_LOW