import cv2
import numpy as np

rep_path = r"C:\Users\Maki Liones\AppData\Local\Temp\vrt_fa38af23\repaired_fa38af23.mp4"
orig_path = r"C:\Users\Maki Liones\AppData\Local\Temp\gradio\a4d0427ffd575e9be347e6ce5173940b26494b1cac94afc44d47c2d9db85b86b\m2196768087813530_qXpnnwv4Oyo.mp4"

cap_r = cv2.VideoCapture(rep_path)
ret_0, f0 = cap_r.read()
cap_r.release()

cap_o = cv2.VideoCapture(orig_path)
cap_o.set(cv2.CAP_PROP_POS_FRAMES, 1140)
ret_o, fo = cap_o.read()
cap_o.release()

diff = cv2.absdiff(f0, fo)
gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
cv2.imwrite("scratch/diff_visual_1140.png", gray_diff * 5) # amplified diff

# Let's check text region at y=900..1000 in both
cv2.imwrite("scratch/crop_fo_text.png", fo[900:1000, 200:520])
cv2.imwrite("scratch/crop_f0_text.png", f0[900:1000, 200:520])

diff_text = cv2.absdiff(fo[900:1000, 200:520], f0[900:1000, 200:520])
print(f"Diff in text region [900:1000, 200:520]: max={diff_text.max()}, mean={diff_text.mean()}")
