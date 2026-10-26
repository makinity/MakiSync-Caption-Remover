import cv2
import numpy as np

# Find where "It looks white" is in the original video
orig_path = r"C:\Users\Maki Liones\AppData\Local\Temp\gradio\a4d0427ffd575e9be347e6ce5173940b26494b1cac94afc44d47c2d9db85b86b\m2196768087813530_qXpnnwv4Oyo.mp4"
rep_path = r"C:\Users\Maki Liones\AppData\Local\Temp\vrt_fa38af23\repaired_fa38af23.mp4"

cap_o = cv2.VideoCapture(orig_path)
cap_r = cv2.VideoCapture(rep_path)

ret_r, fr = cap_r.read()
# Find matching frame in orig
# In the studio UI, the trim was 6.2s starting around 00:35.3 to 00:41.5!
# 35.3 seconds * 30 fps ~ frame 1060!
cap_o.set(cv2.CAP_PROP_POS_FRAMES, 1060)
ret_o, fo = cap_o.read()

# Let's save both around y=900..1000, x=200..500
y1, y2 = 900, 1000
x1, x2 = 200, 500

if ret_r:
    cv2.imwrite("scratch/rep_text_crop.png", fr[y1:y2, x1:x2])
if ret_o:
    cv2.imwrite("scratch/orig_text_crop.png", fo[y1:y2, x1:x2])

# Let's test what white mask does on orig_text_crop vs white_stroke
from app.config import AppConfig
from app.models import ROI
from app.subtitle_mask.color_mask import MaskParams, build_subtitle_mask

if ret_o:
    roi = ROI(x=200, y=900, w=300, h=100)
    for mode in ["white", "white_stroke"]:
        p = MaskParams.from_config(AppConfig(subtitle_color=mode))
        m = build_subtitle_mask(fo, roi, p)
        cv2.imwrite(f"scratch/mask_sub_{mode}.png", m[y1:y2, x1:x2])
        print(f"Sub mask '{mode}' non-zero pixels: {np.count_nonzero(m)}")

cap_o.release()
cap_r.release()
