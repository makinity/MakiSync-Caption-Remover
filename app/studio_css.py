# -*- coding: utf-8 -*-
"""Custom CSS for Caption Remover Studio with adaptive ratio & filmstrip thumbnails."""

STUDIO_CSS = """
/* ==========================================================================
   Caption Remover Studio - Pro Design System (Adaptive 16:9 & 9:16)
   ========================================================================== */

:root {
    --studio-bg: #07090E;
    --studio-surface: #0B0F19;
    --studio-card: #0E1422;
    --studio-card-active: #17132D;
    --studio-border: #1E283A;
    --studio-border-hover: #334155;
    --studio-purple: #8B5CF6;
    --studio-purple-dark: #7C3AED;
    --studio-purple-glow: rgba(139, 92, 246, 0.45);
    --studio-gold: #FFD200;
    --studio-green: #10B981;
    --studio-text: #F8FAFC;
    --studio-text-muted: #94A3B8;
    --studio-text-subtle: #64748B;
}

body, .gradio-container {
    background-color: var(--studio-bg) !important;
    color: var(--studio-text) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
}

/* Hide default Gradio header, footer and WebAssembly trim */
footer, header, button[aria-label*="Trim video"], button[title*="Trim video"], div[class*="trim"] button:first-child {
    display: none !important;
}

/* Keep Gradio Bridge & Output fully active in DOM layout so event handlers fire reliably */
#gradio_backend_bridge,
#gradio_output_wrapper {
    position: fixed !important;
    left: -9999px !important;
    top: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    pointer-events: auto !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    z-index: -999 !important;
}

#gradio_source_wrapper {
    display: contents !important;
}

/* Studio Container */
.studio-app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    padding: 14px 24px 30px 24px;
    box-sizing: border-box;
    background-color: var(--studio-bg);
}

/* --------------------------------------------------------------------------
   Top Navigation Bar
   -------------------------------------------------------------------------- */
.studio-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0 14px 0;
    border-bottom: 1px solid rgba(30, 41, 59, 0.6);
}

.nav-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.studio-logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.studio-title-group {
    display: flex;
    flex-direction: column;
}

.studio-brand-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
}

.brand-highlight {
    color: #A78BFA;
}

.studio-brand-sub {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--studio-text-subtle);
    letter-spacing: 0.08em;
    margin-top: 1px;
}

.nav-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

.status-gpu-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34D399;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 9999px;
    letter-spacing: 0.02em;
}

.gpu-dot {
    width: 6px;
    height: 6px;
    background: #10B981;
    border-radius: 50%;
    box-shadow: 0 0 6px #10B981;
}

.nav-ghost-btn {
    background: transparent;
    border: none;
    color: var(--studio-text-muted);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    padding: 6px 10px;
    border-radius: 6px;
    transition: all 0.15s ease;
}

.nav-ghost-btn:hover {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.05);
}

.nav-export-btn {
    background: linear-gradient(135deg, #7C3AED 0%, #9333EA 100%);
    color: #FFFFFF !important;
    text-decoration: none !important;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 6px 12px;
    border-radius: 6px;
    box-shadow: 0 2px 10px rgba(147, 51, 234, 0.4);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.15s ease;
    cursor: pointer;
}

.nav-export-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(147, 51, 234, 0.6);
}

.nav-icon-btn {
    background: transparent;
    border: 1px solid var(--studio-border);
    color: var(--studio-text-muted);
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
}

.nav-icon-btn:hover {
    color: #FFFFFF;
    border-color: #475569;
}

/* --------------------------------------------------------------------------
   Subbar: Breadcrumb & Title
   -------------------------------------------------------------------------- */
.studio-subbar {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 14px 0 12px 0;
}

.breadcrumb-tag {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--studio-text-subtle);
    letter-spacing: 0.06em;
    margin-bottom: 4px;
}

.project-title {
    font-size: 1.45rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0;
    letter-spacing: -0.02em;
}

.subbar-right {
    display: flex;
    align-items: center;
    gap: 14px;
}

.autosaved-badge {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.76rem;
    color: var(--studio-text-subtle);
    font-weight: 500;
}

.fit-canvas-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: 1px solid var(--studio-border);
    color: var(--studio-text-muted);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.fit-canvas-btn:hover {
    color: #FFFFFF;
    border-color: #475569;
}

/* --------------------------------------------------------------------------
   Main Workspace Layout: 2 Columns
   -------------------------------------------------------------------------- */
.studio-workspace {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 350px;
    gap: 20px;
    margin-top: 4px;
}

.workspace-main {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* --------------------------------------------------------------------------
   Video Monitor Frame & Adaptive Viewport
   -------------------------------------------------------------------------- */
.monitor-container {
    background: var(--studio-surface);
    border: 1px solid var(--studio-border);
    border-radius: 14px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    position: relative;
}

.monitor-top-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: rgba(11, 15, 25, 0.95);
    border-bottom: 1px solid rgba(30, 41, 59, 0.5);
}

.monitor-meta-left, .monitor-meta-right {
    display: flex;
    align-items: center;
    gap: 10px;
}

.preview-tag, .result-tag {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 4px 8px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
}

.preview-tag {
    color: #CBD5E1;
    background: rgba(255, 255, 255, 0.04);
}

.preview-tag.active {
    color: #FFFFFF;
    background: rgba(16, 185, 129, 0.16);
    border: 1px solid rgba(16, 185, 129, 0.35);
}

.result-tag {
    color: #A78BFA;
    background: rgba(139, 92, 246, 0.12);
    border: 1px solid rgba(139, 92, 246, 0.25);
}

.result-tag.active {
    color: #FFFFFF;
    background: rgba(139, 92, 246, 0.28);
    border: 1px solid var(--studio-purple);
    box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
}

.green-indicator {
    width: 6px;
    height: 6px;
    background: #10B981;
    border-radius: 50%;
    box-shadow: 0 0 6px #10B981;
}

.purple-indicator {
    width: 6px;
    height: 6px;
    background: var(--studio-purple);
    border-radius: 50%;
    box-shadow: 0 0 6px var(--studio-purple);
}

.ratio-badge {
    font-size: 0.68rem;
    font-weight: 700;
    color: #A78BFA;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.3);
    padding: 2px 7px;
    border-radius: 4px;
    letter-spacing: 0.03em;
}

.resolution-tag {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--studio-text-subtle);
    font-family: monospace;
}

/* Monitor Viewport & Adaptive Aspect Ratios */
.monitor-viewport {
    position: relative;
    width: 100%;
    height: 480px;
    min-height: 440px;
    max-height: 56vh;
    background: #030509;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Figma / Photoshop Pan & Zoom Styles */
.monitor-viewport.panning-space-active,
.monitor-viewport.panning-space-active * {
    cursor: grab !important;
}

.monitor-viewport.is-panning,
.monitor-viewport.is-panning * {
    cursor: grabbing !important;
    user-select: none !important;
}

.monitor-viewport.panning-space-active #roi_interactive_overlay,
.monitor-viewport.is-panning #roi_interactive_overlay {
    pointer-events: none !important;
}

#video_player_mount {
    will-change: transform;
    transform-origin: center center;
}

/* Floating Zoom Indicator Pill */
.zoom-indicator-pill {
    position: absolute;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 45;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(139, 92, 246, 0.45);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.76rem;
    font-weight: 600;
    color: #F8FAFC;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6), 0 0 12px rgba(139, 92, 246, 0.2);
    pointer-events: auto;
    cursor: pointer;
    user-select: none;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    animation: zoomPillFadeIn 0.25s ease-out;
}

@keyframes zoomPillFadeIn {
    from { opacity: 0; transform: translate(-50%, -6px) scale(0.96); }
    to { opacity: 1; transform: translate(-50%, 0) scale(1); }
}

.zoom-indicator-pill:hover {
    background: rgba(30, 41, 59, 0.95);
    border-color: #8B5CF6;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.7), 0 0 16px rgba(139, 92, 246, 0.35);
}

.zoom-indicator-pill .zoom-pill-icon {
    font-size: 0.8rem;
}

.zoom-indicator-pill .zoom-pill-pct {
    color: #A78BFA;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}

.zoom-indicator-pill .zoom-pill-divider {
    width: 1px;
    height: 12px;
    background: rgba(255, 255, 255, 0.2);
}

.zoom-indicator-pill .zoom-pill-hint {
    color: #94A3B8;
    font-size: 0.72rem;
    font-weight: 500;
}

.fit-canvas-btn.zoom-active {
    background: rgba(139, 92, 246, 0.18) !important;
    border-color: #8B5CF6 !important;
    color: #C4B5FD !important;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.3) !important;
}

/* 16:9 Landscape Video Mode */
.monitor-viewport.viewport-landscape {
    height: 480px;
    max-height: 56vh;
    padding: 0;
}

.monitor-viewport.viewport-landscape #video_player_mount {
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
}

.monitor-viewport.viewport-landscape #video_player_mount video,
.monitor-viewport.viewport-landscape #source_video_player video,
.monitor-viewport.viewport-landscape #studio_clean_video_player {
    width: auto !important;
    height: auto !important;
    max-width: 100% !important;
    max-height: 480px !important;
    object-fit: contain !important;
    border-radius: 6px !important;
    margin: 0 auto !important;
    display: block !important;
    outline: none !important;
}

/* 9:16 Portrait Video Mode - Centered vertical phone card frame */
.monitor-viewport.viewport-portrait {
    height: 580px;
    max-height: 75vh;
    padding: 12px 0;
}

.monitor-viewport.viewport-portrait #video_player_mount {
    width: auto !important;
    height: 100% !important;
    max-height: 556px !important;
    aspect-ratio: 9 / 16 !important;
    max-width: calc(556px * 9 / 16) !important; /* ~312px */
    margin: 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(139, 92, 246, 0.45) !important;
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.9), 0 0 24px rgba(139, 92, 246, 0.25) !important;
    background: #000000 !important;
}

.monitor-viewport.viewport-portrait #video_player_mount .wrap,
.monitor-viewport.viewport-portrait #source_video_player,
.monitor-viewport.viewport-portrait #source_video_player .wrap,
.monitor-viewport.viewport-portrait #studio_clean_video_player {
    width: 100% !important;
    height: 100% !important;
    background: transparent !important;
}

.monitor-viewport.viewport-portrait #video_player_mount video,
.monitor-viewport.viewport-portrait #source_video_player video,
.monitor-viewport.viewport-portrait #studio_clean_video_player {
    width: 100% !important;
    height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    object-fit: contain !important;
    border-radius: 12px !important;
    display: block !important;
    outline: none !important;
}

/* Common Video Player Mount Layout */
#video_player_mount {
    width: 100%;
    height: 100%;
    min-height: 440px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

#video_player_mount > #source_video_player,
#video_player_mount > #studio_clean_video_player {
    position: absolute !important;
    inset: 0 !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

#source_video_player {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    z-index: 10;
}

#source_video_player.hidden {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -1 !important;
}

#studio_clean_video_player {
    z-index: 35 !important;
    cursor: pointer !important;
}

#studio_clean_video_player.hidden {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -1 !important;
}

#studio_clean_video_player.active {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    z-index: 35 !important;
}

#source_video_player .wrap,
#source_video_player > .wrap {
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
}

/* Empty Video Upload Dropzone inside Studio Monitor */
#source_video_player .empty,
#source_video_player .upload-container,
#source_video_player [data-testid="dropzone"] {
    width: 88% !important;
    max-width: 520px !important;
    min-height: 240px !important;
    height: auto !important;
    margin: auto !important;
    padding: 32px 24px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(15, 23, 42, 0.6) !important;
    border: 2px dashed rgba(139, 92, 246, 0.45) !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(139, 92, 246, 0.05) !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

#source_video_player .empty:hover,
#source_video_player .upload-container:hover,
#source_video_player [data-testid="dropzone"]:hover {
    border-color: #A855F7 !important;
    background: rgba(139, 92, 246, 0.12) !important;
    box-shadow: 0 14px 40px rgba(139, 92, 246, 0.25), inset 0 0 30px rgba(139, 92, 246, 0.1) !important;
    transform: translateY(-2px);
}

#source_video_player .empty svg,
#source_video_player .upload-container svg,
#source_video_player [data-testid="dropzone"] svg {
    width: 44px !important;
    height: 44px !important;
    color: #A78BFA !important;
    margin-bottom: 12px !important;
    filter: drop-shadow(0 0 10px rgba(167, 139, 250, 0.5));
}

#source_video_player .empty span,
#source_video_player .upload-container span,
#source_video_player [data-testid="dropzone"] span {
    color: #F8FAFC !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
}

#source_video_player > label > span,
#source_video_player > .label {
    display: none !important;
}

#video_player_mount video,
#source_video_player video,
.monitor-viewport video,
video {
    object-fit: contain !important;
    outline: none;
}

/* Floating Tool Pill Bar over Video */
.video-floating-pill {
    position: absolute;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(15, 20, 32, 0.90);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(139, 92, 246, 0.4);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7), 0 0 16px rgba(139, 92, 246, 0.25);
    border-radius: 9999px;
    display: flex;
    align-items: center;
    padding: 4px 6px;
    z-index: 60;
    user-select: none;
    transition: bottom 0.2s ease;
}

.pill-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: none;
    color: #E2E8F0;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 9999px;
    cursor: pointer;
    transition: all 0.15s ease;
    white-space: nowrap;
}

.pill-btn:hover {
    color: #FFFFFF;
    background: rgba(139, 92, 246, 0.2);
}

.pill-divider {
    width: 1px;
    height: 14px;
    background: rgba(255, 255, 255, 0.12);
}

/* Preset Dropdown Menu */
.pill-dropdown-wrap {
    position: relative;
}

.preset-dropdown-menu {
    display: none;
    position: absolute;
    bottom: 38px;
    left: 50%;
    transform: translateX(-50%);
    background: #0E1422;
    border: 1px solid var(--studio-border);
    border-radius: 10px;
    padding: 6px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.8);
    width: 220px;
    z-index: 80;
}

.preset-dropdown-menu.show {
    display: block;
}

.preset-menu-item {
    font-size: 0.78rem;
    color: #CBD5E1;
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.preset-menu-item:hover, .preset-menu-item.active {
    background: rgba(139, 92, 246, 0.22);
    color: #FFFFFF;
}

/* Interactive ROI Box & Handles */
#roi_interactive_overlay {
    position: absolute;
    pointer-events: auto;
    z-index: 40;
}

#roi_interactive_box {
    position: absolute;
    border: 2px solid var(--studio-purple) !important;
    background: rgba(139, 92, 246, 0.18) !important;
    box-shadow: 0 0 18px rgba(139, 92, 246, 0.45) !important;
    cursor: move;
}

#roi_box_badge {
    position: absolute;
    top: -26px;
    left: 0;
    background: rgba(15, 20, 32, 0.95);
    color: #FFFFFF;
    font-size: 0.68rem;
    font-weight: 700;
    font-family: monospace;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid var(--studio-purple);
    white-space: nowrap;
    pointer-events: none;
}

/* Video Transport Bar */
.monitor-transport-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: #090D16;
    border-top: 1px solid rgba(30, 41, 59, 0.5);
}

.transport-left, .transport-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

.transport-play-btn {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.28);
    color: #FFFFFF !important;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    padding: 0;
}

.transport-play-btn svg {
    display: block !important;
    width: 14px !important;
    height: 14px !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
    color: #FFFFFF !important;
}

.transport-play-btn svg polygon,
.transport-play-btn svg rect {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

.transport-play-btn:hover {
    background: var(--studio-purple);
    border-color: var(--studio-purple);
    box-shadow: 0 0 14px var(--studio-purple-glow);
    transform: scale(1.06);
}

.transport-timecode {
    font-size: 0.78rem;
    font-family: monospace;
    font-weight: 600;
    color: #CBD5E1;
}

.transport-icon-btn {
    background: transparent;
    border: none;
    color: var(--studio-text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
}

.transport-icon-btn:hover {
    color: #FFFFFF;
}

.transport-scale-badge {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--studio-text-subtle);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
}

/* --------------------------------------------------------------------------
   Timeline Trimmer Component with Real Filmstrip
   -------------------------------------------------------------------------- */
.timeline-container {
    background: var(--studio-surface);
    border: 1px solid var(--studio-border);
    border-radius: 14px;
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
}

.timeline-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.timeline-left-title {
    display: flex;
    align-items: center;
    gap: 12px;
}

.timeline-tag-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--studio-text-subtle);
    letter-spacing: 0.06em;
}

.timeline-sequence-name {
    font-size: 0.8rem;
    font-weight: 600;
    color: #CBD5E1;
}

.timeline-right-tools {
    display: flex;
    align-items: center;
    gap: 8px;
}

.timeline-tool-btn {
    background: transparent;
    border: none;
    color: var(--studio-text-muted);
    font-size: 0.74rem;
    font-weight: 600;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
}

.timeline-tool-btn:hover {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.05);
}

.timeline-tracks-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.74rem;
    font-weight: 600;
    color: var(--studio-text-subtle);
    margin-left: 6px;
}

/* Filmstrip Track Viewport */
.timeline-track-viewport {
    position: relative;
    height: 58px;
    background: #020617;
    border: 1px solid var(--studio-border);
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    user-select: none;
}

.capcut-ruler {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    z-index: 5;
    pointer-events: none;
}

.capcut-ruler-tick {
    position: absolute;
    top: 1px;
    transform: translateX(-50%);
    font-size: 0.65rem;
    color: #64748B;
    font-family: monospace;
}

/* Filmstrip Canvas */
.capcut-track-track {
    position: absolute;
    top: 16px;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    overflow: hidden;
    background: #060911;
    z-index: 1;
}

.capcut-filmstrip-canvas {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    filter: brightness(0.85) contrast(1.05);
}

/* Dimmed Outside Areas */
.capcut-dim {
    position: absolute;
    top: 16px;
    bottom: 0;
    background: rgba(3, 5, 9, 0.78);
    backdrop-filter: blur(2px);
    z-index: 8;
    pointer-events: none;
    transition: width 0.04s ease;
}

.capcut-dim-left { left: 0; }
.capcut-dim-right { right: 0; }

/* Draggable Clip Window with Golden Brackets */
.capcut-clip {
    position: absolute;
    top: 16px;
    bottom: 0;
    border-top: 2px solid var(--studio-gold);
    border-bottom: 2px solid var(--studio-gold);
    background: rgba(255, 210, 0, 0.08);
    z-index: 10;
    box-sizing: border-box;
    cursor: grab;
    transition: left 0.04s ease, width 0.04s ease;
}

.capcut-clip-body {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.capcut-clip-len {
    font-size: 0.68rem;
    font-weight: 800;
    color: #FFFFFF;
    background: rgba(0, 0, 0, 0.65);
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid rgba(255, 210, 0, 0.5);
    font-family: monospace;
}

.capcut-handle {
    position: absolute;
    top: -2px;
    bottom: -2px;
    width: 14px;
    background: var(--studio-gold);
    color: #000000;
    font-weight: 900;
    font-size: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: ew-resize;
    z-index: 15;
    user-select: none;
    box-shadow: 0 0 8px rgba(255, 210, 0, 0.5);
}

.capcut-handle-left {
    left: -2px;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

.capcut-handle-right {
    right: -2px;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}

/* Playhead Needle */
.capcut-playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    z-index: 20;
    pointer-events: auto;
    cursor: ew-resize;
    transform: translateX(-50%);
}

.capcut-playhead-pin {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 10px;
    height: 12px;
    background: #EF4444;
    clip-path: polygon(0 0, 100% 0, 50% 100%);
}

.capcut-playhead-line {
    position: absolute;
    top: 12px;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    background: #EF4444;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.8);
}

.capcut-playhead-badge {
    display: none;
}

/* Timeline Bottom Controls */
.timeline-bottom-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
}

.controls-left-btns, .controls-right-extend {
    display: flex;
    align-items: center;
    gap: 8px;
}

.studio-btn-subtle {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--studio-border);
    color: var(--studio-text-muted);
    font-size: 0.74rem;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.studio-btn-subtle:hover {
    color: #FFFFFF;
    border-color: #475569;
}

.studio-btn-play {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.35);
    color: #C4B5FD;
    font-size: 0.74rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.studio-btn-play:hover {
    background: rgba(139, 92, 246, 0.28);
    color: #FFFFFF;
}

.extend-label {
    font-size: 0.72rem;
    color: var(--studio-text-subtle);
    font-weight: 600;
}

.extend-chip {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--studio-border);
    color: var(--studio-text-muted);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
}

.extend-chip:hover {
    color: #FFFFFF;
    border-color: #475569;
}

.trim-toggle-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 8px;
}

.trim-toggle-label {
    font-size: 0.72rem;
    color: var(--studio-text-muted);
    font-weight: 600;
}

/* Custom Switch Slider */
.studio-switch {
    position: relative;
    display: inline-block;
    width: 32px;
    height: 18px;
}

.studio-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.studio-switch-slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background-color: #1E283A;
    transition: 0.2s;
    border-radius: 18px;
}

.studio-switch-slider:before {
    position: absolute;
    content: "";
    height: 12px;
    width: 12px;
    left: 3px;
    bottom: 3px;
    background-color: #FFFFFF;
    transition: 0.2s;
    border-radius: 50%;
}

.studio-switch input:checked + .studio-switch-slider {
    background-color: var(--studio-purple);
}

.studio-switch input:checked + .studio-switch-slider:before {
    transform: translateX(14px);
}

/* --------------------------------------------------------------------------
   Inspector Dock (Right Column)
   -------------------------------------------------------------------------- */
.workspace-inspector {
    background: var(--studio-surface);
    border: 1px solid var(--studio-border);
    border-radius: 14px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

.inspector-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(30, 41, 59, 0.5);
}

.inspector-tag-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--studio-text-subtle);
    letter-spacing: 0.08em;
}

.inspector-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 2px 0 0 0;
    letter-spacing: -0.01em;
}

.inspector-reset-btn {
    background: transparent;
    border: none;
    color: var(--studio-text-muted);
    font-size: 0.74rem;
    font-weight: 600;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 4px;
}

.inspector-reset-btn:hover {
    color: #FFFFFF;
}

/* Inspector Sections */
.inspector-section {
    display: flex;
    flex-direction: column;
}

.section-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 2px;
}

.section-num {
    font-size: 0.68rem;
    font-weight: 800;
    color: var(--studio-purple);
    font-family: monospace;
}

.section-title {
    font-size: 0.84rem;
    font-weight: 700;
    color: #FFFFFF;
}

.section-desc {
    font-size: 0.72rem;
    color: var(--studio-text-subtle);
    margin: 0 0 10px 0;
}

/* Section 01: 2x2 Style Cards Grid */
.style-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.style-card {
    position: relative;
    background: var(--studio-card);
    border: 1px solid var(--studio-border);
    border-radius: 10px;
    padding: 12px 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    min-height: 72px;
    text-align: center;
}

.style-card.card-full-span {
    grid-column: span 2;
    flex-direction: row;
    gap: 12px;
    min-height: 48px;
    padding: 8px 16px;
}

.style-card:hover {
    border-color: #475569;
    background: #111827;
}

.style-card.active {
    background: var(--studio-card-active);
    border-color: var(--studio-purple);
    box-shadow: 0 0 14px var(--studio-purple-glow);
}

.style-card-check {
    position: absolute;
    top: 6px;
    right: 8px;
    font-size: 0.72rem;
    font-weight: 900;
    color: var(--studio-purple);
}

.style-card-icon {
    font-size: 1.15rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1;
}

.stroke-text-icon {
    text-shadow: 0 0 4px #000000, 0 0 6px #000000;
    color: #FFFFFF;
}

.pure-white-icon {
    color: #FFFFFF;
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.65);
}

.banner-box-icon .box-inner {
    display: inline-block;
    width: 22px;
    height: 12px;
    background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%);
    border-radius: 2px;
}

.shield-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #60A5FA;
}

.dark-text-icon {
    color: #64748B;
}

.style-card-label {
    font-size: 0.68rem;
    font-weight: 600;
    color: var(--studio-text-muted);
    line-height: 1.2;
}

.style-card.active .style-card-label {
    color: #F8FAFC;
}

/* Section 02: Inpainting Cards Grid */
.inpaint-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.inpaint-card {
    background: var(--studio-card);
    border: 1px solid var(--studio-border);
    border-radius: 10px;
    padding: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.inpaint-card:hover {
    border-color: #475569;
}

.inpaint-card.active {
    background: var(--studio-card-active);
    border-color: var(--studio-purple);
    box-shadow: 0 0 14px var(--studio-purple-glow);
}

.inpaint-card-icon {
    font-size: 1.1rem;
}

.inpaint-card-text {
    display: flex;
    flex-direction: column;
}

.inpaint-title {
    font-size: 0.74rem;
    font-weight: 700;
    color: #FFFFFF;
}

.inpaint-sub {
    font-size: 0.62rem;
    color: var(--studio-text-subtle);
}

/* Section 03: Precision Tuning Sliders */
.tuning-slider-group {
    background: var(--studio-card);
    border: 1px solid var(--studio-border);
    border-radius: 10px;
    padding: 12px;
}

.tuning-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.tuning-label-wrap {
    display: flex;
    flex-direction: column;
}

.tuning-label {
    font-size: 0.74rem;
    font-weight: 600;
    color: var(--studio-text-muted);
}

.tuning-hint {
    font-size: 0.62rem;
    color: var(--studio-text-subtle);
    font-weight: 500;
    margin-top: 1px;
}

.tuning-val {
    font-size: 0.74rem;
    font-weight: 700;
    color: #FFFFFF;
    font-family: monospace;
}

/* Range Input Styling */
.studio-range {
    width: 100%;
    -webkit-appearance: none;
    appearance: none;
    height: 4px;
    border-radius: 2px;
    background: #1E283A;
    outline: none;
}

.studio-range::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #FFFFFF;
    border: 2px solid var(--studio-purple);
    cursor: pointer;
    box-shadow: 0 0 8px rgba(139, 92, 246, 0.6);
}



/* Bottom CTA Area */
.inspector-cta-area {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: auto;
    padding-top: 10px;
    border-top: 1px solid rgba(30, 41, 59, 0.5);
}

.estimated-time-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.est-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--studio-text-subtle);
    letter-spacing: 0.06em;
}

.est-val {
    font-size: 0.72rem;
    font-weight: 600;
    color: #94A3B8;
    font-family: monospace;
}

.studio-cta-btn {
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #7C3AED 0%, #9333EA 100%);
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 4px 18px rgba(139, 92, 246, 0.4);
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.studio-cta-btn > span,
.studio-cta-btn > div:not(.cta-progress-fill) {
    position: relative;
    z-index: 2;
}

.cta-progress-fill {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    background: linear-gradient(90deg, rgba(236, 72, 153, 0.6), rgba(139, 92, 246, 0.75));
    border-radius: 10px;
    pointer-events: none;
    transition: width 0.3s ease;
    z-index: 1;
}

.studio-cta-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(139, 92, 246, 0.6);
}

.cta-sparkle {
    font-size: 0.95rem;
}

.cta-duration-pill {
    background: rgba(0, 0, 0, 0.25);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-family: monospace;
}

.compare-link-row {
    display: flex;
    justify-content: center;
}

.compare-modal-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: none;
    color: var(--studio-text-muted);
    font-size: 0.76rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
}

.compare-modal-btn:hover {
    color: #FFFFFF;
}

.sparkle-star {
    color: var(--studio-purple);
}

/* --------------------------------------------------------------------------
   Modals Common Design System
   -------------------------------------------------------------------------- */
.studio-modal-backdrop {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(2, 4, 8, 0.85);
    backdrop-filter: blur(8px);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.studio-modal-card {
    background: #0E1422;
    border: 1px solid var(--studio-border);
    border-radius: 14px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(139, 92, 246, 0.15);
    width: 100%;
    max-width: 480px;
    padding: 20px;
    display: flex;
    flex-direction: column;
}

.compare-modal-card {
    max-width: 680px;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}

.modal-tag-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--studio-text-subtle);
    letter-spacing: 0.08em;
}

.modal-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 2px 0 0 0;
}

.modal-close-btn {
    background: transparent;
    border: none;
    color: var(--studio-text-muted);
    font-size: 1rem;
    cursor: pointer;
    padding: 4px;
}

.modal-close-btn:hover { color: #FFFFFF; }

.modal-desc {
    font-size: 0.76rem;
    color: var(--studio-text-muted);
    margin: 0 0 16px 0;
    line-height: 1.4;
}



/* Modal 2: Before / After Split Slider */
.split-slider-viewport {
    position: relative;
    width: 100%;
    height: 380px;
    background: #030509;
    border-radius: 10px;
    overflow: hidden;
    user-select: none;
    cursor: ew-resize;
    margin-bottom: 12px;
}

.split-layer {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.split-layer video,
.split-layer img {
    width: 100%;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    background: transparent;
}

.compare-modal-footer {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 6px;
}

.split-layer-clean {
    z-index: 10;
    clip-path: inset(0 0 0 50%);
}

.compare-badge {
    position: absolute;
    top: 12px;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(0, 0, 0, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.15);
}
.badge-orig { left: 12px; color: #FFFFFF; }
.badge-clean { right: 12px; color: var(--studio-purple); }

.split-divider-line {
    position: absolute;
    top: 0; bottom: 0;
    left: 50%;
    width: 2px;
    background: #FFFFFF;
    z-index: 20;
    transform: translateX(-50%);
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.6);
}

.split-knob {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 26px;
    height: 26px;
    background: #FFFFFF;
    border-radius: 50%;
    box-shadow: 0 0 10px rgba(0,0,0,0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #000000;
}

.modal-bottom-hint {
    font-size: 0.74rem;
    color: var(--studio-text-subtle);
    text-align: center;
    margin: 4px 0 0 0;
}

/* Modal 3: Shortcuts List */
.shortcuts-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.shortcut-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--studio-border);
    border-radius: 6px;
}

.shortcut-desc {
    font-size: 0.78rem;
    color: #CBD5E1;
}

.shortcut-kbd {
    background: #030509;
    border: 1px solid #334155;
    color: var(--studio-purple);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: monospace;
}

/* Modal 4: Docs Content */
.docs-content {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.docs-block h4 {
    margin: 0 0 6px 0;
    font-size: 0.85rem;
    color: #FFFFFF;
}

.docs-block p {
    margin: 4px 0;
    font-size: 0.76rem;
    color: var(--studio-text-muted);
    line-height: 1.4;
}

/* ==========================================================================
   AI Processing Overlay, Progress Bar & Live Estimation
   ========================================================================== */
.processing-overlay {
    position: absolute;
    inset: 0;
    z-index: 120;
    background: rgba(5, 8, 16, 0.88);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    border-radius: 12px;
    animation: fadeInOverlay 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeInOverlay {
    from {
        opacity: 0;
        backdrop-filter: blur(0px);
    }
    to {
        opacity: 1;
        backdrop-filter: blur(14px);
    }
}

.processing-card {
    background: rgba(15, 20, 36, 0.95);
    border: 1px solid rgba(139, 92, 246, 0.35);
    border-radius: 18px;
    padding: 26px 30px;
    max-width: 440px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.75), 0 0 40px rgba(139, 92, 246, 0.25);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    animation: cardZoomIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes cardZoomIn {
    from {
        transform: scale(0.92);
        opacity: 0;
    }
    to {
        transform: scale(1);
        opacity: 1;
    }
}

.processing-spinner-ring {
    position: relative;
    width: 66px;
    height: 66px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}

.spinner-core {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 3.5px solid rgba(139, 92, 246, 0.15);
    border-top-color: #A855F7;
    border-right-color: #EC4899;
    box-shadow: 0 0 20px rgba(168, 85, 247, 0.4);
    animation: procSpin 1.1s cubic-bezier(0.5, 0.1, 0.5, 0.9) infinite;
}

@keyframes procSpin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

.processing-ai-icon {
    font-size: 1.6rem;
    animation: pulseIcon 2s ease-in-out infinite;
    user-select: none;
}

@keyframes pulseIcon {
    0%, 100% {
        transform: scale(1);
        filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.8));
    }
    50% {
        transform: scale(1.18);
        filter: drop-shadow(0 0 16px rgba(236, 72, 153, 0.9));
    }
}

.processing-header {
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
}

.processing-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
    margin: 0;
}

.processing-stage-pill {
    display: inline-flex;
    align-items: center;
    font-size: 0.74rem;
    font-weight: 600;
    padding: 3px 12px;
    border-radius: 9999px;
    background: rgba(168, 85, 247, 0.16);
    color: #D8B4FE;
    border: 1px solid rgba(168, 85, 247, 0.35);
    letter-spacing: 0.01em;
    transition: all 0.2s ease;
}

.proc-progress-track {
    width: 100%;
    height: 10px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    overflow: hidden;
    position: relative;
    margin-bottom: 16px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.5);
}

.proc-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #8B5CF6 0%, #EC4899 50%, #06B6D4 100%);
    background-size: 200% 100%;
    border-radius: 9999px;
    transition: width 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    animation: shimmerGlow 3s ease infinite;
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.75);
}

@keyframes shimmerGlow {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

.proc-stats-row {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 18px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}

.proc-stat-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.stat-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--studio-text-subtle);
    margin-bottom: 3px;
}

.stat-val {
    font-size: 0.88rem;
    font-weight: 700;
    color: #FFFFFF;
    font-family: monospace;
}

.percent-val {
    color: #C084FC;
    text-shadow: 0 0 12px rgba(192, 132, 252, 0.6);
    font-size: 1.05rem;
}

.proc-steps-list {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
    text-align: left;
    padding: 6px 8px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 10px;
}

.proc-step-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.74rem;
    color: #64748B;
    transition: all 0.25s ease;
}

.proc-step-item.active {
    color: #F1F5F9;
    font-weight: 600;
}

.proc-step-item.completed {
    color: #34D399;
    font-weight: 500;
}

.step-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #334155;
    transition: all 0.25s ease;
    flex-shrink: 0;
}

.proc-step-item.active .step-dot {
    background: #A855F7;
    box-shadow: 0 0 10px #A855F7;
    transform: scale(1.3);
}

.proc-step-item.completed .step-dot {
    background: #10B981;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.7);
}

/* Quick Download Chip in Monitor Header */
.monitor-download-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: #FFFFFF !important;
    text-decoration: none !important;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 9999px;
    box-shadow: 0 2px 10px rgba(16, 185, 129, 0.35);
    transition: all 0.2s ease;
    cursor: pointer;
}
.monitor-download-chip:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.55);
}

/* Dedicated Studio Result Dock */
.studio-result-dock {
    margin-top: 14px;
    background: #080C16;
    border: 1px solid rgba(168, 85, 247, 0.35);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6), 0 0 20px rgba(168, 85, 247, 0.15);
    border-radius: 12px;
    padding: 16px;
    animation: fadeInResultDock 0.4s ease forwards;
}

@keyframes fadeInResultDock {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.result-dock-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 12px;
}

.result-dock-title-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
}

.result-dock-sparkle {
    font-size: 1.4rem;
    color: #A855F7;
    text-shadow: 0 0 12px rgba(168, 85, 247, 0.6);
}

.result-dock-title {
    font-size: 1rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0;
    letter-spacing: -0.01em;
}

.result-dock-sub {
    font-size: 0.72rem;
    color: #94A3B8;
    margin: 2px 0 0 0;
}

.result-dock-actions {
    display: flex;
    align-items: center;
    gap: 10px;
}

.result-btn-download {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #7C3AED 0%, #9333EA 100%);
    color: #FFFFFF !important;
    text-decoration: none !important;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(147, 51, 234, 0.4);
    transition: all 0.2s ease;
    cursor: pointer;
}
.result-btn-download:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(147, 51, 234, 0.6);
}

.result-btn-compare {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #E2E8F0;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 8px 14px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
}
.result-btn-compare:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
}

.result-dock-player-wrap {
    width: 100%;
    background: #030509;
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
"""
