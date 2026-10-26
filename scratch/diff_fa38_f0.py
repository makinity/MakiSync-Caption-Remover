import cv2
import numpy as np

rep_path = r"C:\Users\Maki Liones\AppData\Local\Temp\vrt_fa38af23\repaired_fa38af23.mp4"
cap_r = cv2.VideoCapture(rep_path)

ret_0, f0 = cap_r.read()

# Let's inspect the entire frame 0 of repaired_fa38af23.mp4
# Does frame 0 contain "It looks white"?
cv2.imwrite("scratch/fa38_f0.png", f0)

# Where did differences occur in repaired_fa38af23.mp4?
# Let's find what was actually inpainted in repaired_fa38af23.mp4!
# Let's compare frame 0, 30, 60, 90, 120, 150 against orig video around 35.3s (frame 1060)
orig_path = r"C:\Users\Maki Liones\AppData\Local\Temp\gradio\a4d0427ffd575e9be347e6ce5173940b26494b1cac94afc44d47c2d9db85b86b\m2196768087813530_qXpnnwv4Oyo.mp4"
cap_o = cv2.VideoCapture(orig_path)

cap_o.set(cv2.CAP_PROP_POS_FRAMES, 1060)
ret_o0, fo0 = cap_o.read()

diff0 = cv2.absdiff(f0, fo0)
print(f"Max diff between f0 of repaired and frame 1060 of orig: {diff0.max()}")
print(f"Number of changed pixels (diff > 15): {np.count_nonzero(diff0 > 15)}")

# Let's check where the changed pixels are
ys, xs = np.where(diff0.max(axis=2) > 15)
if len(xs) > 0:
    print(f"Changed pixels in frame 0: X=[{xs.min()}, {xs.max()}], Y=[{ys.min()}, {ys.max()}]")
else:
    print("ZERO CHANGED PIXELS in frame 0 between repaired and frame 1060!")

cap_o.release()
cap_r.release()
