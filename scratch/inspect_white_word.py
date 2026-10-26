import cv2
import numpy as np

crop = cv2.imread("scratch/zoom_it_looks_white.png")
# In zoom_it_looks_white (shape 60x250):
# Find where the word "white" is: x from 120 to 250
white_word = crop[:, 120:]
cv2.imwrite("scratch/zoom_white_word.png", white_word)

b, g, r = cv2.split(white_word)
hsv = cv2.cvtColor(white_word, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)

min_rgb = np.minimum(np.minimum(r, g), b)
# In white_stroke: white_core = (min_rgb >= 190) & (s <= 60) & (v >= 195)
core = (min_rgb >= 190) & (s <= 60) & (v >= 195)
print(f"White core in 'white' word: {np.count_nonzero(core)}")

# What are the actual values of the letters 'h', 'i', 't', 'e'?
print(f"Max min_rgb in 'white' word: {min_rgb.max()}")
print(f"Max V in 'white' word: {v.max()}")
print(f"Min S in 'white' word: {s.min()}")

ys, xs = np.where(min_rgb >= 170)
print(f"Pixels with min_rgb >= 170 in 'white' word: {len(xs)}")
for i in range(min(10, len(xs))):
    print(f"  x={xs[i]}, y={ys[i]}: BGR={white_word[ys[i], xs[i]]}, S={s[ys[i], xs[i]]}, V={v[ys[i], xs[i]]}")
