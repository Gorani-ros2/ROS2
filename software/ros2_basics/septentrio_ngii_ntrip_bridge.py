#!/usr/bin/env python3
"""
Septentrio mosaic-go G5 NGII NTRIP RTK & ROS 2 NavSatFix Bridge Node
Location: /home/knu/workspaces/insta360/software/ros2_basics/septentrio_ngii_ntrip_bridge.py

Subscribes: None (Receives RTCM3 from NGII Caster, writes to Septentrio USB serial)
Publishes: /navsat/fix (sensor_msgs/msg/NavSatFix), /navsat/vel (geometry_msgs/msg/TwistStamped)
NTRIP Caster: rts1.ngii.go.kr:2101, Mountpoint: VRS-RTCM34, User: gorani, Pass: ngii
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from geometry_msgs.msg import TwistStamped
import serial
import serial.tools.list_ports
import glob
import time
import socket
import base64
import threading

def find_septentrio_usb_port():
    """Find Septentrio mosaic-go G5 receiver preferring persistent /dev/serial/by-id/ path."""
    by_id_ports = sorted(glob.glob('/dev/serial/by-id/usb-Septentrio*if00*'))
    if by_id_ports:
        return by_id_ports[0], f'Persistent Linux by-id Port ({by_id_ports[0]})'

    ports = serial.tools.list_ports.comports()
    for p in ports:
        if (p.vid == 0x152a and p.pid == 0x8231) or ('Septentrio' in (p.description or '')):
            if ':1.0' in p.hwid:
                return p.device, f'Septentrio Primary USB Port ({p.device})'

    return '/dev/ttyACM0', 'Fallback Port'

class SeptentrioNGIINtripBridge(Node):
    def __init__(self):
        super().__init__('septentrio_ngii_ntrip_bridge')

        detected_port, desc = find_septentrio_usb_port()

        # ROS 2 Parameters
        self.declare_parameter('port', 'auto')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('frame_id', 'gnss')
        self.declare_parameter('caster_host', 'rts1.ngii.go.kr')
        self.declare_parameter('caster_port', 2101)
        self.declare_parameter('mountpoint', 'VRS-RTCM34')
        self.declare_parameter('username', 'gorani')
        self.declare_parameter('password', 'ngii')

        param_port = self.get_parameter('port').value
        self.serial_port = detected_port if (param_port == 'auto' or not param_port) else param_port
        self.baudrate = self.get_parameter('baudrate').value
        self.frame_id = self.get_parameter('frame_id').value

        self.caster_host = self.get_parameter('caster_host').value
        self.caster_port = self.get_parameter('caster_port').value
        self.mountpoint = self.get_parameter('mountpoint').value
        self.username = self.get_parameter('username').value
        self.password = self.get_parameter('password').value

        self.get_logger().info(f"Target Receiver Port: {self.serial_port} ({desc})")
        self.get_logger().info(f"NGII NTRIP Caster: {self.caster_host}:{self.caster_port}/{self.mountpoint}")

        # ROS 2 Publishers
        self.fix_pub = self.create_publisher(NavSatFix, '/navsat/fix', 10)
        self.vel_pub = self.create_publisher(TwistStamped, '/navsat/vel', 10)

        # State
        self.running = True
        self.last_gga_sentence = ""
        self.last_fix_status = None

        # Current Fix State
        self.current_fix = NavSatFix()
        self.current_fix.header.frame_id = self.frame_id
        self.current_fix.status.status = NavSatStatus.STATUS_NO_FIX
        self.current_fix.status.service = (NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS |
                                           NavSatStatus.SERVICE_GALILEO | NavSatStatus.SERVICE_COMPASS)
        self.current_fix.latitude = 0.0
        self.current_fix.longitude = 0.0
        self.current_fix.altitude = 0.0
        self.current_fix.position_covariance = [10.89, 0.0, 0.0, 0.0, 10.89, 0.0, 0.0, 0.0, 43.56]
        self.current_fix.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN

        # Open Serial Port
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1.0)
            cmd = (
                b'\r\n\r\n'
                b'setCOMINComing, USB1, auto, RTCMv3\r\n'
                b'sso, Stream1, USB1, none\r\n'
                b'sno, Stream1, USB1, GGA, sec1\r\n'
            )
            self.ser.write(cmd)
            self.get_logger().info(f"Connected to Septentrio receiver on {self.serial_port}")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial port {self.serial_port}: {e}")
            raise e

        # 1Hz Publisher Timer
        self.timer = self.create_timer(1.0, self.timer_callback)

        # Threads
        self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
        self.ntrip_thread = threading.Thread(target=self.ntrip_client_loop, daemon=True)

        self.serial_thread.start()
        self.ntrip_thread.start()

    def timer_callback(self):
        self.current_fix.header.stamp = self.get_clock().now().to_msg()
        self.fix_pub.publish(self.current_fix)

    def serial_read_loop(self):
        while self.running and rclpy.ok():
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting:
                    raw_line = self.ser.readline().decode('ascii', errors='ignore').strip()
                    for tag in ['$GPGGA', '$GNGGA', '$GAGGA']:
                        pos = raw_line.find(tag)
                        if pos != -1:
                            clean_line = raw_line[pos:]
                            parts = clean_line.split('*')[0].split(',')
                            if len(parts) >= 10 and parts[0] == tag:
                                lat_str, lat_dir = parts[2], parts[3]
                                lon_str, lon_dir = parts[4], parts[5]
                                fix_q, num_sats = parts[6], parts[7]
                                hdop_str, alt_str = parts[8], parts[9]

                                if lat_str and lon_str:
                                    try:
                                        lat = float(lat_str[0:2]) + float(lat_str[2:]) / 60.0
                                        if lat_dir == 'S': lat = -lat
                                        lon = float(lon_str[0:3]) + float(lon_str[3:]) / 60.0
                                        if lon_dir == 'W': lon = -lon
                                        alt = float(alt_str) if alt_str else 0.0
                                        q = int(fix_q) if fix_q.isdigit() else 0
                                        sats = int(num_sats) if num_sats.isdigit() else 0
                                        hdop = float(hdop_str) if hdop_str else 1.0

                                        self.last_gga_sentence = clean_line
                                        self.update_fix(q, lat, lon, alt, sats, hdop)
                                    except ValueError:
                                        pass
                else:
                    time.sleep(0.01)
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"Serial Read Exception: {e}")
                time.sleep(0.1)

    def update_fix(self, fix_quality, lat, lon, alt, sats, hdop):
        has_coord = abs(lat) > 0.000001 and abs(lon) > 0.000001

        status_code = NavSatStatus.STATUS_NO_FIX
        if fix_quality == 1:
            status_code = NavSatStatus.STATUS_FIX
        elif fix_quality in [2, 4, 5]:
            status_code = NavSatStatus.STATUS_GBAS_FIX  # 2 = STATUS_GBAS_FIX (RTK Fixed/Float/DGPS)

        self.current_fix.latitude = lat if has_coord else 0.0
        self.current_fix.longitude = lon if has_coord else 0.0
        self.current_fix.altitude = alt if has_coord else 0.0
        self.current_fix.status.status = status_code

        # Dynamic Covariance Calculation (in m^2) based on Fix Quality & HDOP
        if fix_quality == 4:  # RTK Fixed (1cm precision)
            cov_h = 0.0001  # (0.01m)^2 = 0.0001 m^2
            cov_v = 0.0004  # (0.02m)^2 = 0.0004 m^2
        elif fix_quality == 5:  # RTK Float
            std_h = max(0.05, 0.15 * hdop)
            cov_h = round(std_h ** 2, 6)
            cov_v = round((std_h * 2.0) ** 2, 6)
        elif fix_quality in [1, 2]:  # Standalone 3D / DGPS
            std_h = max(0.2, 0.5 * hdop)
            cov_h = round(std_h ** 2, 6)
            cov_v = round((std_h * 2.0) ** 2, 6)
        else:
            cov_h = 10.89
            cov_v = 43.56

        self.current_fix.position_covariance = [cov_h, 0.0, 0.0, 0.0, cov_h, 0.0, 0.0, 0.0, cov_v]

        state_key = f"{fix_quality}_{has_coord}"
        if self.last_fix_status != state_key:
            q_name = {0: 'NO_FIX', 1: 'Standalone 3D', 2: 'DGPS', 4: 'RTK Fixed (1cm)', 5: 'RTK Float'}.get(fix_quality, f'Quality {fix_quality}')
            if has_coord:
                self.get_logger().info(f"GNSS Position Updated -> [{q_name}] (Sats: {sats}, HDOP: {hdop}) Lat: {lat:.7f}, Lon: {lon:.7f}, Alt: {alt:.2f}m")
            else:
                self.get_logger().info(f"Searching Satellites -> [{q_name}]")
            self.last_fix_status = state_key

    def ntrip_client_loop(self):
        while self.running and rclpy.ok():
            sock = None
            try:
                self.get_logger().info(f"Connecting to NGII Caster {self.caster_host}:{self.caster_port}...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10.0)
                sock.connect((self.caster_host, self.caster_port))

                auth_str = f"{self.username}:{self.password}"
                auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

                req = (
                    f"GET /{self.mountpoint} HTTP/1.1\r\n"
                    f"Host: {self.caster_host}:{self.caster_port}\r\n"
                    f"User-Agent: NTRIP SeptentrioNGIIBridge/1.0\r\n"
                    f"Authorization: Basic {auth_b64}\r\n"
                    f"Connection: close\r\n\r\n"
                )
                sock.sendall(req.encode('ascii'))

                response_hdr = b''
                while b'\r\n\r\n' not in response_hdr:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response_hdr += chunk

                first_line = response_hdr.split(b'\r\n')[0].decode('ascii', errors='ignore')
                if '200' in first_line or 'ICY 200' in first_line:
                    self.get_logger().info(f"NTRIP Connection Established! Mountpoint: '{self.mountpoint}'")
                else:
                    self.get_logger().error(f"NTRIP Caster Rejected Connection: {first_line}")
                    sock.close()
                    time.sleep(5.0)
                    continue

                sock.settimeout(2.0)
                last_gga_tx_time = 0

                while self.running and rclpy.ok():
                    now = time.time()
                    if now - last_gga_tx_time > 5.0:
                        if self.last_gga_sentence:
                            gga_data = (self.last_gga_sentence + "\r\n").encode('ascii')
                            sock.sendall(gga_data)
                            last_gga_tx_time = now
                        else:
                            fallback_gga = "$GNGGA,000000.00,3607.0685,N,12837.9199,E,1,08,1.0,137.0,M,0.0,M,,*47\r\n"
                            sock.sendall(fallback_gga.encode('ascii'))
                            last_gga_tx_time = now

                    try:
                        data = sock.recv(4096)
                        if not data:
                            self.get_logger().warn("NTRIP socket closed by server.")
                            break
                        if self.ser and self.ser.is_open:
                            self.ser.write(data)
                    except socket.timeout:
                        pass
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"NTRIP Client Exception: {e}. Reconnecting in 3s...")
                time.sleep(3.0)
            finally:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

    def destroy_node(self):
        self.running = False
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SeptentrioNGIINtripBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
