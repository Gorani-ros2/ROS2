# 💻 RTK telemetry MQTT 서버 DB 연동 파이프라인 (RTK Telemetry MQTT-DB Bridge)

> **작성 일자**: 2026-08-18  
> **작성 장비**: `knu laptop` (KNU 노트북 PC / Linux Ubuntu 22.04 LTS)  
> **작성 AI**: Antigravity (Google DeepMind Team)  
> **파일명 규격**: `rtk-mqtt-db-bridge.md`  

---

## 📌 Executive Abstract (상세 요약 및 초록)

본 문서는 **Septentrio mosaic-go G5 RTK GNSS 수신기**가 Teltonika RUT241 LTE 라우터를 통해 국토지리정보원(NGII) NTRIP 서버로부터 수신받은 센티미터급 정밀 위치 데이터(`/navsat/fix`)를 ROS 2 노드 기반으로 수집하여, **MQTT 프로토콜**을 거쳐 **서버의 시세밀/공간 데이터베이스(PostgreSQL / TimescaleDB 또는 InfluxDB)**에 실시간으로 적재하는 엔드투엔드 파이프라인 기술 명세서입니다.

자율주행 및 디지털 트윈(Digital Twin) 기반 360 RGB 카메라 + 3D 라이다 융합 매핑 수행 시, 이동 로봇의 정밀 궤적 및 위치 무결성 데이터를 중앙 관제 서버로 실시간 송신하기 위한 MQTT 통신 표준, JSON 페이로드 규격, 데이터베이스 테이블 스키마, 파이썬 브릿지 소스코드 및 무선 네트워크 재연결(Auto-Reconnect) 트러블슈팅 Q&A를 축약 없이 기술합니다.

---

## 1. 개요 및 파이프라인 (Overview & Pipeline)

* **목적**: NGII RTK 보정 데이터 기반 센티미터급 위치 정보를 중앙 서버 DB에 저지연(Low-Latency) 적재 및 디지털 트윈 관제 렌더링 연동.
* **전체 시스템 아키텍처 흐름도 (Mermaid)**:

```mermaid
flowchart LR
    subgraph NGII ["국토지리정보원 (NGII)"]
        NTRIP_SVR["NTRIP Server\n(rtk.ngii.go.kr:2101)"]
    end

    subgraph Robot System ["온보드 로봇 시스템 (Onboard Robot System)"]
        RUT241["Teltonika RUT241\n4G LTE Router"]
        GNSS["Septentrio mosaic-go G5\nRTK Receiver"]
        ROS2_NODE["ROS 2 NMEA/Fix Parser & MQTT Bridge Node\n(rtk_mqtt_db_bridge.py)"]
        
        RUT241 <-->|LTE 무선 통신| NTRIP_SVR
        RUT241 -->|RTCM3 보정 신호 (NTRIP)| GNSS
        GNSS -->|SBF / NavSatFix 10Hz| ROS2_NODE
    end

    subgraph Server System ["중앙 관제 및 서버 (Control Center Server)"]
        MQTT_BROKER["MQTT Broker\n(Mosquitto / EMQX)"]
        DB_SUBSCRIBER["DB Ingestion Worker\n(Python Daemon)"]
        DB["Spatial DB\n(PostgreSQL / TimescaleDB)"]
        
        ROS2_NODE -->|MQTT Publish (QoS 1)\nTopic: telemetry/robot/rtk| MQTT_BROKER
        MQTT_BROKER -->|MQTT Subscribe| DB_SUBSCRIBER
        DB_SUBSCRIBER -->|SQL Insert / Bulk Write| DB
    end
```

---

## 2. 🔗 관련 하드웨어 장비 문서 십자 링크 (Cross-Links)

* 📡 **연동 GNSS 수신기**: [`Septentrio mosaic-go G5 P3H 수신기`](../../hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md)
* 🌐 **연동 4G LTE 라우터**: [`Teltonika RUT241 라우터`](../../hardware/support_sensors/router/teltonika-rut241.md)
* 📹 **연동 3D 라이다**: [`Ouster OS0-128 라이다`](../../hardware/vision_sensors/lidar/ouster-os0-128.md)
* ⏱️ **하드웨어 PPS 동기화**: [`LiDAR + RTK PPS 동기화 및 ROS2 Bag 녹화`](../sensorfusion/lidar-rtk-pps-sync-bag.md)

---

## 3. 필수 환경 및 패키지 의존성 (Prerequisites & Dependencies)

* **운영체제 및 환경**: Ubuntu 22.04 LTS (ROS 2 Humble Hawksbill)
* **Python 라이브러리**:
  * `paho-mqtt` (`pip install paho-mqtt`)
  * `rclpy` (ROS 2 Python Client Library)
  * `psycopg2-binary` (PostgreSQL DB 커넥터, 서버측)
* **MQTT 브로커 및 포트**:
  * Mosquitto / EMQX Broker (Default Port: `1883` / TLS: `8883`)

---

## 4. 소스코드 및 구동 가이드 (Source Code & Execution)

### 🚀 1. ROS 2 MQTT 파이썬 브릿지 노드 (`rtk_mqtt_db_bridge.py`)

Below is the ROS 2 Humble python node that subscribes to `/navsat/fix`, formats the RTK telemetry into a JSON payload, and publishes to the MQTT broker:

```python
#!/usr/bin/env python3
"""
RTK Telemetry ROS 2 to MQTT Bridge Node
Subscribes: /navsat/fix (sensor_msgs/msg/NavSatFix)
Publishes: MQTT Topic 'telemetry/robot/rtk'
"""

import json
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import paho.mqtt.client as mqtt

class RTKMQTTBridgeNode(Node):
    def __init__(self):
        super().__init__('rtk_mqtt_db_bridge')
        
        # ROS 2 Parameters
        self.declare_parameter('mqtt_broker_ip', '218.150.16.158')  # Main Control Center Public IP
        self.declare_parameter('mqtt_broker_port', 1883)
        self.declare_parameter('mqtt_topic', 'robot/sensor/rtk')
        self.declare_parameter('robot_id', 'robot_andong_01')
        
        self.broker_ip = self.get_parameter('mqtt_broker_ip').value
        self.broker_port = self.get_parameter('mqtt_broker_port').value
        self.mqtt_topic = self.get_parameter('mqtt_topic').value
        self.robot_id = self.get_parameter('robot_id').value

        # Initialize MQTT Client
        self.mqtt_client = mqtt.Client(client_id=f"ros2_{self.robot_id}")
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
        try:
            self.mqtt_client.connect(self.broker_ip, self.broker_port, keepalive=60)
            self.mqtt_client.loop_start()
            self.get_logger().info(f"Connected to MQTT Broker at {self.broker_ip}:{self.broker_port}")
        except Exception as e:
            self.get_logger().error(f"MQTT Connection failed: {e}")

        # Subscribe to NavSatFix
        self.subscription = self.create_subscription(
            NavSatFix,
            '/navsat/fix',
            self.navsat_callback,
            10
        )

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.get_logger().info("MQTT Connection Successful (rc=0)")
        else:
            self.get_logger().warn(f"MQTT Connection Error code: {rc}")

    def on_mqtt_disconnect(self, client, userdata, rc):
        self.get_logger().warn(f"MQTT Disconnected (rc={rc}). Attempting auto-reconnect...")

    def navsat_callback(self, msg: NavSatFix):
        # Determine RTK Fix Status String
        # status.status: -1=NO_FIX, 0=FIX (Standalone), 1=SBAS_FIX, 2=GBAS_FIX (RTK)
        status_str = "UNKNOWN"
        if msg.status.status == 2:
            status_str = "RTK_FIXED"
        elif msg.status.status == 1:
            status_str = "RTK_FLOAT_OR_DGPS"
        elif msg.status.status == 0:
            status_str = "STANDALONE_3D_FIX"
        else:
            status_str = "NO_FIX"

        # Calculate estimated horizontal error (1-sigma, meters)
        cov_e = msg.position_covariance[0]  # East variance
        cov_n = msg.position_covariance[4]  # North variance
        horizontal_std = (cov_e + cov_n) ** 0.5 if (cov_e >= 0 and cov_n >= 0) else 999.0

        # Construct Telemetry Payload
        payload = {
            "robot_id": self.robot_id,
            "timestamp": msg.header.stamp.sec + (msg.header.stamp.nanosec * 1e-9),
            "local_sys_time": time.time(),
            "latitude": msg.latitude,
            "longitude": msg.longitude,
            "altitude": msg.altitude,
            "rtk_status": status_str,
            "status_code": int(msg.status.status),
            "service_mask": int(msg.status.service),  # Bitmask 15 = GPS+GLONASS+BeiDou+Galileo
            "horizontal_accuracy_m": round(horizontal_std, 4),
            "position_covariance": list(msg.position_covariance)
        }

        # Publish MQTT message (QoS 1 for reliable delivery)
        json_msg = json.dumps(payload)
        res = self.mqtt_client.publish(self.mqtt_topic, json_msg, qos=1)
        if res.rc == mqtt.MQTT_ERR_SUCCESS:
            self.get_logger().debug(f"Published RTK Telemetry: Lat {msg.latitude:.7f}, Lon {msg.longitude:.7f}, Status: {status_str}")
        else:

            self.get_logger().warn(f"Failed to publish MQTT message, rc: {res.rc}")

    def destroy_node(self):
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RTKMQTTBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

### 🧪 1.1 로컬 테스트용 모의 MQTT 브로커 (`mock_mqtt_broker.py`)

서버 접속 전, 로봇 온보드 환경(127.0.0.1:1883)에서 텔레메트리 페이로드를 즉시 검증하는 파이썬 스크립트:

```bash
# 터미널 1: 로컬 모의 MQTT 브로커 실행
python3 ~/workspaces/insta360/software/protocol/mock_mqtt_broker.py

# 터미널 2: RTK MQTT 브릿지 노드 실행 (로컬 모드)
source /opt/ros/humble/setup.bash
python3 ~/workspaces/insta360/software/protocol/rtk_mqtt_db_bridge.py --ros-args -p mqtt_broker_ip:=127.0.0.1
```

---

### 💾 2. 서버 측 Database Table 스키마 (PostgreSQL / TimescaleDB)

```sql
-- RTK Telemetry Storage Table Schema
CREATE TABLE IF NOT EXISTS robot_rtk_telemetry (
    id BIGSERIAL PRIMARY KEY,
    robot_id VARCHAR(50) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    altitude DOUBLE PRECISION NOT NULL,
    rtk_status VARCHAR(30) NOT NULL,
    status_code INT NOT NULL,
    service_mask INT NOT NULL,
    horizontal_accuracy_m REAL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for Spatial Trajectory and Time Range Query Optimization
CREATE INDEX idx_rtk_robot_time ON robot_rtk_telemetry (robot_id, recorded_at DESC);
CREATE INDEX idx_rtk_status ON robot_rtk_telemetry (rtk_status);
```

---

## 5. 발행 및 구독 토픽 규격 (Topic Specifications)

### 📡 ROS 2 & MQTT 토픽 매핑 표

| 구분 | 토픽 이름 | 데이터 규격 | 비고 |
| :--- | :--- | :--- | :--- |
| **ROS 2 Topic (In)** | `/navsat/fix` | `sensor_msgs/msg/NavSatFix` | 10 Hz 위도/경도/고도 & 공분산 |
| **MQTT Topic (Out)** | `telemetry/robot/rtk` | JSON Text (`application/json`) | QoS 1, KeepAlive 60s |
| **Server DB (Target)** | `robot_rtk_telemetry` | SQL Table Record | PostgreSQL + PostGIS |

---

## 6. ❓ 개발/테스트 Q&A 및 트러블슈팅 (Q&A & Troubleshooting)

### Q1. 국토지리정보원(NGII) NTRIP 접속 시 패킷이 안 들어오고 `status.status`가 RTK(2)로 전환되지 않는 원인은?
* **증상**: NMEA 데이터를 수신하고 있으나 `status.status`가 계속 `0` (Standalone 3D Fix)에 머무름.
* **원인 분석**:
  1. Teltonika RUT241 라우터에 APN 설정 미완료 또는 무선 LTE 인터넷 미연결.
  2. NGII NTRIP 계정 비밀번호 오탈자 또는 동시 접속자 수 초과 (NGII는 동일 ID 중복 접속을 차단함).
  3. Septentrio 수신기에 GGA NMEA 위치 피드백 메세지 송신 미설정 (NGII VRS 서버는 사용자 수신기의 현재 위치 GGA 문장을 받아야 해당 위치 기준의 가상 관측소 보정 데이터를 생성함).
* **해결책**:
  * RUT241 WebUI(`192.168.1.1`)에서 Ping `8.8.8.8` 성공 여부 확인.
  * Septentrio 웹 UI(`192.168.3.1`) ➔ NMEA Out 메뉴에서 `NMEA GGA` 전송 주기를 **1 Hz**로 설정.
  * 정상 연동 시 약 5~7초 이내에 수신기 전면 `RTK LED`가 녹색으로 고정되고 `status.status: 2` (RTK Fixed) 전환 확인.

---

### Q2. 로봇 이동 중 LTE 네트워크 끊김 시 MQTT 페이로드 손실 방지 대책은?
* **증상**: 음영 지역 통과 시 MQTT 연결 끊김으로 데이터 유실.
* **해결책**:
  1. Paho-MQTT `qos=1` 적용하여 ACK 확인 수신.
  2. 로봇 브릿지 노드 내부 링 버퍼(Ring Buffer)에 미전송 페이로드 캐싱 후, 네트워크 재연결(`on_mqtt_connect`) 시 일괄 덤프(Burst Publish) 송신.
  3. 원천 rosbag 파일(`/ouster/points`, `/navsat/fix`)은 로컬 NVMe SSD에 백업 저장하여 이중 안전장치 확보.

---

## 7. 보안 및 전력/발열 관리 수칙 (Security & Safety)

1. **🔒 보안 가이드 (PUBLIC Repository Guardrail)**:
   * 본 레포지토리는 공개(Public) 저장소이므로 NGII 비밀번호, 서버 DB 접속 비밀번호, SSH 키를 소스코드나 문서에 직기재 금지 (`<YOUR_NGII_PASSWORD>`, `<DB_PASSWORD>` 등 환경 변수/파라미터화 필터링 필수).
2. **🌡️ 전력 및 모니터링**:
   * RUT241 LTE 라우터 및 Septentrio GNSS 수신기의 합산 소비 전력은 약 3.5W 이내로 전력 안정성이 뛰어나나, 무선 전파 방열판 표면 온도가 55°C 이상 상승하지 않도록 통풍형 차폐함 내에 배치.
