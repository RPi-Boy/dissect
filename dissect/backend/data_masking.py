import os
import re

# Regex patterns for secrets
PATTERNS = [
    r'AKIA[0-9A-Z]{16}',               # AWS keys
    r'[\w\.-]+@[\w\.-]+',              # Emails
    r'(?i)password\s*=\s*["\'].*?["\']',
    r'(?i)api[_-]?key\s*=\s*["\'].*?["\']'
]

def mask_data(repo_path: str):
    masked_code = ""

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".java")):
                try:
                    with open(os.path.join(root, file), "r", errors="ignore") as f:
                        code = f.read()

                        for pattern in PATTERNS:
                            code = re.sub(pattern, "[REDACTED]", code)

                        masked_code += code + "\n"
                except:
                    continue

    return masked_code