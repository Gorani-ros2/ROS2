#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intel RealSense D405: M3 / M4 Precision Screw 3D Detector & Web Telemetry Hub
- Method 1: Zero-Shot Sub-millimeter Geometric Measurement & 3D Pose Estimation.
- Standalone: Runs locally on laptop with D405 connected via USB 3.0 (No robot required).
- Dual Verification:
  1. Desktop GUI Window (cv2.imshow on DISPLAY=:0)
  2. 1-Click Web Viewer (http://localhost:5000) with live stream, telemetry cards, and controls.
"""

import sys
import os
import time
import math
import argparse
import threading
import numpy as np
import cv2

try:
    import pyrealsense2 as rs
except ImportError:
    print("[ERROR] pyrealsense2 is not installed!")
    sys.exit(1)

from flask import Flask, Response, render_template_string, jsonify, request
import logging

# Suppress flask request logging in terminal for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ==============================================================================
# Global Shared State for Web & Video Streaming
# ==============================================================================
class VisionState:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = True
        self.current_frame = None
        self.current_mask = None
        self.fps = 0.0
        self.m3_count = 0
        self.m4_count = 0
        self.avg_depth_mm = 0.0
        self.detections = []
        self.black_screw_mode = True
        self.thresh_val = 90
        self.auto_foam_roi = True
        self.snapshot_saved = None

state = VisionState()

# ==============================================================================
# Flask Web Application (1-Click Verification)
# ==============================================================================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D405 M3/M4 Screw 3D Inspector</title>
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: #161f30;
            --border: #243247;
            --text: #f1f5f9;
            --text-dim: #94a3b8;
            --m3-color: #22c55e;
            --m4-color: #f97316;
            --accent: #38bdf8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 20px;
        }
        .title-group h1 { font-size: 22px; font-weight: 700; color: #fff; }
        .title-group p { font-size: 13px; color: var(--text-dim); margin-top: 4px; }
        .badge-live {
            background: #ef4444;
            color: #fff;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .badge-live::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #fff;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.8); }
        }
        .grid-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            position: relative;
        }
        .stat-label { font-size: 13px; color: var(--text-dim); font-weight: 500; }
        .stat-val { font-size: 28px; font-weight: 800; margin-top: 6px; }
        .stat-val.m3 { color: var(--m3-color); }
        .stat-val.m4 { color: var(--m4-color); }
        .stat-val.depth { color: var(--accent); }
        .stat-val.fps { color: #e2e8f0; }
        
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        @media (max-width: 1024px) {
            .main-content { grid-template-columns: 1fr; }
        }
        .feed-container {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        .feed-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .feed-header h3 { font-size: 14px; font-weight: 600; }
        .video-box img {
            width: 100%;
            height: auto;
            display: block;
            background: #000;
        }
        .side-panel {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .control-panel {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px;
        }
        .control-panel h3 { font-size: 15px; font-weight: 600; margin-bottom: 14px; }
        .control-group {
            margin-bottom: 14px;
        }
        .control-group label {
            display: block;
            font-size: 12px;
            color: var(--text-dim);
            margin-bottom: 6px;
        }
        .slider-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .slider-row input[type=range] {
            flex: 1;
            accent-color: var(--accent);
        }
        .slider-val {
            font-size: 14px;
            font-weight: 700;
            width: 40px;
            text-align: right;
        }
        .btn-group {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        .btn {
            flex: 1;
            padding: 9px 12px;
            background: #2563eb;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.15s;
        }
        .btn:hover { background: #1d4ed8; }
        .btn-secondary { background: #334155; }
        .btn-secondary:hover { background: #475569; }
        .btn-success { background: #15803d; }
        .btn-success:hover { background: #166534; }
        
        .table-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            margin-top: 20px;
        }
        .table-card h3 { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th, td {
            text-align: left;
            padding: 8px 10px;
            border-bottom: 1px solid var(--border);
        }
        th { color: var(--text-dim); font-weight: 600; }
        .badge-m3 { color: var(--m3-color); font-weight: 700; }
        .badge-m4 { color: var(--m4-color); font-weight: 700; }
        .badge-gray { color: var(--text-dim); }
    </style>
</head>
<body>
    <div class="header">
        <div class="title-group">
            <h1>Intel RealSense D405 Screw Precision 3D Inspector</h1>
            <p>Method 1: Zero-Shot Geometric Measurement & Sub-millimeter Optical 3D Pose Estimation</p>
        </div>
        <div class="badge-live">D405 ACTIVE</div>
    </div>

    <!-- Live Telemetry Stat Cards -->
    <div class="grid-stats">
        <div class="stat-card">
            <div class="stat-label">M3 Screws (Green)</div>
            <div class="stat-val m3" id="stat-m3">0</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">M4 Screws (Orange)</div>
            <div class="stat-val m4" id="stat-m4">0</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Surface Distance (Z)</div>
            <div class="stat-val depth" id="stat-depth">0.0 mm</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Processing Rate</div>
            <div class="stat-val fps" id="stat-fps">0.0 FPS</div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Live Video Stream -->
        <div class="feed-container">
            <div class="feed-header">
                <h3>Live Annotated RGB-D Stream</h3>
                <span style="font-size: 12px; color: var(--text-dim);">1280 × 720 @ 30fps</span>
            </div>
            <div class="video-box">
                <img src="/video_feed" alt="D405 Screw Stream" id="video-stream">
            </div>
        </div>

        <!-- Controls & Secondary Feed -->
        <div class="side-panel">
            <div class="control-panel">
                <h3>Live Vision Controls</h3>
                
                <div class="control-group">
                    <label>Binary Threshold Value (<span id="thresh-display">90</span>)</label>
                    <div class="slider-row">
                        <input type="range" id="thresh-slider" min="20" max="230" value="90" oninput="updateThresh(this.value)">
                        <span class="slider-val" id="thresh-num">90</span>
                    </div>
                </div>

                <div class="btn-group">
                    <button class="btn btn-secondary" onclick="toggleMode()">
                        Mode: <span id="mode-text">Black Screw</span>
                    </button>
                    <button class="btn btn-secondary" onclick="toggleRoi()">
                        Pad ROI: <span id="roi-text">ON</span>
                    </button>
                </div>

                <div class="btn-group">
                    <button class="btn btn-success" onclick="takeSnapshot()">Capture Snapshot</button>
                </div>
                <div id="snap-msg" style="font-size: 12px; color: var(--accent); margin-top: 8px; min-height: 18px;"></div>
            </div>

            <!-- Binary Inspection Mask Feed -->
            <div class="feed-container">
                <div class="feed-header">
                    <h3>Binary Segmentation Mask</h3>
                </div>
                <div class="video-box">
                    <img src="/mask_feed" alt="D405 Mask Stream" style="height: 200px; object-fit: contain;">
                </div>
            </div>
        </div>
    </div>

    <!-- Detected Screws 3D Pose Table -->
    <div class="table-card">
        <h3>Detected Screw 3D Coordinate Log (Camera Optical Frame)</h3>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Class</th>
                    <th>3D Position (X, Y, Z mm)</th>
                    <th>Angle</th>
                    <th>Head Dia (D)</th>
                    <th>Shank Dia (d)</th>
                    <th>Length (L)</th>
                </tr>
            </thead>
            <tbody id="det-table-body">
                <tr><td colspan="7" style="color: var(--text-dim); text-align: center;">Scanning scene...</td></tr>
            </tbody>
        </table>
    </div>

    <script>
        function updateThresh(val) {
            document.getElementById('thresh-display').innerText = val;
            document.getElementById('thresh-num').innerText = val;
            fetch('/api/set_threshold?val=' + val, { method: 'POST' });
        }

        function toggleMode() {
            fetch('/api/toggle_mode', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    document.getElementById('mode-text').innerText = d.black_screw_mode ? 'Black Screw' : 'Silver Screw';
                });
        }

        function toggleRoi() {
            fetch('/api/toggle_roi', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    document.getElementById('roi-text').innerText = d.auto_foam_roi ? 'ON' : 'OFF';
                });
        }

        function takeSnapshot() {
            fetch('/api/snapshot', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    document.getElementById('snap-msg').innerText = 'Saved: ' + d.filename;
                    setTimeout(() => { document.getElementById('snap-msg').innerText = ''; }, 4000);
                });
        }

        // Live Poll Status
        setInterval(() => {
            fetch('/api/status')
                .then(r => r.json())
                .then(d => {
                    document.getElementById('stat-m3').innerText = d.m3_count;
                    document.getElementById('stat-m4').innerText = d.m4_count;
                    document.getElementById('stat-depth').innerText = d.avg_depth_mm.toFixed(1) + ' mm';
                    document.getElementById('stat-fps').innerText = d.fps.toFixed(1) + ' FPS';

                    const tbody = document.getElementById('det-table-body');
                    if (!d.detections || d.detections.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" style="color: var(--text-dim); text-align: center;">No screws detected in current frame</td></tr>';
                    } else {
                        let html = '';
                        d.detections.forEach((item, idx) => {
                            const badge = item.class.includes('M3') ? 'badge-m3' : (item.class.includes('M4') ? 'badge-m4' : 'badge-gray');
                            html += `<tr>
                                <td>${idx + 1}</td>
                                <td class="${badge}">${item.class}</td>
                                <td>[${item.x_3d.toFixed(1)}, ${item.y_3d.toFixed(1)}, ${item.z_3d.toFixed(1)}] mm</td>
                                <td>${item.angle.toFixed(1)}°</td>
                                <td>${item.head_dia.toFixed(2)} mm</td>
                                <td>${item.shank_dia.toFixed(2)} mm</td>
                                <td>${item.length.toFixed(1)} mm</td>
                            </tr>`;
                        });
                        tbody.innerHTML = html;
                    }
                })
                .catch(() => {});
        }, 300);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def generate_stream(feed_type='video'):
    while True:
        with state.lock:
            if feed_type == 'video':
                frame = state.current_frame
            else:
                frame = state.current_mask

        if frame is None:
            time.sleep(0.03)
            continue

        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            time.sleep(0.01)
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.033)

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream('video'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/mask_feed')
def mask_feed():
    return Response(generate_stream('mask'), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    with state.lock:
        return jsonify({
            "fps": state.fps,
            "m3_count": state.m3_count,
            "m4_count": state.m4_count,
            "avg_depth_mm": state.avg_depth_mm,
            "detections": state.detections,
            "black_screw_mode": state.black_screw_mode,
            "thresh_val": state.thresh_val,
            "auto_foam_roi": state.auto_foam_roi
        })

@app.route('/api/set_threshold', methods=['POST'])
def api_set_threshold():
    val = request.args.get('val', default=90, type=int)
    with state.lock:
        state.thresh_val = max(10, min(250, val))
    return jsonify({"success": True, "thresh_val": state.thresh_val})

@app.route('/api/toggle_mode', methods=['POST'])
def api_toggle_mode():
    with state.lock:
        state.black_screw_mode = not state.black_screw_mode
        mode = state.black_screw_mode
    return jsonify({"success": True, "black_screw_mode": mode})

@app.route('/api/toggle_roi', methods=['POST'])
def api_toggle_roi():
    with state.lock:
        state.auto_foam_roi = not state.auto_foam_roi
        roi = state.auto_foam_roi
    return jsonify({"success": True, "auto_foam_roi": roi})

@app.route('/api/snapshot', methods=['POST'])
def api_snapshot():
    fname = f"d405_screw_snap_{int(time.time())}.png"
    with state.lock:
        if state.current_frame is not None:
            cv2.imwrite(fname, state.current_frame)
            return jsonify({"success": True, "filename": fname})
    return jsonify({"success": False, "error": "No frame available"})

# ==============================================================================
# Vision Processing Engine (Zero-Shot Precision Algorithm)
# ==============================================================================
def run_vision_loop(headless=False):
    print("[INFO] Initializing Intel RealSense D405 Pipeline...")
    pipeline = rs.pipeline()
    config = rs.config()

    # D405 sub-millimeter inspection stream: 1280x720 @ 30fps
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

    profile = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            profile = pipeline.start(config)
            print(f"[INFO] D405 Pipeline started successfully (Attempt {attempt}).")
            break
        except Exception as e:
            print(f"[WARN] Failed to start pipeline on attempt {attempt}: {e}")
            if attempt < max_retries:
                # Hardware reset over USB if busy
                try:
                    ctx = rs.context()
                    for dev in ctx.query_devices():
                        dev.hardware_reset()
                    time.sleep(3)
                except Exception:
                    pass
            else:
                print("[ERROR] Could not start RealSense D405.")
                state.running = False
                return

    # Auto-query depth scale (D405 is 0.0001 = 0.1 mm per unit)
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    print(f"[INFO] D405 Depth Scale: {depth_scale} (0.1 mm precision)")

    # Color stream intrinsics
    color_profile = profile.get_stream(rs.stream.color)
    intrinsics = color_profile.as_video_stream_profile().get_intrinsics()
    fx, fy = intrinsics.fx, intrinsics.fy
    cx_cam, cy_cam = intrinsics.ppx, intrinsics.ppy
    print(f"[INFO] Camera Intrinsics: fx={fx:.1f}, fy={fy:.1f}, cx={cx_cam:.1f}, cy={cy_cam:.1f}")

    align = rs.align(rs.stream.color)

    fps_start = time.time()
    frame_count = 0
    fps = 0.0

    # Display GUI window on DISPLAY=:0 if not headless
    gui_enabled = not headless and ('DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ)
    if gui_enabled:
        try:
            cv2.namedWindow("Intel RealSense D405 - Screw Inspector", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Intel RealSense D405 - Screw Inspector", 1280, 720)
        except Exception:
            gui_enabled = False

    try:
        while state.running:
            try:
                frames = pipeline.wait_for_frames(timeout_ms=3000)
            except RuntimeError as e:
                print(f"[WARN] wait_for_frames timeout: {e}")
                time.sleep(0.05)
                continue

            aligned_frames = align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            frame_count += 1
            if frame_count % 15 == 0:
                fps = 15.0 / (time.time() - fps_start)
                fps_start = time.time()

            color_image = np.asanyarray(color_frame.get_data())
            d_raw = np.asanyarray(depth_frame.get_data()) # 16-bit raw units
            h, w = color_image.shape[:2]

            with state.lock:
                black_mode = state.black_screw_mode
                thresh_val = state.thresh_val
                auto_roi = state.auto_foam_roi

            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # 1. Background Pad / Inspection Zone Detection
            if auto_roi and black_mode:
                # White foam pad / A4 paper is bright (> 70 gray)
                pad_mask = (blurred > 70).astype(np.uint8) * 255
                pad_cnts, _ = cv2.findContours(pad_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if pad_cnts:
                    c_foam = max(pad_cnts, key=cv2.contourArea)
                    foam_area = cv2.contourArea(c_foam)
                    if foam_area > 0.08 * h * w:
                        foam_canvas = np.zeros_like(gray)
                        cv2.drawContours(foam_canvas, [c_foam], -1, 255, -1)
                        # Erode slightly (15px) to eliminate mat border edge noise
                        foam_canvas = cv2.erode(foam_canvas, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
                        screw_mask = np.zeros_like(gray)
                        screw_mask[(blurred < thresh_val) & (foam_canvas > 0)] = 255
                    else:
                        _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
                else:
                    _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            elif black_mode:
                # Pure inverted threshold
                _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            else:
                # Silver screw on dark background
                _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)

            # Morphological noise removal
            clean_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            screw_mask = cv2.morphologyEx(screw_mask, cv2.MORPH_OPEN, clean_k)
            screw_mask = cv2.morphologyEx(screw_mask, cv2.MORPH_CLOSE, clean_k)

            contours, _ = cv2.findContours(screw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            vis = color_image.copy()
            detected_items = []
            m3_count = 0
            m4_count = 0
            all_z = []

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Filter out microscopic noise and massive background regions
                if area < 120 or area > 18000:
                    continue

                (cx, cy), radius = cv2.minEnclosingCircle(cnt)
                cx_i, cy_i = int(cx), int(cy)
                if cx_i < 60 or cx_i >= w - 60 or cy_i < 50 or cy_i >= h - 50:
                    continue

                # Query Real Sub-millimeter Depth with Perimeter Fallback
                raw_val = d_raw[cy_i, cx_i]
                z_m = raw_val * depth_scale
                if z_m < 0.05 or z_m > 0.50:
                    # 1. 5x5 ROI inside contour
                    roi_vals = []
                    for dy in range(-4, 5):
                        for dx in range(-4, 5):
                            nx, ny = cx_i + dx, cy_i + dy
                            if 0 <= nx < w and 0 <= ny < h:
                                v = d_raw[ny, nx] * depth_scale
                                if 0.05 < v < 0.50:
                                    roi_vals.append(v)
                    if roi_vals:
                        z_m = float(np.median(roi_vals))
                    else:
                        # 2. Perimeter fallback (sample white pad around black screw)
                        sample_r = int(radius + 8)
                        for angle_deg in range(0, 360, 45):
                            rad = math.radians(angle_deg)
                            ox = int(cx_i + sample_r * math.cos(rad))
                            oy = int(cy_i + sample_r * math.sin(rad))
                            if 0 <= ox < w and 0 <= oy < h:
                                v = d_raw[oy, ox] * depth_scale
                                if 0.05 < v < 0.50:
                                    roi_vals.append(v)
                        if roi_vals:
                            z_m = float(np.median(roi_vals))
                        else:
                            continue

                z_mm = z_m * 1000.0

                # Physical Area Filter in mm^2 (reject noise < 20mm^2 and holes > 130mm^2)
                area_mm2 = area * ((z_mm / fx) ** 2)
                if area_mm2 < 20.0 or area_mm2 > 130.0:
                    continue

                all_z.append(z_mm)

                # MinAreaRect
                rect = cv2.minAreaRect(cnt)
                (rcx, rcy), (rw, rh), angle = rect
                ar = max(rw, rh) / (min(rw, rh) + 1e-5)
                tot_l_mm = (max(rw, rh) * z_mm) / fx
                tot_w_mm = (min(rw, rh) * z_mm) / fx

                # 3D Deprojection (Camera Optical Frame)
                pt_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], z_m)
                x_3d_mm = pt_3d[0] * 1000.0
                y_3d_mm = pt_3d[1] * 1000.0

                # Cross-sectional profiling for Shank vs Head Diameter
                deg = angle
                r_w, r_h = rw, rh
                if r_w < r_h:
                    deg = deg + 90
                    r_w, r_h = r_h, r_w

                # Local rotated patch
                pad = 40
                bx1, by1 = max(0, cx_i - pad), max(0, cy_i - pad)
                bx2, by2 = min(w, cx_i + pad), min(h, cy_i + pad)
                local_mask = np.zeros((by2 - by1, bx2 - bx1), dtype=np.uint8)
                shifted_cnt = cnt - np.array([bx1, by1])
                cv2.drawContours(local_mask, [shifted_cnt], -1, 255, -1)

                sub_cx, sub_cy = rcx - bx1, rcy - by1
                M = cv2.getRotationMatrix2D((sub_cx, sub_cy), deg, 1.0)
                rotated = cv2.warpAffine(local_mask, M, (local_mask.shape[1], local_mask.shape[0]))
                cols = np.sum(rotated > 0, axis=0)
                active = cols[cols > 3]

                if len(active) > 4:
                    head_px = np.max(active)
                    non_head = active[active < head_px * 0.82]
                    shank_px = np.median(non_head) if len(non_head) > 0 else head_px
                    head_dia_mm = (head_px * z_mm) / fx
                    shank_dia_mm = (shank_px * z_mm) / fx
                else:
                    head_dia_mm = tot_w_mm
                    shank_dia_mm = tot_w_mm

                # Classification Rules (ISO 4762 / DIN 912 Standard)
                cls_name = None
                color = (200, 200, 200)

                # Rejection: Exclude objects that exceed M3/M4 physical dimensions (e.g. table edges, large holes)
                if head_dia_mm > 9.0 or tot_l_mm > 42.0 or tot_l_mm < 6.0:
                    continue

                if ar < 1.35:
                    # Upright Screw Head (facing camera)
                    if 4.8 <= head_dia_mm <= 6.2:
                        cls_name = "M3 Head"
                        color = (0, 255, 0) # Green
                        m3_count += 1
                    elif 6.3 <= head_dia_mm <= 8.8:
                        cls_name = "M4 Head"
                        color = (0, 165, 255) # Orange
                        m4_count += 1
                else:
                    # Lying Screw Body
                    # M3: Shank ~3.0mm (2.4 ~ 3.5), Head ~5.5mm (4.8 ~ 6.2)
                    # M4: Shank ~4.0mm (3.6 ~ 4.8), Head ~7.0mm (6.3 ~ 8.8)
                    if (2.4 <= shank_dia_mm <= 3.5) or (head_dia_mm <= 6.2 and shank_dia_mm < 3.6):
                        cls_name = f"M3 Screw (L={tot_l_mm:.0f}mm)"
                        color = (0, 255, 0)
                        m3_count += 1
                    elif (3.6 <= shank_dia_mm <= 4.8) or (6.3 <= head_dia_mm <= 8.8):
                        cls_name = f"M4 Screw (L={tot_l_mm:.0f}mm)"
                        color = (0, 165, 255)
                        m4_count += 1

                if cls_name:
                    box = np.int32(cv2.boxPoints(rect))
                    cv2.drawContours(vis, [box], 0, color, 2)
                    cv2.drawMarker(vis, (cx_i, cy_i), (0, 0, 255), cv2.MARKER_CROSS, 10, 2)

                    # Text Overlay
                    info_line1 = f"{cls_name}"
                    info_line2 = f"3D: [{x_3d_mm:+.1f}, {y_3d_mm:+.1f}, {z_mm:.1f}]mm | {deg:.0f}deg"
                    cv2.putText(vis, info_line1, (cx_i - 40, cy_i - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
                    cv2.putText(vis, info_line2, (cx_i - 40, cy_i - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 255, 255), 1)

                    detected_items.append({
                        "class": cls_name,
                        "x_3d": float(x_3d_mm),
                        "y_3d": float(y_3d_mm),
                        "z_3d": float(z_mm),
                        "angle": float(deg),
                        "head_dia": float(head_dia_mm),
                        "shank_dia": float(shank_dia_mm),
                        "length": float(tot_l_mm)
                    })

            # HUD Display on main frame
            hud = vis[:75, :].copy()
            cv2.rectangle(vis, (0, 0), (w, 75), (20, 20, 20), -1)
            cv2.addWeighted(hud, 0.25, vis[:75, :], 0.75, 0, vis[:75, :])

            avg_z = float(np.mean(all_z)) if all_z else 0.0
            mode_lbl = "BLACK SCREW (White BG)" if black_mode else "SILVER SCREW (Dark BG)"
            cv2.putText(vis, f"D405 Precision Inspector | FPS: {fps:.1f} | Mode: {mode_lbl} | Thresh: {thresh_val}", 
                        (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)
            cv2.putText(vis, f"Detected: M3 = {m3_count} pcs (Green) | M4 = {m4_count} pcs (Orange) | Z_avg: {avg_z:.1f}mm", 
                        (15, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 255), 2)
            cv2.putText(vis, "[Web: http://localhost:5000] | Keys: [B] Mode | [T]/[G] Thresh | [S] Snap | [Q] Quit", 
                        (15, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)

            # Update Global State
            with state.lock:
                state.current_frame = vis
                state.current_mask = screw_mask
                state.fps = fps
                state.m3_count = m3_count
                state.m4_count = m4_count
                state.avg_depth_mm = avg_z
                state.detections = detected_items

            # HighGUI window interaction
            if gui_enabled:
                cv2.imshow("Intel RealSense D405 - Screw Inspector", vis)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    state.running = False
                    break
                elif key == ord('b'):
                    with state.lock:
                        state.black_screw_mode = not state.black_screw_mode
                        print(f"[INFO] Mode toggled to: {'BLACK' if state.black_screw_mode else 'SILVER'}")
                elif key == ord('t'):
                    with state.lock:
                        state.thresh_val = min(245, state.thresh_val + 5)
                        print(f"[INFO] Thresh: {state.thresh_val}")
                elif key == ord('g'):
                    with state.lock:
                        state.thresh_val = max(15, state.thresh_val - 5)
                        print(f"[INFO] Thresh: {state.thresh_val}")
                elif key == ord('s'):
                    fname = f"d405_screw_snap_{int(time.time())}.png"
                    cv2.imwrite(fname, vis)
                    print(f"[INFO] Saved snapshot: {fname}")

    finally:
        pipeline.stop()
        if gui_enabled:
            cv2.destroyAllWindows()
        print("[INFO] D405 Pipeline stopped successfully.")

def run_flask_app(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    parser = argparse.ArgumentParser(description="Intel RealSense D405 Precision Screw 3D Detector")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode without cv2.imshow")
    parser.add_argument("--port", type=int, default=5000, help="Web interface port (default: 5000)")
    args = parser.parse_args()

    print("==================================================================")
    print("   Intel RealSense D405: M3 / M4 Screw 3D Precision Detector")
    print("   Method 1: Zero-Shot Geometric Measurement & 3D Pose Estimator")
    print("==================================================================")
    print(f"👉 1-Click Verification Web Viewer: http://localhost:{args.port}")
    print("👉 Desktop GUI Window: Open on DISPLAY (Press 'q' in window to exit)")
    print("==================================================================")

    # Start Flask Web Server in Daemon Thread
    f_thread = threading.Thread(target=run_flask_app, args=(args.port,), daemon=True)
    f_thread.start()

    # Run Vision Engine on Main Thread (safe for OpenCV HighGUI & signals)
    try:
        run_vision_loop(headless=args.headless)
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
    finally:
        state.running = False
        print("[INFO] Clean shutdown complete.")

if __name__ == "__main__":
    main()
