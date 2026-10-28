"""Gradio web UI for Caption Remover Studio matching v0.dev mockups.

Wraps :func:`app.pipeline.run_pipeline` with:
- Pro Studio workspace (Top bar, Subheader, Monitor Frame, Timeline Trimmer, Inspector Dock)
- Interactive draggable & resizable ROI bounding box overlay on monitor video
- Floating pill bar over video: [Fine tune], preset dropdown, and [Snap]
- CapCut-style visual timeline trimmer with In/Out brackets, scrubber, and extend chips
- 01 Caption & watermark style (2x2 cards with icons)
- 02 Inpainting model (Fast mode OpenCV vs Quality AI LaMa)
- 03 Precision tuning (Mask dilation & Temporal anti-flicker sliders)
- Modal 1: ROI Precision (Advanced pixel coordinates with inputs and reset/apply)
- Modal 2: Comparison View (Interactive before/after split slider)
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

import cv2
import gradio as gr
import numpy as np

from . import __version__
from .config import AppConfig
from .ffmpeg_tools.ffmpeg_wrapper import probe_video
from .pipeline import run_pipeline
from .ffmpeg_tools.browser_compat import ensure_browser_playable_video, patch_gradio_routes
from .studio_html import STUDIO_HTML
from .studio_css import STUDIO_CSS
from .studio_js import STUDIO_JS, RUN_BTN_JS

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


LATEST_REPAIRED_PATH: Optional[str] = None


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
    """When video is uploaded, probe dimensions, setup sliders, and video info."""
    global LATEST_REPAIRED_PATH
    LATEST_REPAIRED_PATH = None

    if not video_path:
        return (
            gr.update(maximum=1920, value=0),
            gr.update(maximum=1080, value=0),
            gr.update(maximum=1920, value=1920),
            gr.update(maximum=1080, value=900),
            gr.update(value=0.0),
            gr.update(value=0.0),
        )

    video_path = ensure_browser_playable_video(video_path)
    W, H = _get_video_dimensions(video_path)
    h_band = max(1, int(H * 0.18))
    left_x, bottom_y, right_x, top_y = 0, H, W, H - h_band

    duration_val = 0.0
    try:
        info = probe_video(video_path, FFPROBE_BIN)
        duration_val = round(info.duration, 2)
    except Exception:
        pass

    return (
        gr.update(maximum=W, value=left_x),
        gr.update(maximum=H, value=bottom_y),
        gr.update(maximum=W, value=right_x),
        gr.update(maximum=H, value=top_y),
        gr.update(value=0.0),
        gr.update(value=duration_val),
    )


def on_video_cleared():
    """Reset UI cleanly when video is cleared."""
    global LATEST_REPAIRED_PATH
    LATEST_REPAIRED_PATH = None

    return (
        gr.update(maximum=1920, value=0),
        gr.update(maximum=1080, value=0),
        gr.update(maximum=1920, value=1920),
        gr.update(maximum=1080, value=900),
        gr.update(value=0.0),
        gr.update(value=0.0),
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
    progress: gr.Progress = gr.Progress(),
) -> Tuple[Optional[str], str]:
    def _update_progress(pct: float, desc: str = ""):
        try:
            if progress is not None and callable(progress):
                progress(pct, desc=desc)
        except Exception:
            pass

    if not video_path:
        raise gr.Error("Please upload a video first!")

    frame_w, frame_h = _get_video_dimensions(video_path)
    roi_tuple = _corners_to_roi(int(left_x), int(bottom_y), int(right_x), int(top_y), frame_w, frame_h)
    if roi_tuple[2] <= 1 or roi_tuple[3] <= 1:
        raise gr.Error("Please drag a box over the subtitle or watermark area you wish to remove.")

    if clip_trim and clip_end > 0 and clip_end <= clip_start:
        raise gr.Error(f"End Time ({clip_end}s) must be greater than Start Time ({clip_start}s)")

    _update_progress(0.05, desc="Preparing working directory...")
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

    mode_label = "Fast Mode (OpenCV)" if process_mode == "fast" else "Quality AI (LaMa)"
    if clip_trim:
        _update_progress(0.05, desc=f"Starting Trimmed Clip Inpainting ({clip_start:.1f}s - {clip_end:.1f}s) via {mode_label}...")
    elif is_preview:
        _update_progress(0.05, desc=f"Starting 3-second Fast Preview via {mode_label}...")
    else:
        _update_progress(0.05, desc=f"Starting Full Video Processing via {mode_label}...")

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
        _update_progress(frac, desc=f"Processing Inpainting ({mode_label})... Elapsed: {int(elapsed)}s")
        time.sleep(1.0)

    t.join()

    if "error" in result_holder:
        raise gr.Error(f"Processing failed: {result_holder['error']}")

    out_file = result_holder.get("path")
    if not out_file or not Path(out_file).exists():
        raise gr.Error("Output file was not generated.")

    _update_progress(1.0, desc=f"Completed in {int(time.time() - start_ts)}s!")
    clean_path_str = str(out_file)
    global LATEST_REPAIRED_PATH
    LATEST_REPAIRED_PATH = clean_path_str
    print(f"[web] Saved LATEST_REPAIRED_PATH: {LATEST_REPAIRED_PATH}")
    return clean_path_str, clean_path_str


# ---------------------------------------------------------------------------
# UI Definition & Assembly
# ---------------------------------------------------------------------------

def build_ui() -> Tuple[gr.Blocks, gr.Theme, str]:
    theme = gr.themes.Soft(
        primary_hue="purple",
        neutral_hue="slate",
    ).set(
        body_background_fill="#07090E",
        block_background_fill="#0B0F19",
        block_border_color="#1E283A",
        input_background_fill="#0E1422",
        input_border_color="#1E283A",
    )

    with gr.Blocks(title="Caption Remover Studio") as demo:
        # 1. Main Studio Layout (HTML/CSS matching Screenshots 1, 2, 3 exactly)
        gr.HTML(STUDIO_HTML)

        # 2. Source video player (STUDIO_JS transplants this into #video_player_mount)
        with gr.Row(elem_id="gradio_source_wrapper"):
            video_in = gr.Video(
                label="Upload Source Video",
                sources=["upload"],
                elem_id="source_video_player",
                interactive=True,
            )

        # 3. Gradio Backend Bridge (Keeps all 14 parameters wired to pipeline with zero breakages)
        with gr.Column(elem_id="gradio_backend_bridge"):
            left_x_slider = gr.Slider(0, 4096, value=0, step=1, elem_id="slider_left_x")
            bottom_y_slider = gr.Slider(0, 4096, value=1080, step=1, elem_id="slider_bottom_y")
            right_x_slider = gr.Slider(0, 4096, value=1920, step=1, elem_id="slider_right_x")
            top_y_slider = gr.Slider(0, 4096, value=900, step=1, elem_id="slider_top_y")

            clip_trim_chk = gr.Checkbox(value=True, elem_id="chk_clip_trim")
            clip_start_num = gr.Number(value=0.0, elem_id="input_clip_start")
            clip_end_num = gr.Number(value=0.0, elem_id="input_clip_end")

            color_radio = gr.Radio(
                choices=[
                    ("white_stroke", "white_stroke"),
                    ("white", "white"),
                    ("colored_box", "colored_box"),
                    ("full_box", "full_box"),
                    ("black", "black"),
                ],
                value="white_stroke",
                elem_id="radio_subtitle_color",
            )
            mode_radio = gr.Radio(
                choices=[
                    ("fast", "fast"),
                    ("quality", "quality"),
                ],
                value="quality",
                elem_id="radio_process_mode",
            )
            preview_chk = gr.Checkbox(value=False, elem_id="chk_preview")
            dilate_slider = gr.Slider(1, 6, value=3, step=1, elem_id="slider_dilate")
            lama_extra_slider = gr.Slider(0, 6, value=0, step=1, elem_id="slider_lama_extra")
            temporal_slider = gr.Slider(1, 24, value=1, step=1, elem_id="slider_temporal")

            run_btn = gr.Button("Remove Captions", elem_id="btn_run_pipeline")

        # 4. Docked Repaired Video Result Tray
        with gr.Row(elem_id="gradio_output_wrapper"):
            with gr.Column(scale=12):
                gr.HTML("<div style='font-size:0.95rem; font-weight:700; color:#F8FAFC; margin-bottom:8px;'>🎬 Clean Output Video Player</div>")
                video_out = gr.Video(
                    label="Clean Repaired Video Output",
                    interactive=False,
                    elem_id="repaired_video_player",
                )
                repaired_path_out = gr.Textbox(
                    value="",
                    elem_id="repaired_path_output",
                    visible=True,
                )

        # 5. Event Wiring
        upload_outputs = [
            left_x_slider, bottom_y_slider, right_x_slider, top_y_slider,
            clip_start_num, clip_end_num,
        ]

        def _on_upload_wrapper(v):
            res = on_video_uploaded(v)
            return res[0], res[1], res[2], res[3], res[4], res[5]

        def _on_clear_wrapper():
            res = on_video_cleared()
            return res[0], res[1], res[2], res[3], res[4], res[5]

        video_in.upload(_on_upload_wrapper, inputs=[video_in], outputs=upload_outputs)
        video_in.clear(_on_clear_wrapper, inputs=[], outputs=upload_outputs)

        # Wire Run Button to pipeline with RUN_BTN_JS parameter extraction
        pipeline_event = run_btn.click(
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
            outputs=[video_out, repaired_path_out],
            js=RUN_BTN_JS,
        )

        pipeline_event.then(
            None,
            inputs=[video_out, repaired_path_out],
            outputs=[],
            js="""(vOut, pOut) => {
                let p = '';
                if (typeof pOut === 'string' && pOut.length > 2) {
                    p = pOut;
                } else if (pOut && typeof pOut.value === 'string' && pOut.value.length > 2) {
                    p = pOut.value;
                } else if (vOut && typeof vOut === 'object' && vOut.video && vOut.video.path) {
                    p = vOut.video.path;
                } else if (vOut && typeof vOut === 'object' && vOut.path) {
                    p = vOut.path;
                } else if (typeof vOut === 'string' && vOut.length > 2) {
                    p = vOut;
                }
                if (typeof window.__onPipelineComplete === 'function') {
                    window.__onPipelineComplete(p);
                } else if (window.__STUDIO && typeof window.__STUDIO.complete === 'function') {
                    window.__STUDIO.complete(p);
                }
            }""",
        )

        # Inject client script
        demo.load(None, None, js=STUDIO_JS)

    return demo, theme, STUDIO_CSS


def main() -> None:
    print(f"[web] ffmpeg = {FFMPEG_BIN}")
    print(f"[web] ffprobe = {FFPROBE_BIN}")
    demo, theme, css = build_ui()
    port = int(os.environ.get('PORT', 0)) or _find_available_port(7860, 50)
    url = f"http://127.0.0.1:{port}"
    print(f"[web] url = {url}")

    # Build comprehensive list of allowed paths for Gradio 6 static asset serving
    temp_dirs = [
        tempfile.gettempdir(),
        os.path.realpath(tempfile.gettempdir()),
        os.path.abspath('.'),
    ]
    for env_k in ('TEMP', 'TMP', 'TMPDIR'):
        val = os.environ.get(env_k)
        if val and os.path.exists(val):
            temp_dirs.append(val)
            temp_dirs.append(os.path.realpath(val))
    allowed_paths = [p for p in set(temp_dirs) if os.path.exists(p)]
    print(f"[web] allowed_paths = {allowed_paths}")

    threading.Thread(target=_wait_and_open_browser, args=(url,), daemon=True).start()
    app, local_url, share_url = demo.queue(max_size=4).launch(
        server_name=os.environ.get('GRADIO_SERVER_NAME', '0.0.0.0' if ('PORT' in os.environ or 'RENDER' in os.environ) else '127.0.0.1'),
        server_port=port,
        inbrowser=False,
        share=False,
        theme=theme,
        css=css,
        allowed_paths=allowed_paths,
        prevent_thread_lock=True,
    )

    from starlette.responses import FileResponse, PlainTextResponse, JSONResponse, RedirectResponse

    async def _status_handler(request):
        global LATEST_REPAIRED_PATH
        path = LATEST_REPAIRED_PATH
        exists = bool(path and os.path.exists(path))
        import torch
        has_cuda = bool(torch.cuda.is_available())
        gpu_name = torch.cuda.get_device_name(0) if has_cuda else "CPU Mode"
        return JSONResponse({
            "has_result": exists,
            "path": path or "",
            "filename": os.path.basename(path) if (path and exists) else "",
            "preview_url": "/preview_result" if exists else "",
            "download_url": "/download_result" if exists else "",
            "cuda_available": has_cuda,
            "device_name": gpu_name,
        })

    async def _preview_handler(request):
        global LATEST_REPAIRED_PATH
        path = LATEST_REPAIRED_PATH
        if not path or not os.path.exists(path):
            return PlainTextResponse("No clean video available yet", status_code=404)
        return FileResponse(path, media_type="video/mp4")

    async def _download_handler(request):
        global LATEST_REPAIRED_PATH
        path = LATEST_REPAIRED_PATH
        if not path or not os.path.exists(path):
            return PlainTextResponse("No clean video available yet", status_code=404)
        fname = os.path.basename(path)
        if not fname.startswith("clean_"):
            fname = f"clean_{fname}"
        return FileResponse(path, media_type="video/mp4", filename=fname)

    async def _legacy_file_redirect(request):
        raw = request.path_params.get("path", "")
        return RedirectResponse(f"/gradio_api/file={raw}")

    app.router.add_route("/status_result", _status_handler)
    app.router.add_route("/preview_result", _preview_handler)
    app.router.add_route("/download_result", _download_handler)
    app.router.add_route("/file={path:path}", _legacy_file_redirect)

    demo.block_thread()


if __name__ == "__main__":
    main()
