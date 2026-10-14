"""Gradio web UI for the subtitle remover studio with CapCut-style Timeline Trimmer.

Wraps :func:`app.pipeline.run_pipeline` with:
- CapCut-style visual timeline trimmer in Step 1 with In/Out brackets, scrubber, and preview
- Interactive draggable ROI selection canvas in Step 2 with instant preset snapping
- Live time sync and frame capture at any video timestamp
- Selective B-roll clip trimming & AI inpainting (outputs only the trimmed segment)
"""

from __future__ import annotations

import os
import shutil
import socket
import tempfile
import threading
import time
import uuid
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional, Tuple

import json
import subprocess
import cv2
import gradio as gr
import numpy as np

from . import __version__
from .config import AppConfig
from .ffmpeg_tools.ffmpeg_wrapper import probe_video
from .pipeline import run_pipeline
from .ffmpeg_tools.browser_compat import ensure_browser_playable_video, patch_gradio_routes

patch_gradio_routes()


# ---------------------------------------------------------------------------
# ffmpeg/ffprobe resolution (static-ffmpeg)
# ---------------------------------------------------------------------------

def _resolve_ffmpeg_bins() -> Tuple[str, str]:
    try:
        from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise

        ffmpeg, ffprobe = get_or_fetch_platform_executables_else_raise()
        return ffmpeg, ffprobe
    except Exception:
        pass

    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    return ffmpeg, ffprobe


FFMPEG_BIN, FFPROBE_BIN = _resolve_ffmpeg_bins()
if FFMPEG_BIN and Path(FFMPEG_BIN).exists():
    _ff_dir = str(Path(FFMPEG_BIN).parent.resolve())
    if _ff_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _ff_dir + os.pathsep + os.environ.get("PATH", "")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_frame_at_time(video_path: Optional[str], timestamp_sec: float = 0.0) -> Optional[np.ndarray]:
    """Read clean RGB frame at a specific timestamp."""
    if not video_path:
        return None
    p = Path(video_path)
    if not p.exists() or p.stat().st_size == 0:
        return None

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    target_frame = max(0, int(round(float(timestamp_sec) * fps)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def _read_first_frame(video_path: str) -> Optional[np.ndarray]:
    return _read_frame_at_time(video_path, 0.0)


def _corners_to_roi(
    left_x: int, bottom_y: int, right_x: int, top_y: int, frame_w: int, frame_h: int
) -> Tuple[int, int, int, int]:
    x1 = max(0, min(frame_w - 1, min(left_x, right_x)))
    x2 = max(1, min(frame_w, max(left_x, right_x)))
    y_low = min(bottom_y, top_y)
    y_high = max(bottom_y, top_y)
    y1 = max(0, min(frame_h - 1, y_low))
    y2 = max(1, min(frame_h, y_high))
    return int(x1), int(y1), int(x2 - x1), int(y2 - y1)


def _get_video_dimensions(video_path: Optional[str]) -> Tuple[int, int]:
    if not video_path or not Path(video_path).exists():
        return 1920, 1080
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return 1920, 1080
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return (w or 1920), (h or 1080)


def _find_available_port(start: int = 7860, max_tries: int = 50) -> int:
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def _wait_and_open_browser(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.3)
    webbrowser.open(url)


# ---------------------------------------------------------------------------
# Gradio callbacks
# ---------------------------------------------------------------------------

def on_video_uploaded(video_path: Optional[str]):
    """When video is uploaded, extract first clean frame, set up sliders and video info."""
    if not video_path:
        return (
            None,
            gr.update(maximum=1920, value=0),
            gr.update(maximum=1080, value=0),
            gr.update(maximum=1920, value=1920),
            gr.update(maximum=1080, value=900),
            gr.update(maximum=100.0, value=0.0),
            gr.update(value=0.0),
            gr.update(value=0.0),
            "",
        )

    video_path = ensure_browser_playable_video(video_path)
    frame = _read_first_frame(video_path)
    if frame is None:
        return (
            None,
            gr.update(maximum=1920, value=0),
            gr.update(maximum=1080, value=0),
            gr.update(maximum=1920, value=1920),
            gr.update(maximum=1080, value=900),
            gr.update(maximum=100.0, value=0.0),
            gr.update(value=0.0),
            gr.update(value=0.0),
            "Processing video file...",
        )

    H, W = frame.shape[:2]
    h_band = max(1, int(H * 0.18))
    left_x, bottom_y, right_x, top_y = 0, H, W, H - h_band

    duration_val = 0.0
    info_str = f"Video Resolution: **{W} x {H}**"
    try:
        info = probe_video(video_path, FFPROBE_BIN)
        duration_val = round(info.duration, 2)
        info_str += f" • Duration: **{duration_val}s** ({info.n_frames} frames @ {info.fps:.2f}fps)"
    except Exception:
        pass

    return (
        frame,
        gr.update(maximum=W, value=left_x),
        gr.update(maximum=H, value=bottom_y),
        gr.update(maximum=W, value=right_x),
        gr.update(maximum=H, value=top_y),
        gr.update(maximum=max(1.0, duration_val), value=0.0),
        gr.update(value=0.0),
        gr.update(value=duration_val),
        info_str,
    )


def on_video_cleared():
    """Reset UI cleanly when video is cleared."""
    return (
        None,
        gr.update(maximum=1920, value=0),
        gr.update(maximum=1080, value=0),
        gr.update(maximum=1920, value=1920),
        gr.update(maximum=1080, value=900),
        gr.update(maximum=100.0, value=0.0),
        gr.update(value=0.0),
        gr.update(value=0.0),
        "",
    )


def on_load_frame_at_time(video_path: Optional[str], timestamp: float):
    if not video_path:
        return None
    return _read_frame_at_time(video_path, float(timestamp or 0.0))


def on_preset_bottom(video_path: Optional[str]):
    w, h = _get_video_dimensions(video_path)
    band = max(1, int(h * 0.18))
    return 0, h, w, h - band


def on_preset_top(video_path: Optional[str]):
    w, h = _get_video_dimensions(video_path)
    band = max(1, int(h * 0.18))
    return 0, band, w, 0


def on_preset_tiktok_br(video_path: Optional[str]):
    w, h = _get_video_dimensions(video_path)
    lx = int(w * 0.68)
    rx = int(w * 0.98)
    ty = int(h * 0.86)
    by = int(h * 0.98)
    return lx, by, rx, ty


def on_preset_tiktok_tl(video_path: Optional[str]):
    w, h = _get_video_dimensions(video_path)
    lx = int(w * 0.02)
    rx = int(w * 0.32)
    ty = int(h * 0.04)
    by = int(h * 0.16)
    return lx, by, rx, ty


def on_preset_center(video_path: Optional[str]):
    w, h = _get_video_dimensions(video_path)
    lx = int(w * 0.08)
    rx = int(w * 0.92)
    ty = int(h * 0.40)
    by = int(h * 0.60)
    return lx, by, rx, ty


def on_preset_full(video_path: Optional[str]):
    w, h = _get_video_dimensions(video_path)
    return 0, h, w, 0


def process_video(
    video_path: Optional[str],
    left_x: int,
    bottom_y: int,
    right_x: int,
    top_y: int,
    clip_trim: bool,
    clip_start: float,
    clip_end: float,
    subtitle_color: str,
    process_mode: str,
    preview_only: bool,
    dilate_iterations: int,
    lama_dilate_extra: int,
    temporal_window: int,
    progress=gr.Progress(track_tqdm=True),
) -> Optional[str]:
    if not video_path:
        raise gr.Error("Please upload a video first!")

    frame_w, frame_h = _get_video_dimensions(video_path)
    roi_tuple = _corners_to_roi(int(left_x), int(bottom_y), int(right_x), int(top_y), frame_w, frame_h)
    if roi_tuple[2] <= 1 or roi_tuple[3] <= 1:
        raise gr.Error("Please select a valid subtitle region using the canvas or sliders")

    if clip_trim and clip_end > 0 and clip_end <= clip_start:
        raise gr.Error(f"End Time ({clip_end}s) must be greater than Start Time ({clip_start}s)")

    progress(0.05, desc="Preparing working directory...")
    session_id = uuid.uuid4().hex[:8]
    work_dir = Path(tempfile.gettempdir()) / f"vrt_{session_id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    out_video_path = work_dir / f"repaired_{session_id}.mp4"

    backend = "opencv" if process_mode == "fast" else "lama"
    is_preview = bool(preview_only and not clip_trim)

    config = AppConfig(
        input_path=str(video_path),
        output_path=str(out_video_path),
        work_dir=str(work_dir),
        save_intermediate=False,
        preview=is_preview,
        preview_seconds=3.0,
        clip_trim=bool(clip_trim),
        clip_start=float(clip_start) if clip_trim else 0.0,
        clip_end=float(clip_end) if clip_trim else 0.0,
        roi=roi_tuple,
        roi_interactive=False,
        subtitle_color=str(subtitle_color),
        dilate_iterations=int(dilate_iterations),
        temporal_window=int(temporal_window),
        temporal_gap_fill=8,
        anti_flicker=True,
        batch_size=4,
        backend=backend,
        lama_device="auto",
        lama_dilate_extra=int(lama_dilate_extra),
        ffmpeg_bin=FFMPEG_BIN,
        ffprobe_bin=FFPROBE_BIN,
    )

    mode_label = "Fast Mode (OpenCV)" if process_mode == "fast" else "Quality Mode (LaMa AI)"
    if clip_trim:
        progress(0.05, desc=f"Starting Trimmed Clip Inpainting ({clip_start:.1f}s - {clip_end:.1f}s) via {mode_label}...")
    elif is_preview:
        progress(0.05, desc=f"Starting 3-second Fast Preview via {mode_label}...")
    else:
        progress(0.05, desc=f"Starting Full Video Processing via {mode_label}...")

    result_holder: dict = {}

    def _worker():
        try:
            result_holder["path"] = run_pipeline(config)
        except Exception as e:
            result_holder["error"] = e

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

    start_ts = time.time()
    while t.is_alive():
        elapsed = time.time() - start_ts
        frac = 0.05 + 0.90 * (1 - 1 / (1 + elapsed / 35.0))
        progress(frac, desc=f"Processing Inpainting ({mode_label})... Elapsed: {int(elapsed)}s")
        time.sleep(1.0)

    t.join()

    if "error" in result_holder:
        raise gr.Error(f"Processing failed: {result_holder['error']}")

    out_file = result_holder.get("path")
    if not out_file or not Path(out_file).exists():
        raise gr.Error("Output file was not generated.")

    progress(1.0, desc=f"Completed in {int(time.time() - start_ts)}s!")
    return str(out_file)



# ---------------------------------------------------------------------------
# CapCut Timeline HTML Component Template
# ---------------------------------------------------------------------------

CAPCUT_TIMELINE_HTML = """
<div id="capcut_timeline_container" class="capcut-container">
    <!-- Header: Title, Live Output Summary, and Toggle -->
    <div class="capcut-header">
        <div class="capcut-title-box">
            <span class="capcut-badge">✂️ CapCut Trimmer</span>
            <span id="capcut_summary_text" class="capcut-summary">Upload video to enable timeline</span>
        </div>
        <div class="capcut-toggle-box">
            <label class="capcut-switch" title="When ON, only the trimmed clip will be processed and exported!">
                <input type="checkbox" id="capcut_trim_toggle" checked>
                <span class="capcut-slider"></span>
            </label>
            <span class="capcut-toggle-text">Trim Output Only</span>
        </div>
    </div>

    <!-- Time Ruler (dynamic ticks) -->
    <div class="capcut-ruler-wrapper" id="capcut_ruler_wrapper">
        <div class="capcut-ruler" id="capcut_ruler"></div>
    </div>

    <!-- Interactive Track Viewport -->
    <div class="capcut-track-wrapper" id="capcut_track_wrapper" title="Click anywhere to jump playhead">
        <!-- Filmstrip background styling -->
        <div class="capcut-track-track"></div>

        <!-- Dimmed outside portions -->
        <div class="capcut-dim capcut-dim-left" id="capcut_dim_left"></div>
        <div class="capcut-dim capcut-dim-right" id="capcut_dim_right"></div>

        <!-- Draggable Selected Clip Window -->
        <div class="capcut-clip" id="capcut_clip">
            <!-- Left In-Handle -->
            <div class="capcut-handle capcut-handle-left" id="capcut_handle_left" title="Drag to adjust Start Cut">
                <div class="capcut-handle-icon">❮</div>
                <div class="capcut-tag" id="capcut_tag_start">00:00.0</div>
            </div>
            <!-- Clip Middle Body (Drag to slide window) -->
            <div class="capcut-clip-body" id="capcut_clip_body" title="Drag to slide the entire trimmed clip window">
                <span class="capcut-clip-len" id="capcut_clip_len">0.0s</span>
            </div>
            <!-- Right Out-Handle -->
            <div class="capcut-handle capcut-handle-right" id="capcut_handle_right" title="Drag to adjust End Cut">
                <div class="capcut-handle-icon">❯</div>
                <div class="capcut-tag" id="capcut_tag_end">00:00.0</div>
            </div>
        </div>

        <!-- Playhead Needle & Scrubber -->
        <div class="capcut-playhead" id="capcut_playhead" title="Drag to scrub video playback">
            <div class="capcut-playhead-pin"></div>
            <div class="capcut-playhead-line"></div>
            <div class="capcut-playhead-badge" id="capcut_playhead_badge">00:00.0</div>
        </div>
    </div>

    <!-- Action Buttons & Quick Presets -->
    <div class="capcut-controls-row">
        <div class="capcut-btn-group">
            <button type="button" id="capcut_btn_set_in" class="capcut-btn capcut-btn-gold" title="Set Start Cut to current video position">
                ❮ Set In [
            </button>
            <button type="button" id="capcut_btn_set_out" class="capcut-btn capcut-btn-gold" title="Set End Cut to current video position">
                Set Out ] ❯
            </button>
            <button type="button" id="capcut_btn_preview" class="capcut-btn capcut-btn-play" title="Play only the selected trimmed clip">
                ▶ Play Clip
            </button>
            <button type="button" id="capcut_btn_sync_frame" class="capcut-btn capcut-btn-sync" title="Load Start Frame into Step 2 Canvas">
                🎯 Load into Canvas
            </button>
            <button type="button" id="capcut_btn_reset" class="capcut-btn" title="Reset to full video">
                ⟲ Reset Full
            </button>
        </div>

        <div class="capcut-quick-chips">
            <span class="capcut-chips-title">Quick Cut:</span>
            <button type="button" class="capcut-chip" data-dur="3">+3s</button>
            <button type="button" class="capcut-chip" data-dur="5">+5s</button>
            <button type="button" class="capcut-chip" data-dur="10">+10s</button>
            <button type="button" class="capcut-chip" data-dur="15">+15s</button>
        </div>
    </div>

    <!-- Precision Millisecond Number Inputs -->
    <div class="capcut-inputs-row">
        <div class="capcut-input-col">
            <span class="capcut-input-label">Start Time:</span>
            <div class="capcut-input-wrap">
                <input type="number" id="capcut_input_start" min="0" step="0.1" value="0.0">
                <span class="capcut-unit">sec</span>
            </div>
        </div>
        <div class="capcut-input-col">
            <span class="capcut-input-label">End Time:</span>
            <div class="capcut-input-wrap">
                <input type="number" id="capcut_input_end" min="0" step="0.1" value="0.0">
                <span class="capcut-unit">sec</span>
            </div>
        </div>
        <div class="capcut-input-col">
            <span class="capcut-input-label">Clip Length:</span>
            <div class="capcut-input-wrap">
                <input type="text" id="capcut_input_duration" readonly value="0.0s">
            </div>
        </div>
    </div>
</div>
"""


# ---------------------------------------------------------------------------
# Interactive Canvas & CapCut Trimmer Client-Side JavaScript
# ---------------------------------------------------------------------------

CLIENT_SCRIPT_JS = """
(() => {
    window.__ROI_DATA = window.__ROI_DATA || null;
    window.__TRIM_DATA = window.__TRIM_DATA || { start: 0, end: 0, enabled: false };

    // -------------------------------------------------------------
    // 1. CapCut Timeline Trimmer Controller
    // -------------------------------------------------------------
    const cc = {
        video: null,
        duration: 0,
        start: 0,
        end: 0,
        enabled: true,
        isPlayingClip: false,
        isDragging: null, // 'left' | 'right' | 'body' | 'playhead'
        dragStartX: 0,
        initialStart: 0,
        initialEnd: 0,
        rulerBuiltFor: -1
    };

    function formatTimecode(secs) {
        if (isNaN(secs) || secs < 0) secs = 0;
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60);
        const ms = Math.floor((secs % 1) * 10);
        const mm = String(m).padStart(2, '0');
        const ss = String(s).padStart(2, '0');
        return mm + ':' + ss + '.' + ms;
    }

    function setGradioInput(containerId, val) {
        const c = document.getElementById(containerId);
        if (!c) return;
        const inp = c.querySelector('input');
        if (!inp) return;

        const prototype = Object.getPrototypeOf(inp);
        const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
        if (setter) {
            setter.call(inp, val);
        } else {
            inp.value = val;
        }
        inp.dispatchEvent(new Event('input', { bubbles: true }));
        inp.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function findVideoElement() {
        const container = document.getElementById('source_video_player');
        if (container) {
            const v = container.querySelector('video');
            if (v) return v;
        }
        return document.querySelector('video');
    }

    function buildRuler(duration) {
        const ruler = document.getElementById('capcut_ruler');
        if (!ruler || duration <= 0) return;
        if (Math.abs(cc.rulerBuiltFor - duration) < 0.2) return;
        cc.rulerBuiltFor = duration;
        ruler.innerHTML = '';

        const steps = 6;
        for (let i = 0; i <= steps; i++) {
            const pct = (i / steps) * 100;
            const sec = (i / steps) * duration;
            const tick = document.createElement('div');
            tick.className = 'capcut-ruler-tick';
            tick.style.left = pct + '%';
            tick.innerText = formatTimecode(sec);
            ruler.appendChild(tick);
        }
    }

    function updateCapcutUI() {
        if (!cc.video || cc.duration <= 0) return;
        const duration = cc.duration;
        const start = Math.max(0, Math.min(duration, cc.start));
        const end = Math.max(start + 0.1, Math.min(duration, cc.end));
        cc.start = Math.round(start * 10) / 10;
        cc.end = Math.round(end * 10) / 10;
        const clipLen = Math.max(0.1, Math.round((cc.end - cc.start) * 10) / 10);

        const leftPct = (cc.start / duration) * 100;
        const rightPct = (cc.end / duration) * 100;
        const widthPct = Math.max(0.5, rightPct - leftPct);

        const dimLeft = document.getElementById('capcut_dim_left');
        const dimRight = document.getElementById('capcut_dim_right');
        const clipEl = document.getElementById('capcut_clip');
        const tagStart = document.getElementById('capcut_tag_start');
        const tagEnd = document.getElementById('capcut_tag_end');
        const clipLenEl = document.getElementById('capcut_clip_len');
        const summaryText = document.getElementById('capcut_summary_text');
        const inputStart = document.getElementById('capcut_input_start');
        const inputEnd = document.getElementById('capcut_input_end');
        const inputDuration = document.getElementById('capcut_input_duration');
        const toggle = document.getElementById('capcut_trim_toggle');

        if (dimLeft) dimLeft.style.width = leftPct + '%';
        if (dimRight) dimRight.style.width = Math.max(0, 100 - rightPct) + '%';
        if (clipEl) {
            clipEl.style.left = leftPct + '%';
            clipEl.style.width = widthPct + '%';
        }

        if (tagStart) tagStart.innerText = formatTimecode(cc.start);
        if (tagEnd) tagEnd.innerText = formatTimecode(cc.end);
        if (clipLenEl) clipLenEl.innerText = clipLen.toFixed(1) + 's';

        if (inputStart && document.activeElement !== inputStart) inputStart.value = cc.start.toFixed(1);
        if (inputEnd && document.activeElement !== inputEnd) inputEnd.value = cc.end.toFixed(1);
        if (inputDuration) inputDuration.value = clipLen.toFixed(1) + 's';

        const isTrimOn = toggle ? toggle.checked : cc.enabled;
        cc.enabled = isTrimOn;

        if (summaryText) {
            if (isTrimOn) {
                summaryText.innerHTML = '<span style="color:#FFD200;">✂️ Output Clip:</span> ' + formatTimecode(cc.start) + ' → ' + formatTimecode(cc.end) + ' <span style="color:#38BDF8;">(' + clipLen.toFixed(1) + 's)</span>';
            } else {
                summaryText.innerHTML = '<span style="color:#94A3B8;">Full Video:</span> 00:00.0 → ' + formatTimecode(duration) + ' (' + duration.toFixed(1) + 's)';
            }
        }

        // Sync with global trim data for run_btn
        window.__TRIM_DATA = {
            start: cc.start,
            end: cc.end,
            enabled: isTrimOn
        };

        // Sync with Gradio inputs
        setGradioInput('input_clip_start', cc.start);
        setGradioInput('input_clip_end', cc.end);
        const chk = document.querySelector('#chk_clip_trim input[type="checkbox"]');
        if (chk && chk.checked !== isTrimOn) {
            chk.click();
        }
    }

    function updatePlayhead() {
        if (!cc.video || cc.duration <= 0) return;
        const curTime = cc.video.currentTime || 0;
        const pct = Math.max(0, Math.min(100, (curTime / cc.duration) * 100));
        const playhead = document.getElementById('capcut_playhead');
        const badge = document.getElementById('capcut_playhead_badge');
        if (playhead) playhead.style.left = pct + '%';
        if (badge) badge.innerText = formatTimecode(curTime);

        // If currently previewing selected clip and reached end, pause
        if (cc.isPlayingClip && curTime >= cc.end) {
            cc.video.pause();
            cc.isPlayingClip = false;
            const btn = document.getElementById('capcut_btn_preview');
            if (btn) btn.innerHTML = '▶ Play Clip';
        }
    }

    function attachCapcutListeners() {
        const container = document.getElementById('capcut_timeline_container');
        if (!container || container.__hasCapcutInit) return;
        container.__hasCapcutInit = true;

        const trackViewport = document.getElementById('capcut_track_wrapper');
        const handleLeft = document.getElementById('capcut_handle_left');
        const handleRight = document.getElementById('capcut_handle_right');
        const clipBody = document.getElementById('capcut_clip_body');
        const playheadPin = document.querySelector('.capcut-playhead-pin');
        const toggle = document.getElementById('capcut_trim_toggle');

        const btnSetIn = document.getElementById('capcut_btn_set_in');
        const btnSetOut = document.getElementById('capcut_btn_set_out');
        const btnPreview = document.getElementById('capcut_btn_preview');
        const btnSyncFrame = document.getElementById('capcut_btn_sync_frame');
        const btnReset = document.getElementById('capcut_btn_reset');
        const inputStart = document.getElementById('capcut_input_start');
        const inputEnd = document.getElementById('capcut_input_end');

        // Toggle Switch
        if (toggle) {
            toggle.addEventListener('change', () => {
                cc.enabled = toggle.checked;
                updateCapcutUI();
            });
        }

        // Pointer drag interactions
        if (handleLeft) {
            handleLeft.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                cc.isDragging = 'left';
            });
        }

        if (handleRight) {
            handleRight.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                cc.isDragging = 'right';
            });
        }

        if (clipBody) {
            clipBody.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                cc.isDragging = 'body';
                cc.dragStartX = e.clientX;
                cc.initialStart = cc.start;
                cc.initialEnd = cc.end;
            });
        }

        if (playheadPin) {
            playheadPin.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                cc.isDragging = 'playhead';
            });
        }

        // Click on track seeking
        if (trackViewport) {
            trackViewport.addEventListener('pointerdown', (e) => {
                if (e.target.closest('.capcut-handle') || e.target.closest('.capcut-clip-body') || e.target.closest('.capcut-playhead-pin')) {
                    return;
                }
                if (!cc.video || cc.duration <= 0) return;
                const rect = trackViewport.getBoundingClientRect();
                const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
                const targetTime = (relX / rect.width) * cc.duration;
                cc.video.currentTime = targetTime;
                updatePlayhead();
            });
        }

        // Global pointermove / pointerup
        window.addEventListener('pointermove', (e) => {
            if (!cc.isDragging || !trackViewport || cc.duration <= 0) return;
            const rect = trackViewport.getBoundingClientRect();
            const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
            const mouseSec = (relX / rect.width) * cc.duration;

            if (cc.isDragging === 'left') {
                cc.start = Math.max(0, Math.min(cc.end - 0.2, mouseSec));
                if (cc.video) cc.video.currentTime = cc.start;
                updateCapcutUI();
                updatePlayhead();
            } else if (cc.isDragging === 'right') {
                cc.end = Math.max(cc.start + 0.2, Math.min(cc.duration, mouseSec));
                if (cc.video) cc.video.currentTime = cc.end;
                updateCapcutUI();
                updatePlayhead();
            } else if (cc.isDragging === 'body') {
                const dxSec = ((e.clientX - cc.dragStartX) / rect.width) * cc.duration;
                const clipLen = cc.initialEnd - cc.initialStart;
                let newStart = cc.initialStart + dxSec;
                if (newStart < 0) newStart = 0;
                if (newStart + clipLen > cc.duration) newStart = cc.duration - clipLen;
                cc.start = newStart;
                cc.end = newStart + clipLen;
                updateCapcutUI();
            } else if (cc.isDragging === 'playhead') {
                if (cc.video) cc.video.currentTime = mouseSec;
                updatePlayhead();
            }
        });

        window.addEventListener('pointerup', () => {
            if (cc.isDragging) {
                cc.isDragging = null;
                updateCapcutUI();
            }
        });

        // Set In button
        if (btnSetIn) {
            btnSetIn.addEventListener('click', () => {
                if (!cc.video) return;
                const cur = Math.round((cc.video.currentTime || 0) * 10) / 10;
                cc.start = cur;
                if (cc.start >= cc.end) {
                    cc.end = Math.min(cc.duration, cc.start + 5.0);
                }
                if (toggle) toggle.checked = true;
                cc.enabled = true;
                updateCapcutUI();
            });
        }

        // Set Out button
        if (btnSetOut) {
            btnSetOut.addEventListener('click', () => {
                if (!cc.video) return;
                const cur = Math.round((cc.video.currentTime || 0) * 10) / 10;
                cc.end = cur;
                if (cc.end <= cc.start) {
                    cc.start = Math.max(0, cc.end - 5.0);
                }
                if (toggle) toggle.checked = true;
                cc.enabled = true;
                updateCapcutUI();
            });
        }

        // Play Clip button
        if (btnPreview) {
            btnPreview.addEventListener('click', () => {
                if (!cc.video) return;
                if (cc.isPlayingClip) {
                    cc.video.pause();
                    cc.isPlayingClip = false;
                    btnPreview.innerHTML = '▶ Play Clip';
                } else {
                    cc.video.currentTime = cc.start;
                    cc.video.play();
                    cc.isPlayingClip = true;
                    btnPreview.innerHTML = '⏸ Stop Clip';
                }
            });
        }

        // Reset Full button
        if (btnReset) {
            btnReset.addEventListener('click', () => {
                cc.start = 0.0;
                cc.end = cc.duration;
                updateCapcutUI();
            });
        }

        // Sync Frame to Step 2 Canvas
        if (btnSyncFrame) {
            btnSyncFrame.addEventListener('click', () => {
                const targetTime = cc.start;
                setGradioInput('input_preview_time', targetTime);
                const syncBtn = document.getElementById('btn_sync_frame_from_player');
                if (syncBtn) syncBtn.click();
            });
        }

        // Quick Cut Chips (+3s, +5s, +10s, +15s)
        container.querySelectorAll('.capcut-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                if (!cc.video || cc.duration <= 0) return;
                const dur = parseFloat(chip.dataset.dur) || 5;
                const cur = Math.round((cc.video.currentTime || 0) * 10) / 10;
                cc.start = cur;
                cc.end = Math.min(cc.duration, cur + dur);
                if (toggle) toggle.checked = true;
                cc.enabled = true;
                updateCapcutUI();
            });
        });

        // Numeric inputs
        if (inputStart) {
            inputStart.addEventListener('change', () => {
                const val = parseFloat(inputStart.value) || 0;
                cc.start = Math.max(0, Math.min(cc.end - 0.2, val));
                updateCapcutUI();
            });
        }

        if (inputEnd) {
            inputEnd.addEventListener('change', () => {
                const val = parseFloat(inputEnd.value) || cc.duration;
                cc.end = Math.max(cc.start + 0.2, Math.min(cc.duration, val));
                updateCapcutUI();
            });
        }
    }

    // -------------------------------------------------------------
    // 2. Interactive Draggable ROI Canvas Controller (Step 2)
    // -------------------------------------------------------------
    let overlay = null;
    let box = null;
    let badge = null;
    let handles = {};
    let isInteracting = false;
    let currentMode = null;
    let activeHandle = null;
    let startX = 0, startY = 0;
    let boxLeft = 0, boxTop = 0, boxWidth = 0, boxHeight = 0;
    let initialBox = { l: 0, t: 0, w: 0, h: 0 };
    let lastLx = null, lastBy = null, lastRx = null, lastTy = null;

    function getRenderedImageRect(img) {
        if (!img) return null;
        const rect = img.getBoundingClientRect();
        const natW = img.naturalWidth || 1;
        const natH = img.naturalHeight || 1;
        const elemW = rect.width;
        const elemH = rect.height;
        if (elemW <= 0 || elemH <= 0) return null;

        const imgRatio = natW / natH;
        const elemRatio = elemW / elemH;
        let renderW, renderH, offsetX, offsetY;

        if (imgRatio > elemRatio) {
            renderW = elemW;
            renderH = elemW / imgRatio;
            offsetX = 0;
            offsetY = (elemH - renderH) / 2;
        } else {
            renderH = elemH;
            renderW = elemH * imgRatio;
            offsetX = (elemW - renderW) / 2;
            offsetY = 0;
        }
        return {
            left: rect.left + offsetX,
            top: rect.top + offsetY,
            width: renderW,
            height: renderH,
            naturalWidth: natW,
            naturalHeight: natH
        };
    }

    function createOverlayElements() {
        const previewBox = document.getElementById('roi_preview_box');
        if (!previewBox) return;

        const img = previewBox.querySelector('img');
        if (!img) return;

        if (overlay && document.contains(overlay)) return;

        const container = img.parentElement;
        if (!container) return;
        container.style.position = 'relative';

        overlay = document.createElement('div');
        overlay.id = 'roi_interactive_overlay';
        overlay.style.position = 'absolute';
        overlay.style.cursor = 'crosshair';
        overlay.style.zIndex = '50';
        overlay.style.pointerEvents = 'auto';
        overlay.style.userSelect = 'none';

        box = document.createElement('div');
        box.id = 'roi_interactive_box';
        box.style.position = 'absolute';
        box.style.border = '2px solid #8B5CF6';
        box.style.background = 'rgba(139, 92, 246, 0.22)';
        box.style.boxShadow = '0 0 14px rgba(139, 92, 246, 0.6)';
        box.style.cursor = 'move';
        box.style.display = 'none';

        badge = document.createElement('div');
        badge.id = 'roi_box_badge';
        badge.style.position = 'absolute';
        badge.style.top = '-28px';
        badge.style.left = '0';
        badge.style.background = 'rgba(15, 23, 42, 0.9)';
        badge.style.color = '#E2E8F0';
        badge.style.fontSize = '11px';
        badge.style.fontWeight = 'bold';
        badge.style.padding = '2px 8px';
        badge.style.borderRadius = '4px';
        badge.style.border = '1px solid #8B5CF6';
        badge.style.whiteSpace = 'nowrap';
        badge.style.pointerEvents = 'none';
        box.appendChild(badge);

        const handlePositions = ['nw', 'ne', 'se', 'sw'];
        handles = {};
        handlePositions.forEach(pos => {
            const h = document.createElement('div');
            h.dataset.handle = pos;
            h.style.position = 'absolute';
            h.style.width = '12px';
            h.style.height = '12px';
            h.style.background = '#FFFFFF';
            h.style.border = '2px solid #8B5CF6';
            h.style.borderRadius = '50%';
            h.style.boxShadow = '0 0 4px rgba(0,0,0,0.5)';
            h.style.zIndex = '55';

            if (pos === 'nw') { h.style.left = '-6px'; h.style.top = '-6px'; h.style.cursor = 'nwse-resize'; }
            if (pos === 'ne') { h.style.right = '-6px'; h.style.top = '-6px'; h.style.cursor = 'nesw-resize'; }
            if (pos === 'se') { h.style.right = '-6px'; h.style.bottom = '-6px'; h.style.cursor = 'nwse-resize'; }
            if (pos === 'sw') { h.style.left = '-6px'; h.style.bottom = '-6px'; h.style.cursor = 'nesw-resize'; }

            box.appendChild(h);
            handles[pos] = h;
        });

        overlay.appendChild(box);
        container.appendChild(overlay);

        setupPointerEvents();
        updateOverlayPosition();
    }

    function updateOverlayPosition() {
        if (!overlay) return;
        const previewBox = document.getElementById('roi_preview_box');
        if (!previewBox) return;
        const img = previewBox.querySelector('img');
        if (!img) return;

        const r = getRenderedImageRect(img);
        if (!r) return;

        const parentRect = img.parentElement.getBoundingClientRect();
        overlay.style.left = (r.left - parentRect.left) + 'px';
        overlay.style.top = (r.top - parentRect.top) + 'px';
        overlay.style.width = r.width + 'px';
        overlay.style.height = r.height + 'px';

        if (window.__ROI_DATA && !isInteracting) {
            syncBoxFromCoordinates(
                window.__ROI_DATA.left_x,
                window.__ROI_DATA.bottom_y,
                window.__ROI_DATA.right_x,
                window.__ROI_DATA.top_y
            );
        }
    }

    function renderBox(natX, natY, natW, natH) {
        if (!box || !overlay) return;
        const previewBox = document.getElementById('roi_preview_box');
        const img = previewBox ? previewBox.querySelector('img') : null;
        if (!img) return;
        const r = getRenderedImageRect(img);
        if (!r) return;

        const scaleX = r.width / r.naturalWidth;
        const scaleY = r.height / r.naturalHeight;

        box.style.display = 'block';
        box.style.left = (natX * scaleX) + 'px';
        box.style.top = (natY * scaleY) + 'px';
        box.style.width = (natW * scaleX) + 'px';
        box.style.height = (natH * scaleY) + 'px';

        if (badge) {
            badge.innerText = '[' + natX + ', ' + natY + '] • ' + natW + ' × ' + natH + ' px';
        }
    }

    function pushCoordinatesToGradio(lx, by, rx, ty) {
        window.__ROI_DATA = { left_x: lx, bottom_y: by, right_x: rx, top_y: ty };
        setGradioInput('slider_left_x', lx);
        setGradioInput('slider_bottom_y', by);
        setGradioInput('slider_right_x', rx);
        setGradioInput('slider_top_y', ty);
    }

    function syncBoxFromCoordinates(lx, by, rx, ty) {
        const previewBox = document.getElementById('roi_preview_box');
        const img = previewBox ? previewBox.querySelector('img') : null;
        if (!img) return;
        const r = getRenderedImageRect(img);
        if (!r) return;

        const natX = Math.min(lx, rx);
        const natY = Math.min(by, ty);
        const natW = Math.abs(rx - lx);
        const natH = Math.abs(ty - by);

        renderBox(natX, natY, natW, natH);

        const scaleX = r.width / r.naturalWidth;
        const scaleY = r.height / r.naturalHeight;
        boxLeft = natX * scaleX;
        boxTop = natY * scaleY;
        boxWidth = natW * scaleX;
        boxHeight = natH * scaleY;
    }

    window.__snapRoiPreset = function(type) {
        const previewBox = document.getElementById('roi_preview_box');
        const img = previewBox ? previewBox.querySelector('img') : null;
        const natW = img ? (img.naturalWidth || 1920) : 1920;
        const natH = img ? (img.naturalHeight || 1080) : 1080;

        let lx = 0, rx = natW, ty = 0, by = natH;
        if (type === 'bottom') {
            const band = Math.round(natH * 0.18);
            lx = 0; rx = natW; ty = natH - band; by = natH;
        } else if (type === 'top') {
            const band = Math.round(natH * 0.18);
            lx = 0; rx = natW; ty = 0; by = band;
        } else if (type === 'tiktok_br') {
            lx = Math.round(natW * 0.68); rx = Math.round(natW * 0.98);
            ty = Math.round(natH * 0.86); by = Math.round(natH * 0.98);
        } else if (type === 'tiktok_tl') {
            lx = Math.round(natW * 0.02); rx = Math.round(natW * 0.32);
            ty = Math.round(natH * 0.04); by = Math.round(natH * 0.16);
        } else if (type === 'center') {
            lx = Math.round(natW * 0.08); rx = Math.round(natW * 0.92);
            ty = Math.round(natH * 0.40); by = Math.round(natH * 0.60);
        } else if (type === 'full') {
            lx = 0; rx = natW; ty = 0; by = natH;
        }

        syncBoxFromCoordinates(lx, by, rx, ty);
        pushCoordinatesToGradio(lx, by, rx, ty);
    };

    function setupPointerEvents() {
        if (!overlay) return;

        overlay.addEventListener('pointerdown', (e) => {
            const overlayRect = overlay.getBoundingClientRect();
            const relX = e.clientX - overlayRect.left;
            const relY = e.clientY - overlayRect.top;

            if (e.target.dataset && e.target.dataset.handle) {
                isInteracting = true;
                currentMode = 'resizing';
                activeHandle = e.target.dataset.handle;
                startX = e.clientX;
                startY = e.clientY;
                initialBox = { l: boxLeft, t: boxTop, w: boxWidth, h: boxHeight };
                e.stopPropagation();
                return;
            }

            if (e.target === box || box.contains(e.target)) {
                isInteracting = true;
                currentMode = 'moving';
                startX = e.clientX;
                startY = e.clientY;
                initialBox = { l: boxLeft, t: boxTop, w: boxWidth, h: boxHeight };
                e.stopPropagation();
                return;
            }

            isInteracting = true;
            currentMode = 'drawing';
            startX = relX;
            startY = relY;
            boxLeft = relX;
            boxTop = relY;
            boxWidth = 0;
            boxHeight = 0;
            initialBox = { l: relX, t: relY, w: 0, h: 0 };
            box.style.display = 'block';
            box.style.left = boxLeft + 'px';
            box.style.top = boxTop + 'px';
            box.style.width = '0px';
            box.style.height = '0px';
        });

        overlay.addEventListener('pointermove', (e) => {
            if (!isInteracting) return;
            const overlayRect = overlay.getBoundingClientRect();
            const relX = e.clientX - overlayRect.left;
            const relY = e.clientY - overlayRect.top;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            if (currentMode === 'drawing') {
                boxLeft = Math.max(0, Math.min(startX, relX));
                boxTop = Math.max(0, Math.min(startY, relY));
                boxWidth = Math.min(overlayRect.width - boxLeft, Math.abs(relX - startX));
                boxHeight = Math.min(overlayRect.height - boxTop, Math.abs(relY - startY));
            } else if (currentMode === 'moving') {
                boxLeft = Math.max(0, Math.min(overlayRect.width - initialBox.w, initialBox.l + dx));
                boxTop = Math.max(0, Math.min(overlayRect.height - initialBox.h, initialBox.t + dy));
                boxWidth = initialBox.w;
                boxHeight = initialBox.h;
            } else if (currentMode === 'resizing') {
                let l = initialBox.l, t = initialBox.t, r = initialBox.l + initialBox.w, b = initialBox.t + initialBox.h;
                if (activeHandle.includes('w')) l = Math.min(r - 10, initialBox.l + dx);
                if (activeHandle.includes('e')) r = Math.max(l + 10, initialBox.l + initialBox.w + dx);
                if (activeHandle.includes('n')) t = Math.min(b - 10, initialBox.t + dy);
                if (activeHandle.includes('s')) b = Math.max(t + 10, initialBox.t + initialBox.h + dy);

                boxLeft = Math.max(0, l);
                boxTop = Math.max(0, t);
                boxWidth = Math.min(overlayRect.width - boxLeft, r - l);
                boxHeight = Math.min(overlayRect.height - boxTop, b - t);
            }

            const previewBox = document.getElementById('roi_preview_box');
            const img = previewBox ? previewBox.querySelector('img') : null;
            if (img) {
                const r = getRenderedImageRect(img);
                if (r) {
                    const natX1 = Math.round((boxLeft / r.width) * r.naturalWidth);
                    const natY1 = Math.round((boxTop / r.height) * r.naturalHeight);
                    const natW = Math.round((boxWidth / r.width) * r.naturalWidth);
                    const natH = Math.round((boxHeight / r.height) * r.naturalHeight);
                    renderBox(natX1, natY1, natW, natH);
                }
            }
        });

        const finishInteraction = () => {
            if (!isInteracting) return;
            isInteracting = false;
            currentMode = null;
            activeHandle = null;

            const previewBox = document.getElementById('roi_preview_box');
            const img = previewBox ? previewBox.querySelector('img') : null;
            if (!img) return;
            const r = getRenderedImageRect(img);
            if (!r) return;

            if (boxWidth < 6 || boxHeight < 6) {
                const tapX = boxLeft;
                const tapY = boxTop;
                const defW = r.width * 0.65;
                const defH = r.height * 0.16;
                boxLeft = Math.max(0, Math.min(r.width - defW, tapX - defW / 2));
                boxTop = Math.max(0, Math.min(r.height - defH, tapY - defH / 2));
                boxWidth = defW;
                boxHeight = defH;
            }

            const natX1 = Math.max(0, Math.min(r.naturalWidth, Math.round((boxLeft / r.width) * r.naturalWidth)));
            const natY1 = Math.max(0, Math.min(r.naturalHeight, Math.round((boxTop / r.height) * r.naturalHeight)));
            const natX2 = Math.max(0, Math.min(r.naturalWidth, Math.round(((boxLeft + boxWidth) / r.width) * r.naturalWidth)));
            const natY2 = Math.max(0, Math.min(r.naturalHeight, Math.round(((boxTop + boxHeight) / r.height) * r.naturalHeight)));

            renderBox(natX1, natY1, natX2 - natX1, natY2 - natY1);
            pushCoordinatesToGradio(natX1, natY2, natX2, natY1);
        };

        overlay.addEventListener('pointerup', finishInteraction);
        overlay.addEventListener('pointercancel', finishInteraction);
    }

    // Main polling loop for canvas + CapCut timeline
    setInterval(() => {
        // CapCut video element detection
        const v = findVideoElement();
        if (v && v !== cc.video) {
            cc.video = v;
            v.addEventListener('timeupdate', updatePlayhead);
            const onMeta = () => {
                if (v.duration && v.duration > 0) {
                    cc.duration = v.duration;
                    if (cc.end <= 0 || cc.end > cc.duration) {
                        cc.end = cc.duration;
                    }
                    buildRuler(cc.duration);
                    updateCapcutUI();
                }
            };
            v.addEventListener('durationchange', onMeta);
            v.addEventListener('loadedmetadata', onMeta);
            v.addEventListener('canplay', onMeta);
        }

        if (cc.video && cc.video.duration && cc.video.duration > 0) {
            if (cc.duration !== cc.video.duration) {
                cc.duration = cc.video.duration;
                if (cc.end <= 0 || cc.end > cc.duration) {
                    cc.end = cc.duration;
                }
                buildRuler(cc.duration);
                updateCapcutUI();
            }
        }

        attachCapcutListeners();
        updatePlayhead();

        // Canvas overlay position & slider sync
        if (!overlay || !document.contains(overlay)) {
            createOverlayElements();
        } else {
            updateOverlayPosition();
        }

        if (!isInteracting) {
            const lxInput = document.querySelector('#slider_left_x input');
            const byInput = document.querySelector('#slider_bottom_y input');
            const rxInput = document.querySelector('#slider_right_x input');
            const tyInput = document.querySelector('#slider_top_y input');
            if (lxInput && byInput && rxInput && tyInput) {
                const curLx = parseInt(lxInput.value);
                const curBy = parseInt(byInput.value);
                const curRx = parseInt(rxInput.value);
                const curTy = parseInt(tyInput.value);
                if (curLx !== lastLx || curBy !== lastBy || curRx !== lastRx || curTy !== lastTy) {
                    lastLx = curLx; lastBy = curBy; lastRx = curRx; lastTy = curTy;
                    syncBoxFromCoordinates(curLx, curBy, curRx, curTy);
                }
            }
        }
    }, 80);

    window.addEventListener('resize', () => {
        updateOverlayPosition();
    });
})();
"""

RUN_BTN_JS = """
(video, lx, by, rx, ty, trim, tStart, tEnd, color, mode, prev, dil, lama, temp) => {
    if (window.__ROI_DATA) {
        lx = window.__ROI_DATA.left_x;
        by = window.__ROI_DATA.bottom_y;
        rx = window.__ROI_DATA.right_x;
        ty = window.__ROI_DATA.top_y;
    }
    if (window.__TRIM_DATA && window.__TRIM_DATA.enabled) {
        trim = true;
        tStart = window.__TRIM_DATA.start;
        tEnd = window.__TRIM_DATA.end;
    }
    return [video, lx, by, rx, ty, trim, tStart, tEnd, color, mode, prev, dil, lama, temp];
}
"""


# ---------------------------------------------------------------------------
# UI Definition & Custom CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
/* App Container & Modern Dark Theme */
.gradio-container {
    max-width: 1440px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* Hide Gradio's client-side WebAssembly Trim button to avoid browser crashes */
button[aria-label*="Trim video"],
button[title*="Trim video"],
div[class*="trim"] button:first-child {
    display: none !important;
}

/* Card Panels */
.card-panel {
    background: #0B1120 !important;
    border: 1px solid #1E293B !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    margin-bottom: 14px !important;
}

.card-header-title {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #F8FAFC !important;
    letter-spacing: -0.01em !important;
    margin-bottom: 12px !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

/* Header Banner */
.hero-header {
    background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%) !important;
    border: 1px solid #312E81 !important;
    border-radius: 16px !important;
    padding: 22px 28px !important;
    margin-bottom: 18px !important;
    box-shadow: 0 8px 30px rgba(79, 70, 229, 0.15) !important;
}

.header-title {
    font-size: 1.85rem !important;
    font-weight: 800 !important;
    color: #FFFFFF !important;
    margin: 0 !important;
    letter-spacing: -0.02em !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}

.header-subtitle {
    color: #94A3B8 !important;
    font-size: 0.95rem !important;
    margin-top: 6px !important;
    margin-bottom: 0 !important;
}

.badge-pill {
    display: inline-block !important;
    padding: 3px 10px !important;
    border-radius: 9999px !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    background: rgba(99, 102, 241, 0.18) !important;
    color: #A5B4FC !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
}

/* Preset Chips */
.preset-chip-group {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    margin-top: 8px !important;
    margin-bottom: 8px !important;
}

.preset-chip-group button {
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    padding: 6px 14px !important;
    font-weight: 600 !important;
    border: 1px solid #334155 !important;
    background: #1E293B !important;
    color: #E2E8F0 !important;
    transition: all 0.15s ease !important;
}

.preset-chip-group button:hover {
    background: #334155 !important;
    border-color: #6366F1 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}

/* Sync Buttons */
.btn-auto-sync {
    background: rgba(99, 102, 241, 0.25) !important;
    border: 1px solid #818CF8 !important;
    color: #E0E7FF !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}
.btn-auto-sync:hover {
    background: rgba(99, 102, 241, 0.45) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35) !important;
}

/* Sliders & High Contrast Labels */
.gr-form label, .gr-box label, label span, .gr-markdown p {
    color: #E2E8F0 !important;
}

/* Primary Call To Action Button */
.primary-cta button {
    background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 14px 28px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
    transition: all 0.2s ease !important;
}

.primary-cta button:hover {
    box-shadow: 0 6px 26px rgba(99, 102, 241, 0.6) !important;
    transform: translateY(-2px) !important;
}

/* ------------------------------------------------------------- */
/* CapCut Timeline Trimmer Component Styling                      */
/* ------------------------------------------------------------- */
.capcut-container {
    background: #070B14 !important;
    border: 1px solid #1E293B !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    margin-top: 14px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45) !important;
    user-select: none !important;
}

.capcut-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 10px !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

.capcut-title-box {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}

.capcut-badge {
    background: linear-gradient(135deg, #0284C7 0%, #6366F1 100%) !important;
    color: #FFFFFF !important;
    font-size: 0.76rem !important;
    font-weight: 800 !important;
    padding: 3px 9px !important;
    border-radius: 6px !important;
    letter-spacing: 0.02em !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
}

.capcut-summary {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #F8FAFC !important;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
}

.capcut-toggle-box {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.capcut-switch {
    position: relative !important;
    display: inline-block !important;
    width: 38px !important;
    height: 20px !important;
    margin: 0 !important;
}

.capcut-switch input {
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
}

.capcut-slider {
    position: absolute !important;
    cursor: pointer !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    background-color: #334155 !important;
    transition: 0.25s !important;
    border-radius: 20px !important;
}

.capcut-slider:before {
    position: absolute !important;
    content: "" !important;
    height: 14px !important;
    width: 14px !important;
    left: 3px !important;
    bottom: 3px !important;
    background-color: white !important;
    transition: 0.25s !important;
    border-radius: 50% !important;
}

.capcut-switch input:checked + .capcut-slider {
    background: #0284C7 !important;
}

.capcut-switch input:checked + .capcut-slider:before {
    transform: translateX(18px) !important;
}

.capcut-toggle-text {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
}

.capcut-ruler-wrapper {
    position: relative !important;
    height: 20px !important;
    margin-bottom: 4px !important;
    overflow: hidden !important;
}

.capcut-ruler {
    position: relative !important;
    width: 100% !important;
    height: 100% !important;
    font-size: 0.72rem !important;
    color: #64748B !important;
    font-family: ui-monospace, monospace !important;
    border-bottom: 1px solid #1E293B !important;
}

.capcut-ruler-tick {
    position: absolute !important;
    bottom: 0 !important;
    transform: translateX(-50%) !important;
    white-space: nowrap !important;
}

.capcut-ruler-tick::after {
    content: "" !important;
    position: absolute !important;
    bottom: 0 !important;
    left: 50% !important;
    width: 1px !important;
    height: 4px !important;
    background: #475569 !important;
}

.capcut-track-wrapper {
    position: relative !important;
    height: 60px !important;
    background: #0F172A !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    cursor: pointer !important;
}

.capcut-track-track {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    background: repeating-linear-gradient(
        90deg,
        #1E293B 0px,
        #1E293B 12px,
        #0F172A 12px,
        #0F172A 24px
    ) !important;
    opacity: 0.35 !important;
    pointer-events: none !important;
}

.capcut-dim {
    position: absolute !important;
    top: 0 !important;
    bottom: 0 !important;
    background: rgba(3, 7, 18, 0.75) !important;
    z-index: 5 !important;
    pointer-events: none !important;
}

.capcut-dim-left {
    left: 0 !important;
}

.capcut-dim-right {
    right: 0 !important;
}

.capcut-clip {
    position: absolute !important;
    top: 0 !important;
    bottom: 0 !important;
    border: 2px solid #FFD200 !important;
    background: rgba(255, 210, 0, 0.12) !important;
    box-shadow: 0 0 16px rgba(255, 210, 0, 0.28) !important;
    z-index: 10 !important;
    display: flex !important;
    align-items: stretch !important;
    box-sizing: border-box !important;
}

.capcut-clip-body {
    flex: 1 !important;
    cursor: grab !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 100% !important;
}

.capcut-clip-body:active {
    cursor: grabbing !important;
}

.capcut-clip-len {
    background: rgba(15, 23, 42, 0.9) !important;
    color: #FDE047 !important;
    font-size: 0.76rem !important;
    font-weight: 800 !important;
    padding: 2px 8px !important;
    border-radius: 4px !important;
    border: 1px solid rgba(255, 210, 0, 0.5) !important;
    font-family: ui-monospace, monospace !important;
    pointer-events: none !important;
}

.capcut-handle {
    width: 20px !important;
    background: #FFD200 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: ew-resize !important;
    position: relative !important;
    z-index: 20 !important;
    transition: background 0.15s ease !important;
}

.capcut-handle:hover {
    background: #FACC15 !important;
    box-shadow: 0 0 10px rgba(255, 210, 0, 0.6) !important;
}

.capcut-handle-left {
    border-top-left-radius: 5px !important;
    border-bottom-left-radius: 5px !important;
}

.capcut-handle-right {
    border-top-right-radius: 5px !important;
    border-bottom-right-radius: 5px !important;
}

.capcut-handle-icon {
    font-size: 11px !important;
    font-weight: 900 !important;
    color: #0F172A !important;
    pointer-events: none !important;
}

.capcut-tag {
    position: absolute !important;
    top: -24px !important;
    background: #0F172A !important;
    color: #F8FAFC !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    padding: 1px 6px !important;
    border-radius: 4px !important;
    border: 1px solid #FFD200 !important;
    white-space: nowrap !important;
    pointer-events: none !important;
    display: none !important;
    font-family: ui-monospace, monospace !important;
}

.capcut-handle:hover .capcut-tag,
.capcut-handle:active .capcut-tag {
    display: block !important;
}

.capcut-playhead {
    position: absolute !important;
    top: 0 !important;
    bottom: 0 !important;
    width: 2px !important;
    z-index: 30 !important;
    pointer-events: none !important;
    transform: translateX(-50%) !important;
}

.capcut-playhead-pin {
    width: 14px !important;
    height: 14px !important;
    background: #EF4444 !important;
    border-radius: 3px !important;
    transform: translateX(-50%) rotate(45deg) !important;
    position: absolute !important;
    top: -4px !important;
    left: 1px !important;
    cursor: grab !important;
    pointer-events: auto !important;
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.8) !important;
}

.capcut-playhead-pin:active {
    cursor: grabbing !important;
}

.capcut-playhead-line {
    width: 2px !important;
    height: 100% !important;
    background: #EF4444 !important;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.6) !important;
}

.capcut-playhead-badge {
    position: absolute !important;
    bottom: -22px !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    background: #EF4444 !important;
    color: #FFFFFF !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    padding: 1px 5px !important;
    border-radius: 3px !important;
    white-space: nowrap !important;
    font-family: ui-monospace, monospace !important;
}

.capcut-controls-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-top: 26px !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

.capcut-btn-group {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    flex-wrap: wrap !important;
}

.capcut-btn {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #E2E8F0 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 6px 12px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}

.capcut-btn:hover {
    background: #334155 !important;
    color: #FFFFFF !important;
    border-color: #64748B !important;
}

.capcut-btn-gold {
    background: rgba(255, 210, 0, 0.15) !important;
    border-color: #FFD200 !important;
    color: #FDE047 !important;
    font-weight: 700 !important;
}

.capcut-btn-gold:hover {
    background: rgba(255, 210, 0, 0.3) !important;
    color: #FFFFFF !important;
}

.capcut-btn-play {
    background: rgba(16, 185, 129, 0.2) !important;
    border-color: #10B981 !important;
    color: #6EE7B7 !important;
    font-weight: 700 !important;
}

.capcut-btn-play:hover {
    background: rgba(16, 185, 129, 0.35) !important;
    color: #FFFFFF !important;
}

.capcut-btn-sync {
    background: rgba(99, 102, 241, 0.2) !important;
    border-color: #818CF8 !important;
    color: #C7D2FE !important;
    font-weight: 700 !important;
}

.capcut-btn-sync:hover {
    background: rgba(99, 102, 241, 0.35) !important;
    color: #FFFFFF !important;
}

.capcut-quick-chips {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}

.capcut-chips-title {
    font-size: 0.78rem !important;
    color: #64748B !important;
    font-weight: 600 !important;
}

.capcut-chip {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #94A3B8 !important;
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    padding: 3px 8px !important;
    border-radius: 4px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
}

.capcut-chip:hover {
    background: #0284C7 !important;
    border-color: #38BDF8 !important;
    color: #FFFFFF !important;
}

.capcut-inputs-row {
    display: flex !important;
    gap: 12px !important;
    margin-top: 10px !important;
    background: #0B0F19 !important;
    border: 1px solid #1E293B !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}

.capcut-input-col {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}

.capcut-input-label {
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: #94A3B8 !important;
    white-space: nowrap !important;
}

.capcut-input-wrap {
    display: flex !important;
    align-items: center !important;
    background: #020617 !important;
    border: 1px solid #334155 !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    width: 100% !important;
}

.capcut-input-wrap input {
    background: transparent !important;
    border: none !important;
    color: #F8FAFC !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    padding: 2px 0 !important;
    font-family: ui-monospace, monospace !important;
    outline: none !important;
}

.capcut-unit {
    font-size: 0.7rem !important;
    color: #64748B !important;
    font-weight: 600 !important;
}
"""


def build_ui() -> Tuple[gr.Blocks, gr.Theme, str]:
    theme = gr.themes.Soft(
        primary_hue="indigo",
        neutral_hue="slate",
    ).set(
        body_background_fill="#030712",
        block_background_fill="#0F172A",
        block_border_color="#1E293B",
        input_background_fill="#020617",
        input_border_color="#334155",
    )

    icon_header = "✨"
    icon_video = "📹"
    icon_target = "🎯"
    icon_palette = "🎨"
    icon_cpu = "⚙️"
    icon_output = "🎬"

    with gr.Blocks(title="Caption Remover Studio") as demo:
        # Header
        with gr.Row(elem_classes=["hero-header"]):
            with gr.Column():
                with gr.Row():
                    with gr.Column(scale=9):
                        gr.HTML(f"""
                        <div>
                            <h1 class="header-title">{icon_header} Video Subtitle Remover Studio</h1>
                            <p class="header-subtitle">CapCut Timeline Trimmer • Interactive Draggable Canvas • LaMa Neural Inpainting</p>
                        </div>
                        """)
                    with gr.Column(scale=3):
                        gr.HTML(f"""
                        <div style="display: flex; gap: 8px; align-items: center; justify-content: flex-end;">
                            <span class="badge-pill">✂️ CapCut Trimmer</span>
                            <span class="badge-pill">🖱️ Draggable Canvas</span>
                            <span class="badge-pill">v{__version__}</span>
                        </div>
                        """)

        # TOP ROW: Video Upload & CapCut Trimmer (Left) + Draggable Canvas (Right)
        with gr.Row(equal_height=True):
            # STEP 1: Video Player + CapCut Trimmer
            with gr.Column(scale=6, elem_classes=["card-panel"]):
                gr.HTML(f"<div class='card-header-title'>{icon_video} Step 1: Upload Source Video & CapCut Trimmer</div>")
                video_in = gr.Video(label="Input Video Player", sources=["upload"], elem_id="source_video_player")
                info_md = gr.Markdown("")
                
                # CapCut-style Visual Timeline Trimmer Component
                gr.HTML(CAPCUT_TIMELINE_HTML)

                # Synchronized Gradio Trim Inputs (hidden from view, kept in sync by CapCut JS)
                clip_trim_chk = gr.Checkbox(value=False, visible=False, elem_id="chk_clip_trim")
                clip_start_num = gr.Number(value=0.0, visible=False, elem_id="input_clip_start")
                clip_end_num = gr.Number(value=0.0, visible=False, elem_id="input_clip_end")

            # STEP 2: Interactive Draggable ROI Canvas
            with gr.Column(scale=6, elem_classes=["card-panel"]):
                gr.HTML(f"<div class='card-header-title'>{icon_target} Step 2: Target Subtitle Region (Draggable Canvas)</div>")
                gr.HTML(
                    """
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 0.85rem; color: #C4B5FD;">
                        <span>🖱️ <b>Drag directly on the frame</b> to draw or resize the target box. Or snap a quick preset:</span>
                    </div>
                    """
                )
                roi_preview = gr.Image(
                    label="Frame Preview & Interactive Draggable Canvas",
                    type="numpy",
                    interactive=False,
                    elem_id="roi_preview_box",
                )

                # Frame Timestamp Selector to jump to the moment where captions appear
                with gr.Row():
                    preview_time_slider = gr.Slider(0, 100, value=0.0, step=0.1, label="Preview Frame Timestamp (s)", info="Slide to view any second of the video", elem_id="input_preview_time", scale=8)
                    sync_frame_btn = gr.Button("🎬 Load Player Frame", size="sm", elem_classes=["btn-auto-sync"], elem_id="btn_sync_frame_from_player", scale=4)

                gr.HTML("<div style='font-size: 0.82rem; color: #94A3B8; margin: 8px 0 4px 0;'>Quick Snap Presets:</div>")
                with gr.Row(elem_classes=["preset-chip-group"]):
                    preset_bottom_btn = gr.Button("⬇️ Bottom 18% (Standard)", size="sm")
                    preset_top_btn = gr.Button("⬆️ Top 18% (Header)", size="sm")
                    preset_tiktok_br_btn = gr.Button("🎴 TikTok (Bottom-Right)", size="sm")
                    preset_tiktok_tl_btn = gr.Button("🎴 TikTok (Top-Left)", size="sm")
                    preset_center_btn = gr.Button("🎯 Center Banner", size="sm")
                    preset_full_btn = gr.Button("⏹️ Full Frame", size="sm")

                with gr.Accordion("⚙️ Manual Coordinate Precision (Pixels)", open=False):
                    with gr.Row():
                        left_x_slider = gr.Slider(0, 1920, value=0, step=1, label="Left X", elem_id="slider_left_x")
                        bottom_y_slider = gr.Slider(0, 1080, value=1080, step=1, label="Bottom Y", elem_id="slider_bottom_y")
                    with gr.Row():
                        right_x_slider = gr.Slider(0, 1920, value=1920, step=1, label="Right X", elem_id="slider_right_x")
                        top_y_slider = gr.Slider(0, 1080, value=900, step=1, label="Top Y", elem_id="slider_top_y")

        # MIDDLE ROW: Subtitle Style & AI Model Backend
        with gr.Row():
            with gr.Column(scale=6, elem_classes=["card-panel"]):
                gr.HTML(f"<div class='card-header-title'>{icon_palette} Step 3: Caption, Banner & Watermark Style</div>")
                color_radio = gr.Radio(
                    choices=[
                        ("✨ White Text + Dark Outline / Stroke", "white_stroke"),
                        ("🎨 Pink / Colored Caption Box Banner", "colored_box"),
                        ("🛡️ Watermark / Logo / Entire Box Area", "full_box"),
                        ("⚪ White Text (No Outline)", "white"),
                        ("⚫ Black / Dark Text", "black"),
                    ],
                    value="white_stroke",
                    label="Target Element Style",
                    info="Select 'Watermark / Entire Box Area' to completely erase TikTok logos, usernames, or solid text boxes!",
                )

            with gr.Column(scale=6, elem_classes=["card-panel"]):
                gr.HTML(f"<div class='card-header-title'>{icon_cpu} Step 4: AI Inpainting Engine</div>")
                mode_radio = gr.Radio(
                    choices=[
                        ("⚡ Fast Mode (OpenCV Telea)", "fast"),
                        ("🧠 Quality Mode (LaMa Deep AI)", "quality"),
                    ],
                    value="fast",
                    label="Inpainting Engine Choice",
                    info="Fast mode finishes in seconds. Quality mode runs LaMa neural inpainter for complex backgrounds.",
                )
                preview_chk = gr.Checkbox(
                    value=False,
                    label="⚡ Fast Preview First 3 Seconds Only (Uncheck for Full Video)",
                )

                with gr.Accordion("⚙️ Precision Tuning Controls (Anti-Blur Defaults)", open=False):
                    dilate_slider = gr.Slider(1, 6, value=2, step=1, label="Mask Dilation (Keep 2-3)", info="Tight mask keeps surrounding background 100% crisp. High values cause blur.")
                    lama_extra_slider = gr.Slider(0, 6, value=1, step=1, label="LaMa Extra Padding (Keep 1-2)", info="Extra edge expansion. Lower values prevent smudge halos.")
                    temporal_slider = gr.Slider(1, 24, value=12, step=1, label="Temporal Smoothing (Anti-Flicker and Karaoke)", info="10-15 recommended. Unifies animated/karaoke words across the phrase so inactive words never ghost.")

        # BOTTOM ROW: Launch Button & Final Video Result
        with gr.Row():
            with gr.Column(elem_classes=["card-panel"], scale=12):
                with gr.Column(elem_classes=["primary-cta"]):
                    run_btn = gr.Button("🚀 Start AI Subtitle Removal", size="lg")

                gr.HTML(f"<div class='card-header-title' style='margin-top: 20px;'>{icon_output} Final Repaired Video Result</div>")
                video_out = gr.Video(label="Repaired Video Output", interactive=False)

        # ---- Event Wiring ----
        upload_outputs = [
            roi_preview,
            left_x_slider, bottom_y_slider, right_x_slider, top_y_slider,
            preview_time_slider,
            clip_start_num, clip_end_num,
            info_md,
        ]

        # Use upload event when file is fully transferred
        video_in.upload(on_video_uploaded, inputs=[video_in], outputs=upload_outputs)
        video_in.clear(on_video_cleared, inputs=[], outputs=upload_outputs)

        # Preview Frame Timestamp changes
        preview_time_slider.release(
            on_load_frame_at_time,
            inputs=[video_in, preview_time_slider],
            outputs=[roi_preview],
        )
        sync_frame_btn.click(
            None,
            inputs=[],
            outputs=[],
            js="() => { if (window.__syncFrameFromPlayer) window.__syncFrameFromPlayer(); }",
        )

        # ROI Preset button wiring (instant JS snap + Python slider update)
        preset_bottom_btn.click(
            on_preset_bottom,
            inputs=[video_in],
            outputs=[left_x_slider, bottom_y_slider, right_x_slider, top_y_slider],
            js="() => { if (window.__snapRoiPreset) window.__snapRoiPreset('bottom'); }",
        )
        preset_top_btn.click(
            on_preset_top,
            inputs=[video_in],
            outputs=[left_x_slider, bottom_y_slider, right_x_slider, top_y_slider],
            js="() => { if (window.__snapRoiPreset) window.__snapRoiPreset('top'); }",
        )
        preset_tiktok_br_btn.click(
            on_preset_tiktok_br,
            inputs=[video_in],
            outputs=[left_x_slider, bottom_y_slider, right_x_slider, top_y_slider],
            js="() => { if (window.__snapRoiPreset) window.__snapRoiPreset('tiktok_br'); }",
        )
        preset_tiktok_tl_btn.click(
            on_preset_tiktok_tl,
            inputs=[video_in],
            outputs=[left_x_slider, bottom_y_slider, right_x_slider, top_y_slider],
            js="() => { if (window.__snapRoiPreset) window.__snapRoiPreset('tiktok_tl'); }",
        )
        preset_center_btn.click(
            on_preset_center,
            inputs=[video_in],
            outputs=[left_x_slider, bottom_y_slider, right_x_slider, top_y_slider],
            js="() => { if (window.__snapRoiPreset) window.__snapRoiPreset('center'); }",
        )
        preset_full_btn.click(
            on_preset_full,
            inputs=[video_in],
            outputs=[left_x_slider, bottom_y_slider, right_x_slider, top_y_slider],
            js="() => { if (window.__snapRoiPreset) window.__snapRoiPreset('full'); }",
        )

        # Run pipeline
        run_btn.click(
            process_video,
            inputs=[
                video_in,
                left_x_slider, bottom_y_slider, right_x_slider, top_y_slider,
                clip_trim_chk, clip_start_num, clip_end_num,
                color_radio,
                mode_radio,
                preview_chk,
                dilate_slider,
                lama_extra_slider,
                temporal_slider,
            ],
            outputs=[video_out],
            js=RUN_BTN_JS,
        )

        # Inject client-side CapCut timeline & draggable canvas script on load
        demo.load(None, None, js=CLIENT_SCRIPT_JS)

    return demo, theme, CUSTOM_CSS


def main() -> None:
    print(f"[web] ffmpeg = {FFMPEG_BIN}")
    print(f"[web] ffprobe = {FFPROBE_BIN}")
    demo, theme, css = build_ui()
    port = int(os.environ.get('PORT', 0)) or _find_available_port(7860, 50)
    url = f"http://127.0.0.1:{port}"
    print(f"[web] url = {url}")
    threading.Thread(target=_wait_and_open_browser, args=(url,), daemon=True).start()
    demo.queue(max_size=4).launch(
        server_name=os.environ.get('GRADIO_SERVER_NAME', '0.0.0.0' if ('PORT' in os.environ or 'RENDER' in os.environ) else '127.0.0.1'),
        server_port=port,
        inbrowser=False,
        share=False,
        theme=theme,
        css=css,
    )


if __name__ == "__main__":
    main()
