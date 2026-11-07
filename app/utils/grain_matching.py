"""High-frequency camera sensor grain & micro-noise matching.

Inpainted regions produced by deep neural networks (LaMa, ProPainter transformer)
naturally exhibit low high-frequency variance (they are mathematically smooth).
Real camera footage contains sensor ISO noise, photon shot noise, and compression artifacts.
When a smooth patch sits beside noisy video, human vision perceives it as a 'blur smudge'.

This module extracts the empirical noise profile from the clean border surrounding
the subtitle mask and seamlessly matches the sensor grain into the repaired area.
"""

from __future__ import annotations

import cv2
import numpy as np


def match_sensor_grain(
    original_bgr: np.ndarray,
    repaired_bgr: np.ndarray,
    mask: np.ndarray,
    border_width: int = 14,
    grain_strength: float = 0.85,
) -> np.ndarray:
    """Inject camera sensor grain into repaired_bgr matching surrounding original_bgr.
    
    Args:
        original_bgr: Source frame (H, W, 3) uint8.
        repaired_bgr: Inpainted frame (H, W, 3) uint8.
        mask: Subtitle binary mask (H, W) uint8 (255 = inpaint zone, 0 = clean).
        border_width: Pixel width around mask to sample camera noise from.
        grain_strength: Multiplier for synthesized grain (0.0 to 1.5).
        
    Returns:
        Frame (H, W, 3) uint8 with matching sensor grain.
    """
    if mask is None or not mask.any():
        return repaired_bgr

    # Create boundary sampling ring (clean background right next to the subtitle)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_outer = cv2.dilate(mask, kernel, iterations=border_width)
    boundary_ring = (dilated_outer > 0) & (mask == 0)

    if not np.any(boundary_ring):
        return repaired_bgr

    orig_f = original_bgr.astype(np.float32)
    rep_f = repaired_bgr.astype(np.float32)

    # High-pass filter to extract sensor noise and micro-texture
    blurred_orig = cv2.GaussianBlur(orig_f, (5, 5), 1.0)
    noise_field = orig_f - blurred_orig

    # Sample standard deviation per color channel in the clean boundary zone
    sampled_std = np.std(noise_field[boundary_ring], axis=0)  # Shape (3,)
    # Clamp to reasonable bounds (avoid noise explosions on sharp high-contrast edges)
    sampled_std = np.clip(sampled_std, 0.5, 9.0) * grain_strength

    # If the video is virtually noiseless, return repaired as is
    if np.all(sampled_std < 0.6):
        return repaired_bgr

    # Synthesize matching uncorrelated sensor noise
    h, w, c = repaired_bgr.shape
    synth_noise = np.random.normal(0.0, 1.0, (h, w, c)).astype(np.float32) * sampled_std

    # Luma-dependent modulation: camera sensors exhibit higher shot noise in midtones/shadows
    gray = cv2.cvtColor(repaired_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    # Bell-shaped curve peaking at mid-dark (luma ~0.4)
    luma_scale = np.clip(1.2 - 0.4 * gray, 0.6, 1.3)[:, :, np.newaxis]
    synth_noise = synth_noise * luma_scale

    # Soft alpha blend only inside the mask zone (feathered edges)
    alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (5, 5), 1.2)[:, :, np.newaxis]
    grained_rep = np.clip(rep_f + synth_noise, 0.0, 255.0)

    out = (rep_f * (1.0 - alpha) + grained_rep * alpha).astype(np.uint8)
    return out

