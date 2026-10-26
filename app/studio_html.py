# -*- coding: utf-8 -*-
"""Pro Studio HTML Template matching v0.dev mockup with adaptive ratio & filmstrip."""

STUDIO_HTML = """
<div class="studio-app">
    <!-- Top Navigation Bar -->
    <header class="studio-nav">
        <div class="nav-left">
            <div class="studio-logo-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="4" width="20" height="16" rx="4"></rect>
                    <path d="m10 9 5 3-5 3V9Z" fill="currentColor"></path>
                </svg>
            </div>
            <div class="studio-title-group">
                <span class="studio-brand-title">Caption Remover <span class="brand-highlight">Studio</span></span>
                <span class="studio-brand-sub">AI VIDEO CLEANUP WORKSPACE</span>
            </div>
        </div>
        <div class="nav-right">
            <div class="status-gpu-pill" id="studio_gpu_status_pill">
                <span class="gpu-dot"></span>
                <span id="studio_gpu_status_text">RTX 2050 CUDA READY</span>
            </div>
            <a href="/download_result" class="nav-export-btn" id="btn_nav_export" download="clean_video.mp4" style="display:none;" title="Download Clean Video (.mp4)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span>Export MP4</span>
            </a>
            <button type="button" class="nav-ghost-btn" id="btn_nav_shortcuts">⌘ Shortcuts</button>
            <button type="button" class="nav-ghost-btn" id="btn_nav_docs">Docs</button>
            <button type="button" class="nav-icon-btn" id="btn_nav_settings" title="Settings">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
            </button>
        </div>
    </header>

    <!-- Subheader: Breadcrumb & Title -->
    <div class="studio-subbar">
        <div class="subbar-left">
            <div class="breadcrumb-tag">PROJECT / CLIP 01</div>
            <h1 class="project-title">Remove captions without leaving a trace.</h1>
        </div>
        <div class="subbar-right">
            <span class="autosaved-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 14.5A4.5 4.5 0 0 0 15 10H14A6 6 0 0 0 2 15a4 4 0 0 0 4 4h13a4.5 4.5 0 0 0 0-9z"></path><path d="m9 15 2 2 4-4"></path></svg>
                Autosaved
            </span>
            <button type="button" class="fit-canvas-btn" id="btn_fit_canvas">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>
                Fit canvas
            </button>
        </div>
    </div>

    <!-- Main Studio Workspace Grid -->
    <div class="studio-workspace">
        <div class="workspace-main">
            <!-- Monitor Frame with Auto-Ratio Support -->
            <div class="monitor-container" id="studio_monitor_frame">
                <div class="monitor-top-meta">
                    <div class="monitor-meta-left">
                        <span class="preview-tag active" id="tab_view_original" title="View Source Video"><span class="green-indicator"></span>PREVIEW / ORIGINAL</span>
                        <span class="result-tag" id="tab_view_result" style="display:none;" title="View Clean Inpainted Output Video"><span class="purple-indicator"></span>✨ CLEAN RESULT</span>
                        <a id="btn_quick_download_top" href="/download_result" class="monitor-download-chip" style="display:none;" download="clean_video.mp4" title="Download Clean Video (.mp4)">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                            <span>Download MP4</span>
                        </a>
                    </div>
                    <div class="monitor-meta-right">
                        <span class="ratio-badge" id="meta_aspect_badge">AUTO RATIO</span>
                        <span class="resolution-tag" id="meta_resolution_fps">Waiting for video...</span>
                    </div>
                </div>
                
                <div class="monitor-viewport" id="studio_monitor_viewport">
                    <div id="video_player_mount">
                        <video id="studio_clean_video_player" class="hidden" controls playsinline style="display: none; width: 100%; height: 100%; object-fit: contain; border-radius: 6px; cursor: pointer; z-index: 25;" title="Clean Result Video Player"></video>
                    </div>

                    <!-- Interactive Floating Pill Bar over video -->
                    <div class="video-floating-pill" id="roi_floating_pill" style="display: none;">
                        <button type="button" class="pill-btn" id="btn_pill_finetune" title="Open Advanced Coordinates Modal">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 7V4h3m10 0h3v3M4 17v3h3m10 0h3v-3"></path><circle cx="12" cy="12" r="3"></circle></svg>
                            Fine tune
                        </button>
                        <div class="pill-divider"></div>
                        <div class="pill-dropdown-wrap">
                            <button type="button" class="pill-btn" id="btn_pill_preset_trigger" title="Select Subtitle Snap Preset">
                                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m6 9 6 6 6-6"></path></svg>
                                <span id="pill_current_preset_label">Bottom subtitle</span>
                            </button>
                            <!-- Dropdown Menu -->
                            <div class="preset-dropdown-menu" id="preset_dropdown_menu">
                                <div class="preset-menu-item active" data-preset="bottom">⬇️ Bottom subtitle (Auto-Fit)</div>
                                <div class="preset-menu-item" data-preset="top">⬆️ Top banner (Auto-Fit)</div>
                                <div class="preset-menu-item" data-preset="tiktok_br">🎴 Watermark (Bottom-Right)</div>
                                <div class="preset-menu-item" data-preset="tiktok_tl">🎴 Watermark (Top-Left)</div>
                                <div class="preset-menu-item" data-preset="center">🎯 Center banner</div>
                                <div class="preset-menu-item" data-preset="full">⏹️ Full frame</div>
                            </div>
                        </div>
                        <div class="pill-divider"></div>
                        <button type="button" class="pill-btn" id="btn_pill_snap" title="Snap to preset">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect width="18" height="18" x="3" y="3" rx="2"></rect><path d="M3 9h18M9 21V9"></path></svg>
                            Snap
                        </button>
                    </div>

                    <!-- AI Processing Overlay with Progress, Percent & Timer -->
                    <div class="processing-overlay" id="studio_processing_overlay" style="display: none;">
                        <div class="processing-card">
                            <div class="processing-spinner-ring">
                                <div class="spinner-core"></div>
                                <span class="processing-ai-icon">✨</span>
                            </div>
                            <div class="processing-header">
                                <h3 class="processing-title">AI Caption Removal in Progress</h3>
                                <span class="processing-stage-pill" id="proc_stage_pill">Initializing neural pipeline...</span>
                            </div>
                            
                            <div class="proc-progress-track">
                                <div class="proc-progress-fill" id="proc_progress_fill" style="width: 5%;"></div>
                            </div>

                            <div class="proc-stats-row">
                                <div class="proc-stat-col">
                                    <span class="stat-label">PROGRESS</span>
                                    <span class="stat-val percent-val" id="proc_percent_text">5%</span>
                                </div>
                                <div class="proc-stat-col">
                                    <span class="stat-label">ELAPSED TIME</span>
                                    <span class="stat-val" id="proc_elapsed_text">00:00</span>
                                </div>
                                <div class="proc-stat-col">
                                    <span class="stat-label">ESTIMATED REMAINING</span>
                                    <span class="stat-val" id="proc_eta_text">Calculating...</span>
                                </div>
                            </div>

                            <div class="proc-steps-list">
                                <div class="proc-step-item active" id="pstep_1">
                                    <span class="step-dot"></span>
                                    <span class="step-label">Step 1: Subtitle detection & mask generation</span>
                                </div>
                                <div class="proc-step-item" id="pstep_2">
                                    <span class="step-dot"></span>
                                    <span class="step-label">Step 2: Temporal anti-flicker smoothing</span>
                                </div>
                                <div class="proc-step-item" id="pstep_3">
                                    <span class="step-dot"></span>
                                    <span class="step-label">Step 3: Neural AI inpainting (LaMa Deep Inpaint)</span>
                                </div>
                                <div class="proc-step-item" id="pstep_4">
                                    <span class="step-dot"></span>
                                    <span class="step-label">Step 4: Seamless frame encode & audio muxing</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Video Transport Bar -->
                <div class="monitor-transport-bar">
                    <div class="transport-left">
                        <button type="button" class="transport-play-btn" id="btn_transport_play" title="Play / Pause (Spacebar)">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
                        </button>
                        <span class="transport-timecode" id="transport_timecode">00:00.0 / 00:00.0</span>
                    </div>
                    <div class="transport-right">
                        <button type="button" class="transport-icon-btn" id="btn_transport_mute" title="Mute / Unmute (M)">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                        </button>
                        <span class="transport-scale-badge" id="transport_scale_badge">100%</span>
                    </div>
                </div>
            </div>

            <!-- Timeline Trimmer Frame with Dynamic Video Thumbnails -->
            <div class="timeline-container">
                <div class="timeline-top-bar">
                    <div class="timeline-left-title">
                        <span class="timeline-tag-label">TIMELINE / TRIMMER</span>
                        <span class="timeline-sequence-name" id="timeline_sequence_info">Source sequence • 00:00.0</span>
                    </div>
                    <div class="timeline-right-tools">
                        <button type="button" class="timeline-tool-btn" id="btn_timeline_zoom_out" title="Zoom Out Timeline">− Zoom</button>
                        <button type="button" class="timeline-tool-btn" id="btn_timeline_zoom_in" title="Zoom In Timeline">+ Zoom</button>
                        <span class="timeline-tracks-btn"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg> Tracks</span>
                    </div>
                </div>

                <!-- Interactive Filmstrip Track with Canvas Thumbnails -->
                <div class="timeline-track-viewport" id="capcut_track_wrapper" title="Click anywhere to scrub playhead">
                    <!-- Dynamic Ticks Along Ruler -->
                    <div class="capcut-ruler" id="capcut_ruler"></div>

                    <!-- Dynamic Filmstrip Thumbnails Canvas Container -->
                    <div class="capcut-track-track" id="capcut_track_thumbnails"></div>

                    <!-- Dimmed Left & Right Cut Offs -->
                    <div class="capcut-dim capcut-dim-left" id="capcut_dim_left"></div>
                    <div class="capcut-dim capcut-dim-right" id="capcut_dim_right"></div>

                    <!-- Draggable Clip Window with Golden Handles -->
                    <div class="capcut-clip" id="capcut_clip">
                        <div class="capcut-handle capcut-handle-left" id="capcut_handle_left" title="Drag to adjust Start Cut">❮</div>
                        <div class="capcut-clip-body" id="capcut_clip_body" title="Drag to slide clip window">
                            <span class="capcut-clip-len" id="capcut_clip_len">0.0s</span>
                        </div>
                        <div class="capcut-handle capcut-handle-right" id="capcut_handle_right" title="Drag to adjust End Cut">❯</div>
                    </div>

                    <!-- Red Playhead Line -->
                    <div class="capcut-playhead" id="capcut_playhead">
                        <div class="capcut-playhead-pin"></div>
                        <div class="capcut-playhead-line"></div>
                        <div class="capcut-playhead-badge" id="capcut_playhead_badge">00:00.0</div>
                    </div>
                </div>

                <!-- Timeline Bottom Controls -->
                <div class="timeline-bottom-controls">
                    <div class="controls-left-btns">
                        <button type="button" class="studio-btn-subtle" id="capcut_btn_set_in" title="Set In point ([)">Set In [</button>
                        <button type="button" class="studio-btn-subtle" id="capcut_btn_set_out" title="Set Out point (])">Set Out ]</button>
                        <button type="button" class="studio-btn-play" id="capcut_btn_preview">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
                            Play selected clip
                        </button>
                    </div>
                    <div class="controls-right-extend">
                        <span class="extend-label">Extend:</span>
                        <button type="button" class="extend-chip" data-dur="3">+3s</button>
                        <button type="button" class="extend-chip" data-dur="5">+5s</button>
                        <button type="button" class="extend-chip" data-dur="10">+10s</button>
                        <div class="trim-toggle-wrap">
                            <span class="trim-toggle-label">Trim output only</span>
                            <label class="studio-switch">
                                <input type="checkbox" id="capcut_trim_toggle" checked>
                                <span class="studio-switch-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dedicated Output & Download Tray (Appears upon pipeline completion) -->
            <div class="studio-result-dock" id="studio_result_dock" style="display: none;">
                <div class="result-dock-header">
                    <div class="result-dock-title-wrap">
                        <span class="result-dock-sparkle">✨</span>
                        <div>
                            <h3 class="result-dock-title">Clean Output Video Ready</h3>
                            <p class="result-dock-sub" id="result_dock_filename">Captions removed cleanly with AI</p>
                        </div>
                    </div>
                    <div class="result-dock-actions">
                        <a id="btn_dock_download_video" href="/download_result" class="result-btn-download" download="clean_video.mp4" title="Download Clean Video (.mp4)">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                            <span>Download Clean Video (.mp4)</span>
                        </a>
                        <button type="button" class="result-btn-compare" id="btn_dock_compare">
                            <span>✦ Compare Before / After</span>
                        </button>
                    </div>
                </div>
                <!-- Embedded Direct Clean Player -->
                <div class="result-dock-player-wrap">
                    <video id="dock_clean_video_player" controls playsinline preload="auto" style="width: 100%; max-height: 420px; border-radius: 8px; background: #000000; outline: none;"></video>
                </div>
            </div>
        </div>

        <!-- Inspector Dock (Right Column) -->
        <aside class="workspace-inspector">
            <div class="inspector-header">
                <div>
                    <span class="inspector-tag-label">INSPECTOR</span>
                    <h2 class="inspector-title">Removal settings</h2>
                </div>
                <button type="button" class="inspector-reset-btn" id="btn_inspector_reset">↺ Reset</button>
            </div>

            <!-- Section 01: Caption & watermark style -->
            <div class="inspector-section">
                <div class="section-title-row">
                    <span class="section-num">01</span>
                    <span class="section-title">Caption & watermark style</span>
                </div>
                <p class="section-desc">Choose the visual signature to remove.</p>
                <div class="style-card-grid">
                    <!-- Card 1: White text + dark stroke -->
                    <div class="style-card active" data-style="white_stroke" id="card_style_white_stroke">
                        <span class="style-card-check">✓</span>
                        <div class="style-card-icon stroke-text-icon">Aa</div>
                        <span class="style-card-label">White text + outline / shadow</span>
                    </div>
                    <!-- Card 2: Pure white text -->
                    <div class="style-card" data-style="white" id="card_style_white">
                        <span class="style-card-check" style="display:none;">✓</span>
                        <div class="style-card-icon pure-white-icon">Aa</div>
                        <span class="style-card-label">Pure white text / logo</span>
                    </div>
                    <!-- Card 3: Dark text -->
                    <div class="style-card" data-style="black" id="card_style_black">
                        <span class="style-card-check" style="display:none;">✓</span>
                        <div class="style-card-icon dark-text-icon">Aa</div>
                        <span class="style-card-label">Dark text</span>
                    </div>
                    <!-- Card 4: Colored box banner -->
                    <div class="style-card" data-style="colored_box" id="card_style_colored_box">
                        <span class="style-card-check" style="display:none;">✓</span>
                        <div class="style-card-icon banner-box-icon"><span class="box-inner"></span></div>
                        <span class="style-card-label">Colored box banner</span>
                    </div>
                    <!-- Card 5: Watermark / logo area -->
                    <div class="style-card card-full-span" data-style="full_box" id="card_style_full_box">
                        <span class="style-card-check" style="display:none;">✓</span>
                        <div class="style-card-icon shield-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                        </div>
                        <span class="style-card-label">Watermark / logo area</span>
                    </div>
                </div>
            </div>

            <!-- Section 02: Inpainting model -->
            <div class="inspector-section">
                <div class="section-title-row">
                    <span class="section-num">02</span>
                    <span class="section-title">Inpainting model</span>
                </div>
                <p class="section-desc">Balance speed and reconstruction quality.</p>
                <div class="inpaint-card-grid">
                    <!-- Fast Mode -->
                    <div class="inpaint-card" data-mode="fast" id="card_mode_fast">
                        <div class="inpaint-card-icon yellow-bolt">⚡</div>
                        <div class="inpaint-card-text">
                            <span class="inpaint-title">Fast mode</span>
                            <span class="inpaint-sub">OpenCV</span>
                        </div>
                    </div>
                    <!-- Quality AI (Selected) -->
                    <div class="inpaint-card active" data-mode="quality" id="card_mode_quality">
                        <div class="inpaint-card-icon purple-sparkle">✨</div>
                        <div class="inpaint-card-text">
                            <span class="inpaint-title">Quality AI</span>
                            <span class="inpaint-sub">LaMa deep neural</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section 03: Precision tuning -->
            <div class="inspector-section">
                <div class="section-title-row">
                    <span class="section-num">03</span>
                    <span class="section-title">Precision tuning</span>
                </div>
                <p class="section-desc">Anti-blur defaults for smooth, artifact-free removal.</p>
                <div class="tuning-slider-group">
                    <!-- Slider 1: Mask Dilation (Keep 3-4 px) -->
                    <div class="tuning-row">
                        <div class="tuning-label-wrap">
                            <span class="tuning-label">Mask dilation</span>
                            <span class="tuning-hint">3–4 px (clean drop-shadow absorption)</span>
                        </div>
                        <span class="tuning-val" id="val_mask_dilation">3 px</span>
                    </div>
                    <input type="range" min="1" max="6" value="3" step="1" class="studio-range" id="input_mask_dilation">

                    <!-- Slider 2: LaMa Extra Padding (Keep 2 px) -->
                    <div class="tuning-row" style="margin-top: 14px;">
                        <div class="tuning-label-wrap">
                            <span class="tuning-label">LaMa extra padding</span>
                            <span class="tuning-hint">Keep 2 px (smooth skin blending)</span>
                        </div>
                        <span class="tuning-val" id="val_lama_extra">2 px</span>
                    </div>
                    <input type="range" min="0" max="6" value="2" step="1" class="studio-range" id="input_lama_extra">

                    <!-- Slider 3: Temporal Anti-Flicker (10-14 recommended) -->
                    <div class="tuning-row" style="margin-top: 14px;">
                        <div class="tuning-label-wrap">
                            <span class="tuning-label">Temporal anti-flicker</span>
                            <span class="tuning-hint">10–14 unifies animated captions</span>
                        </div>
                        <span class="tuning-val" id="val_temporal_window">12</span>
                    </div>
                    <input type="range" min="1" max="24" value="12" step="1" class="studio-range" id="input_temporal_window">
                </div>
            </div>

            <!-- Advanced pixel coordinates trigger button -->
            <div class="advanced-coords-row" id="btn_open_coords_modal">
                <div class="advanced-left">
                    <span class="chevron-arrow">›</span>
                    <span>Advanced pixel coordinates</span>
                </div>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>

            <!-- Bottom CTA Area -->
            <div class="inspector-cta-area">
                <div class="estimated-time-row">
                    <span class="est-label">ESTIMATED PROCESSING</span>
                    <span class="est-val" id="estimated_time_text">~ 18 seconds</span>
                </div>

                <button type="button" class="studio-cta-btn" id="btn_studio_remove_captions">
                    <div class="cta-progress-fill" id="cta_btn_progress_fill" style="width: 0%;"></div>
                    <span class="cta-sparkle" id="cta_sparkle_icon">✨</span>
                    <span id="cta_btn_label">Remove captions</span>
                    <span class="cta-duration-pill" id="cta_clip_duration_pill">7.2s</span>
                </button>

                <div class="compare-link-row">
                    <button type="button" class="compare-modal-btn" id="btn_open_compare_modal">
                        <span class="sparkle-star">✦</span>
                        <span>Compare before & after</span>
                    </button>
                </div>
            </div>
        </aside>
    </div>

    <!-- MODAL 1: Advanced Pixel Coordinates (Screenshot 3) -->
    <div class="studio-modal-backdrop" id="modal_advanced_coords" style="display: none;">
        <div class="studio-modal-card coords-modal-card">
            <div class="modal-header">
                <div>
                    <span class="modal-tag-label">ROI PRECISION</span>
                    <h3 class="modal-title">Advanced pixel coordinates</h3>
                </div>
                <button type="button" class="modal-close-btn" id="btn_close_coords_modal">✕</button>
            </div>
            <p class="modal-desc">Define the exact region to mask. Values are relative to the source frame.</p>
            
            <div class="coords-input-grid">
                <div class="coord-field">
                    <label class="coord-label">Left X</label>
                    <div class="coord-input-wrap">
                        <input type="number" id="modal_input_lx" min="0" value="120">
                        <span class="coord-unit">px</span>
                    </div>
                </div>
                <div class="coord-field">
                    <label class="coord-label">Bottom Y</label>
                    <div class="coord-input-wrap">
                        <input type="number" id="modal_input_by" min="0" value="1650">
                        <span class="coord-unit">px</span>
                    </div>
                </div>
                <div class="coord-field">
                    <label class="coord-label">Right X</label>
                    <div class="coord-input-wrap">
                        <input type="number" id="modal_input_rx" min="0" value="960">
                        <span class="coord-unit">px</span>
                    </div>
                </div>
                <div class="coord-field">
                    <label class="coord-label">Top Y</label>
                    <div class="coord-input-wrap">
                        <input type="number" id="modal_input_ty" min="0" value="1830">
                        <span class="coord-unit">px</span>
                    </div>
                </div>
            </div>

            <div class="modal-bottom-actions">
                <button type="button" class="modal-reset-btn" id="btn_modal_coords_reset">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
                    Reset to detected region
                </button>
                <button type="button" class="modal-apply-btn" id="btn_modal_coords_apply">
                    <span>✦</span> Apply region
                </button>
            </div>
        </div>
    </div>

    <!-- MODAL 2: Before / After Comparison (Screenshot 2) -->
    <div class="studio-modal-backdrop" id="modal_comparison_view" style="display: none;">
        <div class="studio-modal-card compare-modal-card">
            <div class="modal-header">
                <div>
                    <span class="modal-tag-label">COMPARISON VIEW</span>
                    <h3 class="modal-title">Before / After</h3>
                </div>
                <button type="button" class="modal-close-btn" id="btn_close_compare_modal">✕</button>
            </div>

            <!-- Split Screen Slider Viewport -->
            <div class="split-slider-viewport" id="split_slider_viewport">
                <!-- Original Layer (Bottom Layer) -->
                <div class="split-layer split-layer-original">
                    <video id="compare_vid_original" playsinline muted style="width: 100%; height: 100%; object-fit: contain; pointer-events: none;"></video>
                    <img id="compare_img_original" src="" alt="Original Video Frame" style="display: none; width: 100%; height: 100%; object-fit: contain;">
                    <span class="compare-badge badge-orig">ORIGINAL (WITH CAPTIONS)</span>
                </div>
                <!-- Clean Inpainted Layer (Top Layer, clipped by split percentage) -->
                <div class="split-layer split-layer-clean" id="split_layer_clean">
                    <video id="compare_vid_clean" playsinline muted style="width: 100%; height: 100%; object-fit: contain; pointer-events: none;"></video>
                    <img id="compare_img_clean" src="" alt="Clean Inpainted Output" style="display: none; width: 100%; height: 100%; object-fit: contain;">
                    <span class="compare-badge badge-clean">✨ CLEAN RESULT (REPAIRED)</span>
                </div>
                <!-- Draggable Divider Line & Knob -->
                <div class="split-divider-line" id="split_divider_line">
                    <div class="split-knob">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </div>
                </div>
            </div>

            <div class="compare-modal-footer">
                <button type="button" class="studio-btn-play" id="btn_compare_play_toggle" style="margin: 0 auto 8px auto; padding: 6px 18px; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
                    <span id="compare_play_label">Play comparison in sync</span>
                </button>
                <p class="modal-bottom-hint">Drag the slider horizontally to compare before vs after removal.</p>
            </div>
        </div>
    </div>

    <!-- MODAL 3: Keyboard Shortcuts Modal -->
    <div class="studio-modal-backdrop" id="modal_shortcuts_guide" style="display: none;">
        <div class="studio-modal-card shortcuts-modal-card">
            <div class="modal-header">
                <div>
                    <span class="modal-tag-label">PRO WORKFLOW</span>
                    <h3 class="modal-title">Keyboard Shortcuts</h3>
                </div>
                <button type="button" class="modal-close-btn" id="btn_close_shortcuts_modal">✕</button>
            </div>
            <div class="shortcuts-list">
                <div class="shortcut-item">
                    <span class="shortcut-desc">Play / Pause video preview</span>
                    <kbd class="shortcut-kbd">Space</kbd>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-desc">Set In Point at current playhead</span>
                    <kbd class="shortcut-kbd">[</kbd>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-desc">Set Out Point at current playhead</span>
                    <kbd class="shortcut-kbd">]</kbd>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-desc">Mute / Unmute audio</span>
                    <kbd class="shortcut-kbd">M</kbd>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-desc">Fit canvas / Reset zoom</span>
                    <kbd class="shortcut-kbd">F</kbd>
                </div>
                <div class="shortcut-item">
                    <span class="shortcut-desc">Close any modal</span>
                    <kbd class="shortcut-kbd">Esc</kbd>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL 4: Documentation Quick Guide -->
    <div class="studio-modal-backdrop" id="modal_docs_guide" style="display: none;">
        <div class="studio-modal-card docs-modal-card">
            <div class="modal-header">
                <div>
                    <span class="modal-tag-label">KNOWLEDGE BASE</span>
                    <h3 class="modal-title">Caption Remover Guide</h3>
                </div>
                <button type="button" class="modal-close-btn" id="btn_close_docs_modal">✕</button>
            </div>
            <div class="docs-content">
                <div class="docs-block">
                    <h4>⚡ Inpainting Engines</h4>
                    <p><strong>Fast Mode (OpenCV Telea):</strong> Completes in seconds. Ideal for quick drafts or videos with plain solid backgrounds.</p>
                    <p><strong>Quality AI (LaMa Deep Neural):</strong> SOTA deep resolution-robust inpainter. Synthesizes photorealistic textures and patterns behind erased subtitles.</p>
                </div>
                <div class="docs-block">
                    <h4>⚙️ Precision Tuning</h4>
                    <p><strong>Mask Dilation (2–4 px):</strong> Controls how tightly the mask wraps around letters. Keeping it around 3–4 px preserves background sharpness without ghost outlines.</p>
                    <p><strong>Temporal Anti-Flicker (10–14):</strong> Prevents flickering across consecutive frames, especially for animated or karaoke style captions.</p>
                </div>
            </div>
        </div>
    </div>
</div>
"""
