#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import signal
import subprocess
import argparse
from datetime import datetime, timezone
import threading

# Sourcing commands to guarantee ROS 2 Humble environment
ROS_SOURCE = "source /opt/ros/humble/setup.bash && source /home/knu/workspaces/insta360/ouster_ros2/install/setup.bash"

# Auto-re-run ourselves if ROS 2 environment is not sourced yet
if "AMENT_PREFIX_PATH" not in os.environ:
    cmd = f"{ROS_SOURCE} && python3 " + " ".join(f'"{a}"' for a in sys.argv)
    result = subprocess.run(cmd, shell=True, executable='/bin/bash')
    sys.exit(result.returncode)

# Safe to import ROS 2 libraries now
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import sensor_msgs_py.point_cloud2 as pc2
import yaml

from rclpy.qos import qos_profile_sensor_data

try:
    from ouster_sensor_msgs.srv import GetMetadata as OusterGetMetadata
    _HAS_OUSTER_MSGS = True
except ImportError:
    _HAS_OUSTER_MSGS = False
    print("[Warn] ouster_sensor_msgs not found. Metadata service query will be skipped.")

class SingleCloudGrabber(Node):
    def __init__(self):
        super().__init__('single_cloud_grabber')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/ouster/points',
            self.listener_callback,
            qos_profile_sensor_data)
        self.msg = None

    def listener_callback(self, msg):
        self.msg = msg

def grab_single_pointcloud(timeout=10.0):
    """Subscribe to /ouster/points and capture exactly one pointcloud frame."""
    initialized_here = False
    if not rclpy.ok():
        rclpy.init(args=None)
        initialized_here = True
    grabber = SingleCloudGrabber()
    
    start_time = time.time()
    while grabber.msg is None and (time.time() - start_time < timeout):
        rclpy.spin_once(grabber, timeout_sec=0.1)
        
    msg = grabber.msg
    grabber.destroy_node()
    if initialized_here:
        rclpy.shutdown()
    return msg

def save_pcd(msg, filepath):
    """Parse PointCloud2 message and write it as a standard ASCII PCD file."""
    if msg is None:
        print("[Error] Failed to capture PointCloud2 message (timeout).")
        return False
        
    print(f"[LiDAR] Parsing frame containing {msg.width * msg.height} points...")
    points_list = []
    try:
        # Read X, Y, Z and intensity fields
        for p in pc2.read_points(msg, field_names=("x", "y", "z", "intensity"), skip_nans=True):
            points_list.append(p)
    except Exception as e:
        print(f"[Error] Failed to read pointcloud data: {e}")
        return False

    print(f"[LiDAR] Saving {len(points_list)} valid points to: {filepath}")
    with open(filepath, "w") as f:
        f.write("# .PCD v0.7 - Point Cloud Data file format\n")
        f.write("VERSION 0.7\n")
        f.write("FIELDS x y z intensity\n")
        f.write("SIZE 4 4 4 4\n")
        f.write("TYPE F F F F\n")
        f.write("COUNT 1 1 1 1\n")
        f.write(f"WIDTH {len(points_list)}\n")
        f.write("HEIGHT 1\n")
        f.write("VIEWPOINT 0 0 0 1 0 0 0\n")
        f.write(f"POINTS {len(points_list)}\n")
        f.write("DATA ascii\n")
        for p in points_list:
            # Format: X Y Z Intensity
            f.write(f"{p[0]:.4f} {p[1]:.4f} {p[2]:.4f} {p[3]:.4f}\n")
    return True

def run_cmd(cmd, get_output=False):
    """Run a shell command with the ROS 2 environment sourced."""
    full_cmd = f"{ROS_SOURCE} && {cmd}"
    if get_output:
        result = subprocess.run(full_cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8', errors='replace').strip()
        stderr = result.stderr.decode('utf-8', errors='replace').strip()
        return result.returncode == 0, stdout, stderr
    else:
        result = subprocess.run(full_cmd, shell=True, executable='/bin/bash')
        return result.returncode == 0

def start_process(cmd):
    """Start a background process with the ROS 2 environment sourced, using a new session group."""
    full_cmd = f"{ROS_SOURCE} && {cmd}"
    return subprocess.Popen(full_cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

def stop_process(proc):
    """Gracefully terminate a background process using SIGINT in its process group."""
    if proc and proc.poll() is None:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGINT)
            proc.wait(timeout=5)
        except Exception as e:
            print(f"[Warn] Error stopping process: {e}")
            try:
                proc.terminate()
            except:
                pass

def verify_ouster_topics(timeout=15.0):
    """Check if /ouster/points, /ouster/imu and /navsat/fix topics are active."""
    print("[LiDAR] Waiting for active PointCloud and IMU topics...")
    start_time = time.time()
    has_points = False
    has_imu = False
    has_rtk = False

    while time.time() - start_time < timeout:
        success, stdout, _ = run_cmd("ros2 topic list", get_output=True)
        if success:
            topics = stdout.splitlines()
            has_points = any("/ouster/points" in t for t in topics)
            has_imu = any("/ouster/imu" in t for t in topics)
            has_rtk = any("/navsat/fix" in t for t in topics)
            if has_points and has_imu:
                print(f"[LiDAR] Active LiDAR topics detected in {time.time() - start_time:.2f}s!")
                if has_rtk:
                    print("[RTK]   ✅ /navsat/fix active! RTK 1cm coordinates will be recorded in rosbag.")
                else:
                    print("[RTK]   ⚠️ /navsat/fix topic not detected. (Tip: Run septentrio_ngii_ntrip_bridge.py if RTK position is needed)")
                return True
        time.sleep(0.5)
    return False

def extract_media_filenames(stdout):
    """Extract URLs of captured files from main.cpp stdout."""
    filenames = []
    for line in stdout.splitlines():
        if "url:" in line or "-" in line:
            parts = line.strip().split()
            if len(parts) >= 2:
                url = parts[-1]
                if url.startswith("/"):
                    filenames.append(url)
    return filenames

def get_sensor_ip():
    """Read sensor IP from my_ouster_params.yaml or return default."""
    default_ip = "169.254.129.201"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "my_ouster_params.yaml")
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r") as f:
                params = yaml.safe_load(f)
                if params and "/ouster/os_driver" in params:
                    ros_params = params["/ouster/os_driver"].get("ros__parameters", {})
                    sensor_ip = ros_params.get("sensor_hostname", default_ip)
                    return sensor_ip
        except Exception as e:
            print(f"[PCAP] Error parsing my_ouster_params.yaml: {e}")
    return default_ip

def query_and_save_metadata(save_path):
    """Query the Ouster metadata via ROS 2 service and save it to a JSON file."""
    if not _HAS_OUSTER_MSGS:
        print("[Warn] Skipping metadata query: ouster_sensor_msgs package not available.")
        return False

    print("[LiDAR] Querying active Ouster sensor metadata via ROS 2 service...")

    initialized_here = False
    if not rclpy.ok():
        rclpy.init(args=None)
        initialized_here = True

    node = Node('metadata_grabber')
    client = node.create_client(OusterGetMetadata, '/ouster/get_metadata')

    try:
        if not client.wait_for_service(timeout_sec=5.0):
            print("[Warn] /ouster/get_metadata service not available.")
            return False

        req = OusterGetMetadata.Request()
        future = client.call_async(req)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)

        if future.done():
            response = future.result()
            with open(save_path, "w") as f:
                f.write(response.metadata)
            print(f"[LiDAR] Metadata JSON saved successfully to: {save_path}")
            return True
        else:
            print("[Error] Service call to /ouster/get_metadata timed out.")
            return False
    except Exception as e:
        print(f"[Error] Failed during metadata query: {e}")
        return False
    finally:
        node.destroy_node()
        if initialized_here and rclpy.ok():
            rclpy.shutdown()

def get_lidar_interface(sensor_ip):
    """Detect the network interface that routes to the LiDAR sensor IP."""
    try:
        result = subprocess.run(
            f"ip route get {sensor_ip}",
            shell=True, capture_output=True, text=True
        )
        match = re.search(r'dev\s+(\S+)', result.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "eno1"  # fallback to default ethernet interface

def start_pcap_capture(save_dir):
    """Start tcpdump in background to capture Ouster UDP packets."""
    sensor_ip = get_sensor_ip()
    iface = get_lidar_interface(sensor_ip)
    pcap_path = os.path.join(save_dir, "ouster.pcap")
    print(f"[PCAP] Starting raw packet capture to: {pcap_path}")
    print(f"[PCAP] Target Sensor IP: {sensor_ip} | Interface: {iface}")
    
    cmd = f"sudo -n tcpdump -i {iface} 'host {sensor_ip} and udp' -w {pcap_path}"
    proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setpgrp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    return proc

def stop_pcap_capture(proc):
    """Gracefully terminate background tcpdump process."""
    if proc and proc.poll() is None:
        print("[PCAP] Stopping tcpdump process...")
        try:
            pgid = os.getpgid(proc.pid)
            subprocess.run(f"sudo -n kill -INT -- -{pgid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.wait(timeout=5)
            print("[PCAP] PCAP capture stopped and file saved.")
        except Exception as e:
            print(f"[PCAP] [Warn] Error stopping tcpdump: {e}")
            try:
                proc.terminate()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Insta360 X5 & Ouster OS0-128 LiDAR & RTK GNSS Synchronized Controller")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--record", action="store_true", help="Start continuous synchronized recording (stop manually)")
    group.add_argument("--record-time", action="store_true", help="Start time-bounded synchronized recording (default 10s)")
    group.add_argument("--photo", action="store_true", help="Capture synchronized photo (single .jpg & .pcd frame)")
    
    parser.add_argument("--res", default="4K", help="Camera video resolution (e.g., 4K, 8K, 5.7K)")
    parser.add_argument("--fps", default="30", help="Camera frame rate (fps, e.g., 30, 24, 60)")
    parser.add_argument("--duration", type=int, default=10, help="Recording duration in seconds (for --record-time, default: 10)")
    parser.add_argument("--lidar-hz", type=int, default=10, help="LiDAR pointcloud recording rate in Hz (default: 10). Values < 10 will throttle /ouster/points.")
    parser.add_argument("--pcap", action="store_true", help="Record Ouster raw packets as a PCAP file using tcpdump (requires sudo)")
    parser.add_argument("--no-download", action="store_true", help="Skip automatic downloading of recorded camera files over USB HTTP tunnel")
    
    args = parser.parse_args()
    
    # Establish save directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bag_root = os.path.expanduser("~/bags")
    os.makedirs(bag_root, exist_ok=True)
    
    if args.record:
        mode_prefix = "sync_record"
    elif args.record_time:
        mode_prefix = "sync_record_time"
    else:
        mode_prefix = "sync_photo"
        
    lidar_hz = args.lidar_hz if hasattr(args, 'lidar_hz') else 10
    hz_suffix = f"_{lidar_hz}hz" if (args.record or args.record_time) else ""
    save_dir = os.path.join(bag_root, f"{mode_prefix}_{timestamp}{hz_suffix}")
    os.makedirs(save_dir, exist_ok=True)
    
    print("\n==================================================")
    print("  Simultaneous LiDAR + Camera + RTK Controller   ")
    print("==================================================")
    
    # Pre-configure resolution if recording
    if args.record or args.record_time:
        print(f"Target Camera Config: {args.res} @ {args.fps}fps")
        print("[Camera] Configuring resolution...")
        cam_config_cmd = f"./run.sh --set-res {args.res} {args.fps}"
        if not run_cmd(cam_config_cmd):
            print("[Error] Failed to configure camera resolution. Exiting.")
            sys.exit(1)
            
    # Start Ouster LiDAR driver
    print("[LiDAR] Launching Ouster driver node...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(current_dir, "my_ouster_params.yaml")
    ouster_cmd = f"ros2 launch ouster_ros driver.launch.py params_file:={yaml_path} viz:=False"
    ouster_proc = start_process(ouster_cmd)
    
    # Wait for topics to become active
    if not verify_ouster_topics():
        print("[Error] LiDAR failed to stream topics in time. Exiting.")
        stop_process(ouster_proc)
        sys.exit(1)
        
    # Query and save metadata JSON
    query_and_save_metadata(os.path.join(save_dir, "metadata.json"))
        
    if args.record or args.record_time:
        # === RECORDING / RECORD-TIME MODE ===
        # 1. Start Camera Recording
        print("[Camera] Starting recording...")
        cam_start_cmd = "./run.sh --start-only"
        if not run_cmd(cam_start_cmd):
            print("[Error] Failed to start camera recording. Exiting.")
            stop_process(ouster_proc)
            sys.exit(1)
        t_cam_start = time.time()
            
        # 2. Start LiDAR Throttle (if needed) and Rosbag Recording
        throttle_proc = None
        points_topic = "/ouster/points"  # default: record sensor-native rate
        if lidar_hz < 10:
            points_topic = "/ouster/points_throttled"
            throttle_cmd = (
                f"ros2 run topic_tools throttle messages "
                f"/ouster/points {lidar_hz} {points_topic}"
            )
            print(f"[LiDAR] Throttling /ouster/points → {points_topic} at {lidar_hz} Hz")
            throttle_proc = start_process(throttle_cmd)
            time.sleep(1.0)
            if throttle_proc.poll() is not None:
                print("[Error] Throttle node exited immediately. Aborting.")
                run_cmd("./run.sh --stop")
                stop_process(ouster_proc)
                sys.exit(1)

        print(f"[LiDAR+RTK] Starting rosbag2 recording → {save_dir}/bag")
        record_topics = [
            points_topic,
            "/ouster/imu",
            "/ouster/lidar_packets",
            "/ouster/imu_packets",
            "/ouster/metadata",
            "/tf",
            "/tf_static",
            "/navsat/fix",
            "/navsat/vel",
            "/gps/fix",
            "/gps/pos",
            "/gps/vel"
        ]
        topics_str = " ".join(record_topics)
        bag_cmd = f"ros2 bag record {topics_str} -o {save_dir}/bag"
        bag_proc = start_process(bag_cmd)
        t_bag_start = time.time()
        
        # Compute and save time sync metadata
        cam_to_bag_offset = t_bag_start - t_cam_start
        lidar_scan_period = round(1000.0 / lidar_hz, 2) if lidar_hz > 0 else 0
        cam_frames_per_scan = round(int(args.fps) / lidar_hz, 4) if lidar_hz > 0 else 0
        sync_info = {
            "camera_fps": int(args.fps),
            "lidar_hz": lidar_hz,
            "lidar_hz_throttled": lidar_hz < 10,
            "points_topic": points_topic,
            "camera_frame_period_ms": round(1000.0 / int(args.fps), 2),
            "lidar_scan_period_ms": lidar_scan_period,
            "camera_frames_per_lidar_scan": cam_frames_per_scan,
            "t_cam_start_unix": t_cam_start,
            "t_bag_start_unix": t_bag_start,
            "cam_to_bag_offset_sec": round(cam_to_bag_offset, 4),
            "recorded_topics": record_topics,
            "note": (
                f"Camera recording was started {cam_to_bag_offset:.2f}s before rosbag. "
                "The first LiDAR scan in the bag may precede the first valid camera frame by this amount. "
                "Use cam_to_bag_offset_sec to align camera timestamps to rosbag time."
            ),
            "recording_start_iso": datetime.fromtimestamp(t_cam_start, tz=timezone.utc).isoformat()
        }
        sync_info_path = os.path.join(save_dir, "sync_info.json")
        with open(sync_info_path, "w") as f:
            json.dump(sync_info, f, indent=2)
        print(f"[Sync]  Timing & topic info saved → {sync_info_path}")
        print(f"[Sync]  Camera start → Bag start offset: {cam_to_bag_offset:.3f}s")
        
        # 3. Start PCAP Recording (optional)
        pcap_proc = None
        keep_alive_thread = None
        stop_sudo_thread = None
        if args.pcap:
            print("[PCAP] Validating sudo access for tcpdump...")
            try:
                subprocess.run("sudo -v", shell=True, check=True)
            except subprocess.CalledProcessError:
                print("[PCAP] [Error] Sudo validation failed. Cannot record PCAP.")
                stop_process(bag_proc)
                stop_process(ouster_proc)
                run_cmd("./run.sh --stop")
                sys.exit(1)
            
            stop_sudo_thread = threading.Event()
            def sudo_keep_alive():
                while not stop_sudo_thread.is_set():
                    subprocess.run("sudo -v", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    stop_sudo_thread.wait(60)
            
            keep_alive_thread = threading.Thread(target=sudo_keep_alive, daemon=True)
            keep_alive_thread.start()
            
            pcap_proc = start_pcap_capture(save_dir)
            time.sleep(0.5)
            if pcap_proc.poll() is not None:
                print("[PCAP] [Error] tcpdump process exited immediately. Check interface or sudo permissions.")
        
        print("\n--------------------------------------------------")
        print("[System] Synchronized recording is active!")
        print("--------------------------------------------------\n")
        
        try:
            start_record_time = time.time()
            if args.record:
                print("Press ENTER to stop recording...")
                try:
                    input()
                except EOFError:
                    print("[System] Non-interactive environment detected (stdin closed).")
                    print("Recording... Press Ctrl+C to stop.")
                    while True:
                        time.sleep(1)
            else:  # --record-time mode
                print(f"Recording data for {args.duration} seconds...")
                while time.time() - start_record_time < args.duration:
                    time.sleep(0.5)
                    elapsed = int(time.time() - start_record_time)
                    sys.stdout.write(f"\rElapsed time: {elapsed}s / {args.duration}s")
                    sys.stdout.flush()
                print()
        except KeyboardInterrupt:
            print("\n[System] Interrupted by user.")
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            print("\n--------------------------------------------------")
            print("[System] Stopping recording processes...")
            
            if pcap_proc:
                stop_pcap_capture(pcap_proc)
            if keep_alive_thread:
                stop_sudo_thread.set()
                keep_alive_thread.join(timeout=1.0)
                
            print("[LiDAR+RTK] Finalizing rosbag...")
            stop_process(bag_proc)
            
            if throttle_proc:
                print("[LiDAR] Stopping throttle node...")
                stop_process(throttle_proc)
            
            print("[Camera] Requesting recording stop...")
            success, stdout, stderr = run_cmd("./run.sh --stop", get_output=True)
            if not success:
                print("[Error] Failed to stop camera cleanly.")
                stop_process(ouster_proc)
                sys.exit(1)
                
            media_urls = extract_media_filenames(stdout)
            if not media_urls:
                print("[Warn] No recorded file URLs found in stop response.")
            elif getattr(args, 'no_download', False):
                print(f"[Camera] Detected {len(media_urls)} file(s). Automatic download skipped (--no-download set).")
                for url in media_urls:
                    print(f"  - Camera file URL: {url}")
            else:
                print(f"[Camera] Detected {len(media_urls)} files to download.")
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                try:
                    for url in media_urls:
                        filename = os.path.basename(url)
                        local_dest = os.path.join(save_dir, filename)
                        print(f"[Download] Fetching camera file: {filename} (Press Ctrl+C to cancel download if frozen)")
                        download_cmd = f"./run.sh --download {url} {local_dest}"
                        run_cmd(download_cmd)
                except KeyboardInterrupt:
                    print("\n[Download] [Warn] Download interrupted by user (Ctrl+C). Camera file remains on camera SD card.")
                
    else:
        # === PHOTO CAPTURE MODE ===
        print("\n--------------------------------------------------")
        print("[System] Triggering simultaneous photo capture...")
        print("--------------------------------------------------\n")
        
        print("[Camera] Capturing photo...")
        success, stdout, stderr = run_cmd("./run.sh --take-photo", get_output=True)
        if not success:
            print("[Error] Failed to capture camera photo.")
            stop_process(ouster_proc)
            sys.exit(1)
            
        photo_urls = extract_media_filenames(stdout)
        
        print("[LiDAR] Capturing single pointcloud frame...")
        pc_msg = grab_single_pointcloud(timeout=10.0)
        pcd_filepath = os.path.join(save_dir, "lidar_capture.pcd")
        save_pcd(pc_msg, pcd_filepath)
        
        if not photo_urls:
            print("[Warn] No photo URLs returned from camera.")
        else:
            for url in photo_urls:
                filename = os.path.basename(url)
                local_dest = os.path.join(save_dir, filename)
                print(f"[Download] Fetching camera photo: {filename}")
                download_cmd = f"./run.sh --download {url} {local_dest}"
                run_cmd(download_cmd)

    print("[LiDAR] Shutting down driver node...")
    stop_process(ouster_proc)
    
    print("\n==================================================")
    print("      Synchronized Operation Complete             ")
    print(f"Saved Output Directory: {save_dir}")
    print("==================================================")

if __name__ == "__main__":
    main()
