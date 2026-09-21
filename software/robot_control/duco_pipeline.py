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

SPEED_CONFIG_PATH = "/home/knu/workspaces/duco_ros2_control_ws/config/duco_speed.json"
VISION_API_STATUS = "http://localhost:5000/api/status"

def get_speed_multiplier(cli_speed=None):
    if cli_speed is not None and cli_speed > 0:
        return max(0.5, min(float(cli_speed), 3.5))
    if os.path.exists(SPEED_CONFIG_PATH):
        try:
            with open(SPEED_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return max(0.5, min(float(data.get("speed_mult", 2.0)), 3.5))
        except Exception:
            pass
    return 2.0

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

def cmd_step1_level_zero(controller, execute=True, speed_mult=2.0):
    """Step 1: Level robot TCP orientation to exact perpendicular (0.0° tilt)."""
    scale = speed_mult / 2.0
    vel_deg = min(15.0 * scale, 45.0)
    acc_deg = min(25.0 * scale, 60.0)
    print(f"\n[STEP 1] Leveling Robot TCP Orientation to 0° Perpendicular (speed: {vel_deg:.1f} deg/s)...")
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

    print(f"  🚀 Executing leveling motion (speed: {vel_deg:.1f} deg/s)...")
    success = controller.movej(q_target, vel_deg=vel_deg, acc_deg=acc_deg, block=True)
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

def cmd_step3_move_home(controller, execute=True, speed_mult=2.0):
    """Step 3: Move to safe, compact folded standby home pose."""
    scale = speed_mult / 2.0
    vel_deg = min(20.0 * scale, 60.0)
    acc_deg = min(30.0 * scale, 90.0)
    print(f"\n[STEP 3] Moving to Compact Folded Standby Pose ('folded_home', speed: {vel_deg:.1f} deg/s)...")
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

    print(f"  🚀 Moving smoothly to folded home pose (speed: {vel_deg:.1f} deg/s)...")
    success = controller.move_to_named_pose("folded_home", vel_deg=vel_deg, acc_deg=acc_deg)
    if success:
        time.sleep(0.5)
        new_q = controller.get_joints()
        print(f"  ✅ Arrived at Folded Home: {[round(x, 1) for x in new_q]}")
        return True
    else:
        print("  ❌ Failed to reach folded home.")
        return False

def cmd_step4_move_m4_view(controller, execute=True, speed_mult=2.0):
    """Step 4: Return smoothly to 'm4_view' pose."""
    scale = speed_mult / 2.0
    vel_deg = min(20.0 * scale, 60.0)
    acc_deg = min(30.0 * scale, 90.0)
    vel_lift = min(0.06 * scale, 0.18)
    acc_lift = min(0.10 * scale, 0.30)
    print(f"\n[STEP 4] Returning to 'm4_view' Inspection Pose (speed: {vel_deg:.1f} deg/s)...")
    if "m4_view" not in controller.named_poses:
        print("[ERROR] 'm4_view' pose not registered yet! Run step 2 first.")
        return False

    target_q = controller.named_poses["m4_view"]["joints_deg"]
    q_cur = controller.get_joints()
    deltas = [round(abs(target_q[i] - q_cur[i]), 2) for i in range(6)]
    print(f"  Current Joints: {[round(x, 1) for x in q_cur]}")
    print(f"  Target Joints : {target_q}")
    print(f"  Joint Deltas  : {deltas} (Max={max(deltas)}°)")

    cur_tcp = controller.get_tcp_pose()
    if cur_tcp and cur_tcp[2] < 150.0:
        print(f"  ⚠️ Low altitude detected (Z={cur_tcp[2]:.1f}mm < 150mm). Executing vertical linear liftoff first (speed: {vel_lift*1000:.0f} mm/s)...")
        target_lift = [cur_tcp[0], cur_tcp[1], 150.0, 180.0, 0.0, cur_tcp[5]]
        if execute:
            controller.movel(target_lift, vel_m_s=vel_lift, acc_m_s2=acc_lift, block=True)
            time.sleep(0.3)

    print(f"  🚀 Moving to 'm4_view' pose (speed: {vel_deg:.1f} deg/s)...")
    success = controller.move_to_named_pose("m4_view", vel_deg=vel_deg, acc_deg=acc_deg)
    if success:
        time.sleep(0.5)
        new_tcp = controller.get_tcp_pose()
        print(f"  ✅ Arrived at 'm4_view'! TCP: X={new_tcp[0]:.1f}mm, Y={new_tcp[1]:.1f}mm, Z={new_tcp[2]:.1f}mm")
        return True
    else:
        print("  ❌ Failed to reach 'm4_view'.")
        return False

def cmd_step5_visual_servoing(controller, target_screw_idx=None, execute=True, speed_mult=2.0):
    """
    Step 5: Visual Servoing Approach to 10mm height.
    Aligns camera over detected screw and descends to 10mm clearance.
    """
    scale = speed_mult / 2.0
    vel_travel_m_s = min(0.06 * scale, 0.18)
    acc_travel_m_s2 = min(0.10 * scale, 0.30)
    vel_mid_m_s = min(0.04 * scale, 0.12)
    acc_mid_m_s2 = min(0.08 * scale, 0.24)
    vel_desc_m_s = min(0.03 * scale, 0.09)
    acc_desc_m_s2 = min(0.06 * scale, 0.18)
    vel_joint_deg = min(20.0 * scale, 60.0)
    acc_joint_deg = min(30.0 * scale, 90.0)

    print(f"\n[STEP 5] Visual Servoing 10mm Approach Pipeline (Speed: {speed_mult:.1f}x)...")
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
        SAFE_FLOOR_Z = 65.0 # mm (Flange height ensuring ~11-13mm air gap above screw head, zero physical contact)
        cur_tcp = controller.get_tcp_pose()
        if not cur_tcp:
            print("[ERROR] Cannot read TCP pose before descent!")
            continue

        # Transform camera optical offset to robot base frame dynamically using current Rz
        th_rad = math.radians(cur_tcp[5])
        c_th, s_th = math.cos(th_rad), math.sin(th_rad)
        dx_base = c_th * dx_cam + s_th * dy_cam
        dy_base = s_th * dx_cam - c_th * dy_cam

        MID_Z = 130.0       # mm (Closest reliable recognition height: ~8.5cm above table, >7cm D405 blind limit)
        SAFE_FLOOR_Z = 65.0  # mm (Flange height ensuring ~11-13mm air gap above screw head, zero physical contact)

        target_xy_high = [cur_tcp[0] + dx_base, cur_tcp[1] + dy_base, cur_tcp[2], 180.0, 0.0, cur_tcp[5]]
        target_mid     = [target_xy_high[0], target_xy_high[1], MID_Z, 180.0, 0.0, cur_tcp[5]]
        target_low     = [target_xy_high[0], target_xy_high[1], SAFE_FLOOR_Z, 180.0, 0.0, cur_tcp[5]]

        print(f"     Waypoint 1 (High XY)  : X={target_xy_high[0]:.1f}mm, Y={target_xy_high[1]:.1f}mm, Z={target_xy_high[2]:.1f}mm")
        print(f"     Waypoint 2 (Mid Recog): X={target_mid[0]:.1f}mm, Y={target_mid[1]:.1f}mm, Z={target_mid[2]:.1f}mm (~8.5cm height)")
        print(f"     Waypoint 3 (10mm Low) : X={target_low[0]:.1f}mm, Y={target_low[1]:.1f}mm, Z={target_low[2]:.1f}mm (Floor={SAFE_FLOOR_Z}mm)")

        q_cur = controller.get_joints()
        ik_high = controller.cal_ik(target_xy_high, q_cur)
        ik_mid  = controller.cal_ik(target_mid, ik_high if ik_high else q_cur)
        ik_low  = controller.cal_ik(target_low, ik_mid if ik_mid else q_cur)

        if not ik_high or not ik_mid or not ik_low:
            print(f"     ❌ [ERROR] IK check failed for Target #{i+1}! Skipping.")
            continue

        if not execute:
            print(f"     [DRY RUN] Motion sequence for Target #{i+1} verified with IK: OK.")
            continue

        # Execute Waypoint 1: High XY Align in Cartesian space
        print(f"     🚀 [1/5] Aligning XY above screw at high altitude (speed: {vel_travel_m_s*1000:.0f} mm/s)...")
        controller.movel(target_xy_high, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.3)

        # Execute Waypoint 2: Descend to closest recognition height (Z = 130.0mm)
        print(f"     🚀 [2/5] Descending to closest recognition height (Z={MID_Z}mm, speed: {vel_travel_m_s*1000:.0f} mm/s)...")
        controller.movel(target_mid, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.4)

        # Execute Waypoint 3: Mid-altitude visual re-measurement & zeroing
        print(f"     🔍 [3/5] Re-measuring target at high-resolution mid-altitude for sub-mm zeroing...")
        final_xy = [target_mid[0], target_mid[1]]
        mid_screws, _ = query_vision_screws()
        if mid_screws:
            nearest_s = min(mid_screws, key=lambda s: s['x_3d']**2 + s['y_3d']**2)
            d_err = math.hypot(nearest_s['x_3d'], nearest_s['y_3d'])
            print(f"       🎯 Detected screw right below camera: Cam=[{nearest_s['x_3d']:+.2f}, {nearest_s['y_3d']:+.2f}]mm (Residual Error={d_err:.2f}mm)")
            if d_err < 35.0:
                dx_corr = c_th * nearest_s['x_3d'] + s_th * nearest_s['y_3d']
                dy_corr = s_th * nearest_s['x_3d'] - c_th * nearest_s['y_3d']
                final_xy = [target_mid[0] + dx_corr, target_mid[1] + dy_corr]
                print(f"       ✨ Zeroing residual offset: [ΔX_base={dx_corr:+.2f}, ΔY_base={dy_corr:+.2f}] mm")
                target_mid_corrected = [final_xy[0], final_xy[1], MID_Z, 180.0, 0.0, cur_tcp[5]]
                controller.movel(target_mid_corrected, vel_m_s=vel_mid_m_s, acc_m_s2=acc_mid_m_s2, block=True)
                time.sleep(0.3)
        else:
            print(f"       ⚠️ No screw detected at mid-altitude, continuing with high-altitude trajectory...")

        # Execute Waypoint 4: Cartesian Linear Descent to 10mm clearance (Z=65.0mm)
        print(f"     🚀 [4/5] Cartesian linear descent to 10mm clearance (Z={SAFE_FLOOR_Z}mm, speed: {vel_desc_m_s*1000:.0f} mm/s)...")
        target_final_low = [final_xy[0], final_xy[1], SAFE_FLOOR_Z, 180.0, 0.0, cur_tcp[5]]
        controller.movel(target_final_low, vel_m_s=vel_desc_m_s, acc_m_s2=acc_desc_m_s2, block=True)
        
        # Execute Waypoint 5: Hover 1.5s and capture snapshot
        print(f"     📸 [5/5] Hovering at 10mm clearance for 1.5s inspection...")
        time.sleep(1.5)
        try:
            snap_req = urllib.request.Request("http://localhost:5000/api/snapshot", data=b"{}", headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(snap_req, timeout=2.0) as r:
                res = json.loads(r.read().decode())
                print(f"       📷 Snapshot saved: {res.get('filename')}")
        except Exception as e:
            pass

        # Execute Waypoint 6: Retract vertically back up to safety height
        print(f"     🚀 Retracting vertically back up to safety height (speed: {vel_travel_m_s*1000:.0f} mm/s)...")
        target_retract = [final_xy[0], final_xy[1], cur_tcp[2], 180.0, 0.0, cur_tcp[5]]
        controller.movel(target_retract, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.3)

        # Reset cleanly to standard m4_view pose to prevent cumulative drift
        print(f"     🔄 Returning to 'm4_view' standby pose (speed: {vel_joint_deg:.1f} deg/s)...")
        controller.move_to_named_pose("m4_view", vel_deg=vel_joint_deg, acc_deg=acc_joint_deg)
        time.sleep(0.5)
        print(f"     ✅ Completed inspection of Target #{i+1} with 2-stage zeroing!")

    print("\n  🎉 All selected targets completed!")
    return True

def cmd_step5_clock_outer(controller, target_clock=None, execute=True, speed_mult=2.0):
    """
    Executes Cartesian linear interpolated descent on the 4 outermost screws in clockwise order:
      12 o'clock (Top / 상) -> m4_view
      3 o'clock (Right / 우) -> m4_view
      6 o'clock (Bottom / 하) -> m4_view
      9 o'clock (Left / 좌) -> m4_view
    """
    scale = speed_mult / 2.0
    vel_travel_m_s = min(0.06 * scale, 0.18)
    acc_travel_m_s2 = min(0.10 * scale, 0.30)
    vel_mid_m_s = min(0.04 * scale, 0.12)
    acc_mid_m_s2 = min(0.08 * scale, 0.24)
    vel_desc_m_s = min(0.03 * scale, 0.09)
    acc_desc_m_s2 = min(0.06 * scale, 0.18)
    vel_joint_deg = min(20.0 * scale, 60.0)
    acc_joint_deg = min(30.0 * scale, 90.0)

    print(f"\n[STEP 5 - CLOCK] Starting 4 Outermost Screws Clockwise Interpolation Pipeline (Speed: {speed_mult:.1f}x)...")
    print("  Sequence: m4_view -> 12시 10mm -> m4_view -> 3시 10mm -> m4_view -> 6시 10mm -> m4_view -> 9시 10mm -> m4_view")

    if "m4_view" not in controller.named_poses:
        print("[ERROR] 'm4_view' pose not registered!")
        return False

    screws, _ = query_vision_screws()
    if len(screws) < 4:
        print(f"[ERROR] Found only {len(screws)} screws, expected at least 4 outer screws!")
        return False

    # Find the 4 outer screws:
    s_12 = min(screws, key=lambda s: s['y_3d'])
    s_3  = max(screws, key=lambda s: s['x_3d'])
    s_6  = max(screws, key=lambda s: s['y_3d'])
    s_9  = min(screws, key=lambda s: s['x_3d'])

    clock_targets = [
        ("12시 (상 / Top)", s_12),
        ("3시 (우 / Right)", s_3),
        ("6시 (하 / Bottom)", s_6),
        ("9시 (좌 / Left)", s_9)
    ]

    if target_clock is not None:
        clock_targets = [t for t in clock_targets if str(target_clock) in t[0]]
        if not clock_targets:
            print(f"[ERROR] Target clock '{target_clock}' not recognized! Use 12, 3, 6, or 9.")
            return False

    print("\n  📍 Identified Outermost Target Screws:")
    for label, s in clock_targets:
        print(f"    - {label}: Cam=[{s['x_3d']:+.1f}, {s['y_3d']:+.1f}, {s['z_3d']:.1f}]mm | Table=[{s['x_tbl']:+.1f}, {s['y_tbl']:+.1f}]mm (r={s['dist_center']:.1f}mm)")

    SAFE_FLOOR_Z = 65.0 # mm (Flange height ensuring ~11-13mm air gap above screw head, zero physical contact)

    for idx, (label, target) in enumerate(clock_targets):
        print(f"\n=======================================================")
        print(f"  🎯 [{idx+1}/4] Visiting {label} Screw")
        print(f"=======================================================")

        # Re-query vision to get fresh static snapshot coordinates from m4_view
        cur_screws, _ = query_vision_screws()
        if cur_screws:
            if "12" in label:
                target = min(cur_screws, key=lambda s: s['y_3d'])
            elif "3" in label:
                target = max(cur_screws, key=lambda s: s['x_3d'])
            elif "6" in label:
                target = max(cur_screws, key=lambda s: s['y_3d'])
            elif "9" in label:
                target = min(cur_screws, key=lambda s: s['x_3d'])

        dx_cam = target['x_3d']
        dy_cam = target['y_3d']
        z_surface_mm = target['z_3d']

        cur_tcp = controller.get_tcp_pose()
        if not cur_tcp:
            print("[ERROR] Cannot read TCP pose!")
            return False

        # Transform camera optical offset to robot base frame dynamically using current Rz
        th_rad = math.radians(cur_tcp[5])
        c_th, s_th = math.cos(th_rad), math.sin(th_rad)
        dx_base = c_th * dx_cam + s_th * dy_cam
        dy_base = s_th * dx_cam - c_th * dy_cam

        MID_Z = 130.0       # mm (Closest reliable recognition height: ~8.5cm above table, >7cm D405 blind limit)
        SAFE_FLOOR_Z = 65.0  # mm (Flange height ensuring ~11-13mm air gap above screw head, zero physical contact)

        target_xy_high = [cur_tcp[0] + dx_base, cur_tcp[1] + dy_base, cur_tcp[2], 180.0, 0.0, cur_tcp[5]]
        target_mid     = [target_xy_high[0], target_xy_high[1], MID_Z, 180.0, 0.0, cur_tcp[5]]
        target_low     = [target_xy_high[0], target_xy_high[1], SAFE_FLOOR_Z, 180.0, 0.0, cur_tcp[5]]

        print(f"  Current TCP            : X={cur_tcp[0]:.1f}mm, Y={cur_tcp[1]:.1f}mm, Z={cur_tcp[2]:.1f}mm")
        print(f"  Camera Offset (30cm)   : [ΔX_cam={dx_cam:+.1f}, ΔY_cam={dy_cam:+.1f}, Z_cam={z_surface_mm:.1f}] mm")
        print(f"  Base Frame Offset      : [ΔX_base={dx_base:+.1f}, ΔY_base={dy_base:+.1f}] mm")
        print(f"  Waypoint 1 (High XY)   : X={target_xy_high[0]:.1f}, Y={target_xy_high[1]:.1f}, Z={target_xy_high[2]:.1f}mm")
        print(f"  Waypoint 2 (Mid Recog) : X={target_mid[0]:.1f}, Y={target_mid[1]:.1f}, Z={target_mid[2]:.1f}mm (~8.5cm height)")
        print(f"  Waypoint 3 (10mm Low)  : X={target_low[0]:.1f}, Y={target_low[1]:.1f}, Z={target_low[2]:.1f}mm (Safety Floor={SAFE_FLOOR_Z}mm)")

        # Verify Inverse Kinematics reachability
        q_cur = controller.get_joints()
        ik_high = controller.cal_ik(target_xy_high, q_cur)
        ik_mid  = controller.cal_ik(target_mid, ik_high if ik_high else q_cur)
        ik_low  = controller.cal_ik(target_low, ik_mid if ik_mid else q_cur)

        if not ik_high or not ik_mid or not ik_low:
            print(f"  ❌ [ERROR] IK check failed for {label}! Skipping this target.")
            continue

        if not execute:
            print(f"  [DRY RUN] Motion sequence for {label} verified with IK: OK.")
            continue

        # 1. Align XY above target at high altitude (Z = 333.9mm) using Cartesian movel
        print(f"  🚀 [1/5] Aligning camera above {label} at high altitude (speed: {vel_travel_m_s*1000:.0f} mm/s)...")
        controller.movel(target_xy_high, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.3)

        # 2. Descend to closest recognition height (Z = 130.0mm) using Cartesian movel
        print(f"  🚀 [2/5] Descending to closest recognition height (Z={MID_Z}mm, speed: {vel_travel_m_s*1000:.0f} mm/s)...")
        controller.movel(target_mid, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.4)

        # 3. Mid-altitude visual re-measurement & zeroing
        print(f"  🔍 [3/5] Re-measuring target at high-resolution mid-altitude for sub-mm zeroing...")
        final_xy = [target_mid[0], target_mid[1]]
        mid_screws, _ = query_vision_screws()
        if mid_screws:
            nearest_s = min(mid_screws, key=lambda s: s['x_3d']**2 + s['y_3d']**2)
            d_err = math.hypot(nearest_s['x_3d'], nearest_s['y_3d'])
            print(f"    🎯 Detected screw right below camera: Cam=[{nearest_s['x_3d']:+.2f}, {nearest_s['y_3d']:+.2f}]mm (Residual Error={d_err:.2f}mm)")
            if d_err < 35.0:
                dx_corr = c_th * nearest_s['x_3d'] + s_th * nearest_s['y_3d']
                dy_corr = s_th * nearest_s['x_3d'] - c_th * nearest_s['y_3d']
                final_xy = [target_mid[0] + dx_corr, target_mid[1] + dy_corr]
                print(f"    ✨ Zeroing residual offset: [ΔX_base={dx_corr:+.2f}, ΔY_base={dy_corr:+.2f}] mm")
                target_mid_corrected = [final_xy[0], final_xy[1], MID_Z, 180.0, 0.0, cur_tcp[5]]
                controller.movel(target_mid_corrected, vel_m_s=vel_mid_m_s, acc_m_s2=acc_mid_m_s2, block=True)
                time.sleep(0.3)
        else:
            print(f"    ⚠️ No screw detected at mid-altitude, continuing with high-altitude trajectory...")

        # 4. Final Linear Descent to 10mm Clearance (Z = 65.0mm)
        print(f"  🚀 [4/5] Final linear descent to 10mm clearance (Z={SAFE_FLOOR_Z}mm, speed: {vel_desc_m_s*1000:.0f} mm/s)...")
        target_final_low = [final_xy[0], final_xy[1], SAFE_FLOOR_Z, 180.0, 0.0, cur_tcp[5]]
        controller.movel(target_final_low, vel_m_s=vel_desc_m_s, acc_m_s2=acc_desc_m_s2, block=True)
        
        # 5. Hover 1.5 seconds and capture inspection snapshot
        print(f"  📸 [5/5] Hovering at 10mm clearance for 1.5s inspection...")
        time.sleep(1.5)
        try:
            snap_req = urllib.request.Request("http://localhost:5000/api/snapshot", data=b"{}", headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(snap_req, timeout=2.0) as r:
                res = json.loads(r.read().decode())
                print(f"    📷 Snapshot saved: {res.get('filename')}")
        except Exception as e:
            print(f"    [WARN] Snapshot request failed: {e}")

        # 6. Retract vertically back up to high altitude (Z = 333.9mm) using Cartesian movel
        print(f"  🚀 Retracting vertically back to safety height (speed: {vel_travel_m_s*1000:.0f} mm/s)...")
        target_retract = [final_xy[0], final_xy[1], cur_tcp[2], 180.0, 0.0, cur_tcp[5]]
        controller.movel(target_retract, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.3)

        # 7. Return cleanly to standard m4_view pose
        print(f"  🔄 Returning to 'm4_view' standby pose (speed: {vel_joint_deg:.1f} deg/s)...")
        controller.move_to_named_pose("m4_view", vel_deg=vel_joint_deg, acc_deg=acc_joint_deg)
        time.sleep(0.5)
        print(f"  ✅ Completed {label} inspection cycle with 2-stage zeroing!")

    print("\n🎉 All 4 Outermost Screws (12시 -> 3시 -> 6시 -> 9시) successfully visited and returned to m4_view!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Duco-910 5-Step Robot Automation Pipeline")
    parser.add_argument("action", choices=["status", "step1_level", "step2_set_view", "step3_home", "step4_view", "step5_servo", "clock_outer", "run_all"],
                        help="Action to execute")
    parser.add_argument("--execute", action="store_true", help="Execute actual robot motion (default is dry-run for safety)")
    parser.add_argument("--target", type=int, default=None, help="Target screw index for visual servoing (0~6)")
    parser.add_argument("--speed", type=float, default=None, help="Speed multiplier (0.5 to 3.5, default reads from config or 2.0)")
    args = parser.parse_args()

    speed_mult = get_speed_multiplier(args.speed)
    print(f"⚙️ Active Pipeline Speed Multiplier: {speed_mult:.1f}x")

    controller = DucoController()
    if not controller.connect():
        print("[ERROR] Cannot connect to Duco robot at 192.168.1.10:7003!")
        sys.exit(1)

    try:
        if args.action == "status":
            cmd_status(controller)
        elif args.action == "step1_level":
            cmd_step1_level_zero(controller, execute=args.execute, speed_mult=speed_mult)
        elif args.action == "step2_set_view":
            cmd_step2_set_m4_view(controller)
        elif args.action == "step3_home":
            cmd_step3_move_home(controller, execute=args.execute, speed_mult=speed_mult)
        elif args.action == "step4_view":
            cmd_step4_move_m4_view(controller, execute=args.execute, speed_mult=speed_mult)
        elif args.action == "step5_servo":
            cmd_step5_visual_servoing(controller, target_screw_idx=args.target, execute=args.execute, speed_mult=speed_mult)
        elif args.action == "clock_outer":
            cmd_step5_clock_outer(controller, target_clock=args.target, execute=args.execute, speed_mult=speed_mult)
        elif args.action == "run_all":
            print("\n🌟 Executing Complete 5-Step Pipeline Sequence:")
            if not cmd_step1_level_zero(controller, execute=args.execute, speed_mult=speed_mult): return
            if not cmd_step2_set_m4_view(controller): return
            if not cmd_step3_move_home(controller, execute=args.execute, speed_mult=speed_mult): return
            if not cmd_step4_move_m4_view(controller, execute=args.execute, speed_mult=speed_mult): return
            if not cmd_step5_visual_servoing(controller, target_screw_idx=0, execute=args.execute, speed_mult=speed_mult): return
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
