"""
animations.py — Attack Vector Visualization Logic.

Defines the sequence of drawing calls for specific threat vectors
(e.g., SQL Injection, Buffer Overflow) to be rendered on the CanvasRenderer.
"""

import time
from .renderer import CanvasRenderer


def generate_sqli_frame(step: int) -> bytes:
    """Generate a single frame representing an SQL Injection attack.
    
    Args:
        step: The animation step (0 to 100).
        
    Returns:
        JPEG or SVG bytes of the rendered frame.
    """
    canvas = CanvasRenderer(width=600, height=400)
    
    # Static nodes
    client_pos = (100, 200)
    api_pos = (300, 200)
    db_pos = (500, 200)
    
    # Edges
    canvas.draw_edge(client_pos, api_pos)
    canvas.draw_edge(api_pos, db_pos)
    
    # Nodes
    canvas.draw_node(*client_pos, color=(200, 200, 200)) # Client
    canvas.draw_node(*api_pos, color=(255, 165, 0))      # API
    canvas.draw_node(*db_pos, color=(50, 50, 200))       # Database
    
    # Labels
    canvas.add_text("Client", client_pos[0]-25, client_pos[1]-25)
    canvas.add_text("FastAPI", api_pos[0]-25, api_pos[1]-25)
    canvas.add_text("PostgreSQL", db_pos[0]-40, db_pos[1]-25)
    
    # Animation logic: Red payload moving from client to DB
    payload_x = 100 + int((step / 100) * 400)
    
    # Draw malicious payload
    canvas.draw_node(payload_x, 200, color=(0, 0, 255), radius=6)
    canvas.add_text("DROP TABLE", payload_x-20, 180, color=(0, 0, 255))
    
    # Database compromise effect at the end
    if step > 90:
        canvas.draw_node(*db_pos, color=(0, 0, 255), radius=25)
        canvas.add_text("COMPROMISED", db_pos[0]-50, db_pos[1]+40, color=(0, 0, 255))
        
    return canvas.export_jpeg_bytes()


def generate_buffer_overflow_frame(step: int) -> bytes:
    """Generate a frame for a Buffer Overflow memory corruption."""
    canvas = CanvasRenderer(width=600, height=400)
    
    canvas.add_text("Memory Stack", 50, 50)
    
    # Draw memory slots
    for i in range(10):
        y = 100 + (i * 25)
        color = (100, 100, 100)
        
        # Buffer region
        if 3 <= i <= 6:
            color = (50, 200, 50)
            
        # Overflowing region
        if step > (i * 10) and i >= 3:
            color = (0, 0, 255) # Corrupted red
            
        # Return address pointer
        if i == 8:
            canvas.add_text("<-- RET ADDR", 320, y+15, color=(200, 200, 0))
            if step > 80:
                color = (0, 0, 255) # Hijacked
                
        canvas.draw_edge((200, y), (300, y), color=color)
        canvas.draw_edge((200, y+20), (300, y+20), color=color)
        canvas.draw_edge((200, y), (200, y+20), color=color)
        canvas.draw_edge((300, y), (300, y+20), color=color)
        
    if step > 85:
        canvas.add_text("!!! EXECUTION HIJACKED !!!", 150, 380, color=(0, 0, 255))
        
    return canvas.export_jpeg_bytes()
