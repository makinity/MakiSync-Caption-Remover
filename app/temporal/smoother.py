"""Temporal smoothing and anti-flicker gap bridging for video subtitle masks.

Features:
- `bridge_temporal_gaps`: Bridges short gaps (1-8 frames) where subtitle detection dropped out.
- `smooth_masks`: Active-span temporal union that connects animated/karaoke words within
  each subtitle phrase while keeping non-subtitle frames 100% pristine.
"""

from __future__ import annotations

from typing import List
import numpy as np


def bridge_temporal_gaps(masks: List[np.ndarray], max_gap: int = 8) -> List[np.ndarray]:
    """Bridge short temporal gaps where subtitle mask temporarily disappeared."""
    if len(masks) <= 2 or max_gap <= 1:
        return masks

    n = len(masks)
    has_mask = np.array([m.any() for m in masks], dtype=bool)
    if not has_mask.any():
        return masks

    out = [m.copy() for m in masks]
    i = 0
    while i < n:
        if not has_mask[i]:
            gap_start = i
            while i < n and not has_mask[i]:
                i += 1
            gap_len = i - gap_start
            if gap_start > 0 and i < n and gap_len <= max_gap:
                fill_mask = np.maximum(out[gap_start - 1], out[i])
                for g in range(gap_start, i):
                    out[g] = fill_mask.copy()
        else:
            i += 1
    return out


def smooth_masks(
    masks: List[np.ndarray],
    window: int = 12,
    mode: str = "union",
    vote_min: int = 2,
    gap_fill: int = 8,
) -> List[np.ndarray]:
    if len(masks) == 0:
        return masks

    n = len(masks)
    # Check which frames have genuine subtitle text (> 100 pixels)
    has_text = np.array([np.count_nonzero(m) > 100 for m in masks], dtype=bool)
    if not has_text.any():
        return masks

    # Bridge short dropouts between words within a phrase
    bridged = [m.copy() for m in masks]
    if gap_fill > 0:
        i = 0
        while i < n:
            if not has_text[i]:
                gap_start = i
                while i < n and not has_text[i]:
                    i += 1
                gap_len = i - gap_start
                if gap_start > 0 and i < n and gap_len <= gap_fill:
                    fill_mask = np.maximum(bridged[gap_start - 1], bridged[i])
                    for g in range(gap_start, i):
                        bridged[g] = fill_mask.copy()
                        has_text[g] = True
            else:
                i += 1

    if window <= 0:
        return bridged

    out: List[np.ndarray] = []
    for i in range(n):
        if not has_text[i]:
            # Completely blank frame outside subtitle phrases -> keep 100% pristine!
            out.append(np.zeros_like(masks[0]))
            continue

        # Find contiguous active text span around i
        lo = i
        while lo > 0 and (i - lo) < window and has_text[lo - 1]:
            lo -= 1

        hi = i
        while hi < n - 1 and (hi - i) < window and has_text[hi + 1]:
            hi += 1

        stack = bridged[lo : hi + 1]
        if mode == "union":
            acc = np.zeros_like(stack[0])
            for m in stack:
                acc = np.maximum(acc, m)
            out.append(acc)
        elif mode == "vote":
            counts = np.zeros(stack[0].shape, dtype=np.int16)
            for m in stack:
                counts += (m > 0).astype(np.int16)
            keep = (counts >= vote_min).astype(np.uint8) * 255
            out.append(keep)
        else:
            raise ValueError(f"unknown temporal mode: {mode}")

    return out
