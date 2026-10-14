"""Color-threshold subtitle mask generator with Stroke-Anchored Contour Detection.

Features:
* Stroke-Anchored Subtitle Masking: Accurately isolates hardcoded subtitles (white core + dark stroke)
  without leaking into surrounding light backgrounds (e.g. white cell membranes, lab coats, sky)
  or dark background textures (e.g. hair, dark clothes).
* Adaptive Vertical Margin: Auto-expands the search ROI by 35px vertically so subtitle lines across
  different timestamps that sit slightly higher or lower are never partially chopped off.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from ..config import AppConfig
from ..models import ROI


@dataclass
class MaskParams:
    subtitle_color: str
    white_rgb_threshold: int
    hsv_white_v_min: int
    hsv_white_s_max: int
    black_rgb_threshold: int
    hsv_black_v_max: int
    hsv_black_s_max: int
    morph_kernel_size: int
    open_iterations: int
    close_iterations: int
    dilate_iterations: int
    min_component_area: int
    merge_distance: int

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "MaskParams":
        return cls(
            subtitle_color=cfg.subtitle_color,
            white_rgb_threshold=cfg.white_rgb_threshold,
            hsv_white_v_min=cfg.hsv_white_v_min,
            hsv_white_s_max=cfg.hsv_white_s_max,
            black_rgb_threshold=cfg.black_rgb_threshold,
            hsv_black_v_max=cfg.hsv_black_v_max,
            hsv_black_s_max=cfg.hsv_black_s_max,
            morph_kernel_size=cfg.morph_kernel_size,
            open_iterations=cfg.open_iterations,
            close_iterations=cfg.close_iterations,
            dilate_iterations=cfg.dilate_iterations,
            min_component_area=cfg.min_component_area,
            merge_distance=cfg.merge_distance,
        )


def _initial_white_mask(bgr: np.ndarray, p: MaskParams) -> np.ndarray:
    b, g, r = cv2.split(bgr)
    min_c = np.minimum(np.minimum(r, g), b)
    mean_c = (r.astype(np.int32) + g.astype(np.int32) + b.astype(np.int32)) // 3
    rgb_mask = (min_c >= max(100, p.white_rgb_threshold - 30)) & (mean_c >= p.white_rgb_threshold)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    hsv_mask = (v >= p.hsv_white_v_min) & (s <= p.hsv_white_s_max)
    return (rgb_mask & hsv_mask).astype(np.uint8) * 255


def _initial_black_mask(bgr: np.ndarray, p: MaskParams) -> np.ndarray:
    b, g, r = cv2.split(bgr)
    rgb_mask = (
        (r <= p.black_rgb_threshold)
        & (g <= p.black_rgb_threshold)
        & (b <= p.black_rgb_threshold)
    )
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    hsv_mask = (v <= p.hsv_black_v_max) & (s <= p.hsv_black_s_max)
    return (rgb_mask & hsv_mask).astype(np.uint8) * 255


def _morphology(mask: np.ndarray, p: MaskParams) -> np.ndarray:
    k = max(1, p.morph_kernel_size)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    out = mask
    if p.open_iterations > 0:
        out = cv2.morphologyEx(out, cv2.MORPH_OPEN, kernel, iterations=p.open_iterations)
    if p.close_iterations > 0:
        out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, kernel, iterations=p.close_iterations)
    if p.dilate_iterations > 0:
        out = cv2.dilate(out, kernel, iterations=p.dilate_iterations)
    return out


def _filter_components(mask: np.ndarray, p: MaskParams) -> np.ndarray:
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = np.zeros_like(mask)
    for i in range(1, n_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= p.min_component_area:
            out[labels == i] = 255

    if p.merge_distance > 0 and out.any():
        d = max(1, p.merge_distance)
        merge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (d * 2 + 1, d * 2 + 1))
        out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, merge_kernel)
    return out


def build_subtitle_mask(
    frame_bgr: np.ndarray,
    roi: ROI,
    params: MaskParams,
) -> np.ndarray:
    """Return a full-frame uint8 mask (255 = subtitle, 0 = background)."""
    h, w = frame_bgr.shape[:2]
    full_mask = np.zeros((h, w), dtype=np.uint8)

    # Vertical safety margin: prevents partially chopping text lines that sit
    # slightly higher or lower in other frames of the video
    pad_y = 35
    pad_x = 20
    ry1 = max(0, roi.y - pad_y)
    ry2 = min(h, roi.y + roi.h + pad_y)
    rx1 = max(0, roi.x - pad_x)
    rx2 = min(w, roi.x + roi.w + pad_x)

    crop = frame_bgr[ry1:ry2, rx1:rx2]
    if crop.size == 0:
        return full_mask

    if params.subtitle_color == "full_box":
        m = np.full(crop.shape[:2], 255, dtype=np.uint8)
    elif params.subtitle_color == "colored_box":
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]
        color_mask = (s >= 30) & (v >= 70)
        black_text_mask = (v <= 100)
        m = ((color_mask | black_text_mask).astype(np.uint8) * 255)
        m = _morphology(m, params)
        m = _filter_components(m, params)
    elif params.subtitle_color == "white_stroke":
        # High precision stroke-anchored text masking
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]
        b, g, r = cv2.split(crop)
        min_rgb = np.minimum(np.minimum(r, g), b)

        # 1. Dark stroke outline
        stroke = (v <= 75)

        # 2. White text core
        white_core = (min_rgb >= 190) & (s <= 60) & (v >= 195)

        # 3. Only keep stroke near white text and white text near stroke
        k_near = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
        near_white = cv2.dilate(white_core.astype(np.uint8), k_near)
        stroke_near_white = stroke & (near_white > 0)

        near_stroke = cv2.dilate(stroke.astype(np.uint8), k_near)
        core_near_stroke = white_core & (near_stroke > 0)

        combined = ((stroke_near_white | core_near_stroke).astype(np.uint8) * 255)

        # 4. Connect and fill contours containing actual white text
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

        # 5. Dilate by configured iterations to completely cover outer stroke
        dilate_iters = max(1, params.dilate_iterations)
        k_dil = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        m = cv2.dilate(filled, k_dil, iterations=dilate_iters)
    elif params.subtitle_color == "white":
        m = _initial_white_mask(crop, params)
        m = _morphology(m, params)
        m = _filter_components(m, params)
    else:
        m = _initial_black_mask(crop, params)
        m = _morphology(m, params)
        m = _filter_components(m, params)

    full_mask[ry1:ry2, rx1:rx2] = m
    return full_mask
