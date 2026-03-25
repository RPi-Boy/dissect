import re

SECRET_PATTERNS = {
    "AWS_KEY": r'AKIA[0-9A-Z]{16}',
    "EMAIL": r'[\w\.-]+@[\w\.-]+',
    "API_KEY": r'(?i)api[_-]?key\s*=\s*["\'].*?["\']',
    "PASSWORD": r'(?i)password\s*=\s*["\'].*?["\']'
}

def detect_secrets(code: str):
    findings = []

    for name, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, code)
        for match in matches:
            findings.append({
                "type": name,
                "match": match[:10] + "...",
            })

    return findings