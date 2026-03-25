import json
import re

def parse_llm_output(output: str):
    try:
        # Try direct JSON
        return json.loads(output)
    except:
        # Extract JSON block
        match = re.search(r'\{.*\}', output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass

    # Fallback
    return {
        "vulnerability": "Unknown",
        "confidence": 0.5,
        "reasoning": "Parsing failed"
    }