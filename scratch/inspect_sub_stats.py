import cv2
import numpy as np

img = cv2.imread("scratch/fa38_frame_0.png")
# Find text "It looks white"
# It is located around y=900..980, x=220..500
crop = img[910:970, 230:480]
cv2.imwrite("scratch/zoom_it_looks_white.png", crop)

b, g, r = cv2.split(crop)
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)

print("--- Text 'It looks white' stats ---")
print(f"R min={r.min()}, max={r.max()}, mean={r.mean():.1f}")
print(f"G min={g.min()}, max={g.max()}, mean={g.mean():.1f}")
print(f"B min={b.min()}, max={b.max()}, mean={b.mean():.1f}")
print(f"V min={v.min()}, max={v.max()}, mean={v.mean():.1f}")
print(f"S min={s.min()}, max={s.max()}, mean={s.mean():.1f}")

# Look at the dark stroke / shadow of the text
# In white_stroke: stroke = (v <= 75)
stroke_75 = (v <= 75)
print(f"Pixels with V <= 75 in crop: {np.count_nonzero(stroke_75)}")

# What is the V of the shadow around the letters?
# Let's check shadow pixels
print(f"Pixels with V <= 90: {np.count_nonzero(v <= 90)}")
print(f"Pixels with V <= 110: {np.count_nonzero(v <= 110)}")
print(f"Pixels with V <= 130: {np.count_nonzero(v <= 130)}")

# Look at the skin background around the text
# Skin V:
print(f"Skin pixels (V between 140 and 200, S between 50 and 150): {np.count_nonzero((v >= 140) & (v <= 200) & (s >= 50))}")

# Look at the white core of the letters
# In white_stroke: white_core = (min_rgb >= 190) & (s <= 60) & (v >= 195)
min_rgb = np.minimum(np.minimum(r, g), b)
white_core = (min_rgb >= 190) & (s <= 60) & (v >= 195)
print(f"White core pixels in crop: {np.count_nonzero(white_core)}")
