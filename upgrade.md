# Video Subtitle Remover - Planned Upgrades & Enhancements

## 🎯 Feature Upgrade 1: Interactive In-Browser Draggable Selection Canvas (Option A) — **APPLIED**

### 1. Overview & Objective
Replaced the cumbersome numeric 4-slider coordinate selector with a direct, visual click-and-drag bounding box directly on the video preview image.

### 2. User Experience (UX) Flow
1. **Upload Video**: The first frame of the video automatically renders inside the interactive crop canvas.
2. **Click & Drag**: Click any corner of the subtitle, logo, or banner and drag the mouse across the area.
3. **Bounding Box & Handles**:
   - A glowing translucent bounding box appears with 4 corner adjustment handles (`nw`, `ne`, `se`, `sw`).
   - Drag handles to shrink or expand the box.
   - Click inside the box to reposition/move it anywhere on the frame.
   - Live badge shows `[X, Y] • W × H px` in real time.
4. **Automatic Coordinate Sync**:
   - The pixel dimensions and ROI bounds (`x, y, w, h`) are calculated in real time under the hood.
   - Manual numeric sliders are neatly tucked into an optional "Manual Coordinate Precision" collapsible drawer.
   - Quick presets for **Bottom 18% (Standard)**, **Top 18% (Header)**, **TikTok Watermark (Bottom-Right)**, **TikTok Watermark (Top-Left)**, **Center Banner**, and **Full Frame**.

### 3. Benefits for Daily Workflow
- **Speed**: Mark any text, watermark, or banner region in under 2 seconds.
- **Pixel-Tight Fit**: Prevents accidentally over-selecting background area (eliminating blurry artifacts).
- **Faster AI Inpainting**: Tighter bounding boxes reduce the computation LaMa has to do, cutting processing time per frame.

---

## ✂️ Feature Upgrade 2: Time Range Selection & B-Roll Clip Trimming — **APPLIED**

### 1. Overview & Objective
Allows users to specify a targeted time window (Start Time and End Time in seconds) so the app only processes that exact segment, outputting a cleaned, trimmed clip of just that portion.

### 2. User Experience (UX) Flow
1. **Targeted Processing**:
   - FFmpeg extracts and decodes only the frames within the chosen timeframe (e.g., 6 seconds = 180 frames).
   - Audio is extracted losslessly with millisecond accuracy for that segment.
   - The AI inpainting model runs *only* on those frames instead of the entire video.
2. **Trimmed Output Clip**:
   - The final video output is cut precisely to that selected segment with clean audio.

---

## 🎬 Feature Upgrade 3: CapCut-Style Multi-Track Timeline Trimmer in Step 1 — **APPLIED**

### 1. Overview & Objective
Brings video editing directly under the video player in Step 1 with a rich, interactive CapCut-style timeline. Users can scrub, set In/Out points, drag cut brackets, slide clip windows, preview their cut, and export **only that trimmed part** as the final output.

### 2. User Experience (UX) Flow
1. **CapCut Timeline Strip**:
   - Located directly below the Step 1 video player.
   - Dynamic time ruler with auto-generated tick marks based on video duration.
   - Draggable yellow In-Handle (`[`) and Out-Handle (`]`).
   - Draggable active clip window in the center to slide the cut window across the video.
   - Dimmed overlays over excluded sections outside the cut.
   - Red playhead needle that tracks video playback live and can be dragged to scrub.
2. **CapCut Quick Actions**:
   - **`[ ❮ Set In [ ]`**: Sets start cut to current video playhead.
   - **`[ Set Out ] ❯ ]`**: Sets end cut to current video playhead.
   - **`[ ▶ Play Clip ]`**: Plays only the trimmed segment and automatically pauses at the cut end for instant review.
   - **`[ 🎯 Load into Canvas ]`**: Sends the start cut frame directly to Step 2 so the user can position their subtitle removal box over the text.
   - **`[ ⟲ Reset Full ]`**: Restores the full video selection.
   - **Quick chips**: `+3s`, `+5s`, `+10s`, `+15s` for 1-click clipping.
3. **Live Output Readout & Toggle**:
   - Live badge shows `✂️ Output Clip: 00:08.1 → 00:14.5 (Duration: 6.4s)`.
   - `[ ✓ ] Trim Output Only` switch.
   - Millisecond input fields (`Start Time`, `End Time`, `Clip Length`) two-way bound to the handles.

---

## 🚀 Future Performance Roadmap
- **CUDA / DirectML GPU Acceleration**: Speed up LaMa AI inpainting from ~2s/frame down to ~0.03s/frame.
- **Keyframe Interpolation / Frame Skipping**: Inpaint static captions across keyframes and blend, cutting CPU processing time by 50%+.
- **Multi-Region Support**: Select multiple boxes in a single pass (e.g., top TikTok watermark AND bottom text).
