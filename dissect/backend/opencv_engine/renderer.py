import cv2
import numpy as np
from backend.opencv_engine.animations import animate_flow
from backend.opencv_engine.overlay import draw_overlay

def render_attack(graph: dict, risk: str):
    """
    Renders attack simulation as a simple animation
    """

    width, height = 900, 500
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    nodes = graph.get("nodes", [])

    positions = {}
    step_x = width // (len(nodes) + 1)

    for i, node in enumerate(nodes):
        positions[node] = (step_x * (i + 1), height // 2)

    # Draw nodes
    for node, pos in positions.items():
        cv2.circle(frame, pos, 20, (0, 255, 0), -1)
        cv2.putText(frame, node[:10], (pos[0] - 40, pos[1] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Draw edges
    for src, dst in graph.get("edges", []):
        if src in positions and dst in positions:
            cv2.line(frame, positions[src], positions[dst], (255, 255, 255), 2)

    # Animate attack
    animate_flow(frame, positions, graph.get("edges", []))

    # Add overlay (risk label)
    draw_overlay(frame, risk)

    cv2.imshow("DISSECT - Attack Simulation", frame)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()