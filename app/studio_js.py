# -*- coding: utf-8 -*-
"""Client-side JavaScript controller for Caption Remover Studio with auto-ratio & filmstrip."""

STUDIO_JS = """
(() => {
    // -------------------------------------------------------------
    // Helper: Gradio input setter with React/Svelte synthetic events
    // -------------------------------------------------------------
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

    function setGradioRadio(containerId, valueToSelect) {
        const c = document.getElementById(containerId);
        if (!c) return;
        const radios = c.querySelectorAll('input[type="radio"]');
        radios.forEach(r => {
            if (r.value === valueToSelect) {
                r.checked = true;
                r.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    function formatTimecode(sec) {
        if (!sec || isNaN(sec) || sec < 0) sec = 0;
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        const ms = Math.floor((sec % 1) * 10);
        const mm = String(m).padStart(2, '0');
        const ss = String(s).padStart(2, '0');
        return mm + ':' + ss + '.' + ms;
    }

    // -------------------------------------------------------------
    // State Store
    // -------------------------------------------------------------
    const studio = {
        video: null,
        duration: 0,
        trimEnabled: true,
        trimStart: 0,
        trimEnd: 0,
        isPlayingClip: false,
        isDraggingTimeline: null,
        timelineDragStartX: 0,
        timelineInitStart: 0,
        timelineInitEnd: 0,
        rulerBuiltFor: -1,
        // Active style & mode (Anti-blur smooth removal defaults)
        activeStyle: 'white_stroke',
        activeMode: 'quality',
        maskDilation: 2,
        lamaExtra: 1,
        temporalWindow: 12,
        selectedPreset: 'bottom',
        detectedRatio: '16:9',
        activeMonitorTab: 'original',
        lastRepVideoSrc: '',
        isProcessing: false,
    };

    window.__STUDIO = studio;
    window.__ROI_DATA = window.__ROI_DATA || { left_x: 0, bottom_y: 1080, right_x: 1920, top_y: 885 };
    window.__TRIM_DATA = window.__TRIM_DATA || { start: 0, end: 0, enabled: false };

    function findSourceVideo() {
        const sourceWrap = document.getElementById('source_video_player');
        if (sourceWrap) {
            const v = sourceWrap.querySelector('video');
            if (v) return v;
        }
        const mount = document.getElementById('video_player_mount');
        if (mount) {
            const v = mount.querySelector('video');
            if (v) return v;
        }
        return document.querySelector('video');
    }

    function getVideoSource(v) {
        if (!v) return '';
        if (v.currentSrc && typeof v.currentSrc === 'string' && v.currentSrc.trim() !== '') {
            return v.currentSrc.trim();
        }
        if (v.src && typeof v.src === 'string' && v.src.trim() !== '') {
            return v.src.trim();
        }
        const sourceTag = v.querySelector('source');
        if (sourceTag) {
            if (sourceTag.src && typeof sourceTag.src === 'string' && sourceTag.src.trim() !== '') {
                return sourceTag.src.trim();
            }
            const attr = sourceTag.getAttribute('src');
            if (attr && typeof attr === 'string' && attr.trim() !== '') {
                return attr.trim();
            }
        }
        return '';
    }

    function findRepairedVideo() {
        const repWrap = document.getElementById('repaired_video_player');
        if (repWrap) {
            const v = repWrap.querySelector('video');
            if (v) return v;
        }
        const outWrap = document.getElementById('gradio_output_wrapper');
        if (outWrap) {
            const v = outWrap.querySelector('video');
            if (v) return v;
        }
        const srcVideo = findSourceVideo();
        const srcWrap = document.getElementById('source_video_player');
        const allVideos = Array.from(document.querySelectorAll('video'));
        for (const v of allVideos) {
            if (v !== srcVideo && (!srcWrap || !srcWrap.contains(v))) {
                return v;
            }
        }
        return null;
    }

    function getDirectRepairedPath() {
        const wrap = document.getElementById('repaired_path_output');
        if (wrap) {
            const el = wrap.querySelector('textarea, input');
            if (el && el.value && el.value.trim() !== '') {
                return el.value.trim();
            }
            if (wrap.innerText && wrap.innerText.trim().length > 3) {
                return wrap.innerText.trim();
            }
        }
        const repVideo = findRepairedVideo();
        if (repVideo) {
            const src = getVideoSource(repVideo);
            if (src && src.trim() !== '') return src.trim();
        }
        return '';
    }

    function getActiveVideo() {
        if (studio.activeMonitorTab === 'result') {
            const cleanPlayer = document.getElementById('studio_clean_video_player');
            if (cleanPlayer && cleanPlayer.style.display !== 'none' && cleanPlayer.src && cleanPlayer.src !== '') {
                return cleanPlayer;
            }
            const repPlayer = findRepairedVideo();
            if (repPlayer) return repPlayer;
        }
        return studio.video || findSourceVideo();
    }

    // -------------------------------------------------------------
    // Video Mounting & Transport Controls
    // -------------------------------------------------------------
    function mountVideoIntoStudio() {
        const mount = document.getElementById('video_player_mount');
        const sourcePlayer = document.getElementById('source_video_player');
        if (!mount) return;

        if (sourcePlayer && !mount.contains(sourcePlayer)) {
            mount.appendChild(sourcePlayer);
        }
    }

    // -------------------------------------------------------------
    // Auto-detect Aspect Ratio (16:9 vs 9:16)
    // -------------------------------------------------------------
    // Auto-detect Aspect Ratio (16:9 vs 9:16 portrait)
    // -------------------------------------------------------------
    function detectAndApplyAspectRatio(v) {
        if (!v || !v.videoWidth || !v.videoHeight) return;

        const w = v.videoWidth;
        const h = v.videoHeight;
        const ratio = w / h;

        const viewport = document.getElementById('studio_monitor_viewport');
        const badge = document.getElementById('meta_aspect_badge');
        const resFps = document.getElementById('meta_resolution_fps');

        v.style.objectFit = 'contain';

        let ratioText = '16:9';
        const isPortrait = (ratio < 0.95);

        if (isPortrait) {
            // Portrait video (e.g. 1080x1920 -> 9:16)
            ratioText = ratio <= 0.65 ? '9:16' : (ratio <= 0.85 ? '4:5' : '3:4');
            if (viewport) {
                viewport.classList.remove('viewport-landscape');
                viewport.classList.add('viewport-portrait');
            }
        } else if (ratio >= 1.2) {
            // Landscape video (e.g. 1920x1080 -> 16:9)
            ratioText = ratio >= 1.9 ? '21:9' : '16:9';
            if (viewport) {
                viewport.classList.remove('viewport-portrait');
                viewport.classList.add('viewport-landscape');
            }
        } else {
            // Square / Standard (1:1 or 4:3)
            ratioText = '1:1';
            if (viewport) {
                viewport.classList.remove('viewport-portrait');
                viewport.classList.add('viewport-landscape');
            }
        }

        studio.detectedRatio = ratioText;

        if (badge) badge.innerText = ratioText;
        if (resFps) resFps.innerText = w + ' × ' + h + ' • 24 FPS';

        // Auto-adapt ROI preset when video dimensions change
        if (studio.lastW !== w || studio.lastH !== h) {
            studio.lastW = w;
            studio.lastH = h;
            setTimeout(() => {
                if (typeof window.__snapRoiPreset === 'function') {
                    window.__snapRoiPreset('bottom');
                }
                updateOverlayPosition();
            }, 60);
        }
    }

    function updateTransportUI() {
        const v = getActiveVideo();
        const timecodeEl = document.getElementById('transport_timecode');
        const playBtn = document.getElementById('btn_transport_play');
        const muteBtn = document.getElementById('btn_transport_mute');

        if (!v || isNaN(v.duration) || v.duration <= 0) {
            if (timecodeEl) timecodeEl.innerText = '00:00.0 / 00:00.0';
            return;
        }

        const cur = v.currentTime || 0;
        const dur = v.duration || 0;
        if (timecodeEl) {
            timecodeEl.innerText = formatTimecode(cur) + ' / ' + formatTimecode(dur);
        }

        if (playBtn) {
            if (v.paused) {
                playBtn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>';
            } else {
                playBtn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
            }
        }

        if (muteBtn) {
            if (v.muted) {
                muteBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>';
            } else {
                muteBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>';
            }
        }
    }

    function attachTransportListeners() {
        const playBtn = document.getElementById('btn_transport_play');
        const muteBtn = document.getElementById('btn_transport_mute');
        const fitBtn = document.getElementById('btn_fit_canvas');

        if (playBtn && !playBtn.__hasInit) {
            playBtn.__hasInit = true;
            playBtn.addEventListener('click', () => {
                const v = getActiveVideo();
                if (!v) return;
                if (v.paused) v.play(); else v.pause();
                updateTransportUI();
            });
        }

        if (muteBtn && !muteBtn.__hasInit) {
            muteBtn.__hasInit = true;
            muteBtn.addEventListener('click', () => {
                const v = getActiveVideo();
                if (!v) return;
                v.muted = !v.muted;
                updateTransportUI();
            });
        }

        if (fitBtn && !fitBtn.__hasInit) {
            fitBtn.__hasInit = true;
            fitBtn.addEventListener('click', () => {
                const v = studio.video || findSourceVideo();
                if (!v) return;
                v.style.objectFit = 'contain';
                detectAndApplyAspectRatio(v);
                setTimeout(() => {
                    updateOverlayPosition();
                }, 50);
            });
        }
    }

    // -------------------------------------------------------------
    // Dynamic Video Filmstrip Thumbnails Generator
    // -------------------------------------------------------------
    function generateFilmstripThumbnails(video, duration) {
        const track = document.getElementById('capcut_track_thumbnails');
        if (!track || !video || duration <= 0) return;

        const src = video.src || video.currentSrc || '';
        if (!src) return;

        const key = src + '_' + Math.round(duration);
        if (track.__filmstripKey === key) return;
        track.__filmstripKey = key;

        let canvas = track.querySelector('canvas.capcut-filmstrip-canvas');
        if (!canvas) {
            track.innerHTML = '';
            canvas = document.createElement('canvas');
            canvas.className = 'capcut-filmstrip-canvas';
            track.appendChild(canvas);
        }

        const numThumbs = 12;
        const thumbW = 120;
        const thumbH = 68;
        canvas.width = numThumbs * thumbW;
        canvas.height = thumbH;
        const ctx = canvas.getContext('2d');

        // Initial sleek gradient
        const grad = ctx.createLinearGradient(0, 0, canvas.width, 0);
        grad.addColorStop(0, '#1E1B4B');
        grad.addColorStop(0.5, '#0F172A');
        grad.addColorStop(1, '#1E1B4B');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        for (let i = 0; i < numThumbs; i++) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
            ctx.lineWidth = 1;
            ctx.strokeRect(i * thumbW, 0, thumbW, thumbH);
        }

        // Headless seeker video element
        const seeker = document.createElement('video');
        seeker.crossOrigin = 'anonymous';
        seeker.muted = true;
        seeker.playsInline = true;
        seeker.src = src;

        let frameIdx = 0;

        function renderNextFrame() {
            if (frameIdx >= numThumbs) {
                seeker.removeAttribute('src');
                seeker.load();
                return;
            }
            const timePoint = Math.min(duration - 0.05, Math.max(0.05, (frameIdx / (numThumbs - 1)) * duration));
            seeker.currentTime = timePoint;
        }

        seeker.addEventListener('seeked', () => {
            try {
                ctx.drawImage(seeker, frameIdx * thumbW, 0, thumbW, thumbH);
                ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)';
                ctx.strokeRect(frameIdx * thumbW, 0, thumbW, thumbH);
            } catch (e) {}
            frameIdx++;
            renderNextFrame();
        });

        seeker.addEventListener('loadeddata', () => {
            renderNextFrame();
        });
    }

    // -------------------------------------------------------------
    // CapCut Timeline Trimmer Controller
    // -------------------------------------------------------------
    function buildRuler(duration) {
        const ruler = document.getElementById('capcut_ruler');
        if (!ruler || duration <= 0) return;
        if (Math.abs(studio.rulerBuiltFor - duration) < 0.2) return;
        studio.rulerBuiltFor = duration;
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

    function updateTimelineUI() {
        if (!studio.video || studio.duration <= 0) return;
        const duration = studio.duration;
        const start = Math.max(0, Math.min(duration, studio.trimStart));
        const end = Math.max(start + 0.1, Math.min(duration, studio.trimEnd));
        studio.trimStart = Math.round(start * 10) / 10;
        studio.trimEnd = Math.round(end * 10) / 10;
        const clipLen = Math.max(0.1, Math.round((studio.trimEnd - studio.trimStart) * 10) / 10);

        const leftPct = (studio.trimStart / duration) * 100;
        const rightPct = (studio.trimEnd / duration) * 100;
        const widthPct = Math.max(0.5, rightPct - leftPct);

        const dimLeft = document.getElementById('capcut_dim_left');
        const dimRight = document.getElementById('capcut_dim_right');
        const clipEl = document.getElementById('capcut_clip');
        const clipLenEl = document.getElementById('capcut_clip_len');
        const toggle = document.getElementById('capcut_trim_toggle');
        const seqInfo = document.getElementById('timeline_sequence_info');
        const ctaPill = document.getElementById('cta_clip_duration_pill');
        const estText = document.getElementById('estimated_time_text');

        if (dimLeft) dimLeft.style.width = leftPct + '%';
        if (dimRight) dimRight.style.width = Math.max(0, 100 - rightPct) + '%';
        if (clipEl) {
            clipEl.style.left = leftPct + '%';
            clipEl.style.width = widthPct + '%';
        }
        if (clipLenEl) clipLenEl.innerText = clipLen.toFixed(1) + 's';

        const isTrimOn = toggle ? toggle.checked : studio.trimEnabled;
        studio.trimEnabled = isTrimOn;

        if (seqInfo) {
            seqInfo.innerText = 'Source sequence • ' + formatTimecode(duration);
        }

        if (ctaPill) {
            const displaySec = isTrimOn ? clipLen : duration;
            ctaPill.innerText = displaySec.toFixed(1) + 's';
        }

        if (estText) {
            const effSec = isTrimOn ? clipLen : duration;
            const factor = (studio.activeMode === 'fast') ? 0.35 : 2.5;
            const estSeconds = Math.max(4, Math.round(effSec * factor));
            estText.innerText = '~ ' + estSeconds + ' seconds';
        }

        window.__TRIM_DATA = {
            start: studio.trimStart,
            end: studio.trimEnd,
            enabled: isTrimOn
        };

        setGradioInput('input_clip_start', studio.trimStart);
        setGradioInput('input_clip_end', studio.trimEnd);
        const chk = document.querySelector('#chk_clip_trim input[type="checkbox"]');
        if (chk && chk.checked !== isTrimOn) {
            chk.click();
        }
    }

    function updatePlayhead() {
        if (!studio.video || studio.duration <= 0) return;
        const curTime = studio.video.currentTime || 0;
        const pct = Math.max(0, Math.min(100, (curTime / studio.duration) * 100));
        const playhead = document.getElementById('capcut_playhead');
        const badge = document.getElementById('capcut_playhead_badge');
        if (playhead) playhead.style.left = pct + '%';
        if (badge) badge.innerText = formatTimecode(curTime);

        if (studio.isPlayingClip && curTime >= studio.trimEnd) {
            studio.video.pause();
            studio.isPlayingClip = false;
            const btn = document.getElementById('capcut_btn_preview');
            if (btn) btn.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg> Play selected clip';
        }
    }

    function attachTimelineListeners() {
        const trackViewport = document.getElementById('capcut_track_wrapper');
        if (!trackViewport || trackViewport.__hasTimelineInit) return;
        trackViewport.__hasTimelineInit = true;

        const handleLeft = document.getElementById('capcut_handle_left');
        const handleRight = document.getElementById('capcut_handle_right');
        const clipBody = document.getElementById('capcut_clip_body');
        const playhead = document.getElementById('capcut_playhead');
        const toggle = document.getElementById('capcut_trim_toggle');

        const btnSetIn = document.getElementById('capcut_btn_set_in');
        const btnSetOut = document.getElementById('capcut_btn_set_out');
        const btnPreview = document.getElementById('capcut_btn_preview');

        if (toggle) {
            toggle.addEventListener('change', () => {
                studio.trimEnabled = toggle.checked;
                updateTimelineUI();
            });
        }

        if (handleLeft) {
            handleLeft.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                studio.isDraggingTimeline = 'left';
            });
        }

        if (handleRight) {
            handleRight.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                studio.isDraggingTimeline = 'right';
            });
        }

        if (clipBody) {
            clipBody.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                studio.isDraggingTimeline = 'body';
                studio.timelineDragStartX = e.clientX;
                studio.timelineInitStart = studio.trimStart;
                studio.timelineInitEnd = studio.trimEnd;
            });
        }

        if (playhead) {
            playhead.addEventListener('pointerdown', (e) => {
                e.stopPropagation();
                studio.isDraggingTimeline = 'playhead';
            });
        }

        trackViewport.addEventListener('pointerdown', (e) => {
            if (e.target.closest('.capcut-handle') || e.target.closest('.capcut-clip-body') || e.target.closest('#capcut_playhead')) {
                return;
            }
            if (!studio.video || studio.duration <= 0) return;
            const rect = trackViewport.getBoundingClientRect();
            const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
            const targetTime = (relX / rect.width) * studio.duration;
            studio.video.currentTime = targetTime;
            updatePlayhead();
            updateTransportUI();
        });

        window.addEventListener('pointermove', (e) => {
            if (!studio.isDraggingTimeline || !trackViewport || studio.duration <= 0) return;
            const rect = trackViewport.getBoundingClientRect();
            const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
            const mouseSec = (relX / rect.width) * studio.duration;

            if (studio.isDraggingTimeline === 'left') {
                studio.trimStart = Math.max(0, Math.min(studio.trimEnd - 0.2, mouseSec));
                if (studio.video) studio.video.currentTime = studio.trimStart;
                updateTimelineUI();
                updatePlayhead();
                updateTransportUI();
            } else if (studio.isDraggingTimeline === 'right') {
                studio.trimEnd = Math.max(studio.trimStart + 0.2, Math.min(studio.duration, mouseSec));
                if (studio.video) studio.video.currentTime = studio.trimEnd;
                updateTimelineUI();
                updatePlayhead();
                updateTransportUI();
            } else if (studio.isDraggingTimeline === 'body') {
                const dxSec = ((e.clientX - studio.timelineDragStartX) / rect.width) * studio.duration;
                const clipLen = studio.timelineInitEnd - studio.timelineInitStart;
                let newStart = studio.timelineInitStart + dxSec;
                if (newStart < 0) newStart = 0;
                if (newStart + clipLen > studio.duration) newStart = studio.duration - clipLen;
                studio.trimStart = newStart;
                studio.trimEnd = newStart + clipLen;
                updateTimelineUI();
            } else if (studio.isDraggingTimeline === 'playhead') {
                if (studio.video) studio.video.currentTime = mouseSec;
                updatePlayhead();
                updateTransportUI();
            }
        });

        window.addEventListener('pointerup', () => {
            if (studio.isDraggingTimeline) {
                studio.isDraggingTimeline = null;
                updateTimelineUI();
            }
        });

        if (btnSetIn) {
            btnSetIn.addEventListener('click', () => {
                if (!studio.video) return;
                const cur = Math.round((studio.video.currentTime || 0) * 10) / 10;
                studio.trimStart = cur;
                if (studio.trimStart >= studio.trimEnd) {
                    studio.trimEnd = Math.min(studio.duration, studio.trimStart + 5.0);
                }
                if (toggle) toggle.checked = true;
                studio.trimEnabled = true;
                updateTimelineUI();
            });
        }

        if (btnSetOut) {
            btnSetOut.addEventListener('click', () => {
                if (!studio.video) return;
                const cur = Math.round((studio.video.currentTime || 0) * 10) / 10;
                studio.trimEnd = cur;
                if (studio.trimEnd <= studio.trimStart) {
                    studio.trimStart = Math.max(0, studio.trimEnd - 5.0);
                }
                if (toggle) toggle.checked = true;
                studio.trimEnabled = true;
                updateTimelineUI();
            });
        }

        if (btnPreview) {
            btnPreview.addEventListener('click', () => {
                if (!studio.video) return;
                if (studio.isPlayingClip) {
                    studio.video.pause();
                    studio.isPlayingClip = false;
                    btnPreview.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg> Play selected clip';
                } else {
                    studio.video.currentTime = studio.trimStart;
                    studio.video.play();
                    studio.isPlayingClip = true;
                    btnPreview.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg> Stop clip';
                }
                updateTransportUI();
            });
        }

        document.querySelectorAll('.extend-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                if (!studio.video || studio.duration <= 0) return;
                const dur = parseFloat(chip.dataset.dur) || 3;
                const cur = Math.round((studio.video.currentTime || 0) * 10) / 10;
                studio.trimStart = cur;
                studio.trimEnd = Math.min(studio.duration, cur + dur);
                if (toggle) toggle.checked = true;
                studio.trimEnabled = true;
                updateTimelineUI();
            });
        });
    }

    // -------------------------------------------------------------
    // Interactive Draggable ROI Canvas Controller (Monitor Overlay)
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

    function getRenderedMediaRect(el) {
        if (!el) return null;
        const rect = el.getBoundingClientRect();
        const natW = el.videoWidth || el.naturalWidth || 1920;
        const natH = el.videoHeight || el.naturalHeight || 1080;
        const elemW = rect.width;
        const elemH = rect.height;
        if (elemW <= 0 || elemH <= 0) return null;

        const elRatio = natW / natH;
        const elemRatio = elemW / elemH;
        let renderW, renderH, offsetX, offsetY;

        if (elRatio > elemRatio) {
            renderW = elemW;
            renderH = elemW / elRatio;
            offsetX = 0;
            offsetY = (elemH - renderH) / 2;
        } else {
            renderH = elemH;
            renderW = elemH * elRatio;
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
        const video = findSourceVideo();
        if (!video) return;

        if (overlay && document.contains(overlay)) return;

        const container = video.parentElement || document.getElementById('studio_monitor_viewport');
        if (!container) return;
        container.style.position = 'relative';

        overlay = document.createElement('div');
        overlay.id = 'roi_interactive_overlay';
        overlay.style.position = 'absolute';
        overlay.style.cursor = 'crosshair';
        overlay.style.zIndex = '30';
        overlay.style.pointerEvents = 'auto';
        overlay.style.userSelect = 'none';

        overlay.addEventListener('dblclick', (e) => {
            if (e.target.closest('#roi_interactive_box')) return;
            if (video.paused) video.play(); else video.pause();
            updateTransportUI();
        });

        box = document.createElement('div');
        box.id = 'roi_interactive_box';
        box.style.position = 'absolute';
        box.style.border = '2px solid #8B5CF6';
        box.style.background = 'rgba(139, 92, 246, 0.22)';
        box.style.boxShadow = '0 0 16px rgba(139, 92, 246, 0.6)';
        box.style.cursor = 'move';
        box.style.display = 'none';

        badge = document.createElement('div');
        badge.id = 'roi_box_badge';
        badge.innerText = 'ROI: 640 × 180 px';
        box.appendChild(badge);

        const handlePositions = ['nw', 'ne', 'se', 'sw'];
        handles = {};
        handlePositions.forEach(pos => {
            const h = document.createElement('div');
            h.dataset.handle = pos;
            h.style.position = 'absolute';
            h.style.width = '10px';
            h.style.height = '10px';
            h.style.background = '#FFFFFF';
            h.style.border = '2px solid #8B5CF6';
            h.style.borderRadius = '50%';
            h.style.boxShadow = '0 0 6px rgba(0,0,0,0.8)';
            h.style.zIndex = '35';

            if (pos === 'nw') { h.style.left = '-5px'; h.style.top = '-5px'; h.style.cursor = 'nwse-resize'; }
            if (pos === 'ne') { h.style.right = '-5px'; h.style.top = '-5px'; h.style.cursor = 'nesw-resize'; }
            if (pos === 'se') { h.style.right = '-5px'; h.style.bottom = '-5px'; h.style.cursor = 'nwse-resize'; }
            if (pos === 'sw') { h.style.left = '-5px'; h.style.bottom = '-5px'; h.style.cursor = 'nesw-resize'; }

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
        const video = findSourceVideo();
        const pill = document.getElementById('roi_floating_pill');
        if (!video) {
            overlay.style.display = 'none';
            if (pill) pill.style.display = 'none';
            return;
        }

        const r = getRenderedMediaRect(video);
        if (!r || r.width <= 0) {
            overlay.style.display = 'none';
            if (pill) pill.style.display = 'none';
            return;
        }
        overlay.style.display = 'block';

        const offsetParent = overlay.offsetParent || video.parentElement || document.getElementById('studio_monitor_viewport');
        const parentRect = offsetParent ? offsetParent.getBoundingClientRect() : { left: 0, top: 0 };
        overlay.style.left = Math.round(r.left - parentRect.left) + 'px';
        overlay.style.top = Math.round(r.top - parentRect.top) + 'px';
        overlay.style.width = Math.round(r.width) + 'px';
        overlay.style.height = Math.round(r.height) + 'px';

        // Keep floating pill anchored at the bottom of the rendered video
        if (pill) {
            pill.style.display = 'flex';
            const viewportRect = document.getElementById('studio_monitor_viewport').getBoundingClientRect();
            const relBottom = viewportRect.bottom - r.top - r.height;
            pill.style.bottom = Math.max(16, relBottom + 16) + 'px';
        }

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
        const video = findSourceVideo();
        if (!video) return;
        const r = getRenderedMediaRect(video);
        if (!r || !r.naturalWidth || r.naturalWidth <= 0) return;

        const scaleX = r.width / r.naturalWidth;
        const scaleY = r.height / r.naturalHeight;

        box.style.display = 'block';
        box.style.left = (natX * scaleX) + 'px';
        box.style.top = (natY * scaleY) + 'px';
        box.style.width = (natW * scaleX) + 'px';
        box.style.height = (natH * scaleY) + 'px';

        if (badge) {
            badge.innerText = 'ROI: ' + natW + ' × ' + natH + ' px';
        }
    }

    function pushCoordinatesToGradio(lx, by, rx, ty) {
        window.__ROI_DATA = { left_x: lx, bottom_y: by, right_x: rx, top_y: ty };
        setGradioInput('slider_left_x', lx);
        setGradioInput('slider_bottom_y', by);
        setGradioInput('slider_right_x', rx);
        setGradioInput('slider_top_y', ty);

        const inLx = document.getElementById('modal_input_lx');
        const inBy = document.getElementById('modal_input_by');
        const inRx = document.getElementById('modal_input_rx');
        const inTy = document.getElementById('modal_input_ty');
        if (inLx) inLx.value = lx;
        if (inBy) inBy.value = by;
        if (inRx) inRx.value = rx;
        if (inTy) inTy.value = ty;
    }

    function syncBoxFromCoordinates(lx, by, rx, ty) {
        const video = findSourceVideo();
        if (!video) return;
        const r = getRenderedMediaRect(video);
        if (!r || !r.naturalWidth || r.naturalWidth <= 0) return;

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

    // Smart ratio-adaptive presets for 16:9 and 9:16
    window.__snapRoiPreset = function(type) {
        studio.selectedPreset = type;
        const video = findSourceVideo();
        const natW = video ? (video.videoWidth || 1920) : 1920;
        const natH = video ? (video.videoHeight || 1080) : 1080;
        const isLandscape = (natW / natH) >= 1.2;

        let lx = 0, rx = natW, ty = 0, by = natH;
        let label = 'Bottom subtitle';

        if (type === 'bottom') {
            if (isLandscape) {
                // 16:9 Landscape: center bottom subtitle area
                lx = Math.round(natW * 0.10);
                rx = Math.round(natW * 0.90);
                ty = Math.round(natH * 0.80);
                by = Math.round(natH * 0.96);
            } else {
                // 9:16 Portrait: vertical video subtitle band
                lx = Math.round(natW * 0.05);
                rx = Math.round(natW * 0.95);
                ty = Math.round(natH * 0.78);
                by = Math.round(natH * 0.94);
            }
            label = 'Bottom subtitle';
        } else if (type === 'top') {
            if (isLandscape) {
                lx = Math.round(natW * 0.10);
                rx = Math.round(natW * 0.90);
                ty = Math.round(natH * 0.04);
                by = Math.round(natH * 0.20);
            } else {
                lx = Math.round(natW * 0.05);
                rx = Math.round(natW * 0.95);
                ty = Math.round(natH * 0.04);
                by = Math.round(natH * 0.18);
            }
            label = 'Top banner';
        } else if (type === 'tiktok_br') {
            lx = Math.round(natW * 0.68); rx = Math.round(natW * 0.98);
            ty = Math.round(natH * 0.86); by = Math.round(natH * 0.98);
            label = 'Watermark (Bottom-Right)';
        } else if (type === 'tiktok_tl') {
            lx = Math.round(natW * 0.02); rx = Math.round(natW * 0.32);
            ty = Math.round(natH * 0.03); by = Math.round(natH * 0.15);
            label = 'Watermark (Top-Left)';
        } else if (type === 'center') {
            lx = Math.round(natW * 0.12); rx = Math.round(natW * 0.88);
            ty = Math.round(natH * 0.42); by = Math.round(natH * 0.58);
            label = 'Center banner';
        } else if (type === 'full') {
            lx = 0; rx = natW; ty = 0; by = natH;
            label = 'Full frame';
        }

        const pillLabel = document.getElementById('pill_current_preset_label');
        if (pillLabel) pillLabel.innerText = label;

        pushCoordinatesToGradio(lx, by, rx, ty);
        syncBoxFromCoordinates(lx, by, rx, ty);
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

            const video = findSourceVideo();
            if (video) {
                const r = getRenderedMediaRect(video);
                if (r && r.naturalWidth > 0) {
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

            const video = findSourceVideo();
            if (!video) return;
            const r = getRenderedMediaRect(video);
            if (!r || !r.naturalWidth) return;

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

    // -------------------------------------------------------------
    // Floating Video Pill Bar Listeners
    // -------------------------------------------------------------
    function attachPillListeners() {
        const btnFineTune = document.getElementById('btn_pill_finetune');
        const btnPresetTrig = document.getElementById('btn_pill_preset_trigger');
        const menu = document.getElementById('preset_dropdown_menu');
        const btnSnap = document.getElementById('btn_pill_snap');

        if (btnFineTune && !btnFineTune.__hasInit) {
            btnFineTune.__hasInit = true;
            btnFineTune.addEventListener('click', () => {
                openCoordsModal();
            });
        }

        if (btnPresetTrig && !btnPresetTrig.__hasInit) {
            btnPresetTrig.__hasInit = true;
            btnPresetTrig.addEventListener('click', (e) => {
                e.stopPropagation();
                if (menu) menu.classList.toggle('show');
            });

            document.addEventListener('click', () => {
                if (menu) menu.classList.remove('show');
            });
        }

        if (menu && !menu.__hasInit) {
            menu.__hasInit = true;
            menu.querySelectorAll('.preset-menu-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const p = item.dataset.preset;
                    menu.querySelectorAll('.preset-menu-item').forEach(i => i.classList.remove('active'));
                    item.classList.add('active');
                    window.__snapRoiPreset(p);
                    menu.classList.remove('show');
                });
            });
        }

        if (btnSnap && !btnSnap.__hasInit) {
            btnSnap.__hasInit = true;
            btnSnap.addEventListener('click', () => {
                window.__snapRoiPreset(studio.selectedPreset || 'bottom');
            });
        }
    }

    // -------------------------------------------------------------
    // Inspector Controls
    // -------------------------------------------------------------
    function attachInspectorListeners() {
        // Section 01: Style Cards
        const styleCards = document.querySelectorAll('.style-card');
        styleCards.forEach(card => {
            if (card.__hasInit) return;
            card.__hasInit = true;
            card.addEventListener('click', () => {
                styleCards.forEach(c => {
                    c.classList.remove('active');
                    const chk = c.querySelector('.style-card-check');
                    if (chk) chk.style.display = 'none';
                });
                card.classList.add('active');
                const chk = card.querySelector('.style-card-check');
                if (chk) chk.style.display = 'block';

                const styleVal = card.dataset.style;
                studio.activeStyle = styleVal;
                setGradioRadio('radio_subtitle_color', styleVal);
            });
        });

        // Section 02: Inpainting Cards
        const inpaintCards = document.querySelectorAll('.inpaint-card');
        inpaintCards.forEach(card => {
            if (card.__hasInit) return;
            card.__hasInit = true;
            card.addEventListener('click', () => {
                inpaintCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                const modeVal = card.dataset.mode;
                studio.activeMode = modeVal;
                setGradioRadio('radio_process_mode', modeVal);
                updateTimelineUI();
            });
        });

        // Section 03: Precision Tuning (3 Sliders)
        const dilSlider = document.getElementById('input_mask_dilation');
        const dilVal = document.getElementById('val_mask_dilation');
        if (dilSlider && !dilSlider.__hasInit) {
            dilSlider.__hasInit = true;
            dilSlider.addEventListener('input', () => {
                studio.maskDilation = dilSlider.value;
                if (dilVal) dilVal.innerText = dilSlider.value + ' px';
                setGradioInput('slider_dilate', dilSlider.value);
            });
        }

        const lamaSlider = document.getElementById('input_lama_extra');
        const lamaVal = document.getElementById('val_lama_extra');
        if (lamaSlider && !lamaSlider.__hasInit) {
            lamaSlider.__hasInit = true;
            lamaSlider.addEventListener('input', () => {
                studio.lamaExtra = lamaSlider.value;
                if (lamaVal) lamaVal.innerText = lamaSlider.value + ' px';
                setGradioInput('slider_lama_extra', lamaSlider.value);
            });
        }

        const tempSlider = document.getElementById('input_temporal_window');
        const tempVal = document.getElementById('val_temporal_window');
        if (tempSlider && !tempSlider.__hasInit) {
            tempSlider.__hasInit = true;
            tempSlider.addEventListener('input', () => {
                studio.temporalWindow = tempSlider.value;
                if (tempVal) tempVal.innerText = tempSlider.value;
                setGradioInput('slider_temporal', tempSlider.value);
            });
        }

        // Advanced Coords Row trigger
        const advRow = document.getElementById('btn_open_coords_modal');
        if (advRow && !advRow.__hasInit) {
            advRow.__hasInit = true;
            advRow.addEventListener('click', openCoordsModal);
        }

        // Inspector Reset Button (Restores anti-blur smooth removal defaults)
        const resetBtn = document.getElementById('btn_inspector_reset');
        if (resetBtn && !resetBtn.__hasInit) {
            resetBtn.__hasInit = true;
            resetBtn.addEventListener('click', () => {
                const card1 = document.getElementById('card_style_white_stroke');
                if (card1) card1.click();

                const cardQ = document.getElementById('card_mode_quality');
                if (cardQ) cardQ.click();

                if (dilSlider) { dilSlider.value = 2; dilSlider.dispatchEvent(new Event('input')); }
                if (lamaSlider) { lamaSlider.value = 1; lamaSlider.dispatchEvent(new Event('input')); }
                if (tempSlider) { tempSlider.value = 12; tempSlider.dispatchEvent(new Event('input')); }

                window.__snapRoiPreset('bottom');
            });
        }

        // -------------------------------------------------------------
        // Processing Overlay & Progress Bar Controller
        // -------------------------------------------------------------
        let procProgressTimer = null;
        let procStartTime = 0;
        let procEstTotalSec = 30;

        function formatMinuteSecond(sec) {
            const totalSec = Math.max(0, Math.floor(sec));
            const mins = Math.floor(totalSec / 60);
            const remSec = totalSec % 60;
            const padSec = remSec < 10 ? '0' + remSec : remSec;
            if (mins > 0) {
                return `${mins}m ${padSec}s`;
            }
            return `0m ${padSec}s`;
        }

        function pollGradioProgress() {
            try {
                const els = document.querySelectorAll('.progress-text, .meta-text, #gradio_backend_bridge [class*="progress"]');
                for (const el of els) {
                    const txt = el.innerText || '';
                    const match = txt.match(/(\d+)%/);
                    if (match) {
                        return parseInt(match[1]);
                    }
                }
            } catch (e) {}
            return null;
        }

        function startProcessingProgress() {
            if (procProgressTimer) clearInterval(procProgressTimer);
            studio.isProcessing = true;
            window.__STUDIO = window.__STUDIO || {};
            window.__STUDIO.isProcessing = true;

            const repVideo = findRepairedVideo();
            studio.lastRepVideoSrc = getVideoSource(repVideo);
            studio.processingStartTime = Date.now();

            const pOut = document.querySelector('#repaired_path_output textarea, #repaired_path_output input');
            if (pOut) pOut.value = '';

            const overlay = document.getElementById('studio_processing_overlay');
            const fillBar = document.getElementById('proc_progress_fill');
            const pctText = document.getElementById('proc_percent_text');
            const elText = document.getElementById('proc_elapsed_text');
            const etaText = document.getElementById('proc_eta_text');
            const stagePill = document.getElementById('proc_stage_pill');
            const ctaBtn = document.getElementById('btn_studio_remove_captions');
            const ctaFill = document.getElementById('cta_btn_progress_fill');
            const ctaLabel = document.getElementById('cta_btn_label');
            const durPill = document.getElementById('cta_clip_duration_pill');

            const step1 = document.getElementById('pstep_1');
            const step2 = document.getElementById('pstep_2');
            const step3 = document.getElementById('pstep_3');
            const step4 = document.getElementById('pstep_4');

            // Reset all step items
            [step1, step2, step3, step4].forEach(s => {
                if (s) s.classList.remove('active', 'completed');
            });
            if (step1) step1.classList.add('active');

            // Estimate total duration
            let clipLen = 5.0;
            if (window.__TRIM_DATA && window.__TRIM_DATA.enabled && window.__TRIM_DATA.end > window.__TRIM_DATA.start) {
                clipLen = Math.max(1.0, window.__TRIM_DATA.end - window.__TRIM_DATA.start);
            } else if (studio.duration && studio.duration > 0) {
                clipLen = studio.duration;
            }

            const isFast = (studio.activeMode === 'fast');
            procEstTotalSec = isFast ? Math.max(8, Math.round(clipLen * 1.5)) : Math.max(30, Math.round(clipLen * 11.5));
            procStartTime = Date.now();

            if (overlay) {
                overlay.style.display = 'flex';
                overlay.style.opacity = '1';
            }
            if (fillBar) fillBar.style.width = '4%';
            if (pctText) pctText.innerText = '4%';
            if (elText) elText.innerText = '0m 00s';
            if (etaText) etaText.innerText = `~${formatMinuteSecond(procEstTotalSec)} remaining`;
            if (stagePill) stagePill.innerText = 'Step 1/4: Subtitle detection & mask generation...';

            if (ctaFill) ctaFill.style.width = '4%';
            if (ctaLabel) ctaLabel.innerText = 'Initializing AI...';

            procProgressTimer = setInterval(() => {
                if (!studio.isProcessing) {
                    clearInterval(procProgressTimer);
                    return;
                }

                const elapsedMs = Date.now() - procStartTime;
                const elapsedSec = elapsedMs / 1000;
                const elapsedStr = formatMinuteSecond(elapsedSec);

                // Safety polling: automatically complete if output path has arrived
                if (elapsedSec > 2) {
                    const directP = getDirectRepairedPath();
                    if (directP && directP.length > 3 && directP !== studio.lastFinishedPath) {
                        console.log('[studio] Polling loop detected finished output:', directP);
                        studio.lastFinishedPath = directP;
                        completeProcessingProgress(directP);
                        return;
                    }
                }

                // Asymptotic curve approaching 95%
                const progressRatio = elapsedSec / Math.max(8, procEstTotalSec);
                let currentPct = 4 + 91 * (1 - Math.exp(-progressRatio * 1.85));

                // Optional blend with Gradio's internal progress if available
                const grPct = pollGradioProgress();
                if (grPct && grPct > currentPct && grPct < 98) {
                    currentPct = grPct;
                }

                if (currentPct > 95) currentPct = 95;
                const pctInt = Math.min(95, Math.max(4, Math.round(currentPct)));

                // Calculate remaining time
                const estRemaining = Math.max(2, procEstTotalSec - elapsedSec);
                let remainingStr = '';
                if (pctInt >= 92) {
                    remainingStr = '~Finalizing video encode...';
                } else {
                    remainingStr = `~${formatMinuteSecond(estRemaining)} remaining`;
                }

                // Check pipeline stages
                if (pctInt < 18) {
                    if (stagePill) stagePill.innerText = 'Step 1/4: Subtitle detection & mask generation...';
                    if (step1) step1.classList.add('active');
                } else if (pctInt < 30) {
                    if (stagePill) stagePill.innerText = 'Step 2/4: Temporal anti-flicker smoothing...';
                    if (step1) { step1.classList.remove('active'); step1.classList.add('completed'); }
                    if (step2) step2.classList.add('active');
                } else if (pctInt < 88) {
                    if (stagePill) stagePill.innerText = isFast ? 'Step 3/4: Fast OpenCV inpainting...' : 'Step 3/4: Neural LaMa inpainting...';
                    if (step1) { step1.classList.remove('active'); step1.classList.add('completed'); }
                    if (step2) { step2.classList.remove('active'); step2.classList.add('completed'); }
                    if (step3) step3.classList.add('active');
                } else {
                    if (stagePill) stagePill.innerText = 'Step 4/4: Frame encode & audio muxing...';
                    if (step3) { step3.classList.remove('active'); step3.classList.add('completed'); }
                    if (step4) step4.classList.add('active');
                }

                // Update overlay UI
                if (fillBar) fillBar.style.width = pctInt + '%';
                if (pctText) pctText.innerText = pctInt + '%';
                if (elText) elText.innerText = elapsedStr;
                if (etaText) etaText.innerText = remainingStr;

                // Update CTA button UI
                if (ctaFill) ctaFill.style.width = pctInt + '%';
                if (ctaLabel) ctaLabel.innerText = `Inpainting ${pctInt}% (${elapsedStr})`;
                if (durPill) durPill.innerText = remainingStr.replace(' remaining', '');

            }, 200);
        }

        function completeProcessingProgress(cleanPath) {
            studio.isProcessing = false;
            window.__STUDIO = window.__STUDIO || {};
            window.__STUDIO.isProcessing = false;
            if (procProgressTimer) {
                clearInterval(procProgressTimer);
                procProgressTimer = null;
            }

            let finalPath = '';
            if (typeof cleanPath === 'string' && cleanPath.trim() !== '') {
                finalPath = cleanPath.trim();
            } else if (cleanPath && typeof cleanPath === 'object') {
                if (cleanPath.video && typeof cleanPath.video.path === 'string') {
                    finalPath = cleanPath.video.path.trim();
                } else if (typeof cleanPath.path === 'string') {
                    finalPath = cleanPath.path.trim();
                } else if (typeof cleanPath.value === 'string') {
                    finalPath = cleanPath.value.trim();
                } else if (typeof cleanPath.data === 'string') {
                    finalPath = cleanPath.data.trim();
                } else if (Array.isArray(cleanPath) && cleanPath.length > 0) {
                    finalPath = typeof cleanPath[0] === 'string' ? cleanPath[0].trim() : (cleanPath[0]?.path || '');
                }
            }
            if (!finalPath) {
                finalPath = getDirectRepairedPath();
            }

            if (finalPath) {
                studio.lastFinishedPath = finalPath;
                let cleanUrl = '';
                if (finalPath.startsWith('http://') || finalPath.startsWith('https://') || finalPath.startsWith('/file=') || finalPath.startsWith('blob:')) {
                    cleanUrl = finalPath;
                } else {
                    const normPath = finalPath.split(String.fromCharCode(92)).join('/');
                    cleanUrl = '/file=' + encodeURI(normPath);
                }
                const cleanPlayer = document.getElementById('studio_clean_video_player');
                if (cleanPlayer) {
                    cleanPlayer.src = cleanUrl;
                    cleanPlayer.load();
                }
                const cmpAfter = document.getElementById('compare_video_after');
                if (cmpAfter) {
                    cmpAfter.src = cleanUrl;
                    cmpAfter.load();
                }
            }

            const overlay = document.getElementById('studio_processing_overlay');
            const fillBar = document.getElementById('proc_progress_fill');
            const pctText = document.getElementById('proc_percent_text');
            const etaText = document.getElementById('proc_eta_text');
            const stagePill = document.getElementById('proc_stage_pill');
            const ctaBtn = document.getElementById('btn_studio_remove_captions');
            const ctaFill = document.getElementById('cta_btn_progress_fill');
            const ctaLabel = document.getElementById('cta_btn_label');
            const durPill = document.getElementById('cta_clip_duration_pill');

            const step1 = document.getElementById('pstep_1');
            const step2 = document.getElementById('pstep_2');
            const step3 = document.getElementById('pstep_3');
            const step4 = document.getElementById('pstep_4');

            if (fillBar) fillBar.style.width = '100%';
            if (pctText) pctText.innerText = '100%';
            if (etaText) etaText.innerText = 'Done!';
            if (stagePill) stagePill.innerText = '✨ Caption Removal Complete!';

            [step1, step2, step3, step4].forEach(s => {
                if (s) {
                    s.classList.remove('active');
                    s.classList.add('completed');
                }
            });

            if (ctaFill) ctaFill.style.width = '100%';
            if (ctaLabel) ctaLabel.innerText = '✨ Complete!';
            if (durPill) durPill.innerText = 'Done';

            setTimeout(() => {
                if (overlay) {
                    overlay.style.transition = 'opacity 0.4s ease';
                    overlay.style.opacity = '0';
                    setTimeout(() => {
                        overlay.style.display = 'none';
                        overlay.style.opacity = '1';
                    }, 400);
                }

                if (ctaBtn) {
                    ctaBtn.disabled = false;
                    ctaBtn.style.opacity = '1';
                    ctaBtn.style.cursor = 'pointer';
                    if (ctaLabel) ctaLabel.innerText = 'Remove captions';
                    const spk = document.getElementById('cta_sparkle_icon');
                    if (spk) spk.innerText = '✨';
                    const cf = document.getElementById('cta_btn_progress_fill');
                    if (cf) cf.style.width = '0%';
                    if (durPill && window.__TRIM_DATA && window.__TRIM_DATA.enabled) {
                        const len = Math.max(0.1, window.__TRIM_DATA.end - window.__TRIM_DATA.start);
                        durPill.innerText = len.toFixed(1) + 's';
                    }
                }

                // Switch to clean result tab and play video
                const tabClean = document.getElementById('tab_view_result');
                if (tabClean) {
                    tabClean.style.display = 'flex';
                    tabClean.click();
                }
            }, 600);
        }

        window.__onPipelineComplete = function(cleanPath) {
            console.log('[studio] window.__onPipelineComplete invoked:', cleanPath);
            completeProcessingProgress(cleanPath);
        };
        studio.complete = completeProcessingProgress;

        function cancelProcessingProgress() {
            studio.isProcessing = false;
            if (procProgressTimer) {
                clearInterval(procProgressTimer);
                procProgressTimer = null;
            }
            const overlay = document.getElementById('studio_processing_overlay');
            if (overlay) overlay.style.display = 'none';

            const ctaBtn = document.getElementById('btn_studio_remove_captions');
            if (ctaBtn) {
                ctaBtn.disabled = false;
                ctaBtn.style.opacity = '1';
                ctaBtn.style.cursor = 'pointer';
                const ctaLabel = document.getElementById('cta_btn_label');
                if (ctaLabel) ctaLabel.innerText = 'Remove captions';
                const spk = document.getElementById('cta_sparkle_icon');
                if (spk) spk.innerText = '✨';
                const cf = document.getElementById('cta_btn_progress_fill');
                if (cf) cf.style.width = '0%';
            }
        }

        // Primary Action: Remove Captions Button
        const ctaBtn = document.getElementById('btn_studio_remove_captions');
        if (ctaBtn && !ctaBtn.__hasInit) {
            ctaBtn.__hasInit = true;
            ctaBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const videoEl = findSourceVideo();
                if (!videoEl || !videoEl.src || videoEl.src === '') {
                    alert('Please upload or drag a video into the monitor first!');
                    return;
                }

                // Visual button loading feedback
                ctaBtn.disabled = true;
                ctaBtn.style.opacity = '0.9';
                ctaBtn.style.cursor = 'wait';

                // Start live animated processing overlay and progress counter
                startProcessingProgress();

                // Sync all parameters into Gradio inputs
                if (window.__ROI_DATA) {
                    setGradioInput('slider_left_x', Math.round(window.__ROI_DATA.left_x));
                    setGradioInput('slider_bottom_y', Math.round(window.__ROI_DATA.bottom_y));
                    setGradioInput('slider_right_x', Math.round(window.__ROI_DATA.right_x));
                    setGradioInput('slider_top_y', Math.round(window.__ROI_DATA.top_y));
                }

                const isTrim = Boolean(window.__TRIM_DATA && window.__TRIM_DATA.enabled && window.__TRIM_DATA.end > window.__TRIM_DATA.start);
                setGradioInput('input_clip_start', isTrim ? Number(window.__TRIM_DATA.start) : 0);
                setGradioInput('input_clip_end', isTrim ? Number(window.__TRIM_DATA.end) : 0);

                const trimChk = document.querySelector('#chk_clip_trim input[type="checkbox"]');
                if (trimChk && trimChk.checked !== isTrim) {
                    trimChk.click();
                }

                if (studio.activeStyle) setGradioRadio('radio_subtitle_color', studio.activeStyle);
                if (studio.activeMode) setGradioRadio('radio_process_mode', studio.activeMode);

                const dilInp = document.getElementById('input_mask_dilation');
                if (dilInp) setGradioInput('slider_dilate', dilInp.value || 2);

                const lamaInp = document.getElementById('input_lama_extra');
                if (lamaInp) setGradioInput('slider_lama_extra', lamaInp.value || 1);

                const tempInp = document.getElementById('input_temporal_window');
                if (tempInp) setGradioInput('slider_temporal', tempInp.value || 12);

                // Find and click the Gradio run button
                let gradioRun = document.getElementById('btn_run_pipeline');
                if (gradioRun) {
                    if (gradioRun.tagName !== 'BUTTON') {
                        const b = gradioRun.querySelector('button');
                        if (b) gradioRun = b;
                    }
                    gradioRun.click();
                } else {
                    console.error('Could not find #btn_run_pipeline in DOM');
                    cancelProcessingProgress();
                }
            });
        }

        // Compare Before & After Button
        const compareBtn = document.getElementById('btn_open_compare_modal');
        if (compareBtn && !compareBtn.__hasInit) {
            compareBtn.__hasInit = true;
            compareBtn.addEventListener('click', openCompareModal);
        }
    }

    // -------------------------------------------------------------
    // In-Monitor View Switcher (Original vs Clean Result)
    // -------------------------------------------------------------
    function setupMonitorTabs() {
        const tabOrig = document.getElementById('tab_view_original');
        const tabClean = document.getElementById('tab_view_result');
        const repVideo = findRepairedVideo();
        const ctaBtn = document.getElementById('btn_studio_remove_captions');

        if (studio.isProcessing) {
            const currentRepSrc = getVideoSource(repVideo);
            const directPath = getDirectRepairedPath();
            const elapsedSinceStart = (Date.now() - (studio.processingStartTime || 0)) / 1000;

            const hasDirectPath = Boolean(directPath && directPath !== '');
            const hasNewVideoSrc = Boolean(currentRepSrc && currentRepSrc !== '' && currentRepSrc !== studio.lastRepVideoSrc);
            const hasLoadedVideo = Boolean(repVideo && (repVideo.duration > 0 || repVideo.readyState >= 1) && repVideo !== findSourceVideo());

            // Check if Gradio's run button has finished execution (leaves loading/disabled state after starting)
            const gradioRun = document.getElementById('btn_run_pipeline');
            const gradioNotBusy = Boolean(
                gradioRun &&
                elapsedSinceStart > 3 &&
                !gradioRun.classList.contains('loading') &&
                !gradioRun.hasAttribute('disabled') &&
                !document.querySelector('#gradio_backend_bridge .loading')
            );

            if (hasDirectPath || hasNewVideoSrc || (hasLoadedVideo && currentRepSrc) || (gradioNotBusy && elapsedSinceStart > 4)) {
                studio.lastRepVideoSrc = currentRepSrc;
                completeProcessingProgress(directPath);
            }
        }

        // Check if an error toast was displayed to restore button state
        const errorToast = document.querySelector('.toast-wrap, .toast.error, div[class*="toast"]');
        if (studio.isProcessing && errorToast) {
            cancelProcessingProgress();
        }

        if (tabOrig && !tabOrig.__hasTabInit) {
            tabOrig.__hasTabInit = true;
            tabOrig.addEventListener('click', () => {
                studio.activeMonitorTab = 'original';
                tabOrig.classList.add('active');
                if (tabClean) tabClean.classList.remove('active');

                const srcPlayer = document.getElementById('source_video_player');
                const cleanPlayer = document.getElementById('studio_clean_video_player');
                const repPlayer = document.getElementById('repaired_video_player');
                const roiOverlay = document.getElementById('roi_canvas_overlay');
                const roiPill = document.getElementById('roi_floating_pill');
                if (cleanPlayer) cleanPlayer.style.display = 'none';
                if (repPlayer) repPlayer.style.display = 'none';
                if (srcPlayer) srcPlayer.style.display = 'block';
                if (roiOverlay) roiOverlay.style.display = 'block';
                if (roiPill) roiPill.style.display = 'flex';
            });
        }

        if (tabClean && !tabClean.__hasTabInit) {
            tabClean.__hasTabInit = true;
            tabClean.addEventListener('click', () => {
                studio.activeMonitorTab = 'result';
                tabClean.classList.add('active');
                if (tabOrig) tabOrig.classList.remove('active');

                const srcPlayer = document.getElementById('source_video_player');
                const cleanPlayer = document.getElementById('studio_clean_video_player');
                const repPlayer = document.getElementById('repaired_video_player');
                const roiOverlay = document.getElementById('roi_canvas_overlay');
                const roiPill = document.getElementById('roi_floating_pill');
                if (srcPlayer) srcPlayer.style.display = 'none';

                const srcVid = findSourceVideo();
                const curTime = (srcVid ? srcVid.currentTime : 0);

                if (cleanPlayer && cleanPlayer.src && cleanPlayer.src !== '') {
                    cleanPlayer.style.display = 'block';
                    if (repPlayer) repPlayer.style.display = 'none';
                    cleanPlayer.currentTime = curTime;
                    cleanPlayer.play().catch(() => {});
                } else if (repPlayer) {
                    repPlayer.style.display = 'block';
                    const repVid = repPlayer.querySelector('video') || findRepairedVideo();
                    if (repVid) {
                        repVid.style.display = 'block';
                        repVid.currentTime = curTime;
                        repVid.play().catch(() => {});
                    }
                }
                if (roiOverlay) roiOverlay.style.display = 'none';
                if (roiPill) roiPill.style.display = 'none';
            });
        }
    }

    // -------------------------------------------------------------
    // Modals Management (Shortcuts, Docs, Coords, Compare)
    // -------------------------------------------------------------
    function openCoordsModal() {
        const modal = document.getElementById('modal_advanced_coords');
        if (!modal) return;
        const cur = window.__ROI_DATA || { left_x: 120, bottom_y: 1650, right_x: 960, top_y: 1830 };
        const inLx = document.getElementById('modal_input_lx');
        const inBy = document.getElementById('modal_input_by');
        const inRx = document.getElementById('modal_input_rx');
        const inTy = document.getElementById('modal_input_ty');
        if (inLx) inLx.value = cur.left_x;
        if (inBy) inBy.value = cur.bottom_y;
        if (inRx) inRx.value = cur.right_x;
        if (inTy) inTy.value = cur.top_y;

        modal.style.display = 'flex';
    }

    function closeAllModals() {
        document.querySelectorAll('.studio-modal-backdrop').forEach(m => m.style.display = 'none');
    }

    function captureVideoFrameToDataUrl(videoEl) {
        if (!videoEl || videoEl.readyState < 2) return null;
        try {
            const canvas = document.createElement('canvas');
            canvas.width = videoEl.videoWidth || 1920;
            canvas.height = videoEl.videoHeight || 1080;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL('image/jpeg', 0.95);
        } catch (e) {
            return null;
        }
    }

    function openCompareModal() {
        const modal = document.getElementById('modal_comparison_view');
        if (!modal) return;

        const srcVideo = findSourceVideo();
        const cleanPlayer = document.getElementById('studio_clean_video_player');
        const repVideo = (cleanPlayer && cleanPlayer.src && cleanPlayer.src !== '') ? cleanPlayer : findRepairedVideo();

        const imgOrig = document.getElementById('compare_img_original');
        const imgClean = document.getElementById('compare_img_clean');

        const srcData = captureVideoFrameToDataUrl(srcVideo);
        const repData = captureVideoFrameToDataUrl(repVideo);

        if (imgOrig) imgOrig.src = srcData || '';
        if (imgClean) imgClean.src = repData || srcData || '';

        modal.style.display = 'flex';
        initSplitSlider();
    }

    function initSplitSlider() {
        const viewport = document.getElementById('split_slider_viewport');
        const divider = document.getElementById('split_divider_line');
        const cleanLayer = document.getElementById('split_layer_clean');
        if (!viewport || !divider || !cleanLayer) return;

        let isDraggingSplit = false;

        function setSplitPosition(pct) {
            pct = Math.max(0, Math.min(100, pct));
            divider.style.left = pct + '%';
            cleanLayer.style.clipPath = 'polygon(' + pct + '% 0%, 100% 0%, 100% 100%, ' + pct + '% 100%)';
        }

        setSplitPosition(50);

        if (!viewport.__hasSplitInit) {
            viewport.__hasSplitInit = true;

            viewport.addEventListener('pointerdown', (e) => {
                isDraggingSplit = true;
                const rect = viewport.getBoundingClientRect();
                const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
                setSplitPosition((relX / rect.width) * 100);
            });

            window.addEventListener('pointermove', (e) => {
                if (!isDraggingSplit) return;
                const rect = viewport.getBoundingClientRect();
                const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
                setSplitPosition((relX / rect.width) * 100);
            });

            window.addEventListener('pointerup', () => {
                isDraggingSplit = false;
            });
        }
    }

    function attachAllModalListeners() {
        // Modal 1: Coords
        const modalCoords = document.getElementById('modal_advanced_coords');
        if (modalCoords && !modalCoords.__hasInit) {
            modalCoords.__hasInit = true;
            document.getElementById('btn_close_coords_modal')?.addEventListener('click', () => modalCoords.style.display = 'none');
            modalCoords.addEventListener('click', (e) => { if (e.target === modalCoords) modalCoords.style.display = 'none'; });

            document.getElementById('btn_modal_coords_reset')?.addEventListener('click', () => window.__snapRoiPreset('bottom'));
            document.getElementById('btn_modal_coords_apply')?.addEventListener('click', () => {
                const lx = parseInt(document.getElementById('modal_input_lx')?.value) || 0;
                const by = parseInt(document.getElementById('modal_input_by')?.value) || 0;
                const rx = parseInt(document.getElementById('modal_input_rx')?.value) || 0;
                const ty = parseInt(document.getElementById('modal_input_ty')?.value) || 0;
                pushCoordinatesToGradio(lx, by, rx, ty);
                syncBoxFromCoordinates(lx, by, rx, ty);
                modalCoords.style.display = 'none';
            });
        }

        // Modal 2: Compare
        const modalCompare = document.getElementById('modal_comparison_view');
        if (modalCompare && !modalCompare.__hasInit) {
            modalCompare.__hasInit = true;
            document.getElementById('btn_close_compare_modal')?.addEventListener('click', () => modalCompare.style.display = 'none');
            modalCompare.addEventListener('click', (e) => { if (e.target === modalCompare) modalCompare.style.display = 'none'; });
        }

        // Modal 3: Shortcuts
        const modalShortcuts = document.getElementById('modal_shortcuts_guide');
        const btnShortcuts = document.getElementById('btn_nav_shortcuts');
        if (modalShortcuts && !modalShortcuts.__hasInit) {
            modalShortcuts.__hasInit = true;
            btnShortcuts?.addEventListener('click', () => modalShortcuts.style.display = 'flex');
            document.getElementById('btn_close_shortcuts_modal')?.addEventListener('click', () => modalShortcuts.style.display = 'none');
            modalShortcuts.addEventListener('click', (e) => { if (e.target === modalShortcuts) modalShortcuts.style.display = 'none'; });
        }

        // Modal 4: Docs
        const modalDocs = document.getElementById('modal_docs_guide');
        const btnDocs = document.getElementById('btn_nav_docs');
        if (modalDocs && !modalDocs.__hasInit) {
            modalDocs.__hasInit = true;
            btnDocs?.addEventListener('click', () => modalDocs.style.display = 'flex');
            document.getElementById('btn_close_docs_modal')?.addEventListener('click', () => modalDocs.style.display = 'none');
            modalDocs.addEventListener('click', (e) => { if (e.target === modalDocs) modalDocs.style.display = 'none'; });
        }
    }

    // -------------------------------------------------------------
    // Global Keyboard Shortcuts
    // -------------------------------------------------------------
    function setupKeyboardShortcuts() {
        if (window.__shortcutsRegistered) return;
        window.__shortcutsRegistered = true;

        window.addEventListener('keydown', (e) => {
            if (['input', 'textarea', 'select'].includes(document.activeElement?.tagName?.toLowerCase())) {
                return;
            }

            if (e.key === 'Escape') {
                closeAllModals();
                return;
            }

            const v = getActiveVideo();
            if (!v) return;

            if (e.code === 'Space') {
                e.preventDefault();
                if (v.paused) v.play(); else v.pause();
                updateTransportUI();
            } else if (e.key === '[' || e.key === '{') {
                e.preventDefault();
                document.getElementById('capcut_btn_set_in')?.click();
            } else if (e.key === ']' || e.key === '}') {
                e.preventDefault();
                document.getElementById('capcut_btn_set_out')?.click();
            } else if (e.key === 'm' || e.key === 'M') {
                v.muted = !v.muted;
                updateTransportUI();
            } else if (e.key === 'f' || e.key === 'F') {
                document.getElementById('btn_fit_canvas')?.click();
            }
        });
    }

    // -------------------------------------------------------------
    // Main Studio Lifecycle & Polling Loop
    // -------------------------------------------------------------
    setInterval(() => {
        mountVideoIntoStudio();

        const v = findSourceVideo();
        if (!v && studio.video) {
            studio.video = null;
            studio.duration = 0;
            const viewport = document.getElementById('studio_monitor_viewport');
            if (viewport) {
                viewport.classList.remove('viewport-portrait');
                viewport.classList.remove('viewport-landscape');
            }
            const badge = document.getElementById('meta_aspect_badge');
            if (badge) badge.innerText = 'AUTO RATIO';
            const resFps = document.getElementById('meta_resolution_fps');
            if (resFps) resFps.innerText = 'Waiting for video...';
            const pill = document.getElementById('roi_floating_pill');
            if (pill) pill.style.display = 'none';
            const tabClean = document.getElementById('tab_view_result');
            if (tabClean) tabClean.style.display = 'none';
            const tabOrig = document.getElementById('tab_view_original');
            if (tabOrig) tabOrig.classList.add('active');
        }

        const cleanPlayer = document.getElementById('studio_clean_video_player');
        if (cleanPlayer && !cleanPlayer.__hasTimeListener) {
            cleanPlayer.__hasTimeListener = true;
            cleanPlayer.addEventListener('timeupdate', () => {
                if (studio.activeMonitorTab === 'result') {
                    updateTransportUI();
                }
            });
        }

        if (v && v !== studio.video) {
            studio.video = v;
            v.addEventListener('timeupdate', () => {
                updatePlayhead();
                updateTransportUI();
            });

            const onMeta = () => {
                detectAndApplyAspectRatio(v);
                if (v.duration && v.duration > 0) {
                    studio.duration = v.duration;
                    if (studio.trimEnd <= 0 || studio.trimEnd > studio.duration) {
                        studio.trimEnd = studio.duration;
                    }
                    buildRuler(studio.duration);
                    updateTimelineUI();
                    updateTransportUI();
                    generateFilmstripThumbnails(v, studio.duration);
                }
            };
            v.addEventListener('durationchange', onMeta);
            v.addEventListener('loadedmetadata', onMeta);
            v.addEventListener('loadeddata', onMeta);
            v.addEventListener('canplay', onMeta);
            v.addEventListener('playing', onMeta);

            if (v.readyState >= 1) onMeta();
        }

        if (studio.video) {
            detectAndApplyAspectRatio(studio.video);
            if (studio.video.duration && studio.video.duration > 0) {
                if (studio.duration !== studio.video.duration) {
                    studio.duration = studio.video.duration;
                    if (studio.trimEnd <= 0 || studio.trimEnd > studio.duration) {
                        studio.trimEnd = studio.duration;
                    }
                    buildRuler(studio.duration);
                    updateTimelineUI();
                }
                generateFilmstripThumbnails(studio.video, studio.duration);
            }
        }

        attachTransportListeners();
        attachTimelineListeners();
        attachPillListeners();
        attachInspectorListeners();
        attachAllModalListeners();
        setupMonitorTabs();
        setupKeyboardShortcuts();

        // Overlay element lifecycle
        if (!overlay || !document.contains(overlay)) {
            createOverlayElements();
        } else {
            updateOverlayPosition();
        }

        // Sync slider changes from python/gradio
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
(...args) => {
    try {
        let [video, lx, by, rx, ty, trim, tStart, tEnd, color, mode, prev, dil, lama, temp] = args;
        const studio = window.__STUDIO || {};

        if (window.__ROI_DATA) {
            lx = Math.round(Number(window.__ROI_DATA.left_x) || 0);
            by = Math.round(Number(window.__ROI_DATA.bottom_y) || 1080);
            rx = Math.round(Number(window.__ROI_DATA.right_x) || 1920);
            ty = Math.round(Number(window.__ROI_DATA.top_y) || 900);
        }

        const isTrim = Boolean(window.__TRIM_DATA && window.__TRIM_DATA.enabled && window.__TRIM_DATA.end > window.__TRIM_DATA.start);
        trim = isTrim;
        if (isTrim) {
            tStart = Number(window.__TRIM_DATA.start) || 0.0;
            tEnd = Number(window.__TRIM_DATA.end) || 0.0;
        } else {
            tStart = 0.0;
            tEnd = 0.0;
        }

        color = studio.activeStyle || color || 'white_stroke';
        mode = studio.activeMode || mode || 'quality';
        prev = false;

        const dilInp = document.getElementById('input_mask_dilation');
        dil = parseInt((dilInp ? dilInp.value : studio.maskDilation) || 2) || 2;

        const lamaInp = document.getElementById('input_lama_extra');
        lama = parseInt((lamaInp ? lamaInp.value : studio.lamaExtra) || 1) || 1;

        const tempInp = document.getElementById('input_temporal_window');
        temp = parseInt((tempInp ? tempInp.value : studio.temporalWindow) || 12) || 12;

        return [video, lx, by, rx, ty, trim, tStart, tEnd, color, mode, prev, dil, lama, temp];
    } catch (err) {
        console.error('RUN_BTN_JS execution error:', err);
        return args;
    }
}
"""

