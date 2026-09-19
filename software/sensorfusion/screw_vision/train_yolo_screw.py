#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast YOLO11 / YOLOv8 Training Script for M3/M4 Screws
Leverages NVIDIA RTX 5070 Laptop GPU for ultra-fast convergence (< 10 min).
"""

import os
import sys
import argparse
import torch
from ultralytics import YOLO

def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLO on M3/M4 Screws")
    parser.add_argument("--data", type=str, default="./screw_yolo_dataset/screw_data.yaml", help="Path to data.yaml")
    parser.add_argument("--model", type=str, default="./yolo11n.pt", help="Pretrained weights (.pt)")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--device", type=str, default="0", help="CUDA device index (0 for RTX 5070)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("==================================================================")
    print("        M3 / M4 Screw YOLO11 Custom Model Training")
    print("==================================================================")
    print(f" PyTorch Version : {torch.__version__}")
    print(f" CUDA Available  : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f" GPU Device      : {torch.cuda.get_device_name(0)}")
    print(f" Dataset YAML    : {args.data}")
    print(f" Pretrained Model: {args.model}")
    print(f" Epochs          : {args.epochs}")
    print(f" Image Size      : {args.imgsz}x{args.imgsz}")
    print("==================================================================")
    
    if not os.path.exists(args.data):
        print(f"[ERROR] Dataset configuration '{args.data}' not found!")
        print("Please run 'python3 auto_dataset_collector.py' first to collect and auto-label screw samples.")
        sys.exit(1)
        
    model = YOLO(args.model)
    
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device if torch.cuda.is_available() else "cpu",
        project="screw_runs",
        name="screw_m3_m4",
        save=True,
        plots=True,
        verbose=True,
        # Augmentation tailored for metallic screws (rotation & scale)
        degrees=180.0,
        flipud=0.5,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.2,
        hsv_v=0.4
    )
    
    print("==================================================================")
    print(" [SUCCESS] Training completed!")
    print(f" Best Weights saved at: screw_runs/screw_m3_m4/weights/best.pt")
    print("==================================================================")

if __name__ == '__main__':
    main()
