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
        return max(0.5, min(float(cli_speed), 20.0))
    if os.path.exists(SPEED_CONFIG_PATH):
        try:
            with open(SPEED_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return max(0.5, min(float(data.get("speed_mult", 5.0)), 20.0))
        except Exception:
            pass
    return 5.0

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
    """Step 1: Level robot TCP orientation to 0° perpendicular relative to workpiece table using D405 plane measurement."""
    scale = speed_mult
    vel_deg = min(10.0 * scale, 150.0)
    acc_deg = min(15.0 * scale, 250.0)
    print(f"\n[STEP 1] Camera-Referenced Table Leveling (Target Tilt: 0.0° / 0.0°, speed: {vel_deg:.1f} deg/s)...")
    tcp = controller.get_tcp_pose()
    if not tcp:
        print("[ERROR] Could not read robot TCP pose!")
        return False

    # Query live camera tilt from vision API
    _, v_meta = query_vision_screws()
    target_rx, target_ry = 178.22, -0.70  # Calibrated physical table-perpendicular orientation
    if v_meta and "pitch_deg" in v_meta and "roll_deg" in v_meta:
        cur_pitch = v_meta["pitch_deg"]
        cur_roll = v_meta["roll_deg"]
        print(f"  📷 Live D405 Table Tilt Measurement: Pitch = {cur_pitch:+.2f}°, Roll = {cur_roll:+.2f}°")
        # Dynamic closed-loop adjustment: Δpitch = -1.006 * ΔRx, Δroll = -0.926 * ΔRy
        d_rx = -(cur_pitch / 1.006)
        d_ry = +(cur_roll / 0.926)
        target_rx = round(tcp[3] + d_rx, 2)
        target_ry = round(tcp[4] + d_ry, 2)
        print(f"  🎯 Calculated Camera-Perpendicular Orientation: Rx = {target_rx}°, Ry = {target_ry}° (Residual Tilt -> 0.00°)")
    else:
        print(f"  ℹ️ Vision API offline; using calibrated table normal: Rx={target_rx}°, Ry={target_ry}°")

    target_tcp = [tcp[0], tcp[1], tcp[2], target_rx, target_ry, tcp[5]]
    q_cur = controller.get_joints()
    q_target = controller.cal_ik(target_tcp, q_cur)
    
    if not q_target:
        print("[ERROR] Inverse kinematics computation failed!")
        return False

    deltas = [round(abs(q_target[i] - q_cur[i]), 2) for i in range(6)]
    print(f"  Current TCP : X={tcp[0]:.1f}mm, Y={tcp[1]:.1f}mm, Z={tcp[2]:.1f}mm | Rx={tcp[3]:.2f}°, Ry={tcp[4]:.2f}°, Rz={tcp[5]:.2f}°")
    print(f"  Target TCP  : X={target_tcp[0]:.1f}mm, Y={target_tcp[1]:.1f}mm, Z={target_tcp[2]:.1f}mm | Rx={target_rx}°, Ry={target_ry}°, Rz={tcp[5]:.2f}°")
    print(f"  Joint Deltas: {deltas} (Max={max(deltas)}°)")

    if not execute:
        print("[DRY RUN] Motion planned successfully. Run with --execute to move robot.")
        return True

    print(f"  🚀 Executing camera-referenced leveling motion (speed: {vel_deg:.1f} deg/s)...")
    success = controller.movej(q_target, vel_deg=vel_deg, acc_deg=acc_deg, block=True)
    if success:
        time.sleep(1.0)
        new_tcp = controller.get_tcp_pose()
        _, new_meta = query_vision_screws()
        tilt_str = ""
        if new_meta and "pitch_deg" in new_meta:
            tilt_str = f" | New Camera Tilt: P={new_meta['pitch_deg']:+.2f}°, R={new_meta['roll_deg']:+.2f}°"
        print(f"  ✅ Camera Leveled Successfully! TCP: Rx={new_tcp[3]:.2f}°, Ry={new_tcp[4]:.2f}°{tilt_str}")
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
    scale = speed_mult
    vel_deg = min(15.0 * scale, 180.0)
    acc_deg = min(20.0 * scale, 300.0)
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
    scale = speed_mult
    vel_deg = min(15.0 * scale, 180.0)
    acc_deg = min(20.0 * scale, 300.0)
    vel_lift = min(0.05 * scale, 0.80)
    acc_lift = min(0.10 * scale, 2.0)
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

def solve_nearest_neighbor(screws, start_mode="center"):
    """
    Solves Traveling Salesperson Problem using Greedy Nearest-Neighbor heuristic.
    """
    remaining = list(screws)
    if not remaining:
        return []
    if start_mode == "center":
        # Start at the screw closest to optical center (r ~ 0)
        current = min(remaining, key=lambda s: s.get("dist_center", 999.0))
    else:  # "sweep" / "corner" - start from leftmost/top-left screw in table frame
        current = min(remaining, key=lambda s: s.get("x_tbl", 0.0) + s.get("y_tbl", 0.0))

    route = [current]
    remaining.remove(current)
    while remaining:
        next_s = min(remaining, key=lambda s: (s.get("x_tbl", 0) - current.get("x_tbl", 0))**2 + (s.get("y_tbl", 0) - current.get("y_tbl", 0))**2)
        route.append(next_s)
        remaining.remove(next_s)
        current = next_s
    return route

def cmd_step5_nn_tour(controller, start_mode="center", max_targets=None, execute=True, speed_mult=2.0):
    """
    Step 5 (Nearest-Neighbor Autonomous Inspection Tour):
    1. Reads all currently detected screws from D405 vision API.
    2. Optimizes inspection route using Nearest-Neighbor heuristic (Center-first or Corner sweep).
    3. 1st target: 3D Diagonal descent from m4_view (Z=334mm) to mid recognition height (Z=130mm).
    4. Mid-altitude high-resolution zeroing (Z=130mm).
    5. Final linear vertical descent to 10mm clearance (Z=65mm).
    6. Hover 1.5s & trigger snapshot.
    7. Vertical lift to safe surface clearance (Z=100mm, 47mm air gap above screw heads).
    8. Inter-target transit: Direct 3D diagonal linear glide from Z=100mm to next target Z=130mm (NO return to m4_view between screws!).
    9. After final screw: 3D diagonal linear ascent return to m4_view.
    """
    scale = speed_mult
    vel_travel_m_s = min(0.05 * scale, 1.00)   # up to 1,000 mm/s at 20x
    acc_travel_m_s2 = min(0.12 * scale, 2.50)  # up to 2.5 m/s²
    vel_mid_m_s = min(0.04 * scale, 0.60)     # up to 600 mm/s
    acc_mid_m_s2 = min(0.10 * scale, 2.00)
    vel_desc_m_s = min(0.025 * scale, 0.25)   # up to 250 mm/s
    acc_desc_m_s2 = min(0.06 * scale, 1.00)

    mode_label = "중심 우선 (Center-First)" if start_mode == "center" else "외곽 스위프 (Corner-Sweep)"
    if max_targets == 1:
        mode_label = "중심 최인접 1개 단일 접근 (Single)"

    print(f"\n=======================================================")
    print(f"  ⚡ [STEP 5] NEAREST-NEIGHBOR TOUR: {mode_label}")
    print(f"  ⚡ Active Speed: {speed_mult:.1f}x | 3D Diagonal Glide Enabled")
    print(f"=======================================================")

    screws, _ = query_vision_screws()
    if not screws:
        print("[ERROR] No M4 screws detected by vision API! Ensure screw_detector_d405.py is running.")
        return False

    tcp_m4_view = controller.named_poses.get("m4_view", {}).get("tcp_mm_deg") or controller.get_tcp_pose()
    if not tcp_m4_view:
        print("[ERROR] Could not read 'm4_view' pose!")
        return False

    route = solve_nearest_neighbor(screws, start_mode=start_mode)
    if max_targets is not None:
        route = route[:max_targets]

    print(f"  Found {len(screws)} detected screws. Computed Nearest-Neighbor path ({len(route)} targets):")
    for idx, s in enumerate(route):
        print(f"    [{idx+1}/{len(route)}] {s['class']} | Table=[{s['x_tbl']:+.1f}, {s['y_tbl']:+.1f}]mm | Cam=[{s['x_3d']:+.1f}, {s['y_3d']:+.1f}, {s['z_3d']:.1f}]mm | r={s['dist_center']:.1f}mm")

    MID_Z = 130.0        # mm (Closest reliable recognition height)
    LIFT_Z = 100.0       # mm (Safe clearance lift height between screws)
    SAFE_FLOOR_Z = 65.0  # mm (10mm clearance above screw head)

    # Orientation reference from m4_view (Rx=178.22°, Ry=-0.70°, Rz=94.01°)
    rx, ry, rz = tcp_m4_view[3], tcp_m4_view[4], tcp_m4_view[5]
    th_rad = math.radians(rz)
    c_th, s_th = math.cos(th_rad), math.sin(th_rad)

    # Pre-flight IK verification for all targets
    print("\n  🔍 Verifying IK reachability for tour trajectory...")
    waypoints_plan = []
    q_seed = controller.get_joints()
    for idx, s in enumerate(route):
        dx_base = c_th * s['x_3d'] + s_th * s['y_3d']
        dy_base = s_th * s['x_3d'] - c_th * s['y_3d']
        target_xy = [tcp_m4_view[0] + dx_base, tcp_m4_view[1] + dy_base]

        w_mid  = [target_xy[0], target_xy[1], MID_Z, rx, ry, rz]
        w_low  = [target_xy[0], target_xy[1], SAFE_FLOOR_Z, rx, ry, rz]
        w_lift = [target_xy[0], target_xy[1], LIFT_Z, rx, ry, rz]

        ik_mid  = controller.cal_ik(w_mid, q_seed)
        ik_low  = controller.cal_ik(w_low, ik_mid if ik_mid else q_seed)
        ik_lift = controller.cal_ik(w_lift, ik_low if ik_low else q_seed)

        if not ik_mid or not ik_low or not ik_lift:
            print(f"  ❌ [ERROR] IK check failed for Target #{idx+1} at Table [{s['x_tbl']:+.1f}, {s['y_tbl']:+.1f}]mm!")
            return False
        q_seed = ik_lift
        waypoints_plan.append((target_xy, s))

    print(f"  ✅ All {len(route)} targets passed IK validation!")

    if not execute:
        print("  [DRY RUN] IK verification successful. Skipping physical motion.")
        return True

    # Execution Loop with Visited Spatial Memory Filter
    visited_history = []  # Tracks absolute [X_base, Y_base] of already visited screws
    EXCLUSION_RADIUS_MM = 20.0  # M4 screw is ~8mm dia; 20mm radius strictly prevents revisiting prior screws

    for idx, (target_xy, target_meta) in enumerate(waypoints_plan):
        print(f"\n-------------------------------------------------------")
        print(f"  🎯 [{idx+1}/{len(waypoints_plan)}] Visiting Screw: Table=[{target_meta['x_tbl']:+.1f}, {target_meta['y_tbl']:+.1f}]mm (r={target_meta['dist_center']:.1f}mm)")
        print(f"-------------------------------------------------------")

        target_mid = [target_xy[0], target_xy[1], MID_Z, rx, ry, rz]

        if idx == 0:
            print(f"  ⚡ [1/5] 3D Diagonal Descent from m4_view to Target #{idx+1} Mid (Z={MID_Z}mm)...")
        else:
            print(f"  ⚡ [1/5] 3D Diagonal Low-Clearance Glide to Target #{idx+1} Mid (Z={MID_Z}mm)...")

        controller.movel(target_mid, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.2)

        # Mid-altitude zeroing with Visited Spatial Exclusion Filter
        print(f"  🔍 [2/5] Re-measuring target at Z={MID_Z}mm for sub-mm zeroing...")
        final_xy = [target_xy[0], target_xy[1]]
        mid_screws, _ = query_vision_screws()
        if mid_screws:
            # Filter out any detected screws within EXCLUSION_RADIUS_MM of already visited locations!
            unvisited_candidates = []
            for ms in mid_screws:
                cand_dx = c_th * ms['x_3d'] + s_th * ms['y_3d']
                cand_dy = s_th * ms['x_3d'] - c_th * ms['y_3d']
                cand_xy = [target_mid[0] + cand_dx, target_mid[1] + cand_dy]

                is_already_visited = False
                for v_xy in visited_history:
                    if math.hypot(cand_xy[0] - v_xy[0], cand_xy[1] - v_xy[1]) < EXCLUSION_RADIUS_MM:
                        is_already_visited = True
                        break

                if not is_already_visited:
                    unvisited_candidates.append(ms)
                else:
                    print(f"    🚫 Ignored nearby screw at Cam=[{ms['x_3d']:+.1f}, {ms['y_3d']:+.1f}]mm: ALREADY VISITED!")

            if unvisited_candidates:
                nearest_s = min(unvisited_candidates, key=lambda s: s['x_3d']**2 + s['y_3d']**2)
                d_err = math.hypot(nearest_s['x_3d'], nearest_s['y_3d'])
                print(f"    🎯 Target detected below camera: Cam=[{nearest_s['x_3d']:+.2f}, {nearest_s['y_3d']:+.2f}]mm (Residual={d_err:.2f}mm)")
                if d_err < 35.0:
                    dx_corr = c_th * nearest_s['x_3d'] + s_th * nearest_s['y_3d']
                    dy_corr = s_th * nearest_s['x_3d'] - c_th * nearest_s['y_3d']
                    final_xy = [target_mid[0] + dx_corr, target_mid[1] + dy_corr]
                    print(f"    ✨ Zeroing residual offset: [ΔX={dx_corr:+.2f}, ΔY={dy_corr:+.2f}] mm")
                    target_mid_corr = [final_xy[0], final_xy[1], MID_Z, rx, ry, rz]
                    controller.movel(target_mid_corr, vel_m_s=vel_mid_m_s, acc_m_s2=acc_mid_m_s2, block=True)
                    time.sleep(0.2)
            else:
                print(f"    ℹ️ All nearby detections were already visited; continuing with planned waypoint...")
        else:
            print(f"    ⚠️ No screw detected at mid-altitude, maintaining planned trajectory...")

        # Mark this location in spatial history so it can NEVER be revisited or confused
        visited_history.append([final_xy[0], final_xy[1]])
        print(f"  🏷️ Locked Target #{idx+1} as [VISITED] (Total Visited: {len(visited_history)}/{len(waypoints_plan)})")

        # Vertical descent to 10mm clearance
        print(f"  🚀 [3/5] Vertical descent to 10mm clearance (Z={SAFE_FLOOR_Z}mm)...")
        target_low = [final_xy[0], final_xy[1], SAFE_FLOOR_Z, rx, ry, rz]
        controller.movel(target_low, vel_m_s=vel_desc_m_s, acc_m_s2=acc_desc_m_s2, block=True)

        # Hover & Snapshot
        print(f"  📸 [4/5] Hovering 1.5s & capturing inspection snapshot...")
        time.sleep(1.5)
        try:
            snap_req = urllib.request.Request("http://localhost:5000/api/snapshot", data=b"{}", headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(snap_req, timeout=2.0) as r:
                res = json.loads(r.read().decode())
                print(f"    📷 Snapshot saved: {res.get('filename')}")
        except Exception as e:
            print(f"    [WARN] Snapshot request failed: {e}")

        # Safe surface clearance lift
        print(f"  ⚡ [5/5] Vertical lift to safe surface clearance (Z={LIFT_Z}mm)...")
        target_lift = [final_xy[0], final_xy[1], LIFT_Z, rx, ry, rz]
        controller.movel(target_lift, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
        time.sleep(0.2)

        if idx < len(waypoints_plan) - 1:
            print(f"  ➡️ Target #{idx+1} done. Gliding directly to Target #{idx+2} at safe Z={LIFT_Z}mm...")

    # Final ascent return to m4_view
    print(f"\n🏁 All {len(waypoints_plan)} screws inspected! 3D Diagonal return to 'm4_view' standby pose...")
    controller.movel(tcp_m4_view, vel_m_s=vel_travel_m_s, acc_m_s2=acc_travel_m_s2, block=True)
    time.sleep(0.5)
    print("🎉 Nearest-Neighbor Autonomous Tour Completed Successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Duco-910 Automated M4 Inspection Pipeline")
    parser.add_argument("action", choices=["status", "step1_level", "step2_set_view", "step3_home", "step4_view", "nn_center", "nn_sweep", "single_servo", "run_all"],
                        help="Action to execute")
    parser.add_argument("--execute", action="store_true", help="Execute actual robot motion (default is dry-run for safety)")
    parser.add_argument("--speed", type=float, default=None, help="Speed multiplier (0.5 to 20.0, default reads from config or 5.0)")
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
        elif args.action == "nn_center":
            cmd_step5_nn_tour(controller, start_mode="center", execute=args.execute, speed_mult=speed_mult)
        elif args.action == "nn_sweep":
            cmd_step5_nn_tour(controller, start_mode="sweep", execute=args.execute, speed_mult=speed_mult)
        elif args.action == "single_servo":
            cmd_step5_nn_tour(controller, start_mode="center", max_targets=1, execute=args.execute, speed_mult=speed_mult)
        elif args.action == "run_all":
            print("\n🌟 Executing Complete Pipeline Sequence:")
            if not cmd_step1_level_zero(controller, execute=args.execute, speed_mult=speed_mult): return
            if not cmd_step2_set_m4_view(controller): return
            if not cmd_step3_move_home(controller, execute=args.execute, speed_mult=speed_mult): return
            if not cmd_step4_move_m4_view(controller, execute=args.execute, speed_mult=speed_mult): return
            if not cmd_step5_nn_tour(controller, start_mode="center", execute=args.execute, speed_mult=speed_mult): return
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()
