import cv2
import numpy as np

img = cv2.imread("scratch/fa38_frame_0.png")
# Subtitle "It looks white" is at y=910..970, x=220..500
# Let's set ROI covering the subtitle: y=890..980, x=200..520
roi_y1, roi_y2 = 890, 980
roi_x1, roi_x2 = 200, 520
crop = img[roi_y1:roi_y2, roi_x1:roi_x2]

b, g, r = cv2.split(crop)
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
s = hsv[:, :, 1]
v = hsv[:, :, 2]
min_rgb = np.minimum(np.minimum(r, g), b)

# White core
white_core = (min_rgb >= 190) & (s <= 60) & (v >= 195)
k_near = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
near_white = cv2.dilate(white_core.astype(np.uint8), k_near)

# Compare stroke <= 75 vs stroke <= 120 near white text
for stroke_v in [75, 95, 115, 125]:
    stroke = (v <= stroke_v)
    stroke_near_white = stroke & (near_white > 0)
    near_stroke = cv2.dilate(stroke.astype(np.uint8), k_near)
    core_near_stroke = white_core & (near_stroke > 0)
    combined = ((stroke_near_white | core_near_stroke).astype(np.uint8) * 255)
    
    k_connect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, k_connect)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(closed)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= 20:
            mask_cnt = np.zeros_like(closed)
            cv2.drawContours(mask_cnt, [cnt], -1, 255, -1)
            if np.count_nonzero(white_core & (mask_cnt > 0)) >= 5:
                filled[mask_cnt > 0] = 255
    k_dil = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    m = cv2.dilate(filled, k_dil, iterations=2)
    cv2.imwrite(f"scratch/stroke_v_{stroke_v}.png", m)
    print(f"Stroke V<={stroke_v}: detected pixels={np.count_nonzero(m)}")
