#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Geometric Screw Detector (M3 & M4)
No training dataset required - Zero-Shot physical measurement via Camera Geometry
Supported:
  - DIN 912 (Socket Head Cap Screw / 렌치볼트): M3 Head ~5.5mm, M4 Head ~7.0mm
  - DIN 7985 (Pan Head / 둥근머리볼트): M3 Head ~5.6mm, M4 Head ~8.0mm
  - DIN 933 (Hex Bolt / 육각볼트): M3 Head 5.5mm, M4 Head 7.0mm
  - Lying screws: Body diameter M3 ~3.0mm, M4 ~4.0mm
"""

import sys
import os
import time
import math
import argparse
import numpy as np
import cv2

def parse_args():
    parser = argparse.ArgumentParser(description="M3/M4 Screw Geometric Detector")
    parser.add_argument("--camera", type=int, default=0, help="V4L2 camera index (/dev/videoN)")
    parser.add_argument("--distance", type=float, default=150.0, help="Camera height Z above workspace in mm (default: 150mm)")
    parser.add_argument("--focal", type=float, default=950.0, help="Focal length in pixels (fx/fy). Default 950 for typical 720p/1080p webcams")
    parser.add_argument("--dark-bg", action="store_true", default=True, help="Set True if using black/dark mat (recommended for metallic screws)")
    parser.add_argument("--save-dir", type=str, default="./captured_screws", help="Directory to save labeled samples")
    return parser.parse_args()

class ScrewDetector:
    def __init__(self, distance_mm=150.0, focal_px=950.0, dark_bg=True):
        self.distance_mm = distance_mm
        self.focal_px = focal_px
        self.dark_bg = dark_bg
        
        # CLAHE for specular reflection suppression
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        
        # M3 / M4 Specification Thresholds (in mm)
        self.specs = {
            "M3_HEAD": {"d_min": 4.6, "d_max": 6.1, "color": (0, 255, 0)},     # Green
            "M4_HEAD": {"d_min": 6.3, "d_max": 8.3, "color": (0, 165, 255)},   # Orange
            "M3_BODY": {"w_min": 2.5, "w_max": 3.4, "color": (255, 255, 0)},   # Cyan
            "M4_BODY": {"w_min": 3.6, "w_max": 4.6, "color": (255, 0, 255)},   # Magenta
        }

    def px_to_mm(self, px):
        return (px * self.distance_mm) / self.focal_px

    def mm_to_px(self, mm):
        return (mm * self.focal_px) / self.distance_mm

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE to balance metallic highlights
        enhanced = self.clahe.apply(gray)
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        # Thresholding
        if self.dark_bg:
            # Metallic screw is brighter than black pad
            _, thresh = cv2.threshold(blurred, 65, 255, cv2.THRESH_BINARY)
        else:
            # Screw is darker than light table
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
        # Morphology (close small holes from hex socket / reflections)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter out tiny specks (< 1.5mm diameter) or huge objects
            min_area_px = math.pi * ((self.mm_to_px(1.5) / 2) ** 2)
            max_area_px = math.pi * ((self.mm_to_px(25.0) / 2) ** 2)
            if area < min_area_px or area > max_area_px:
                continue
                
            # Minimum enclosing circle & bounding rotated rectangle
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            dia_px = radius * 2.0
            dia_mm = self.px_to_mm(dia_px)
            
            rect = cv2.minAreaRect(cnt)
            (rcx, rcy), (rw, rh), angle = rect
            
            # Ensure rw is length, rh is width
            length_px = max(rw, rh)
            width_px = min(rw, rh)
            aspect_ratio = length_px / (width_px + 1e-5)
            
            length_mm = self.px_to_mm(length_px)
            width_mm = self.px_to_mm(width_px)
            
            label = None
            color = (200, 200, 200)
            det_type = "unknown"
            
            # 1. Check for Upright Screw Head (Aspect ratio close to 1.0)
            if aspect_ratio < 1.45:
                det_type = "head"
                if self.specs["M3_HEAD"]["d_min"] <= dia_mm <= self.specs["M3_HEAD"]["d_max"]:
                    label = f"M3 Head (D={dia_mm:.1f}mm)"
                    color = self.specs["M3_HEAD"]["color"]
                    cls_name = "M3_HEAD"
                elif self.specs["M4_HEAD"]["d_min"] <= dia_mm <= self.specs["M4_HEAD"]["d_max"]:
                    label = f"M4 Head (D={dia_mm:.1f}mm)"
                    color = self.specs["M4_HEAD"]["color"]
                    cls_name = "M4_HEAD"
                else:
                    label = f"Round (D={dia_mm:.1f}mm)"
                    cls_name = "UNKNOWN_HEAD"
            # 2. Check for Lying Screw Body (Aspect ratio >= 1.7)
            elif aspect_ratio >= 1.7:
                det_type = "lying"
                if self.specs["M3_BODY"]["w_min"] <= width_mm <= self.specs["M3_BODY"]["w_max"]:
                    label = f"M3 Screw (L={length_mm:.1f}, W={width_mm:.1f}mm)"
                    color = self.specs["M3_BODY"]["color"]
                    cls_name = "M3_BODY"
                elif self.specs["M4_BODY"]["w_min"] <= width_mm <= self.specs["M4_BODY"]["w_max"]:
                    label = f"M4 Screw (L={length_mm:.1f}, W={width_mm:.1f}mm)"
                    color = self.specs["M4_BODY"]["color"]
                    cls_name = "M4_BODY"
                else:
                    label = f"Rod (W={width_mm:.1f}mm)"
                    cls_name = "UNKNOWN_BODY"
                    
            if label:
                detections.append({
                    "class": cls_name,
                    "label": label,
                    "color": color,
                    "type": det_type,
                    "center": (int(cx), int(cy)),
                    "diameter_mm": dia_mm,
                    "width_mm": width_mm,
                    "length_mm": length_mm,
                    "angle": angle if rw >= rh else angle + 90,
                    "contour": cnt,
                    "rect": rect,
                    "radius": radius
                })
                
        return detections, opened

def main():
    args = parse_args()
    os.makedirs(args.save_dir, exist_ok=True)
    
    print("==================================================================")
    print("       Duco-910 Vision: M3 / M4 Screw Geometric Detector")
    print("==================================================================")
    print(f" Camera Index     : /dev/video{args.camera}")
    print(f" Working Height Z : {args.distance} mm")
    print(f" Focal Length fx  : {args.focal} px")
    print(f" Dark Background  : {args.dark_bg}")
    print(f" Save Directory   : {args.save_dir}")
    print(" Controls:")
    print("   [+] / [-] : Increase / Decrease working distance Z by 5mm")
    print("   [S]       : Save current frame & crop labeled dataset")
    print("   [Q]       : Quit")
    print("==================================================================")
    
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera /dev/video{args.camera}!")
        print("Tip: Run 'ls -l /dev/video*' or 'v4l2-ctl --list-devices' to check index.")
        sys.exit(1)
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    detector = ScrewDetector(distance_mm=args.distance, focal_px=args.focal, dark_bg=args.dark_bg)
    
    fps_start = time.time()
    frame_count = 0
    fps = 0.0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to read frame from camera.")
            time.sleep(0.05)
            continue
            
        frame_count += 1
        if frame_count % 15 == 0:
            fps = 15.0 / (time.time() - fps_start)
            fps_start = time.time()
            
        detections, binary_mask = detector.process_frame(frame)
        
        # Visual Annotations
        vis = frame.copy()
        
        m3_count = 0
        m4_count = 0
        
        for det in detections:
            cx, cy = det["center"]
            color = det["color"]
            label = det["label"]
            
            if "M3" in det["class"]:
                m3_count += 1
            elif "M4" in det["class"]:
                m4_count += 1
                
            if det["type"] == "head":
                # Draw circle & center cross
                cv2.circle(vis, (cx, cy), int(det["radius"]), color, 2)
                cv2.drawMarker(vis, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 12, 2)
            else:
                # Draw oriented bounding box
                box = cv2.boxPoints(det["rect"])
                box = np.int0(box)
                cv2.drawContours(vis, [box], 0, color, 2)
                cv2.drawMarker(vis, (cx, cy), (0, 0, 255), cv2.MARKER_CROSS, 12, 2)
                
                # Draw orientation line
                angle_rad = math.radians(det["angle"])
                line_len = 25
                x2 = int(cx + line_len * math.cos(angle_rad))
                y2 = int(cy + line_len * math.sin(angle_rad))
                cv2.line(vis, (cx, cy), (x2, y2), (0, 255, 255), 2)
                
            # Text background & label
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(vis, (cx - 10, cy - th - 12), (cx - 10 + tw + 6, cy - 2), (20, 20, 20), -1)
            cv2.putText(vis, label, (cx - 8, cy - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
        # Top HUD Banner
        hud_bg = vis[:75, :].copy()
        cv2.rectangle(vis, (0, 0), (vis.shape[1], 75), (25, 25, 25), -1)
        cv2.addWeighted(hud_bg, 0.2, vis[:75, :], 0.8, 0, vis[:75, :])
        
        mode_str = "SILVER (Dark BG)" if detector.dark_bg else "BLACK SCREW (Light BG)"
        cv2.putText(vis, f"Duco Screw Vision | Z: {detector.distance_mm:.1f}mm | FPS: {fps:.1f} | Mode: {mode_str}", 
                    (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(vis, f"Detected: M3 = {m3_count} pcs | M4 = {m4_count} pcs  [B: Toggle Black/Silver | +/-: Z | S: Snap | Q: Quit]", 
                    (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
        cv2.imshow("Duco M3/M4 Screw Detector", vis)
        cv2.imshow("Binary Mask (Inspection)", binary_mask)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('b'):
            detector.dark_bg = not detector.dark_bg
            print(f"[INFO] Mode toggled: {'SILVER SCREW (Dark BG)' if detector.dark_bg else 'BLACK SCREW (Light BG)'}")
        elif key == ord('+') or key == ord('='):
            detector.distance_mm += 5.0
            print(f"[INFO] Distance Z increased to: {detector.distance_mm:.1f} mm")
        elif key == ord('-') or key == ord('_'):
            detector.distance_mm = max(30.0, detector.distance_mm - 5.0)
            print(f"[INFO] Distance Z decreased to: {detector.distance_mm:.1f} mm")
        elif key == ord('s'):
            saved_count += 1
            img_path = os.path.join(args.save_dir, f"screw_sample_{int(time.time())}_{saved_count}.png")
            cv2.imwrite(img_path, frame)
            print(f"[INFO] Captured frame saved to: {img_path}")
            
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Screw detector terminated cleanly.")

if __name__ == '__main__':
    main()
