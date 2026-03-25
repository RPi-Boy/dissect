import cv2
import time

def animate_flow(frame, positions, edges):
    """
    Simulates red attack packets moving through graph
    """

    for src, dst in edges:
        if src in positions and dst in positions:
            start = positions[src]
            end = positions[dst]

            steps = 20
            for i in range(steps):
                temp = frame.copy()

                x = int(start[0] + (end[0] - start[0]) * (i / steps))
                y = int(start[1] + (end[1] - start[1]) * (i / steps))

                cv2.circle(temp, (x, y), 8, (0, 0, 255), -1)

                cv2.imshow("DISSECT - Attack Simulation", temp)
                cv2.waitKey(30)