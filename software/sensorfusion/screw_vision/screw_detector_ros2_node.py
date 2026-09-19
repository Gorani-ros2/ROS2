#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS 2 Humble Node for M3/M4 Screw Detection & 3D Pose Estimation
Publishes:
  - /screw_detection/poses (geometry_msgs/msg/PoseArray) - 3D grasp coordinates for Duco-910
  - /screw_detection/debug_image (sensor_msgs/msg/Image) - Visual overlay for rqt / RViz
Supports:
  - Geometric Zero-Shot Mode (OpenCV)
  - YOLO Deep Learning Mode (YOLOv8 / YOLO11 weights)
"""

import sys
import os
import math
import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from cv_bridge import CvBridge

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseArray, Pose, Point, Quaternion
from screw_geometric_detector import ScrewDetector

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

class ScrewVisionNode(Node):
    def __init__(self):
        super().__init__('screw_vision_node')
        
        # Parameters
        self.declare_parameter('mode', 'geometric')  # 'geometric' or 'yolo'
        self.declare_parameter('camera_device', 0)
        self.declare_parameter('image_topic', '')    # If set, subscribes to ROS topic instead of V4L2
        self.declare_parameter('distance_mm', 150.0)
        self.declare_parameter('focal_px', 950.0)
        self.declare_parameter('yolo_weights', 'screw_runs/screw_m3_m4/weights/best.pt')
        self.declare_parameter('conf_thresh', 0.4)
        
        self.mode = self.get_parameter('mode').value
        self.cam_dev = self.get_parameter('camera_device').value
        self.img_topic = self.get_parameter('image_topic').value
        self.dist_mm = self.get_parameter('distance_mm').value
        self.focal_px = self.get_parameter('focal_px').value
        self.weights = self.get_parameter('yolo_weights').value
        self.conf_thresh = self.get_parameter('conf_thresh').value
        
        self.bridge = CvBridge()
        self.geometric_detector = ScrewDetector(distance_mm=self.dist_mm, focal_px=self.focal_px)
        
        # YOLO model setup if in YOLO mode
        self.yolo_model = None
        if self.mode == 'yolo':
            if not YOLO_AVAILABLE:
                self.get_logger().error("ultralytics package not installed! Falling back to geometric mode.")
                self.mode = 'geometric'
            elif os.path.exists(self.weights):
                self.get_logger().info(f"Loading YOLO weights from: {self.weights}")
                self.yolo_model = YOLO(self.weights)
            else:
                self.get_logger().warn(f"Weights '{self.weights}' not found! Falling back to geometric mode.")
                self.mode = 'geometric'
                
        # Publishers
        self.pose_pub = self.create_publisher(PoseArray, '/screw_detection/poses', 10)
        self.debug_img_pub = self.create_publisher(Image, '/screw_detection/debug_image', 10)
        
        # Camera Source: ROS Topic or direct V4L2 capture
        if self.img_topic:
            self.get_logger().info(f"Subscribing to image topic: {self.img_topic}")
            self.create_subscription(Image, self.img_topic, self.image_callback, 10)
        else:
            self.get_logger().info(f"Opening local camera /dev/video{self.cam_dev}")
            self.cap = cv2.VideoCapture(self.cam_dev)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.timer = self.create_timer(0.033, self.timer_callback) # ~30 Hz
            
        self.get_logger().info(f"ScrewVisionNode initialized successfully in [{self.mode.upper()}] mode.")

    def timer_callback(self):
        ret, frame = self.cap.read()
        if ret:
            self.process_and_publish(frame)

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.process_and_publish(frame)
        except Exception as e:
            self.get_logger().error(f"Failed to convert ROS Image: {e}")

    def process_and_publish(self, frame):
        h, w = frame.shape[:2]
        vis = frame.copy()
        
        pose_array = PoseArray()
        pose_array.header.stamp = self.get_clock().now().to_msg()
        pose_array.header.frame_id = "camera_color_optical_frame"
        
        detections = []
        
        if self.mode == 'geometric':
            dets, _ = self.geometric_detector.process_frame(frame)
            for d in dets:
                cx, cy = d["center"]
                angle_deg = d["angle"]
                cls_name = d["class"]
                
                # Convert 2D image coordinates to 3D Camera Frame (Z = dist_mm)
                # X_cam = (u - cx_img) * Z / fx
                # Y_cam = (v - cy_img) * Z / fy
                x_3d = ((cx - w / 2.0) * self.dist_mm) / self.focal_px / 1000.0 # to meters
                y_3d = ((cy - h / 2.0) * self.dist_mm) / self.focal_px / 1000.0 # to meters
                z_3d = self.dist_mm / 1000.0                                    # to meters
                
                # Quaternion from yaw angle
                yaw_rad = math.radians(angle_deg)
                qz = math.sin(yaw_rad / 2.0)
                qw = math.cos(yaw_rad / 2.0)
                
                p = Pose()
                p.position = Point(x=x_3d, y=y_3d, z=z_3d)
                p.orientation = Quaternion(x=0.0, y=0.0, z=qz, w=qw)
                pose_array.poses.append(p)
                
                # Visualization
                color = d["color"]
                if d["type"] == "head":
                    cv2.circle(vis, (cx, cy), int(d["radius"]), color, 2)
                else:
                    box = np.int0(cv2.boxPoints(d["rect"]))
                    cv2.drawContours(vis, [box], 0, color, 2)
                    
                cv2.putText(vis, f"{cls_name} ({x_3d*1000:.0f}, {y_3d*1000:.0f}mm)", 
                            (cx - 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        elif self.mode == 'yolo':
            results = self.yolo_model(frame, conf=self.conf_thresh, verbose=False)
            boxes = results[0].boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                cls_id = int(box.cls[0].cpu().numpy())
                conf = float(box.conf[0].cpu().numpy())
                cls_name = self.yolo_model.names[cls_id]
                
                x1, y1, x2, y2 = xyxy
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                
                x_3d = ((cx - w / 2.0) * self.dist_mm) / self.focal_px / 1000.0
                y_3d = ((cy - h / 2.0) * self.dist_mm) / self.focal_px / 1000.0
                z_3d = self.dist_mm / 1000.0
                
                p = Pose()
                p.position = Point(x=x_3d, y=y_3d, z=z_3d)
                p.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
                pose_array.poses.append(p)
                
                cv2.rectangle(vis, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(vis, f"{cls_name} {conf:.2f}", (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
        # Publish
        self.pose_pub.publish(pose_array)
        
        try:
            debug_msg = self.bridge.cv2_to_imgmsg(vis, encoding="bgr8")
            self.debug_img_pub.publish(debug_msg)
        except Exception as e:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = ScrewVisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
