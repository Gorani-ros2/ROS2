#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from geometry_msgs.msg import TwistStamped
import serial
import serial.tools.list_ports
import glob
import time
import struct
import math
import threading

def find_septentrio_usb_port():
    """Scan physical USB ports (/dev/ttyACM*, /dev/ttyUSB*) preferring ttyACM0 (USB1)."""
    physical_ports = sorted(glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))
    if not physical_ports:
        return '/dev/ttyACM0', 'Fallback Port'
    for p in physical_ports:
        if 'ACM0' in p or 'USB0' in p:
            return p, 'Primary USB Port (USB1)'
    return physical_ports[0], 'Secondary USB Port'

class SeptentrioNMEAFixNode(Node):
    def __init__(self):
        super().__init__('septentrio_gnss_driver')

        detected_port, desc = find_septentrio_usb_port()

        # ROS 2 Parameters
        self.declare_parameter('port', 'auto')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('frame_id', 'gnss')

        param_port = self.get_parameter('port').value
        if param_port == 'auto' or not param_port:
            self.serial_port = detected_port
            self.get_logger().info(f"Connected Physical USB Receiver Found: {self.serial_port} ({desc})")
        else:
            self.serial_port = param_port
            self.get_logger().info(f"Using Manually Specified Port: {self.serial_port}")

        self.baudrate = self.get_parameter('baudrate').value
        self.frame_id = self.get_parameter('frame_id').value

        # Official Septentrio Publishers (/navsatfix, /twist)
        self.fix_pub = self.create_publisher(NavSatFix, '/navsatfix', 10)
        self.vel_pub = self.create_publisher(TwistStamped, '/twist', 10)

        # State
        self.running = True
        self._last_fix_q = None

        # Continuous 1Hz NavSatFix State
        self.current_fix_msg = NavSatFix()
        self.current_fix_msg.header.frame_id = self.frame_id
        self.current_fix_msg.status.status = NavSatStatus.STATUS_NO_FIX
        self.current_fix_msg.status.service = NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS | NavSatStatus.SERVICE_GALILEO | NavSatStatus.SERVICE_COMPASS
        self.current_fix_msg.latitude = 0.0
        self.current_fix_msg.longitude = 0.0
        self.current_fix_msg.altitude = 0.0
        self.current_fix_msg.position_covariance = [10.89, 0.0, 0.0, 0.0, 10.89, 0.0, 0.0, 0.0, 43.56]
        self.current_fix_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN

        # Unconditional 1Hz ROS 2 Timer
        self.timer = self.create_timer(1.0, self.timer_callback)

        self.get_logger().info(f"Opening Septentrio Serial Port on {self.serial_port} ({self.baudrate} baud)...")
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1.0)
            self.ser.write(b'\r\n\r\nsso, Stream1, USB1, PVTGeodetic, sec1\r\nsno, Stream1, USB1, GGA+RMC, sec1\r\n')
            self.get_logger().info(f"Septentrio port {self.serial_port} initialized successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial port {self.serial_port}: {e}")
            raise e

        # Start Reader Thread
        self.reader_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.reader_thread.start()

    def timer_callback(self):
        self.current_fix_msg.header.stamp = self.get_clock().now().to_msg()
        self.fix_pub.publish(self.current_fix_msg)

    def read_serial_loop(self):
        buf = b''
        while self.running and rclpy.ok():
            try:
                if hasattr(self, 'ser') and self.ser and self.ser.is_open:
                    if self.ser.in_waiting:
                        buf += self.ser.read(self.ser.in_waiting)
                        if len(buf) > 16384:
                            buf = buf[-4096:]

                        # 1. Native SBF Frame Decoder (PVTGeodetic)
                        while True:
                            idx = buf.find(b'\xd3\x00\x15>')
                            if idx == -1:
                                break
                            if idx + 80 > len(buf):
                                break
                            payload = buf[idx+8:idx+80]
                            buf = buf[idx+80:]
                            mode = payload[2] & 0x0F
                            lat_r, lon_r, alt_m = struct.unpack('<ddd', payload[8:32])
                            lat_d = math.degrees(lat_r)
                            lon_d = math.degrees(lon_r)
                            self.update_fix_from_sbf(mode, 0, lat_d, lon_d, alt_m)

                        # 2. Fallback ASCII NMEA Parser
                        while b'\n' in buf:
                            line_raw, buf = buf.split(b'\n', 1)
                            idx = line_raw.find(b'$')
                            if idx != -1:
                                line = line_raw[idx:].decode('ascii', errors='ignore').strip()
                                parts = line.split('*')[0].split(',')
                                msg_type = parts[0]
                                if msg_type in ['$GNGGA', '$GPGGA']:
                                    self.parse_gga(parts)
                    else:
                        time.sleep(0.01)
            except Exception as e:
                if self.running:
                    self.get_logger().warn(f"Serial Read Error: {e}")
                time.sleep(0.1)

    def update_fix_from_sbf(self, mode, err, lat, lon, alt):
        has_coord = abs(lat) > 0.000001 and abs(lon) > 0.000001
        
        status_code = NavSatStatus.STATUS_NO_FIX
        if mode == 1:
            status_code = NavSatStatus.STATUS_FIX
        elif mode in [2, 4, 5]:
            status_code = NavSatStatus.STATUS_GBAS_FIX

        self.current_fix_msg.latitude = lat if has_coord else 0.0
        self.current_fix_msg.longitude = lon if has_coord else 0.0
        self.current_fix_msg.altitude = alt if has_coord else 0.0
        self.current_fix_msg.status.status = status_code
        cov = 0.0001 if mode == 4 else (0.25 if mode in [2, 5] else (0.01 if has_coord else 10.89))
        self.current_fix_msg.position_covariance = [cov, 0.0, 0.0, 0.0, cov, 0.0, 0.0, 0.0, cov * 4.0]

        state_key = f"{mode}_{has_coord}"
        if self._last_fix_q != state_key:
            q_name = {0:'NO_FIX (Searching Satellites)', 1:'Standalone 3D Fix', 2:'DGPS Fix', 4:'RTK Fixed', 5:'RTK Float'}.get(mode, f'Mode {mode}')
            if has_coord:
                self.get_logger().info(f"GNSS Satellite Position Fixed! [{q_name}] -> Lat: {lat:.7f}, Lon: {lon:.7f}, Alt: {alt:.2f}m")
            else:
                self.get_logger().info(f"GNSS Hardware Searching... [{q_name}] -> Waiting for Satellite Lock")
            self._last_fix_q = state_key

    def parse_gga(self, parts):
        if len(parts) < 10:
            return
        lat_str = parts[2]
        lon_str = parts[4]
        fix_quality = parts[6]
        alt_str = parts[9]
        if lat_str and lon_str:
            try:
                lat = float(lat_str[0:2]) + float(lat_str[2:]) / 60.0
                if parts[3] == 'S': lat = -lat
                lon = float(lon_str[0:3]) + float(lon_str[3:]) / 60.0
                if parts[5] == 'W': lon = -lon
                alt = float(alt_str) if alt_str else 0.0
                mode = int(fix_quality) if fix_quality.isdigit() else 1
                self.update_fix_from_sbf(mode, 0, lat, lon, alt)
            except ValueError:
                pass

    def destroy_node(self):
        self.running = False
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SeptentrioNMEAFixNode()
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
