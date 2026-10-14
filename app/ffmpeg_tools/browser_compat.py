from __future__ import annotations
import json, os, shutil, subprocess
from pathlib import Path
from typing import Optional

def _resolve_ffmpeg_executables() -> tuple[str, str]:
    try:
        from static_ffmpeg.run import get_or_fetch_platform_executables_else_raise
        return get_or_fetch_platform_executables_else_raise()
    except Exception:
        pass
    return shutil.which('ffmpeg') or 'ffmpeg', shutil.which('ffprobe') or 'ffprobe'

FFMPEG_BIN, FFPROBE_BIN = _resolve_ffmpeg_executables()

def ensure_browser_playable_video(video_path: Optional[str | Path]) -> str:
    if not video_path:
        return '' if video_path is None else str(video_path)
    path_obj = Path(video_path)
    if not path_obj.exists() or path_obj.is_dir() or path_obj.stat().st_size == 0:
        return str(video_path)
    ext = path_obj.suffix.lower()
    video_exts = {'.mp4', '.mov', '.m4v', '.webm', '.mkv', '.avi', '.flv', '.wmv', '.ts'}
    if ext not in video_exts:
        return str(video_path)
    has_moov_in_head = False
    if ext in {'.mp4', '.mov', '.m4v'}:
        try:
            with open(path_obj, 'rb') as f:
                head = f.read(4096)
                if b'moov' in head:
                    has_moov_in_head = True
        except Exception:
            pass
    codec_name = ''
    try:
        probe_cmd = [FFPROBE_BIN, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'v:0', str(path_obj)]
        probe_out = subprocess.check_output(probe_cmd)
        probe_data = json.loads(probe_out)
        streams = probe_data.get('streams', [])
        if streams:
            codec_name = streams[0].get('codec_name', '').lower()
    except Exception:
        pass
    is_browser_codec = codec_name in {'h264', 'vp8', 'vp9', 'av1'}
    if is_browser_codec and has_moov_in_head and ext in {'.mp4', '.webm'}:
        return str(video_path)
    tmp_out = path_obj.parent / f'_fast_{path_obj.stem}.mp4'
    try:
        if is_browser_codec and ext in {'.mp4', '.mov', '.m4v'}:
            remux_cmd = [FFMPEG_BIN, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(path_obj), '-c', 'copy', '-movflags', '+faststart', str(tmp_out)]
            res = subprocess.run(remux_cmd, capture_output=True)
            if res.returncode == 0 and tmp_out.exists() and tmp_out.stat().st_size > 0:
                shutil.move(str(tmp_out), str(path_obj))
                return str(path_obj)
        transcode_cmd = [FFMPEG_BIN, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(path_obj), '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '22', '-c:a', 'aac', '-b:a', '128k', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(tmp_out)]
        res = subprocess.run(transcode_cmd, capture_output=True)
        if res.returncode == 0 and tmp_out.exists() and tmp_out.stat().st_size > 0:
            target_path = path_obj.with_suffix('.mp4')
            if target_path != path_obj and path_obj.exists():
                path_obj.unlink()
            shutil.move(str(tmp_out), str(target_path))
            return str(target_path)
    except Exception as e:
        print('[BrowserCompat Warning]', e)
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except Exception:
                pass
    return str(video_path)

_routes_patched = False

def patch_gradio_routes() -> None:
    global _routes_patched
    if _routes_patched:
        return
    try:
        import gradio.routes as _gr_routes
        _orig_upload_fn = _gr_routes.upload_fn
        _orig_file_response = _gr_routes.file_response
        async def _safe_upload_fn(*args, **kwargs):
            kwargs['force_move'] = True
            output_files, files_to_copy, locations = await _orig_upload_fn(*args, **kwargs)
            if output_files:
                for f in output_files:
                    try:
                        ensure_browser_playable_video(f)
                    except Exception:
                        pass
            return output_files, files_to_copy, locations
        def _safe_file_response(developer_path, user_path):
            try:
                resolved = _gr_routes.routes_safe_join(developer_path, user_path)
                ensure_browser_playable_video(resolved)
            except Exception:
                pass
            return _orig_file_response(developer_path, user_path)
        _gr_routes.upload_fn = _safe_upload_fn
        _gr_routes.file_response = _safe_file_response
        _routes_patched = True
    except Exception as err:
        print('[BrowserCompat Patch Note]', err)

