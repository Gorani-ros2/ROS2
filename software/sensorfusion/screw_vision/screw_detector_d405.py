#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dedicated Intel RealSense D405 M3/M4 Screw Detector & 3D Pose Estimator
- No robot required! Runs 100% locally on laptop with D405 connected via USB 3.0.
- Uses real-time sub-millimeter Depth from D405 (Optimal range: 7cm ~ 18cm).
- Hardware-aligned RGB-D with zero parallax.
- Zero-Shot: Identifies M3 vs M4 screws and outputs true 3D coordinates (X, Y, Z) in mm.
"""

import sys
import os
import time
import math
import numpy as np
import cv2

try:
    import pyrealsense2 as rs
except ImportError:
    print("[ERROR] pyrealsense2 is not installed!")
    sys.exit(1)

def main():
    print("==================================================================")
    print("   Intel RealSense D405: M3 / M4 Screw 3D Precision Detector")
    print("   (Standalone Desktop Mode - No Robot Required!)")
    print("==================================================================")

    # Initialize RealSense Pipeline
    pipeline = rs.pipeline()
    config = rs.config()

    # D405 Recommended Sub-millimeter Inspection Stream: 1280x720 @ 30fps
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

    print("[INFO] Connecting to Intel RealSense D405...")
    try:
        profile = pipeline.start(config)
    except Exception as e:
        print(f"\n[ERROR] Failed to start RealSense D405 pipeline: {e}")
        print("\n💡 점검 사항:")
        print(" 1. D405 카메라가 노트북의 USB 3.0 / USB-C 포트에 단단히 꽂혀 있는지 확인하세요.")
        print(" 2. 터미널에서 'rs-enumerate-devices -s' 명령어로 카메라 인식을 확인하세요.")
        print(" 3. 'realsense-viewer'로 카메라 펌웨어 및 화면이 정상 출력되는지 테스트할 수 있습니다.")
        sys.exit(1)

    # Align depth to color frame
    align = rs.align(rs.stream.color)
    
    # Obtain camera intrinsic parameters
    color_profile = profile.get_stream(rs.stream.color)
    intrinsics = color_profile.as_video_stream_profile().get_intrinsics()
    fx = intrinsics.fx
    fy = intrinsics.fy
    cx_cam = intrinsics.ppx
    cy_cam = intrinsics.ppy

    print(f"[SUCCESS] D405 Connected! Color Intrinsics: fx={fx:.1f}, fy={fy:.1f}, ppx={cx_cam:.1f}, ppy={cy_cam:.1f}")
    print("\nControls:")
    print("   [S] : Save annotated frame snapshot")
    print("   [Q] : Quit detector")
    print("==================================================================")

    # M3 / M4 Specification Rules (in mm)
    # D405 optimal range: 70mm ~ 180mm
    specs = {
        "M3_HEAD": {"d_min": 4.6, "d_max": 6.1, "color": (0, 255, 0)},     # Green
        "M4_HEAD": {"d_min": 6.3, "d_max": 8.3, "color": (0, 165, 255)},   # Orange
        "M3_BODY": {"w_min": 2.5, "w_max": 3.4, "color": (255, 255, 0)},   # Cyan
        "M4_BODY": {"w_min": 3.6, "w_max": 4.6, "color": (255, 0, 255)},   # Magenta
    }

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    fps_start = time.time()
    frame_count = 0
    fps = 0.0

    try:
        while True:
            frames = pipeline.wait_for_frames(timeout_ms=5000)
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
            h, w = color_image.shape[:2]

            # 1. Preprocessing for metallic reflections
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            enhanced = clahe.apply(gray)
            blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

            # 2. Adaptive / Otsu Thresholding
            # Dark background mat assumption
            _, thresh = cv2.threshold(blurred, 65, 255, cv2.THRESH_BINARY)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
            opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)

            contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            vis = color_image.copy()
            m3_count = 0
            m4_count = 0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 80 or area > 45000:
                    continue

                (cx, cy), radius = cv2.minEnclosingCircle(cnt)
                cx_i, cy_i = int(cx), int(cy)
                if cx_i < 0 or cx_i >= w or cy_i < 0 or cy_i >= h:
                    continue

                # Query Real Sub-millimeter Depth from D405
                # Distance in meters (typically 0.07m ~ 0.20m for close-up)
                z_dist_m = depth_frame.get_distance(cx_i, cy_i)
                if z_dist_m < 0.04 or z_dist_m > 0.45:
                    # Sample median depth in 5x5 ROI if center point had a specular hole
                    roi_z = []
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            nx, ny = cx_i + dx, cy_i + dy
                            if 0 <= nx < w and 0 <= ny < h:
                                d = depth_frame.get_distance(nx, ny)
                                if 0.04 < d < 0.45:
                                    roi_z.append(d)
                    if roi_z:
                        z_dist_m = float(np.median(roi_z))
                    else:
                        continue

                z_dist_mm = z_dist_m * 1000.0

                # Calculate physical diameter using actual D405 depth
                dia_px = radius * 2.0
                dia_mm = (dia_px * z_dist_mm) / fx

                rect = cv2.minAreaRect(cnt)
                (rcx, rcy), (rw, rh), angle = rect
                length_px = max(rw, rh)
                width_px = min(rw, rh)
                aspect_ratio = length_px / (width_px + 1e-5)

                width_mm = (width_px * z_dist_mm) / fx
                length_mm = (length_px * z_dist_mm) / fx

                # Deproject 2D pixel + Depth to real-world 3D camera coordinates (in mm)
                point_3d = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], z_dist_m)
                x_3d_mm = point_3d[0] * 1000.0
                y_3d_mm = point_3d[1] * 1000.0

                cls_name = None
                label = None
                color = (200, 200, 200)

                # Upright Screw Head
                if aspect_ratio < 1.45:
                    if specs["M3_HEAD"]["d_min"] <= dia_mm <= specs["M3_HEAD"]["d_max"]:
                        cls_name = "M3_HEAD"
                        label = f"M3 Head (D={dia_mm:.1f}mm)"
                        color = specs["M3_HEAD"]["color"]
                        m3_count += 1
                    elif specs["M4_HEAD"]["d_min"] <= dia_mm <= specs["M4_HEAD"]["d_max"]:
                        cls_name = "M4_HEAD"
                        label = f"M4 Head (D={dia_mm:.1f}mm)"
                        color = specs["M4_HEAD"]["color"]
                        m4_count += 1

                    if cls_name:
                        cv2.circle(vis, (cx_i, cy_i), int(radius), color, 2)
                        cv2.drawMarker(vis, (cx_i, cy_i), (0, 0, 255), cv2.MARKER_CROSS, 12, 2)
                # Lying Screw Body
                elif aspect_ratio >= 1.7:
                    if specs["M3_BODY"]["w_min"] <= width_mm <= specs["M3_BODY"]["w_max"]:
                        cls_name = "M3_BODY"
                        label = f"M3 Screw (L={length_mm:.1f}, W={width_mm:.1f}mm)"
                        color = specs["M3_BODY"]["color"]
                        m3_count += 1
                    elif specs["M4_BODY"]["w_min"] <= width_mm <= specs["M4_BODY"]["w_max"]:
                        cls_name = "M4_BODY"
                        label = f"M4 Screw (L={length_mm:.1f}, W={width_mm:.1f}mm)"
                        color = specs["M4_BODY"]["color"]
                        m4_count += 1

                    if cls_name:
                        box = np.int0(cv2.boxPoints(rect))
                        cv2.drawContours(vis, [box], 0, color, 2)
                        cv2.drawMarker(vis, (cx_i, cy_i), (0, 0, 255), cv2.MARKER_CROSS, 12, 2)

                if cls_name:
                    coord_str = f"3D: [{x_3d_mm:+.1f}, {y_3d_mm:+.1f}, {z_dist_mm:.1f}] mm"
                    cv2.putText(vis, label, (cx_i - 15, cy_i - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    cv2.putText(vis, coord_str, (cx_i - 15, cy_i - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)

            # HUD Display
            hud = vis[:70, :].copy()
            cv2.rectangle(vis, (0, 0), (w, 70), (20, 20, 20), -1)
            cv2.addWeighted(hud, 0.25, vis[:70, :], 0.75, 0, vis[:70, :])

            cv2.putText(vis, f"Intel RealSense D405 Precision Inspection | FPS: {fps:.1f}", 
                        (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(vis, f"Detected on Desk: M3 = {m3_count} pcs | M4 = {m4_count} pcs", 
                        (15, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

            cv2.imshow("Intel RealSense D405 - Screw Detection", vis)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('s'):
                fname = f"d405_screw_snap_{int(time.time())}.png"
                cv2.imwrite(fname, vis)
                print(f"[INFO] Snapshot saved to: {fname}")

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        print("[INFO] D405 Pipeline stopped.")

if __name__ == '__main__':
    main()
