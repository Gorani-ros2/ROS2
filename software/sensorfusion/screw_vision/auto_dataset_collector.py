#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic Dataset Collector & Auto-Annotator for M3/M4 Screws
Generates YOLO-formatted dataset (images + labels) using calibrated geometric detection.
Zero manual bounding-box annotation needed!
"""

import os
import sys
import time
import argparse
import random
import cv2
import yaml
from screw_geometric_detector import ScrewDetector

def parse_args():
    parser = argparse.ArgumentParser(description="Auto Dataset Collector for M3/M4 Screws")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (/dev/videoN)")
    parser.add_argument("--distance", type=float, default=150.0, help="Camera height Z in mm")
    parser.add_argument("--focal", type=float, default=950.0, help="Focal length fx in px")
    parser.add_argument("--output", type=str, default="./screw_yolo_dataset", help="Dataset root directory")
    parser.add_argument("--auto-interval", type=float, default=1.5, help="Auto capture interval in seconds (0 to disable)")
    return parser.parse_args()

CLASS_MAP = {
    "M3_HEAD": 0,
    "M3_BODY": 1,
    "M4_HEAD": 2,
    "M4_BODY": 3
}

CLASS_NAMES = ["m3_head", "m3_body", "m4_head", "m4_body"]

def main():
    args = parse_args()
    
    train_img_dir = os.path.join(args.output, "train", "images")
    train_lbl_dir = os.path.join(args.output, "train", "labels")
    val_img_dir = os.path.join(args.output, "val", "images")
    val_lbl_dir = os.path.join(args.output, "val", "labels")
    
    for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)
        
    # Generate data.yaml
    data_yaml_path = os.path.join(args.output, "screw_data.yaml")
    yaml_content = {
        "path": os.path.abspath(args.output),
        "train": "train/images",
        "val": "val/images",
        "names": {i: name for i, name in enumerate(CLASS_NAMES)}
    }
    with open(data_yaml_path, "w") as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    print(f"[INFO] Created YOLO dataset config: {data_yaml_path}")
    
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera /dev/video{args.camera}")
        sys.exit(1)
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    detector = ScrewDetector(distance_mm=args.distance, focal_px=args.focal)
    
    total_saved = 0
    last_auto_time = time.time()
    auto_mode = False
    
    print("==================================================================")
    print("     M3 / M4 Screws Auto-Annotation & Dataset Collector")
    print("==================================================================")
    print(" Controls:")
    print("   [SPACE] : Capture & Auto-Label 1 Frame immediately")
    print("   [A]     : Toggle Automatic Interval Capture (Every 1.5s)")
    print("   [+] / [-] : Adjust Distance Z (5mm step)")
    print("   [Q]     : Quit and finish dataset collection")
    print("==================================================================")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        h, w = frame.shape[:2]
        detections, mask = detector.process_frame(frame)
        
        vis = frame.copy()
        valid_boxes = []
        
        for det in detections:
            cls_name = det["class"]
            if cls_name not in CLASS_MAP:
                continue
            cls_id = CLASS_MAP[cls_name]
            
            # Extract bounding box in pixel coordinates
            if det["type"] == "head":
                cx, cy = det["center"]
                r = det["radius"]
                x1 = max(0, int(cx - r * 1.15))
                y1 = max(0, int(cy - r * 1.15))
                x2 = min(w, int(cx + r * 1.15))
                y2 = min(h, int(cy + r * 1.15))
            else:
                box = cv2.boxPoints(det["rect"])
                x_coords = [p[0] for p in box]
                y_coords = [p[1] for p in box]
                x1 = max(0, int(min(x_coords) - 4))
                y1 = max(0, int(min(y_coords) - 4))
                x2 = min(w, int(max(x_coords) + 4))
                y2 = min(h, int(max(y_coords) + 4))
                
            bw = x2 - x1
            bh = y2 - y1
            if bw <= 0 or bh <= 0:
                continue
                
            # Normalized YOLO format (x_center, y_center, width, height)
            norm_xc = (x1 + bw / 2.0) / w
            norm_yc = (y1 + bh / 2.0) / h
            norm_w = bw / w
            norm_h = bh / h
            
            valid_boxes.append((cls_id, norm_xc, norm_yc, norm_w, norm_h))
            
            # Draw on display
            color = det["color"]
            cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
            cv2.putText(vis, f"{CLASS_NAMES[cls_id]}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        
        # Status overlay
        cv2.putText(vis, f"Dataset Collector | Auto: {'ON' if auto_mode else 'OFF'} | Saved: {total_saved} frames",
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(vis, f"Valid Objects in frame: {len(valid_boxes)}",
                    (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                    
        cv2.imshow("Auto Dataset Collector", vis)
        
        now = time.time()
        should_save = False
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            should_save = True
        elif key == ord('a'):
            auto_mode = not auto_mode
            print(f"[INFO] Auto mode switched to: {auto_mode}")
        elif key == ord('+') or key == ord('='):
            detector.distance_mm += 5.0
        elif key == ord('-') or key == ord('_'):
            detector.distance_mm = max(30.0, detector.distance_mm - 5.0)
            
        if auto_mode and (now - last_auto_time >= args.auto_interval) and len(valid_boxes) > 0:
            should_save = True
            last_auto_time = now
            
        if should_save and len(valid_boxes) > 0:
            total_saved += 1
            # 80% train, 20% val
            is_val = (random.random() < 0.2)
            target_img_dir = val_img_dir if is_val else train_img_dir
            target_lbl_dir = val_lbl_dir if is_val else train_lbl_dir
            
            filename = f"screw_{int(time.time()*1000)}"
            img_file = os.path.join(target_img_dir, f"{filename}.jpg")
            lbl_file = os.path.join(target_lbl_dir, f"{filename}.txt")
            
            cv2.imwrite(img_file, frame)
            with open(lbl_file, "w") as f:
                for b in valid_boxes:
                    f.write(f"{b[0]} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")
                    
            split_tag = "VAL" if is_val else "TRAIN"
            print(f"  [{split_tag}] Saved {filename}.jpg ({len(valid_boxes)} objects labeled)")
            
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[DONE] Dataset collection finished! Total images saved: {total_saved}")
    print(f"Run training with: python3 train_yolo_screw.py --data {data_yaml_path}")

if __name__ == '__main__':
    main()
