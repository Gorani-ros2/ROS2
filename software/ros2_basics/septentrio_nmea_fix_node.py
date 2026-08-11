#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from geometry_msgs.msg import TwistStamped
import serial
import time
import threading

class SeptentrioFixNode(Node):
    def __init__(self):
        super().__init__('septentrio_nmea_fix_node')
        
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('frame_id', 'gnss')
        
        self.port = self.get_parameter('port').value
        self.baud = self.get_parameter('baud').value
        self.frame_id = self.get_parameter('frame_id').value
        
        self.fix_pub = self.create_publisher(NavSatFix, '/fix', 10)
        self.vel_pub = self.create_publisher(TwistStamped, '/fix/velocity', 10)
        
        self.get_logger().info(f"Connecting to Septentrio GNSS on {self.port} ({self.baud} baud)...")
        
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            # Enable NMEA GGA, RMC, ZDA stream on USB1 port at 1Hz
            self.ser.write(b'sno, Stream1, USB1, GGA+RMC+ZDA+GSA, sec1\n')
            time.sleep(0.5)
            self.ser.read_all()
            self.get_logger().info("NMEA stream configured successfully on receiver.")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial port {self.port}: {e}")
            raise e

        self.running = True
        self.thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.thread.start()

    def read_serial_loop(self):
        while self.running and rclpy.ok():
            try:
                line = self.ser.readline().decode('ascii', errors='replace').strip()
                if not line or not line.startswith('$'):
                    continue
                
                parts = line.split('*')[0].split(',')
                msg_type = parts[0]
                
                if msg_type in ['$GNGGA', '$GPGGA']:
                    self.parse_gga(parts)
                elif msg_type in ['$GNRMC', '$GPRMC']:
                    self.parse_rmc(parts)
            except Exception as e:
                self.get_logger().warn(f"Serial read error: {e}")
                time.sleep(0.1)

    def parse_gga(self, parts):
        # NMEA GGA format:
        # $GNGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
        if len(parts) < 10:
            return
        
        lat_str = parts[2]
        lat_dir = parts[3]
        lon_str = parts[4]
        lon_dir = parts[5]
        fix_quality = parts[6]
        num_sats = parts[7]
        hdop = parts[8]
        alt_str = parts[9]
        
        fix_msg = NavSatFix()
        fix_msg.header.stamp = self.get_clock().now().to_msg()
        fix_msg.header.frame_id = self.frame_id
        
        # Status mapping
        status_code = NavSatStatus.STATUS_NO_FIX
        if fix_quality == '1':
            status_code = NavSatStatus.STATUS_FIX
        elif fix_quality in ['2', '4', '5']:
            status_code = NavSatStatus.STATUS_GBAS_FIX  # DGPS / RTK
            
        fix_msg.status.status = status_code
        fix_msg.status.service = NavSatStatus.SERVICE_GPS | NavSatStatus.SERVICE_GLONASS | NavSatStatus.SERVICE_GALILEO | NavSatStatus.SERVICE_COMPASS
        
        if lat_str and lon_str:
            try:
                lat = float(lat_str[0:2]) + float(lat_str[2:]) / 60.0
                if lat_dir == 'S':
                    lat = -lat
                    
                lon = float(lon_str[0:3]) + float(lon_str[3:]) / 60.0
                if lon_dir == 'W':
                    lon = -lon
                    
                fix_msg.latitude = lat
                fix_msg.longitude = lon
                
                if alt_str:
                    fix_msg.altitude = float(alt_str)
                    
                if hdop:
                    h_var = (float(hdop) * 3.0) ** 2
                    fix_msg.position_covariance = [h_var, 0.0, 0.0, 0.0, h_var, 0.0, 0.0, 0.0, h_var * 4.0]
                    fix_msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_APPROXIMATED
                    
                self.fix_pub.publish(fix_msg)
            except ValueError:
                pass

    def parse_rmc(self, parts):
        # NMEA RMC format for ground speed
        if len(parts) < 9:
            return
        speed_knots = parts[7]
        track_deg = parts[8]
        
        if speed_knots:
            try:
                speed_mps = float(speed_knots) * 0.514444
                vel_msg = TwistStamped()
                vel_msg.header.stamp = self.get_clock().now().to_msg()
                vel_msg.header.frame_id = self.frame_id
                vel_msg.twist.linear.x = speed_mps
                self.vel_pub.publish(vel_msg)
            except ValueError:
                pass

    def destroy_node(self):
        self.running = False
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SeptentrioFixNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
