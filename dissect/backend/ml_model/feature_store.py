FEATURE_STORE = {}

def store_features(job_id: str, features: dict):
    FEATURE_STORE[job_id] = features

def get_features(job_id: str):
    return FEATURE_STORE.get(job_id, {})