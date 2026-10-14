"""Central configuration for the subtitle removal pipeline.

All knobs that the rest of the codebase reads live in :class:`AppConfig`.
The CLI in ``app.main`` builds an instance of this and passes it to the
pipeline. Defaults are tuned to be reasonable for typical 1080p videos
with bottom-aligned hard subtitles, but every value can be overridden
from the command line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


SubtitleColor = str  # "white" | "black" | "white_stroke" | "colored_box" | "full_box"
Backend = str        # "lama" | "opencv" | "propainter" | "e2fgvi"


@dataclass
class AppConfig:
    # ---- I/O --------------------------------------------------------
    input_path: str = ""
    output_path: str = "output.mp4"
    work_dir: str = "work"
    save_intermediate: bool = True

    # ---- Run mode ---------------------------------------------------
    preview: bool = False
    preview_seconds: float = 3.0

    # ---- Clip Trimming (B-Roll Mode) -------------------------------
    clip_trim: bool = False
    clip_start: float = 0.0
    clip_end: float = 0.0

    # ---- ROI --------------------------------------------------------
    # (x, y, w, h) in absolute pixels of the source video.
    # When None and ``roi_interactive`` is True the user is asked to
    # draw the box over the first frame.
    roi: Optional[Tuple[int, int, int, int]] = None
    roi_interactive: bool = False

    # ---- Subtitle color ---------------------------------------------
    subtitle_color: SubtitleColor = "white"

    # White color thresholds (tuned for compressed hard subtitles)
    white_rgb_threshold: int = 175       # min value on RGB channels
    hsv_white_v_min: int = 180           # HSV V min for white
    hsv_white_s_max: int = 75            # HSV S max for white (handles video compression)

    # Black color thresholds
    black_rgb_threshold: int = 60        # max value on each RGB channel
    hsv_black_v_max: int = 70            # HSV V max for black
    hsv_black_s_max: int = 90            # HSV S max for black

    # ---- Mask post-processing ---------------------------------------
    morph_kernel_size: int = 3
    dilate_iterations: int = 3
    close_iterations: int = 1
    open_iterations: int = 0             # 0 prevents eroding thin letter strokes
    min_component_area: int = 20
    merge_distance: int = 6              # used to merge nearby components

    # ---- Anti-Flicker & Temporal smoothing --------------------------
    temporal_window: int = 12             # +/- frames; 0 disables smoothing
    temporal_mode: str = "union"         # union | vote
    temporal_vote_min: int = 2           # min hits across window for vote
    temporal_gap_fill: int = 8           # bridge subtitle gaps up to 8 frames (~250ms)
    anti_flicker: bool = True

    # ---- Inpainting backend -----------------------------------------
    backend: Backend = "lama"
    lama_device: str = "auto"            # "auto" | "cpu" | "cuda" | "mps"
    lama_dilate_extra: int = 4           # extra dilation feeding LaMa
    lama_crop_padding: int = 32          # context around subtitle bbox
    batch_size: int = 4                  # batch size for neural inference
    opencv_inpaint_radius: float = 3.0

    # ---- FFmpeg -----------------------------------------------------
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    output_video_codec: str = "libx264"
    output_pix_fmt: str = "yuv420p"
    output_crf: int = 18

    # ---- Misc -------------------------------------------------------
    frame_ranges: List[Tuple[int, int]] = field(default_factory=list)

    def validate(self) -> None:
        if self.clip_trim and self.clip_end > 0 and self.clip_end <= self.clip_start:
            raise ValueError('clip_end must be greater than clip_start')
        if self.subtitle_color not in ("white", "black", "white_stroke", "colored_box", "full_box"):
            raise ValueError(
                f"subtitle_color must be 'white', 'black', 'white_stroke', 'colored_box', or 'full_box', got {self.subtitle_color!r}"
            )
        if self.backend not in ("lama", "opencv", "propainter", "e2fgvi"):
            raise ValueError(f"unknown backend {self.backend!r}")
        if self.temporal_window < 0:
            raise ValueError("temporal_window must be >= 0")
        if self.temporal_gap_fill < 0:
            raise ValueError("temporal_gap_fill must be >= 0")
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        if self.lama_crop_padding < 0:
            raise ValueError("lama_crop_padding must be >= 0")
        if self.opencv_inpaint_radius <= 0:
            raise ValueError("opencv_inpaint_radius must be > 0")
        if self.roi is not None:
            x, y, w, h = self.roi
            if w <= 0 or h <= 0:
                raise ValueError(f"invalid roi size: {self.roi}")
