import cv2
import numpy as np

img = cv2.imread("scratch/fa38_frame_0.png")
h, w = img.shape[:2]

# Let's find white pixels in fa38_frame_0.png
b, g, r = cv2.split(img)
white = (r > 230) & (g > 230) & (b > 230)
# Look in the lower third (y > 700)
white_lower = white.copy()
white_lower[:700, :] = False
ys, xs = np.where(white_lower)
if len(xs) > 0:
    print(f"Text 'It looks white' bounds: X=[{xs.min()}, {xs.max()}], Y=[{ys.min()}, {ys.max()}]")
else:
    print("No white text found in lower third!")

# Let's test what white mask detects on this exact frame with ROI covering it
from app.config import AppConfig
from app.models import ROI
from app.subtitle_mask.color_mask import MaskParams, build_subtitle_mask

roi = ROI(x=xs.min()-10, y=ys.min()-10, w=xs.max()-xs.min()+20, h=ys.max()-ys.min()+20)
print(f"Testing ROI: {roi}")

for mode in ["white", "white_stroke"]:
    p = MaskParams.from_config(AppConfig(subtitle_color=mode))
    m = build_subtitle_mask(img, roi, p)
    cv2.imwrite(f"scratch/mask_it_looks_white_{mode}.png", m)
    print(f"Mode {mode} mask pixels: {np.count_nonzero(m)}")
