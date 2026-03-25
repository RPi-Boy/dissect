from backend.repo_processor import clone_repo
from backend.data_masking import mask_data
from backend.ai_engine.llm_analyzer import analyze_code
from backend.ml_model.predict import predict_risk
from backend.graph_engine.graph_builder import build_graph
from backend.opencv_engine.renderer import render_attack
from backend.reporting.report_generator import generate_report

from backend.pipeline.state_manager import update_state, mark_completed


def run_pipeline(repo_url: str, job_id: str):
    try:
        print(f"[+] Starting job {job_id}")

        # Step 1: Clone Repo
        update_state(job_id, "CLONING", 10)
        repo_path = clone_repo(repo_url)

        # Step 2: Mask Data
        update_state(job_id, "MASKING", 25)
        masked_code = mask_data(repo_path)

        # Step 3: Build Graph
        update_state(job_id, "GRAPH_BUILDING", 40)
        graph = build_graph(masked_code)

        # Step 4: LLM Analysis
        update_state(job_id, "LLM_ANALYSIS", 60)
        llm_result = analyze_code(masked_code)

        # Step 5: Risk Prediction
        update_state(job_id, "ML_SCORING", 75)
        risk = predict_risk(llm_result, graph)

        # Step 6: Visualization
        update_state(job_id, "RENDERING", 90)
        render_attack(graph, risk)

        # Step 7: Report
        report = generate_report(llm_result, risk)

        # Done
        mark_completed(job_id, report)

        print(f"[✓] Job {job_id} completed")

    except Exception as e:
        print(f"[ERROR] {str(e)}")