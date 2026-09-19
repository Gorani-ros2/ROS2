#include <iostream>
#include <vector>
#include <memory>
#include <cstring>
#include <cmath>
#include "duco_ros_driver/DucoCobot.h"

static std::unique_ptr<DucoRPC::DucoCobot> g_robot = nullptr;

extern "C" {

int duco_connect(const char* ip, int port) {
    try {
        g_robot = std::make_unique<DucoRPC::DucoCobot>(std::string(ip), port);
        return g_robot->open();
    } catch (const std::exception& e) {
        std::cerr << "[DucoBridge] Error: " << e.what() << std::endl;
        return -1;
    }
}

int duco_disconnect() {
    if (g_robot) {
        g_robot->close();
        g_robot.reset();
        return 0;
    }
    return -1;
}

int duco_get_joints(double* q_out) {
    if (!g_robot) return -1;
    try {
        std::vector<double> q;
        g_robot->get_actual_joints_position(q);
        if (q.size() >= 6) {
            for (int i = 0; i < 6; ++i) q_out[i] = q[i];
            return 0;
        }
    } catch (...) {}
    return -1;
}

int duco_get_tcp_pose(double* pose_out) {
    if (!g_robot) return -1;
    try {
        std::vector<double> pose;
        g_robot->get_tcp_pose(pose);
        if (pose.size() >= 6) {
            for (int i = 0; i < 6; ++i) pose_out[i] = pose[i];
            return 0;
        }
    } catch (...) {}
    return -1;
}

int duco_get_robot_state(int8_t* state_out) {
    if (!g_robot) return -1;
    try {
        std::vector<int8_t> st;
        g_robot->get_robot_state(st);
        if (st.size() >= 4) {
            for (int i = 0; i < 4; ++i) state_out[i] = st[i];
            return 0;
        }
    } catch (...) {}
    return -1;
}

int duco_is_moving() {
    if (!g_robot) return -1;
    try {
        return g_robot->robotmoving() ? 1 : 0;
    } catch (...) {
        return -1;
    }
}

int duco_movej(const double* q_in, double v, double a, bool block) {
    if (!g_robot) return -1;
    try {
        std::vector<double> q(q_in, q_in + 6);
        return g_robot->movej(q, v, a, 0.0, block);
    } catch (...) {
        return -1;
    }
}

int duco_movej2(const double* q_in, double v_rad_s, double a_rad_s2, bool block) {
    if (!g_robot) return -1;
    try {
        std::vector<double> q(q_in, q_in + 6);
        return g_robot->movej2(q, v_rad_s, a_rad_s2, 0.0, block);
    } catch (...) {
        return -1;
    }
}

int duco_movel(const double* pose_in, double v, double a, bool block) {
    if (!g_robot) return -1;
    try {
        std::vector<double> p(pose_in, pose_in + 6);
        std::vector<double> q_near;
        return g_robot->movel(p, v, a, 0.0, q_near, "default", "default", block);
    } catch (...) {
        return -1;
    }
}

int duco_tcp_move(const double* offset_in, double v, double a, bool block) {
    if (!g_robot) return -1;
    try {
        std::vector<double> off(offset_in, offset_in + 6);
        return g_robot->tcp_move(off, v, a, 0.0, "default", block);
    } catch (...) {
        return -1;
    }
}

int duco_stop() {
    if (!g_robot) return -1;
    try {
        return g_robot->stop(true);
    } catch (...) {
        return -1;
    }
}

int duco_cal_ik(double* q_out, const double* pose_in, const double* q_near_in) {
    if (!g_robot) return -1;
    try {
        std::vector<double> p(pose_in, pose_in + 6);
        std::vector<double> q_near(q_near_in, q_near_in + 6);
        std::vector<double> q_res, tool, wobj;
        g_robot->cal_ikine(q_res, p, q_near, tool, wobj);
        if (q_res.size() >= 6) {
            for (int i = 0; i < 6; ++i) q_out[i] = q_res[i];
            return 0;
        }
    } catch (...) {}
    return -1;
}

int duco_cal_fk(double* pose_out, const double* q_in) {
    if (!g_robot) return -1;
    try {
        std::vector<double> q(q_in, q_in + 6);
        std::vector<double> p_res, tool, wobj;
        g_robot->cal_fkine(p_res, q, tool, wobj);
        if (p_res.size() >= 6) {
            for (int i = 0; i < 6; ++i) pose_out[i] = p_res[i];
            return 0;
        }
    } catch (...) {}
    return -1;
}

}
