"""LaMa image inpainting backend with Anti-Flicker Stable ROI and Batched Tensor Processing.

Features:
* Stable Crop Bounds: Computes a single fixed ROI crop box across all video frames to
  completely eliminate spatial jitter, texture hopping, and coordinate flicker.
* Batched Tensor Inpainting: Processes frames in parallel batches directly on PyTorch tensors,
  avoiding per-frame PIL conversions and drastically speeding up processing on both CPU and GPU.
* Modulo-8 Reflection Padding: Dynamic padding ensures the network receives exact multiples
  of 8 without seam artifacts or distortion.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm

from ..config import AppConfig
from ..utils.logging_utils import get_logger
from .base import InpaintingBackend

log = get_logger("inpaint.lama")


def _pick_device(pref: str) -> str:
    if pref and pref != "auto":
        return pref
    try:
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


class LaMaBackend(InpaintingBackend):
    name = "lama"

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.device = _pick_device(cfg.lama_device)
        self._lama = None  # lazy
        self._pil_image = None

    def warmup(self) -> None:
        if self._lama is not None:
            return
        try:
            from simple_lama_inpainting import SimpleLama
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "simple-lama-inpainting is not installed. Run "
                "`pip install simple-lama-inpainting`."
            ) from e
        log.info("Loading LaMa on device=%s (first run downloads ~200MB weights)...", self.device)
        try:
            self._lama = SimpleLama(device=torch.device(self.device))
        except TypeError:
            self._lama = SimpleLama()
        self._pil_image = Image
        log.info("LaMa ready on %s.", self.device)

    def _get_stable_crop_bounds(
        self,
        frame_shape: Tuple[int, int],
        roi: Optional[Tuple[int, int, int, int]],
        masks: Optional[List[np.ndarray]] = None,
    ) -> Tuple[int, int, int, int]:
        """Compute a single static bounding box for the entire video clip.
        
        Using an identical crop box for all frames eliminates spatial flicker
        and background texture shifting.
        """
        h_frame, w_frame = frame_shape[:2]
        pad = max(0, self.cfg.lama_crop_padding) + max(0, self.cfg.lama_dilate_extra) * 2

        if roi is not None:
            rx, ry, rw, rh = roi
            x1 = max(0, rx - pad)
            y1 = max(0, ry - pad)
            x2 = min(w_frame, rx + rw + pad)
            y2 = min(h_frame, ry + rh + pad)
        elif masks is not None:
            all_pts = []
            for m in masks:
                pts = cv2.findNonZero(m)
                if pts is not None:
                    all_pts.append(pts)
            if not all_pts:
                return 0, 0, w_frame, h_frame
            merged_pts = np.vstack(all_pts)
            x, y, w, h = cv2.boundingRect(merged_pts)
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(w_frame, x + w + pad)
            y2 = min(h_frame, y + h + pad)
        else:
            return 0, 0, w_frame, h_frame

        return x1, y1, x2, y2

    def inpaint(self, frame_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Single-frame fallback inpainting."""
        if self._lama is None:
            self.warmup()

        if not mask.any():
            return frame_bgr

        h_frame, w_frame = frame_bgr.shape[:2]
        x1, y1, x2, y2 = self._get_stable_crop_bounds((h_frame, w_frame), self.cfg.roi, [mask])

        frame_crop = frame_bgr[y1:y2, x1:x2]
        mask_crop = mask[y1:y2, x1:x2].copy()

        if self.cfg.lama_dilate_extra > 0:
            k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            mask_crop = cv2.dilate(mask_crop, k, iterations=self.cfg.lama_dilate_extra)

        rgb = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        chw = np.transpose(rgb, (2, 0, 1))[np.newaxis, :, :, :]
        m_norm = (mask_crop > 0).astype(np.float32)[np.newaxis, np.newaxis, :, :]

        dev = self._lama.device if hasattr(self._lama, "device") else torch.device(self.device)
        tensor_crop = torch.from_numpy(chw).to(dev)
        tensor_mask = torch.from_numpy(m_norm).to(dev)

        crop_h, crop_w = tensor_crop.shape[2], tensor_crop.shape[3]
        pad_h = (8 - crop_h % 8) % 8
        pad_w = (8 - crop_w % 8) % 8
        if pad_h > 0 or pad_w > 0:
            tensor_crop = F.pad(tensor_crop, (0, pad_w, 0, pad_h), mode="reflect")
            tensor_mask = F.pad(tensor_mask, (0, pad_w, 0, pad_h), mode="constant", value=0.0)

        with torch.inference_mode():
            res = self._lama.model(tensor_crop, tensor_mask)
            if pad_h > 0 or pad_w > 0:
                res = res[:, :, :crop_h, :crop_w]
            res = torch.clamp(res, 0.0, 1.0)
            res_np = (res[0].permute(1, 2, 0).detach().cpu().numpy() * 255.0).astype(np.uint8)

        repaired_bgr = cv2.cvtColor(res_np, cv2.COLOR_RGB2BGR)
        alpha = cv2.GaussianBlur(mask_crop.astype(np.float32) / 255.0, (5, 5), 1.2)[:, :, np.newaxis]
        blended = (frame_crop.astype(np.float32) * (1.0 - alpha) + repaired_bgr.astype(np.float32) * alpha).astype(np.uint8)
        out = frame_bgr.copy()
        out[y1:y2, x1:x2] = blended
        return out

    def inpaint_video(
        self,
        frames_bgr: List[np.ndarray],
        masks: List[np.ndarray],
    ) -> List[np.ndarray]:
        if len(frames_bgr) != len(masks):
            raise ValueError("frames and masks must have the same length")

        if self._lama is None:
            self.warmup()

        n_frames = len(frames_bgr)
        if n_frames == 0:
            return []

        h_frame, w_frame = frames_bgr[0].shape[:2]
        x1, y1, x2, y2 = self._get_stable_crop_bounds(
            (h_frame, w_frame),
            roi=self.cfg.roi,
            masks=masks,
        )

        log.info(
            "LaMa stable static crop: [%d:%d, %d:%d] (size %dx%d) across all frames",
            y1, y2, x1, x2, (x2 - x1), (y2 - y1),
        )

        # Active frames that actually have subtitle pixels inside the crop
        active_indices = [i for i, m in enumerate(masks) if m[y1:y2, x1:x2].any()]
        log.info("LaMa will process %d/%d active subtitle frames", len(active_indices), n_frames)

        out_frames = [f.copy() for f in frames_bgr]
        if not active_indices:
            return out_frames

        dilate_k = None
        if self.cfg.lama_dilate_extra > 0:
            dilate_k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        batch_size = max(1, getattr(self.cfg, "batch_size", 4))
        dev = self._lama.device if hasattr(self._lama, "device") else torch.device(self.device)

        for b_start in tqdm(range(0, len(active_indices), batch_size), desc="lama"):
            b_indices = active_indices[b_start : b_start + batch_size]
            b_crops = []
            b_masks = []

            for idx in b_indices:
                f_crop = frames_bgr[idx][y1:y2, x1:x2]
                m_crop = masks[idx][y1:y2, x1:x2]
                if dilate_k is not None:
                    m_crop = cv2.dilate(m_crop, dilate_k, iterations=self.cfg.lama_dilate_extra)

                # BGR -> RGB normalized float32 CHW
                rgb = cv2.cvtColor(f_crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
                b_crops.append(np.transpose(rgb, (2, 0, 1)))

                # Mask 1HW
                m_norm = (m_crop > 0).astype(np.float32)[np.newaxis, :, :]
                b_masks.append(m_norm)

            tensor_crops = torch.from_numpy(np.stack(b_crops)).to(dev)
            tensor_masks = torch.from_numpy(np.stack(b_masks)).to(dev)

            crop_h, crop_w = tensor_crops.shape[2], tensor_crops.shape[3]
            pad_h = (8 - crop_h % 8) % 8
            pad_w = (8 - crop_w % 8) % 8
            if pad_h > 0 or pad_w > 0:
                tensor_crops = F.pad(tensor_crops, (0, pad_w, 0, pad_h), mode="reflect")
                tensor_masks = F.pad(tensor_masks, (0, pad_w, 0, pad_h), mode="constant", value=0.0)

            with torch.inference_mode():
                inpainted_batch = self._lama.model(tensor_crops, tensor_masks)
                if pad_h > 0 or pad_w > 0:
                    inpainted_batch = inpainted_batch[:, :, :crop_h, :crop_w]
                inpainted_batch = torch.clamp(inpainted_batch, 0.0, 1.0)
                res_np = (inpainted_batch.permute(0, 2, 3, 1).detach().cpu().numpy() * 255.0).astype(np.uint8)

            for i, idx in enumerate(b_indices):
                repaired_bgr = cv2.cvtColor(res_np[i], cv2.COLOR_RGB2BGR)
                f_crop = frames_bgr[idx][y1:y2, x1:x2]
                m_crop = masks[idx][y1:y2, x1:x2]
                if dilate_k is not None:
                    m_crop = cv2.dilate(m_crop, dilate_k, iterations=self.cfg.lama_dilate_extra)

                # Seamless sub-pixel alpha feathering: only inpaint where the subtitle mask is!
                # Keeps 100% of surrounding background pixel-crisp with zero blur smudges!
                alpha = cv2.GaussianBlur(m_crop.astype(np.float32) / 255.0, (5, 5), 1.2)[:, :, np.newaxis]
                blended = (f_crop.astype(np.float32) * (1.0 - alpha) + repaired_bgr.astype(np.float32) * alpha).astype(np.uint8)
                out_frames[idx][y1:y2, x1:x2] = blended

        return out_frames
