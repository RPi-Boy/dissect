from backend.ai_engine.prompt_builder import build_prompt
from backend.ai_engine.report_parser import parse_llm_output
from backend.ai_engine.local_llm import run_local_llm
from backend.ai_engine.confidence_calibrator import calibrate_confidence
from backend.ai_engine.cot_validator import validate_reasoning

def analyze_code(code: str):
    prompt = build_prompt(code)

    # Run local LLM (Ollama)
    raw_output = run_local_llm(prompt)

    parsed = parse_llm_output(raw_output)

    # Validate reasoning
    is_valid = validate_reasoning(parsed.get("reasoning", ""))

    # Adjust confidence
    confidence = calibrate_confidence(parsed.get("confidence", 0.5), is_valid)

    parsed["confidence"] = confidence
    parsed["valid_reasoning"] = is_valid

    return parsed