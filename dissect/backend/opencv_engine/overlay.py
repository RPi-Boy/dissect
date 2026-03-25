import cv2

def draw_overlay(frame, risk: str):
    """
    Adds risk label and UI overlay
    """

    color = (0, 255, 0)

    if risk == "HIGH":
        color = (0, 165, 255)
    elif risk == "CRITICAL":
        color = (0, 0, 255)

    cv2.rectangle(frame, (0, 0), (900, 60), (30, 30, 30), -1)

    cv2.putText(frame, f"RISK LEVEL: {risk}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                2)