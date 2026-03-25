def build_prompt(code: str):
    return f"""
You are a security auditor.

Analyze the following code and detect vulnerabilities.

Return JSON:
{{
  "vulnerability": "...",
  "confidence": 0.0-1.0,
  "reasoning": "..."
}}

Code:
{code[:5000]}
"""