import cv2
import numpy as np

rep_path = r"C:\Users\Maki Liones\AppData\Local\Temp\vrt_fa38af23\repaired_fa38af23.mp4"
cap_r = cv2.VideoCapture(rep_path)
ret_0, f0 = cap_r.read()
cap_r.release()

orig_path = r"C:\Users\Maki Liones\AppData\Local\Temp\gradio\a4d0427ffd575e9be347e6ce5173940b26494b1cac94afc44d47c2d9db85b86b\m2196768087813530_qXpnnwv4Oyo.mp4"
cap_o = cv2.VideoCapture(orig_path)
total = int(cap_o.get(cv2.CAP_PROP_FRAME_COUNT))

# Find matching frame
# Let's check a small region (her nose/eye at y=400..500, x=300..400)
ref_patch = f0[400:500, 300:400]

min_diff = 1e9
best_idx = -1
for i in range(0, total, 10):
    cap_o.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap_o.read()
    if not ret:
        break
    patch = frame[400:500, 300:400]
    d = np.mean(cv2.absdiff(ref_patch, patch))
    if d < min_diff:
        min_diff = d
        best_idx = i

print(f"Best match for f0 is at frame {best_idx} (diff={min_diff:.2f})")
# Check around best_idx
for i in range(max(0, best_idx-10), min(total, best_idx+10)):
    cap_o.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap_o.read()
    patch = frame[400:500, 300:400]
    d = np.mean(cv2.absdiff(ref_patch, patch))
    if d < min_diff:
        min_diff = d
        best_idx = i

print(f"Exact match for f0 is at frame {best_idx} ({best_idx/30.0:.2f}s)")
cap_o.set(cv2.CAP_PROP_POS_FRAMES, best_idx)
ret, match_frame = cap_o.read()
cap_o.release()

# Now compare f0 and match_frame!
diff = cv2.absdiff(f0, match_frame)
ys, xs = np.where(diff.max(axis=2) > 15)
if len(xs) > 0:
    print(f"Regions inpainted in frame {best_idx}: X=[{xs.min()}, {xs.max()}], Y=[{ys.min()}, {ys.max()}], total changed={len(xs)}")
else:
    print("NO INPAINTING OCCURRED IN THIS FRAME AT ALL!")
