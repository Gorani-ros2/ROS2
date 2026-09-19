#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duco-910 Robot Vision-Guided Control Pipeline
Executes the 5-step automation workflow:
  1. Level TCP to 0° perpendicular orientation at 30cm height
  2. Define and persist 'm4_view' named pose
  3. Move to safe, compact folded standby home pose
  4. Return to 'm4_view'
  5. Sequential visual servoing approach to 10mm height for each detected M4 screw
"""

import os
import sys
import time
import json
import math
import urllib.request
import argparse
import numpy as np

sys.path.insert(0, "/home/knu/workspaces/duco_ros2_control_ws")
from duco_controller import DucoController, CONFIG_PATH

VISION_API_STATUS = "http://localhost:5000/api/status"

def query_vision_screws():
    """Query live detected M4 screws from local vision API."""
    try:
        req = urllib.request.Request(VISION_API_STATUS, headers={'User-Agent': 'DucoPipeline/1.0'})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            detections = data.get("detections", [])
            return detections, data
    except Exception as e:
        print(f"[WARN] Vision API offline or unreachable: {e}")
        return [], None

def cmd_status(controller):
    st = controller.get_status()
    print("\n=======================================================")
    print("   🤖 DUCO-910 ROBOT CONTROLLER STATUS")
    print("=======================================================")
    print(f"Connection   : {'🟢 Connected (192.168.1.10:7003)' if st['connected'] else '🔴 Disconnected'}")
    print(f"Robot State  : {st['robot_state']} (6 = Normal Operational)")
    print(f"Safety State : {st['safety_state']} (5 = Servos Enabled)")
    print(f"Motion State : {'🏃 MOVING' if st['is_moving'] else '⏸️ IDLE'}")
    if st['joints_deg']:
        q = [round(v, 2) for v in st['joints_deg']]
        print(f"Joints (deg) : J1={q[0]}°, J2={q[1]}°, J3={q[2]}°, J4={q[3]}°, J5={q[4]}°, J6={q[5]}°")
    if st['tcp_mm_deg']:
        p = [round(v, 2) for v in st['tcp_mm_deg']]
        print(f"TCP Pose     : X={p[0]}mm, Y={p[1]}mm, Z={p[2]}mm | Rx={p[3]}°, Ry={p[4]}°, Rz={p[5]}°")
    print("-------------------------------------------------------")
    print("📁 Registered Named Poses:")
    for name, info in controller.named_poses.items():
        q_s = [round(x, 1) for x in info.get("joints_deg", [])]
        print(f"  - [{name}]: Joints={q_s} | {info.get('description', '')}")
    print("=======================================================\n")
    return st

def cmd_step1_level_zero(controller, execute=True):
    """Step 1: Level robot TCP orientation to exact perpendicular (0.0° tilt)."""
    print("\n[STEP 1] Leveling Robot TCP Orientation to 0° Perpendicular...")
    tcp = controller.get_tcp_pose()
    if not tcp:
        print("[ERROR] Could not read robot TCP pose!")
        return False

    # Rx = -180.0° (straight down), Ry = 0.0° (level)
    target_tcp = [tcp[0], tcp[1], tcp[2], -180.0, 0.0, tcp[5]]
    q_cur = controller.get_joints()
    q_target = controller.cal_ik(target_tcp)
    
    if not q_target:
        print("[ERROR] Inverse kinematics computation failed!")
        return False

    deltas = [round(abs(q_target[i] - q_cur[i]), 2) for i in range(6)]
    print(f"  Current TCP : X={tcp[0]:.1f}mm, Y={tcp[1]:.1f}mm, Z={tcp[2]:.1f}mm | Rx={tcp[3]:.1f}°, Ry={tcp[4]:.1f}°, Rz={tcp[5]:.1f}°")
    print(f"  Target TCP  : X={target_tcp[0]:.1f}mm, Y={target_tcp[1]:.1f}mm, Z={target_tcp[2]:.1f}mm | Rx=-180.0°, Ry=0.0°, Rz={tcp[5]:.1f}°")
    print(f"  Joint Deltas: {deltas} (Max={max(deltas)}°)")

    if not execute:
        print("[DRY RUN] Motion planned successfully. Run with --execute to move robot.")
        return True

    print("  🚀 Executing gentle leveling motion (speed: 6.0 deg/s)...")
    success = controller.movej(q_target, vel_deg=6.0, acc_deg=10.0, block=True)
    if success:
        time.sleep(0.5)
        new_tcp = controller.get_tcp_pose()
        print(f"  ✅ Leveled Successfully! New TCP: Rx={new_tcp[3]:.2f}°, Ry={new_tcp[4]:.2f}°, Z={new_tcp[2]:.1f}mm")
        return True
    else:
        print("  ❌ Movement command returned failure!")
        return False

def cmd_step2_set_m4_view(controller):
    """Step 2: Define and register current pose as 'm4_view'."""
    print("\n[STEP 2] Defining and Registering 'm4_view' Pose...")
    success, info = controller.set_m4_view()
    if success:
        print(f"  ✅ 'm4_view' registered successfully in {CONFIG_PATH}!")
        print(f"  Joints : {info['joints_deg']}")
        print(f"  TCP    : {info['tcp_mm_deg']}")
        return True
    else:
        print("  ❌ Failed to register 'm4_view' pose.")
        return False

def cmd_step3_move_home(controller, execute=True):
    """Step 3: Move to safe, compact folded standby home pose."""
    print("\n[STEP 3] Moving to Compact Folded Standby Pose ('folded_home')...")
    if "folded_home" not in controller.named_poses:
        print("[ERROR] 'folded_home' pose definition not found!")
        return False

    target_q = controller.named_poses["folded_home"]["joints_deg"]
    q_cur = controller.get_joints()
    deltas = [round(abs(target_q[i] - q_cur[i]), 2) for i in range(6)]
    print(f"  Current Joints: {[round(x, 1) for x in q_cur]}")
    print(f"  Target Joints : {target_q}")
    print(f"  Joint Deltas  : {deltas} (Max={max(deltas)}°)")

    if not execute:
        print("[DRY RUN] Trajectory ready. Run with --execute to move robot.")
        return True

    print("  🚀 Moving smoothly to folded home pose (speed: 10.0 deg/s)...")
    success = controller.move_to_named_pose("folded_home", vel_deg=10.0, acc_deg=15.0)
    if success:
        time.sleep(0.5)
        new_q = controller.get_joints()
        print(f"  ✅ Arrived at Folded Home: {[round(x, 1) for x in new_q]}")
        return True
    else:
        print("  ❌ Failed to reach folded home.")
        return False

def cmd_step4_move_m4_view(controller, execute=True):
    """Step 4: Return smoothly to 'm4_view' pose."""
    print("\n[STEP 4] Returning to 'm4_view' Inspection Pose...")
    if "m4_view" not in controller.named_poses:
        print("[ERROR] 'm4_view' pose not registered yet! Run step 2 first.")
        return False

    target_q = controller.named_poses["m4_view"]["joints_deg"]
    q_cur = controller.get_joints()
    deltas = [round(abs(target_q[i] - q_cur[i]), 2) for i in range(6)]
    print(f"  Current Joints: {[round(x, 1) for x in q_cur]}")
    print(f"  Target Joints : {target_q}")
    print(f"  Joint Deltas  : {deltas} (Max={max(deltas)}°)")

    if not execute:
        print("[DRY RUN] Trajectory ready. Run with --execute to move robot.")
        return True

    print("  🚀 Moving to 'm4_view' pose (speed: 10.0 deg/s)...")
    success = controller.move_to_named_pose("m4_view", vel_deg=10.0, acc_deg=15.0)
    if success:
        time.sleep(0.5)
        new_tcp = controller.get_tcp_pose()
        print(f"  ✅ Arrived at 'm4_view'! TCP: X={new_tcp[0]:.1f}mm, Y={new_tcp[1]:.1f}mm, Z={new_tcp[2]:.1f}mm")
        return True
    else:
        print("  ❌ Failed to reach 'm4_view'.")
        return False

def cmd_step5_visual_servoing(controller, target_screw_idx=None, execute=True):
    """
    Step 5: Visual Servoing Approach to 10mm height.
    Aligns camera over detected screw and descends to 10mm clearance.
    """
    print("\n[STEP 5] Visual Servoing 10mm Approach Pipeline...")
    screws, v_meta = query_vision_screws()
    if not screws:
        print("[ERROR] No M4 screws detected by vision API! Ensure screw_detector_d405.py is running.")
        return False

    print(f"  Found {len(screws)} detected M4 screws via live vision API:")
    for idx, s in enumerate(screws):
        print(f"   [{idx}] {s['class']} | Table: [{s['x_tbl']:+.1f}, {s['y_tbl']:+.1f}]mm | Cam: [{s['x_3d']:+.1f}, {s['y_3d']:+.1f}, {s['z_3d']:.1f}]mm")

    # Select target screws
    targets_to_visit = [screws[target_screw_idx]] if target_screw_idx is not None else screws

    tcp_m4_view = controller.get_tcp_pose()
    if not tcp_m4_view:
        print("[ERROR] Could not read current TCP pose!")
        return False

    for i, target in enumerate(targets_to_visit):
        t_name = target['class']
        # Optical frame offset: X_cam (image right), Y_cam (image down)
        dx_cam = target['x_3d']
        dy_cam = target['y_3d']
        z_surface_mm = target['z_3d'] # e.g. ~292 mm

        print(f"\n  🎯 Target #{i+1}: {t_name} at Cam offset ΔX={dx_cam:+.1f}mm, ΔY={dy_cam:+.1f}mm, Surface Z={z_surface_mm:.1f}mm")
        
        # Safe Waypoint 1: Hover above target at safety height (Z = current view height, e.g. 334mm)
        # In tool frame with camera facing down:
        # moving camera by dx_cam, dy_cam aligns the optical axis directly over the screw!
        # Hard Safety Floor: Table surface is at Base Z ~42mm. Never descend below Base Z = 52mm.
        MIN_SAFE_BASE_Z = 52.0 # mm
        cur_tcp = controller.get_tcp_pose()
        if not cur_tcp:
            print("[ERROR] Cannot read TCP pose before descent!")
            continue
        max_safe_descent = max(0.0, cur_tcp[2] - MIN_SAFE_BASE_Z)
        descent_dist_mm = min(max(0.0, z_surface_mm - 10.0), max_safe_descent)

        print(f"     Waypoint 1 (XY Align)   : Offset [ΔX={dx_cam:+.1f}, ΔY={dy_cam:+.1f}] mm")
        print(f"     Waypoint 2 (10mm Height): Descend by {descent_dist_mm:.1f} mm -> Base Z={(cur_tcp[2] - descent_dist_mm):.1f}mm (10mm clearance)")

        if not execute:
            print(f"     [DRY RUN] Motion sequence for Target #{i+1} verified.")
            continue

        # Execute Waypoint 1: XY Align over screw center
        print(f"     🚀 [1/3] Aligning XY above screw (speed: 30 mm/s)...")
        controller.tcp_move([dx_cam, dy_cam, 0.0, 0.0, 0.0, 0.0], vel_m_s=0.03, acc_m_s2=0.05, block=True)
        time.sleep(0.5)

        # Execute Waypoint 2: Descend along Tool +Z to 10mm clearance
        print(f"     🚀 [2/3] Descending to 10mm clearance (speed: 20 mm/s)...")
        controller.tcp_move([0.0, 0.0, descent_dist_mm, 0.0, 0.0, 0.0], vel_m_s=0.02, acc_m_s2=0.04, block=True)
        time.sleep(2.0) # Hover 2 seconds for close-up inspection

        # Execute Waypoint 3: Retract back up to safety height
        print(f"     🚀 [3/3] Retracting back up to safety height...")
        controller.tcp_move([0.0, 0.0, -descent_dist_mm, 0.0, 0.0, 0.0], vel_m_s=0.03, acc_m_s2=0.05, block=True)
        time.sleep(0.5)

        # Reset cleanly to standard m4_view pose to prevent cumulative drift
        controller.move_to_named_pose("m4_view", vel_deg=10.0, acc_deg=15.0)
        time.sleep(0.5)
        print(f"     ✅ Completed inspection of Target #{i+1}!")

    print("\n  🎉 All selected targets completed!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Duco-910 5-Step Robot Automation Pipeline")
    parser.add_argument("action", choices=["status", "step1_level", "step2_set_view", "step3_home", "step4_view", "step5_servo", "run_all"],
                        help="Action to execute")
    parser.add_argument("--execute", action="store_true", help="Execute actual robot motion (default is dry-run for safety)")
    parser.add_argument("--target", type=int, default=None, help="Target screw index for visual servoing (0~6)")
    args = parser.parse_args()

    controller = DucoController()
    if not controller.connect():
        print("[ERROR] Cannot connect to Duco robot at 192.168.1.10:7003!")
        sys.exit(1)

    try:
        if args.action == "status":
            cmd_status(controller)
        elif args.action == "step1_level":
            cmd_step1_level_zero(controller, execute=args.execute)
        elif args.action == "step2_set_view":
            cmd_step2_set_m4_view(controller)
        elif args.action == "step3_home":
            cmd_step3_move_home(controller, execute=args.execute)
        elif args.action == "step4_view":
            cmd_step4_move_m4_view(controller, execute=args.execute)
        elif args.action == "step5_servo":
            cmd_step5_visual_servoing(controller, target_screw_idx=args.target, execute=args.execute)
        elif args.action == "run_all":
            print("\n🌟 Executing Complete 5-Step Pipeline Sequence:")
            if not cmd_step1_level_zero(controller, execute=args.execute): return
            if not cmd_step2_set_m4_view(controller): return
            if not cmd_step3_move_home(controller, execute=args.execute): return
            if not cmd_step4_move_m4_view(controller, execute=args.execute): return
            if not cmd_step5_visual_servoing(controller, target_screw_idx=0, execute=args.execute): return
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
