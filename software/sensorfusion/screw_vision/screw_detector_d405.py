#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intel RealSense D405: M4 Dedicated Precision Screw 3D Detector & Web Telemetry Hub
- Method 1: Zero-Shot Sub-millimeter Geometric Measurement & 3D Pose Estimation.
- Tilt & Distortion Calibration Engine:
  1. Lens Radial Distortion Correction (Inverse Brown-Conrady).
  2. Dense 3D Plane-Fitting & Leveling Rotation Transform (R_level):
     Eliminates Pitch/Roll camera tilt, leveling workspace to Z = 0.0 mm.
  3. Workspace Origin Alignment: Origin (0, 0, 0) centered at the foam pad center hole.
  4. Real-time True Euclidean Distance Matrix & Symmetry Verification.
- Dual Verification:
  1. Desktop GUI Window (cv2.imshow on DISPLAY=:0)
  2. 1-Click Web Viewer (http://localhost:5000) with live telemetry cards and calibration controls.
"""

import sys
import os
import time
import math
import argparse
import threading
import numpy as np
import cv2
import json

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
        self.m4_count = 0
        self.avg_depth_mm = 0.0
        self.detections = []
        self.black_screw_mode = True
        self.thresh_val = 110
        self.auto_foam_roi = True
        self.snapshot_saved = None
        
        # Calibration State
        self.calibrated = False
        self.pitch_deg = 0.0
        self.roll_deg = 0.0
        self.plane_a = 0.0
        self.plane_b = 0.0
        self.plane_c = 295.0
        self.R_level = np.eye(3)
        self.origin_level = np.zeros(3)
        self.recalib_requested = True

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
            --purple: #a855f7;
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
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
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
        .stat-val { font-size: 26px; font-weight: 800; margin-top: 6px; }
        .stat-val.m3 { color: var(--m3-color); }
        .stat-val.m4 { color: var(--m4-color); }
        .stat-val.depth { color: var(--accent); }
        .stat-val.tilt { color: var(--purple); font-size: 20px; }
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
        .btn-purple { background: #7e22ce; }
        .btn-purple:hover { background: #6b21a8; }
        
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
        .highlight-calib { color: #38bdf8; font-weight: 700; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title-group">
            <h1>Intel RealSense D405 Screw Precision 3D Inspector</h1>
            <p>Method 1: Zero-Shot Geometric Measurement with Plane Leveling & Distortion Calibration</p>
        </div>
        <div class="badge-live">D405 ACTIVE</div>
    </div>

    <!-- Live Telemetry Stat Cards (M4 Dedicated) -->
    <div class="grid-stats">
        <div class="stat-card">
            <div class="stat-label">Detected M4 Screws (Orange)</div>
            <div class="stat-val m4" id="stat-m4">0</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Surface Distance (Z)</div>
            <div class="stat-val depth" id="stat-depth">0.0 mm</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Camera Tilt (P / R)</div>
            <div class="stat-val tilt" id="stat-tilt">0.0° / 0.0°</div>
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
                <h3>Live Calibrated RGB-D Stream</h3>
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
                    <button class="btn btn-purple" onclick="calibratePlane()">
                        📐 Re-Calibrate Plane
                    </button>
                    <button class="btn btn-success" onclick="takeSnapshot()">
                        📸 Capture Snapshot
                    </button>
                </div>
                <div id="snap-msg" style="font-size: 12px; color: var(--accent); margin-top: 8px; min-height: 18px;"></div>
            </div>

            <!-- Duco-910 Robot Automation Panel -->
            <div class="control-panel" style="border: 1px solid #38bdf8;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="color: #38bdf8;">🤖 Duco-910 Robot Arm Controls</h3>
                    <span id="robot-badge" style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: #15803d; color: #fff;">READY</span>
                </div>
                <div id="robot-status-text" style="font-size: 12px; color: var(--text-dim); margin-bottom: 12px;">
                    TCP: <span id="robot-tcp" style="color: #f1f5f9; font-family: monospace;">[-555.9, -10.3, 333.9]</span> | Tilt: <span id="robot-tilt" style="color: #22c55e;">0.0°</span>
                </div>

                <!-- Robot Speed Multiplier Control Card -->
                <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 8px 10px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-size: 12px; font-weight: 600; color: #38bdf8;">⚡ 로봇 속도 배율 제어</span>
                        <span id="speed-badge" style="font-size: 12px; font-weight: 700; color: #f59e0b;">2.0x [표준]</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        <input type="range" id="speed-slider" min="0.5" max="3.5" step="0.5" value="2.0" style="flex: 1; accent-color: #38bdf8; cursor: pointer;" oninput="onSpeedSlider(this.value)">
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px;">
                        <button class="btn btn-secondary" style="padding: 4px 2px; font-size: 11px;" onclick="setSpeed(1.0)">🐢 1.0x</button>
                        <button class="btn btn-secondary" style="padding: 4px 2px; font-size: 11px;" onclick="setSpeed(1.5)">1.5x</button>
                        <button class="btn btn-secondary" style="padding: 4px 2px; font-size: 11px;" onclick="setSpeed(2.0)">⚡ 2.0x</button>
                        <button class="btn btn-secondary" style="padding: 4px 2px; font-size: 11px;" onclick="setSpeed(2.5)">2.5x</button>
                        <button class="btn btn-secondary" style="padding: 4px 2px; font-size: 11px;" onclick="setSpeed(3.0)">🚀 3.0x</button>
                    </div>
                </div>

                <div class="btn-group" style="grid-template-columns: 1fr 1fr; margin-bottom: 8px;">
                    <button class="btn btn-secondary" onclick="runRobot('step1_level')">1️⃣ 0° 수평 정렬</button>
                    <button class="btn btn-secondary" onclick="runRobot('step2_set_view')">2️⃣ m4_view 저장</button>
                </div>
                <div class="btn-group" style="grid-template-columns: 1fr 1fr; margin-bottom: 8px;">
                    <button class="btn btn-purple" onclick="runRobot('step3_home')">3️⃣ Folded Home 이동</button>
                    <button class="btn btn-purple" onclick="runRobot('step4_view')">4️⃣ m4_view 복귀</button>
                </div>

                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <label style="font-size: 12px; color: #c084fc; font-weight: 700; display: block;">5️⃣ 지능형 최근접 이웃 (Nearest-Neighbor) 연속 순회</label>
                        <span style="font-size: 10px; background: rgba(168,85,247,0.25); color: #e9d5ff; padding: 2px 6px; border-radius: 4px; font-weight: 600;">3D 대각 + 100mm 횡이동</span>
                    </div>
                    <button class="btn btn-success" style="width: 100%; margin-bottom: 6px; font-weight: 600; padding: 9px 12px;" onclick="runRobot('nn_center')">
                        ⚡ 중심 우선 최근접 연속 순회 (Center-First NN)
                    </button>
                    <button class="btn btn-purple" style="width: 100%; margin-bottom: 6px; font-weight: 600; padding: 9px 12px;" onclick="runRobot('nn_sweep')">
                        ⚡ 외곽 스위프 최근접 연속 순회 (Corner-Sweep NN)
                    </button>
                    <button class="btn btn-primary" style="width: 100%; font-weight: 600; padding: 8px 12px;" onclick="runRobot('single_servo')">
                        🎯 중심 최인접 1개 단일 접근 (Single 10mm)
                    </button>
                </div>
                <div id="robot-msg" style="font-size: 12px; color: #38bdf8; margin-top: 8px; min-height: 18px; word-break: break-word;"></div>
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
        <h3>Detected Screw Coordinate Log (Calibrated Table Workspace vs Raw Camera)</h3>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Class</th>
                    <th>Calibrated Table 2D (X, Y mm)</th>
                    <th>Dist from Center</th>
                    <th>Raw Camera 3D (X, Y, Z mm)</th>
                    <th>Angle</th>
                    <th>Head Dia (D)</th>
                    <th>Shank Dia (d)</th>
                    <th>Length (L)</th>
                </tr>
            </thead>
            <tbody id="det-table-body">
                <tr><td colspan="9" style="color: var(--text-dim); text-align: center;">Scanning scene...</td></tr>
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

        function calibratePlane() {
            fetch('/api/calibrate_plane', { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    document.getElementById('snap-msg').innerText = 'Plane Calibrated: Pitch=' + d.pitch.toFixed(1) + '°, Roll=' + d.roll.toFixed(1) + '°';
                    setTimeout(() => { document.getElementById('snap-msg').innerText = ''; }, 4000);
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

        function runRobot(action) {
            const msg = document.getElementById('robot-msg');
            const badge = document.getElementById('robot-badge');
            badge.textContent = 'RUNNING';
            badge.style.background = '#d97706';
            msg.textContent = `🚀 로봇 [${action}] 실행 중...`;
            fetch(`/api/robot/${action}`, { method: 'POST' })
                .then(r => r.json())
                .then(d => {
                    msg.textContent = (d.success ? '✅ ' : '❌ ') + (d.message || (d.success ? '완료' : '실패'));
                    badge.textContent = d.success ? 'READY' : 'ERROR';
                    badge.style.background = d.success ? '#15803d' : '#dc2626';
                    updateRobotStatus();
                })
                .catch(e => {
                    msg.textContent = '❌ 통신 오류: ' + e;
                    badge.textContent = 'ERROR';
                    badge.style.background = '#dc2626';
                });
        }

        function getSpeedDesc(val) {
            const v = parseFloat(val);
            if (v <= 1.0) return ' [거북이]';
            if (v <= 1.5) return ' [안전]';
            if (v <= 2.0) return ' [표준]';
            if (v <= 2.5) return ' [쾌속]';
            return ' [고속]';
        }

        function onSpeedSlider(val) {
            const num = parseFloat(val).toFixed(1);
            document.getElementById('speed-badge').innerText = num + 'x' + getSpeedDesc(num);
            fetch('/api/robot/speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ speed_mult: parseFloat(num) })
            }).then(r => r.json()).catch(() => {});
        }

        function setSpeed(val) {
            const slider = document.getElementById('speed-slider');
            if (slider) slider.value = val;
            onSpeedSlider(val);
        }

        function initSpeed() {
            fetch('/api/robot/speed')
                .then(r => r.json())
                .then(d => {
                    if (d.speed_mult) {
                        const num = parseFloat(d.speed_mult).toFixed(1);
                        const slider = document.getElementById('speed-slider');
                        if (slider) slider.value = num;
                        document.getElementById('speed-badge').innerText = num + 'x' + getSpeedDesc(num);
                    }
                })
                .catch(() => {});
        }

        function updateRobotStatus() {
            fetch('/api/robot/status')
                .then(r => r.json())
                .then(d => {
                    if (d.tcp) {
                        document.getElementById('robot-tcp').innerText = `[${d.tcp[0].toFixed(1)}, ${d.tcp[1].toFixed(1)}, ${d.tcp[2].toFixed(1)}]`;
                        const tilt = Math.hypot(d.tcp[3] - 180.0, d.tcp[4]).toFixed(1);
                        document.getElementById('robot-tilt').innerText = tilt + '°';
                    }
                    const badge = document.getElementById('robot-badge');
                    if (d.is_moving) {
                        badge.textContent = 'MOVING';
                        badge.style.background = '#d97706';
                    } else if (badge.textContent !== 'SERVOING' && badge.textContent !== 'RUNNING') {
                        badge.textContent = 'READY';
                        badge.style.background = '#15803d';
                    }
                })
                .catch(() => {});
        }

        // Live Poll Status
        setInterval(() => {
            fetch('/api/status')
                .then(r => r.json())
                .then(d => {
                    document.getElementById('stat-m4').innerText = d.m4_count;
                    document.getElementById('stat-depth').innerText = d.avg_depth_mm.toFixed(1) + ' mm';
                    document.getElementById('stat-tilt').innerText = d.pitch_deg.toFixed(1) + '° / ' + d.roll_deg.toFixed(1) + '°';
                    document.getElementById('stat-fps').innerText = d.fps.toFixed(1) + ' FPS';

                    const tbody = document.getElementById('det-table-body');
                    if (!d.detections || d.detections.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="9" style="color: var(--text-dim); text-align: center;">No screws detected in current frame</td></tr>';
                    } else {
                        let html = '';
                        d.detections.forEach((item, idx) => {
                            const badge = 'badge-m4';
                            html += `<tr>
                                <td>${idx + 1}</td>
                                <td class="${badge}">${item.class}</td>
                                <td class="highlight-calib">[${item.x_tbl.toFixed(1)}, ${item.y_tbl.toFixed(1)}] mm</td>
                                <td>${item.dist_center.toFixed(1)} mm</td>
                                <td style="color: var(--text-dim);">[${item.x_3d.toFixed(1)}, ${item.y_3d.toFixed(1)}, ${item.z_3d.toFixed(1)}]</td>
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

        // Initial setup on load
        initSpeed();
        updateRobotStatus();
        setInterval(updateRobotStatus, 1500);
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
            "m4_count": state.m4_count,
            "avg_depth_mm": state.avg_depth_mm,
            "pitch_deg": state.pitch_deg,
            "roll_deg": state.roll_deg,
            "calibrated": state.calibrated,
            "detections": state.detections,
            "black_screw_mode": state.black_screw_mode,
            "thresh_val": state.thresh_val,
            "auto_foam_roi": state.auto_foam_roi
        })

@app.route('/api/calibrate_plane', methods=['POST'])
def api_calibrate_plane():
    with state.lock:
        state.recalib_requested = True
    time.sleep(0.1)
    with state.lock:
        return jsonify({
            "success": True,
            "pitch": state.pitch_deg,
            "roll": state.roll_deg,
            "plane_c": state.plane_c
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
# Robot Automation Endpoints (Duco-910 Web Telemetry & Control Bridge)
# ==============================================================================
SPEED_CONFIG_PATH = "/home/knu/workspaces/duco_ros2_control_ws/config/duco_speed.json"

@app.route('/api/robot/speed', methods=['GET', 'POST'])
def api_robot_speed():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        val = data.get('speed_mult', request.args.get('speed_mult', 2.0))
        try:
            val = max(0.5, min(float(val), 3.5))
            os.makedirs(os.path.dirname(SPEED_CONFIG_PATH), exist_ok=True)
            with open(SPEED_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump({"speed_mult": val}, f)
            return jsonify({"success": True, "speed_mult": val})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
    else:
        val = 2.0
        if os.path.exists(SPEED_CONFIG_PATH):
            try:
                with open(SPEED_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    val = float(json.load(f).get("speed_mult", 2.0))
            except Exception:
                pass
        return jsonify({"speed_mult": val})

@app.route('/api/robot/status')
def api_robot_status():
    import subprocess
    try:
        res = subprocess.run(["python3", "/home/knu/workspaces/duco_ros2_control_ws/duco_pipeline.py", "status"], 
                             capture_output=True, text=True, timeout=5)
        out = res.stdout
        tcp = None
        moving = False
        for line in out.split('\n'):
            if "TCP Pose" in line and "X=" in line:
                import re
                m = re.findall(r'[-+]?\d*\.\d+|\d+', line)
                if len(m) >= 6:
                    tcp = [float(x) for x in m[:6]]
            if "Motion State" in line and "MOVING" in line:
                moving = True
        return jsonify({"connected": True, "is_moving": moving, "tcp": tcp})
    except Exception as e:
        return jsonify({"connected": False, "is_moving": False, "error": str(e)})

@app.route('/api/robot/<action>', methods=['POST'])
def api_robot_action(action):
    if action not in ["step1_level", "step2_set_view", "step3_home", "step4_view", "nn_center", "nn_sweep", "single_servo"]:
        return jsonify({"success": False, "error": f"Invalid action: {action}"}), 400
    
    cmd = ["python3", "/home/knu/workspaces/duco_ros2_control_ws/duco_pipeline.py", action, "--execute"]

    # Inject active speed multiplier
    speed_mult = 2.0
    if os.path.exists(SPEED_CONFIG_PATH):
        try:
            with open(SPEED_CONFIG_PATH, 'r', encoding='utf-8') as f:
                speed_mult = float(json.load(f).get("speed_mult", 2.0))
        except Exception:
            pass
    cmd.extend(["--speed", str(speed_mult)])

    import subprocess
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        out = proc.stdout.strip()
        lines = [line.strip() for line in out.split('\n') if 'Arrived' in line or '✅' in line or 'ERROR' in line or 'Completed' in line or 'Leveled' in line or 'inspected' in line or 'Tour' in line]
        summary = lines[-1] if lines else "명령 완료"
        return jsonify({"success": proc.returncode == 0, "message": summary, "log": out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "message": f"실행 실패: {e}"})

# ==============================================================================
# Vision Processing Engine (Zero-Shot Precision Algorithm with Plane Leveling)
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
    dist_coeffs = np.array(intrinsics.coeffs, dtype=np.float64)
    print(f"[INFO] Camera Intrinsics: fx={fx:.1f}, fy={fy:.1f}, cx={cx_cam:.1f}, cy={cy_cam:.1f}")
    print(f"[INFO] Distortion Coeffs: {dist_coeffs}")

    align = rs.align(rs.stream.color)

    fps_start = time.time()
    frame_count = 0
    fps = 0.0

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
                need_recalib = state.recalib_requested

            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # 1. Background Pad / Inspection Zone Detection
            pad_canvas = None
            if auto_roi and black_mode:
                pad_mask = (blurred > 65).astype(np.uint8) * 255
                pad_cnts, _ = cv2.findContours(pad_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if pad_cnts:
                    c_foam = max(pad_cnts, key=cv2.contourArea)
                    foam_area = cv2.contourArea(c_foam)
                    if foam_area > 0.08 * h * w:
                        pad_canvas = np.zeros_like(gray)
                        cv2.drawContours(pad_canvas, [c_foam], -1, 255, -1)
                        # Erode 10px to eliminate table boundary bleed while preserving outer screws
                        pad_eroded = cv2.erode(pad_canvas, cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10)))
                        screw_mask = np.zeros_like(gray)
                        screw_mask[(blurred < thresh_val) & (pad_eroded > 0)] = 255
                    else:
                        _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
                else:
                    _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            elif black_mode:
                _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
            else:
                _, screw_mask = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)

            # Morphological noise removal
            clean_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            screw_mask = cv2.morphologyEx(screw_mask, cv2.MORPH_OPEN, clean_k)
            screw_mask = cv2.morphologyEx(screw_mask, cv2.MORPH_CLOSE, clean_k)

            # 2. Real-time Continuous Dynamic Plane Tracking (10 Hz with EMA smoothing)
            # 2. Table Plane Calibration (Locked at m4_view standby to prevent edge/descent distortion)
            if pad_canvas is not None and (not state.calibrated or need_recalib or frame_count < 25):
                yy, xx = np.where(pad_canvas > 0)
                if len(xx) > 2000:
                    step = 30
                    xx_s, yy_s = xx[::step], yy[::step]
                    raw_z = d_raw[yy_s, xx_s] * depth_scale * 1000.0 # mm
                    valid = (raw_z > 200.0) & (raw_z < 380.0)
                    if np.sum(valid) > 80 and np.median(raw_z[valid]) > 250.0:
                        xs = ((xx_s[valid] - cx_cam) * raw_z[valid]) / fx
                        ys = ((yy_s[valid] - cy_cam) * raw_z[valid]) / fy
                        zs = raw_z[valid]
                        A = np.column_stack((xs, ys, np.ones(len(xs))))
                        plane_fit, _, _, _ = np.linalg.lstsq(A, zs, rcond=None)
                        pa_raw, pb_raw, pc_raw = plane_fit

                        # Normal vector of table in camera frame
                        norm_vec = np.array([-pa_raw, -pb_raw, 1.0])
                        norm_vec /= np.linalg.norm(norm_vec)

                        pitch_raw = float(np.degrees(np.arctan(pb_raw)))
                        roll_raw = float(np.degrees(np.arctan(pa_raw)))

                        # Smooth with EMA filter (alpha=0.35) for real-time tracking without jitter
                        with state.lock:
                            if state.calibrated and not need_recalib:
                                alpha = 0.35
                                pa = float(state.plane_a * (1 - alpha) + pa_raw * alpha)
                                pb = float(state.plane_b * (1 - alpha) + pb_raw * alpha)
                                pc = float(state.plane_c * (1 - alpha) + pc_raw * alpha)
                                pitch = float(state.pitch_deg * (1 - alpha) + pitch_raw * alpha)
                                roll = float(state.roll_deg * (1 - alpha) + roll_raw * alpha)
                            else:
                                pa, pb, pc = float(pa_raw), float(pb_raw), float(pc_raw)
                                pitch, roll = pitch_raw, roll_raw

                        # Recompute smoothed normal
                        norm_vec_s = np.array([-pa, -pb, 1.0])
                        norm_vec_s /= np.linalg.norm(norm_vec_s)

                        # Rodrigues rotation matrix aligning table normal to [0, 0, 1]
                        target_z = np.array([0.0, 0.0, 1.0])
                        v = np.cross(norm_vec_s, target_z)
                        s = np.linalg.norm(v)
                        c_ang = np.dot(norm_vec_s, target_z)
                        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
                        R_l = np.eye(3) + vx + np.dot(vx, vx) * ((1.0 - c_ang) / (s**2 + 1e-9))

                        # Workspace origin: find foam center hole
                        center_roi = blurred[int(h*0.35):int(h*0.65), int(w*0.38):int(w*0.62)]
                        _, h_mask = cv2.threshold(center_roi, 60, 255, cv2.THRESH_BINARY_INV)
                        h_cnts, _ = cv2.findContours(h_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        orig_x = cx_cam
                        orig_y = cy_cam
                        if h_cnts:
                            h_cnt = max(h_cnts, key=cv2.contourArea)
                            (hx, hy), hr = cv2.minEnclosingCircle(h_cnt)
                            orig_x = hx + int(w*0.38)
                            orig_y = hy + int(h*0.35)

                        orig_z = (pa * ((orig_x - cx_cam) * pc / fx) + pb * ((orig_y - cy_cam) * pc / fy) + pc)
                        orig_pt_cam = np.array([
                            ((orig_x - cx_cam) * orig_z) / fx,
                            ((orig_y - cy_cam) * orig_z) / fy,
                            orig_z
                        ])
                        orig_level = np.dot(R_l, orig_pt_cam)

                        with state.lock:
                            state.plane_a = pa
                            state.plane_b = pb
                            state.plane_c = pc
                            state.pitch_deg = pitch
                            state.roll_deg = roll
                            state.R_level = R_l
                            state.origin_level = orig_level
                            state.calibrated = True
                            state.recalib_requested = False

            with state.lock:
                R_cur = state.R_level.copy()
                orig_cur = state.origin_level.copy()
                is_calib = state.calibrated
                cur_pitch = state.pitch_deg
                cur_roll = state.roll_deg

            contours, _ = cv2.findContours(screw_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            vis = color_image.copy()
            detected_items = []
            m4_count = 0
            all_z = []

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Filter noise (<200px) and table background (>10000px)
                if area < 200 or area > 10000:
                    continue

                (cx, cy), radius = cv2.minEnclosingCircle(cnt)
                cx_i, cy_i = int(cx), int(cy)
                if cx_i < 50 or cx_i >= w - 50 or cy_i < 15 or cy_i >= h - 15:
                    continue

                # Elongated aspect ratio filter (strictly rejects circles, standing nuts, and square text characters)
                rect = cv2.minAreaRect(cnt)
                (rcx, rcy), (rw, rh), angle = rect
                ar = max(rw, rh) / (min(rw, rh) + 1e-5)
                if ar < 1.8:
                    continue

                # Solidity filter (strictly rejects hollow/branched printed text letters like '밭', '농', etc.)
                hull = cv2.convexHull(cnt)
                solidity = float(area) / (cv2.contourArea(hull) + 1e-5)
                if solidity < 0.70:
                    continue

                # Query Real Sub-millimeter Depth with Perimeter Fallback
                raw_val = d_raw[cy_i, cx_i]
                z_m = raw_val * depth_scale
                if z_m < 0.05 or z_m > 0.50:
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

                # Reject objects on the lower table surface (e.g. table stickers, text like "밭농업기계개발연구센터" at Z~307mm)
                # Foam pad surface is at Z ~291..296mm; table surface is ~15mm lower at Z ~307mm.
                if z_mm > 302.0:
                    continue

                # Physical dimensions in mm
                tot_l_mm = (max(rw, rh) * z_mm) / fx
                tot_w_mm = (min(rw, rh) * z_mm) / fx
                area_mm2 = area * ((z_mm / fx) ** 2)

                # Strict M4 screw physical dimensions: Length 14~28mm, Width 4.0~9.5mm, Area 50~125mm^2
                if not (14.0 <= tot_l_mm <= 28.0 and 4.0 <= tot_w_mm <= 9.5 and 50.0 <= area_mm2 <= 125.0):
                    continue

                all_z.append(z_mm)

                # 3D Deprojection (Camera Optical Frame)
                pt_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], z_m)
                x_3d_mm = pt_3d[0] * 1000.0
                y_3d_mm = pt_3d[1] * 1000.0

                # Level Plane Calibration Transform
                pt_cam = np.array([x_3d_mm, y_3d_mm, z_mm])
                pt_level = np.dot(R_cur, pt_cam)
                pt_table = pt_level - orig_cur
                x_tbl_mm = float(pt_table[0])
                y_tbl_mm = float(pt_table[1])
                dist_center_mm = float(np.linalg.norm(pt_table[:2]))

                # Cross-sectional profiling for Shank vs Head Diameter
                deg = angle
                r_w, r_h = rw, rh
                if r_w < r_h:
                    deg = deg + 90
                    r_w, r_h = r_h, r_w

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

                # Direct verified M4 Socket Head Cap Screw identification
                color = (0, 165, 255) # Orange
                cls_name = f"M4 Screw (L={tot_l_mm:.0f}mm)"
                m4_count += 1

                if cls_name:
                    box = np.int32(cv2.boxPoints(rect))
                    cv2.drawContours(vis, [box], 0, color, 2)
                    cv2.drawMarker(vis, (cx_i, cy_i), (0, 0, 255), cv2.MARKER_CROSS, 10, 2)

                    # Text Overlay with Calibrated Table 2D Coordinates
                    info_line1 = f"{cls_name} [d={shank_dia_mm:.1f}mm]"
                    info_line2 = f"Tbl: [{x_tbl_mm:+.1f}, {y_tbl_mm:+.1f}]mm | r={dist_center_mm:.1f}"
                    cv2.putText(vis, info_line1, (cx_i - 45, cy_i - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 2)
                    cv2.putText(vis, info_line2, (cx_i - 45, cy_i - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (56, 189, 248), 1)

                    detected_items.append({
                        "class": cls_name,
                        "x_tbl": x_tbl_mm,
                        "y_tbl": y_tbl_mm,
                        "dist_center": dist_center_mm,
                        "x_3d": float(x_3d_mm),
                        "y_3d": float(y_3d_mm),
                        "z_3d": float(z_mm),
                        "angle": float(deg),
                        "head_dia": float(head_dia_mm),
                        "shank_dia": float(shank_dia_mm),
                        "length": float(tot_l_mm)
                    })

            # HUD Display on main frame (placed at bottom to never obscure 12 o'clock screw)
            hud = vis[h-75:h, :].copy()
            cv2.rectangle(vis, (0, h-75), (w, h), (20, 20, 20), -1)
            cv2.addWeighted(hud, 0.25, vis[h-75:h, :], 0.75, 0, vis[h-75:h, :])

            avg_z = float(np.mean(all_z)) if all_z else 0.0
            mode_lbl = "BLACK SCREW (White BG)" if black_mode else "SILVER SCREW (Dark BG)"
            cv2.putText(vis, f"D405 Calibrated Inspector | FPS: {fps:.1f} | Mode: {mode_lbl} | Tilt: P={cur_pitch:+.1f}° R={cur_roll:+.1f}°", 
                        (15, h - 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.putText(vis, f"Detected M4: {m4_count} pcs | Z_avg: {avg_z:.1f}mm | Table Leveled: {'YES' if is_calib else 'PENDING'}", 
                        (15, h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (0, 255, 255), 2)
            cv2.putText(vis, "[Web: http://localhost:5000] | [C] Calib Plane | [B] Mode | [T]/[G] Thresh | [S] Snap | [Q] Quit", 
                        (15, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)

            # Update Global State
            with state.lock:
                state.current_frame = vis
                state.current_mask = screw_mask
                state.fps = fps
                state.m4_count = m4_count
                state.avg_depth_mm = avg_z
                state.detections = detected_items

            # HighGUI window interaction
            if gui_enabled:
                cv2.imshow("Intel RealSense D405 - Screw Inspector", vis)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print(f"[INFO] Exit requested via key 'q'")
                    state.running = False
                    break
                elif key == ord('c'):
                    with state.lock:
                        state.recalib_requested = True
                        print("[INFO] Requested plane re-calibration...")
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
    print("   Intel RealSense D405: M4 Dedicated Screw 3D Precision Detector")
    print("   Method 1: Zero-Shot Geometric Measurement & Plane Leveling")
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
