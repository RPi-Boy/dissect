"""
attack_simulator.py — Threat Visualization Controller.

Bridges the OpenAPI web framework with the OpenCV drawing engines to
provide animated streams (M-JPEG) of specific attack surfaces identified
by the LLM in the "Brain" engine.
"""

import asyncio
from typing import AsyncGenerator

from opencv_engine.animations import (
    generate_sqli_frame, 
    generate_buffer_overflow_frame
)


async def simulate_attack_stream(attack_type: str) -> AsyncGenerator[bytes, None]:
    """Generate a sequence of JPEG frames for an attack animation.
    
    This acts as an M-JPEG boundary stream, yielding individual 
    frames with the appropriate multipart HTTP headers.

    Args:
        attack_type: The identifier for the attack visualization (e.g., 'sqli').

    Yields:
        M-JPEG multipart byte chunks.
    """
    # 100 frames per animation loop
    for step in range(101):
        if attack_type == "sqli":
            frame_bytes = generate_sqli_frame(step)
        elif attack_type == "buffer_overflow":
            frame_bytes = generate_buffer_overflow_frame(step)
        else:
            # Fallback to general/unknown attack
            frame_bytes = generate_sqli_frame(step) 
            
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        
        # ~30 FPS
        await asyncio.sleep(0.033)
