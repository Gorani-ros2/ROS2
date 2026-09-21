#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duco-910 Robot Controller Bridge (Python ctypes to C++ libDucoCobotAPI)
Provides high-level motion primitives, named poses, and safety checks.
"""

import os
import sys
import json
import math
import time
import ctypes
import numpy as np

SO_PATH = "/home/knu/workspaces/duco_ros2_control_ws/lib/libduco_bridge.so"
CONFIG_PATH = "/home/knu/workspaces/duco_ros2_control_ws/config/duco_named_poses.json"

class DucoController:
    def __init__(self, ip="192.168.1.10", port=7003):
        self.ip = ip
        self.port = port
        self.connected = False
        self._load_library()
        self._load_named_poses()

    def _load_library(self):
        if not os.path.exists(SO_PATH):
            raise FileNotFoundError(f"Shared library not found: {SO_PATH}")
        self.lib = ctypes.CDLL(SO_PATH)
        
        self.lib.duco_connect.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.lib.duco_connect.restype = ctypes.c_int

        self.lib.duco_disconnect.restype = ctypes.c_int

        self.lib.duco_get_joints.argtypes = [ctypes.POINTER(ctypes.c_double)]
        self.lib.duco_get_joints.restype = ctypes.c_int

        self.lib.duco_get_tcp_pose.argtypes = [ctypes.POINTER(ctypes.c_double)]
        self.lib.duco_get_tcp_pose.restype = ctypes.c_int

        self.lib.duco_get_robot_state.argtypes = [ctypes.POINTER(ctypes.c_int8)]
        self.lib.duco_get_robot_state.restype = ctypes.c_int

        self.lib.duco_is_moving.restype = ctypes.c_int

        self.lib.duco_movej.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double, ctypes.c_bool]
        self.lib.duco_movej.restype = ctypes.c_int

        self.lib.duco_movej2.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double, ctypes.c_bool]
        self.lib.duco_movej2.restype = ctypes.c_int

        self.lib.duco_movel.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double, ctypes.c_bool]
        self.lib.duco_movel.restype = ctypes.c_int

        self.lib.duco_tcp_move.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double, ctypes.c_bool]
        self.lib.duco_tcp_move.restype = ctypes.c_int

        self.lib.duco_stop.restype = ctypes.c_int

        self.lib.duco_cal_ik.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        self.lib.duco_cal_ik.restype = ctypes.c_int

        self.lib.duco_cal_fk.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        self.lib.duco_cal_fk.restype = ctypes.c_int

    def _load_named_poses(self):
        self.named_poses = {
            "folded_home": {
                "joints_deg": [0.0, -10.0, -110.0, 30.0, 90.0, 0.0],
                "description": "Safe, compact folded standby pose (low center of gravity, non-singular, downward tool)"
            },
            "candle_home": {
                "joints_deg": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "description": "MoveIt standard zero position (straight up)"
            }
        }
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.named_poses.update(data)
            except Exception as e:
                print(f"[WARN] Failed to load named poses: {e}")
        else:
            self._save_named_poses()

    def _save_named_poses(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.named_poses, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save named poses: {e}")

    def connect(self):
        ret = self.lib.duco_connect(self.ip.encode('utf-8'), self.port)
        self.connected = (ret == 0)
        return self.connected

    def disconnect(self):
        if self.connected:
            self.lib.duco_disconnect()
            self.connected = False

    def is_moving(self):
        return bool(self.lib.duco_is_moving())

    def stop(self):
        return self.lib.duco_stop() == 0

    def get_joints(self):
        """Returns joint angles in degrees: [J1, J2, J3, J4, J5, J6]"""
        q = (ctypes.c_double * 6)()
        if self.lib.duco_get_joints(q) == 0:
            return [float(np.degrees(v)) for v in q]
        return None

    def get_tcp_pose(self):
        """Returns Cartesian TCP pose: [X_mm, Y_mm, Z_mm, Rx_deg, Ry_deg, Rz_deg]"""
        p = (ctypes.c_double * 6)()
        if self.lib.duco_get_tcp_pose(p) == 0:
            return [
                float(p[0] * 1000.0), # mm
                float(p[1] * 1000.0), # mm
                float(p[2] * 1000.0), # mm
                float(np.degrees(p[3])), # deg
                float(np.degrees(p[4])), # deg
                float(np.degrees(p[5]))  # deg
            ]
        return None

    def get_status(self):
        st = (ctypes.c_int8 * 4)()
        self.lib.duco_get_robot_state(st)
        joints = self.get_joints()
        tcp = self.get_tcp_pose()
        moving = self.is_moving()
        return {
            "connected": self.connected,
            "robot_state": int(st[0]),
            "program_state": int(st[1]),
            "safety_state": int(st[2]),
            "mode": int(st[3]),
            "is_moving": moving,
            "joints_deg": joints,
            "tcp_mm_deg": tcp
        }

    def cal_ik(self, target_tcp_mm_deg, q_near_deg=None):
        """Calculate Inverse Kinematics for target TCP pose."""
        if q_near_deg is None:
            q_near_deg = self.get_joints()
            if q_near_deg is None:
                return None
        
        p_in = (ctypes.c_double * 6)()
        p_in[0] = target_tcp_mm_deg[0] / 1000.0
        p_in[1] = target_tcp_mm_deg[1] / 1000.0
        p_in[2] = target_tcp_mm_deg[2] / 1000.0
        p_in[3] = math.radians(target_tcp_mm_deg[3])
        p_in[4] = math.radians(target_tcp_mm_deg[4])
        p_in[5] = math.radians(target_tcp_mm_deg[5])

        q_in = (ctypes.c_double * 6)()
        for i in range(6):
            q_in[i] = math.radians(q_near_deg[i])

        q_out = (ctypes.c_double * 6)()
        if self.lib.duco_cal_ik(q_out, p_in, q_in) == 0:
            return [float(np.degrees(q_out[i])) for i in range(6)]
        return None

    def wait_motion_done(self, timeout=60.0):
        """Polls until robot is completely idle and not moving."""
        time.sleep(0.4)
        t0 = time.time()
        while time.time() - t0 < timeout:
            st = self.get_status()
            if not st['is_moving'] and st['program_state'] in (0, 3, 4, 5):
                return True
            time.sleep(0.2)
        return False

    def movej(self, target_joints_deg, vel_deg=20.0, acc_deg=30.0, block=True):
        """Move joints directly using movej. Safety clamped speed."""
        # Safety velocity clamping: max 50 deg/s for agile test motion
        v_clamped = min(float(vel_deg), 50.0)
        a_clamped = min(float(acc_deg), 80.0)
        v_rad = math.radians(v_clamped)
        a_rad = math.radians(a_clamped)

        q_in = (ctypes.c_double * 6)()
        for i in range(6):
            q_in[i] = math.radians(target_joints_deg[i])

        ret = self.lib.duco_movej2(q_in, v_rad, a_rad, block)
        if block:
            self.wait_motion_done()
        return ret in (0, 4, 5) # 0: success, 4: ST_Finished, 5: ST_Interrupt

    def movel(self, target_tcp_mm_deg, vel_m_s=0.06, acc_m_s2=0.10, block=True):
        """Move linear in Cartesian space using movel. Safety clamped speed."""
        v_clamped = min(float(vel_m_s), 0.16) # max 160 mm/s
        a_clamped = min(float(acc_m_s2), 0.30)

        p_in = (ctypes.c_double * 6)()
        p_in[0] = target_tcp_mm_deg[0] / 1000.0
        p_in[1] = target_tcp_mm_deg[1] / 1000.0
        p_in[2] = target_tcp_mm_deg[2] / 1000.0
        p_in[3] = math.radians(target_tcp_mm_deg[3])
        p_in[4] = math.radians(target_tcp_mm_deg[4])
        p_in[5] = math.radians(target_tcp_mm_deg[5])

        ret = self.lib.duco_movel(p_in, v_clamped, a_clamped, block)
        if block:
            self.wait_motion_done()
        return ret in (0, 4, 5)

    def tcp_move(self, offset_mm_deg, vel_m_s=0.06, acc_m_s2=0.10, block=True):
        """Move relative in Tool frame [dx_mm, dy_mm, dz_mm, drx_deg, dry_deg, drz_deg]."""
        v_clamped = min(float(vel_m_s), 0.16)
        a_clamped = min(float(acc_m_s2), 0.30)
        off_in = (ctypes.c_double * 6)()
        off_in[0] = offset_mm_deg[0] / 1000.0
        off_in[1] = offset_mm_deg[1] / 1000.0
        off_in[2] = offset_mm_deg[2] / 1000.0
        off_in[3] = math.radians(offset_mm_deg[3]) if len(offset_mm_deg) > 3 else 0.0
        off_in[4] = math.radians(offset_mm_deg[4]) if len(offset_mm_deg) > 4 else 0.0
        off_in[5] = math.radians(offset_mm_deg[5]) if len(offset_mm_deg) > 5 else 0.0

        ret = self.lib.duco_tcp_move(off_in, v_clamped, a_clamped, block)
        if block:
            self.wait_motion_done()
        return ret in (0, 4, 5)

    def level_tcp_to_zero(self, vel_deg=6.0, acc_deg=10.0):
        """
        Step 1: Level robot TCP orientation to exact perpendicular (0.0° tilt).
        Rx = -180.0°, Ry = 0.0°, preserving X, Y, Z and Rz.
        """
        tcp = self.get_tcp_pose()
        if not tcp:
            return False, "Failed to read current TCP pose"
        
        target_tcp = [
            tcp[0], # keep X
            tcp[1], # keep Y
            tcp[2], # keep Z
            -180.0, # exact Rx 0° tilt (-180° points straight down)
            0.0,    # exact Ry 0° tilt
            tcp[5]  # keep current Rz rotation
        ]

        target_q = self.cal_ik(target_tcp)
        if not target_q:
            return False, "IK solution failed for leveled TCP"

        cur_q = self.get_joints()
        deltas = [abs(target_q[i] - cur_q[i]) for i in range(6)]
        if max(deltas) > 15.0:
            return False, f"Safety stop: unexpected large joint delta ({max(deltas):.1f}° > 15°)"

        print(f"[DucoController] Leveling TCP to 0°: Target J={np.round(target_q, 2)} (max delta={max(deltas):.2f}°)")
        success = self.movej(target_q, vel_deg=vel_deg, acc_deg=acc_deg, block=True)
        return success, target_q

    def set_m4_view(self):
        """
        Step 2: Define current leveled pose as 'm4_view'.
        """
        q = self.get_joints()
        tcp = self.get_tcp_pose()
        if not q or not tcp:
            return False, "Failed to read current pose"
        
        self.named_poses["m4_view"] = {
            "joints_deg": [round(v, 4) for v in q],
            "tcp_mm_deg": [round(v, 4) for v in tcp],
            "description": "Standard M4 screw inspection pose at ~30cm height, 0° perpendicular tilt",
            "timestamp": time.time()
        }
        self._save_named_poses()
        print(f"[DucoController] Successfully registered 'm4_view' pose: {self.named_poses['m4_view']}")
        return True, self.named_poses["m4_view"]

    def move_to_named_pose(self, name, vel_deg=20.0, acc_deg=30.0):
        """Move to a registered named pose ('folded_home', 'm4_view', etc.)"""
        if name not in self.named_poses:
            print(f"[DucoController] Error: Named pose '{name}' not found")
            return False
        target_q = self.named_poses[name]["joints_deg"]
        print(f"[DucoController] Moving to '{name}': {target_q}")
        success = self.movej(target_q, vel_deg=vel_deg, acc_deg=acc_deg, block=True)
        return bool(success)

if __name__ == "__main__":
    controller = DucoController()
    if controller.connect():
        st = controller.get_status()
        print("Robot Connected successfully!")
        print("Status:", json.dumps(st, indent=2))
        controller.disconnect()
    else:
        print("Failed to connect to Duco robot at 192.168.1.10:7003")
