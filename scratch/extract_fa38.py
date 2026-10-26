import cv2
import numpy as np

rep_path = r"C:\Users\Maki Liones\AppData\Local\Temp\vrt_fa38af23\repaired_fa38af23.mp4"
cap = cv2.VideoCapture(rep_path)
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Repaired fa38af23: {w}x{h}, {total} frames, fps={fps}")

# Extract frame 0, 30, 60, 90, 120, 150, 180
for i in range(0, total, 20):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f"scratch/fa38_frame_{i}.png", frame)

cap.release()
print("Saved sample frames from fa38af23")
