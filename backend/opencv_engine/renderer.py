"""
renderer.py — Headless OpenCV Canva & Fallback.

Provides a drawing canvas for programmatic security visualizations.
If OpenCV is missing in the environment, provides a fallback that returns
a robust text-based SVG or pure black image bytes to prevent crashes.
"""

import logging
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("OpenCV (cv2) not found. Renderer will use SVG fallbacks.")


class CanvasRenderer:
    """Manages the drawing surface for attack animations."""

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        if HAS_CV2:
            # Create a blank dark-themed canvas
            self.frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Background color (dark gray/blue)
            self.frame[:] = (30, 20, 20)

    def draw_node(self, x: int, y: int, color: tuple[int, int, int] = (0, 255, 0), radius: int = 15):
        """Draw a server/function node on the canvas."""
        if HAS_CV2:
            cv2.circle(self.frame, (x, y), radius, color, -1)
            cv2.circle(self.frame, (x, y), radius + 2, (255, 255, 255), 1)

    def draw_edge(self, pt1: tuple[int, int], pt2: tuple[int, int], color: tuple[int,int,int]=(100,100,100)):
        """Draw a connecting line between nodes."""
        if HAS_CV2:
            cv2.line(self.frame, pt1, pt2, color, 2)

    def add_text(self, text: str, x: int, y: int, color: tuple[int,int,int] = (255, 255, 255)):
        """Add label text."""
        if HAS_CV2:
            cv2.putText(self.frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)

    def export_jpeg_bytes(self) -> bytes:
        """Export the current frame as JPEG bytes for HTTP streaming."""
        if HAS_CV2:
            _, buffer = cv2.imencode('.jpg', self.frame)
            return buffer.tobytes()
        else:
            # Fallback to a simple SVG if OpenCV is not installed
            svg = f'''<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="#1a1a2e" />
                <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#ff4c4c" font-family="monospace" font-size="24">
                    [OpenCV Missing] Threat Visualization Disabled
                </text>
            </svg>'''
            return svg.encode("utf-8")
