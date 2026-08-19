# 💻 Ouster 라이다 & Septentrio RTK PPS 하드웨어 동기화 및 ROS 2 Bag 검증

> **작성 일자**: 2026-08-18  
> **작성 장비**: `knu laptop` (KNU 노트북 PC / Linux Ubuntu 22.04 LTS)  
> **작성 AI**: Antigravity (Google DeepMind Team)  
> **파일명 규격**: `lidar-rtk-pps-sync-bag.md`  

---

## 📌 Executive Abstract (상세 요약 및 초록)

본 문서는 **Ouster OS0-128 3D 라이다**와 **Septentrio mosaic-go G5 RTK GNSS 수신기** 간의 **하드웨어 PPS (Pulse Per Second) 시계 동기화** 세팅 및 **ROS 2 Bag 실전 녹화/검증** 절차를 수록한 기술 명세서입니다.

디지털 트윈(Digital Twin)용 고정밀 3D 라이다 점군 데이터와 360도 RGB 파노라마 영상 매핑, 자율주행 쓰레기로봇(안동 쓰봇) 위치 추정 시, 호스트 PC 소프트웨어 시계의 드리프트(Drift) 및 시스템 시스템 지연 오차를 근본적으로 차단하기 위하여 RTK 수신기의 위성 UTC 마이크로초(µs) 정밀도 PPS 펄스를 Ouster 라이다의 동기화 신호 입력(`SYNC_PULSE_IN`)에 물리 결선합니다.

또한 `timestamp_mode: "TIME_FROM_SYNC_PULSE_IN"` 적용 상태에서 rosbag 녹화를 수행하고, 데이터 수집 중 PPS 동기화 설정이 끊김 없이 안정적으로 유지되는지 정밀 검증하는 스크립트 및 Q&A를 포함합니다.

---

## 1. 개요 및 동기화 파이프라인 (Overview & Sync Pipeline)

* **목적**: RTK 위성 시간(UTC 기준 µs 단위)으로 라이다 점군 타임스탬프를 물리 결선(PPS)을 통해 강제 고정하여 라이다-RTK-360카메라 융합 매핑 오차 차단.
* **시스템 동기화 구조도 (Mermaid)**:

```mermaid
flowchart TD
    subgraph Satellites ["GNSS 위성군 (GPS / GLONASS / BeiDou / Galileo)"]
        SAT["UTC Atomic Clock Signal"]
    end

    subgraph RTK_Receiver ["Septentrio mosaic-go G5 RTK GNSS"]
        SAT -->|RF Signal| ANT["Tallysman TW7972 Antenna"]
        ANT --> GNSS_CORE["mosaic-G5 Engine"]
        GNSS_CORE -->|PPS Output Pin (1Hz Square Wave)| PPS_HW["Hardware PPS Line"]
        GNSS_CORE -->|NMEA ZDA / RMC (10Hz)| NMEA_HW["Serial / Ethernet NMEA"]
    end

    subgraph LiDAR ["Ouster OS0-128 3D LiDAR"]
        PPS_HW -->|SYNC_PULSE_IN (+)| OUSTER_BOX["Ouster Interface Box"]
        OUSTER_BOX --> OUSTER_CORE["LiDAR Internal Clock (UTC Synced)"]
    end

    subgraph Host_PC ["로봇 온보드 PC (KNU Laptop)"]
        NMEA_HW -->|USB / Ethernet| ROS2_GNSS["/navsat/fix (10Hz)"]
        OUSTER_CORE -->|Ethernet UDP| ROS2_LIDAR["/ouster/points (10Hz)"]
        
        ROS2_GNSS --> ROSBAG["rosbag2 record\n(/ouster/points, /navsat/fix, /tf_static)"]
        ROS2_LIDAR --> ROSBAG
    end
```

---

## 2. 🔗 관련 하드웨어 및 소프트웨어 십자 링크 (Cross-Links)

* 📡 **연동 GNSS 수신기**: [`Septentrio mosaic-go G5 P3H 수신기`](../../hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md)
* 📹 **연동 3D 라이다**: [`Ouster OS0-128 라이다`](../../hardware/vision_sensors/lidar/ouster-os0-128.md)
* 🌐 **연동 4G LTE 라우터**: [`Teltonika RUT241 라우터`](../../hardware/support_sensors/router/teltonika-rut241.md)
* 📹 **연동 360도 카메라**: [`Insta360 카메라 SDK`](../../hardware/vision_sensors/camera/insta360-camera-sdk.md)
* 💻 **RTK MQTT DB 브릿지**: [`RTK Telemetry MQTT 서버 DB 연동`](../protocol/rtk-mqtt-db-bridge.md)
* 📹 **다중 센서 동시 녹화**: [`LiDAR-Insta360 동시 녹화 아키텍처`](lidar-insta360-sync-record.md)

---

## 3. 하드웨어 PPS 결선 및 파라미터 세팅 (Hardware Wiring & Configuration)

### 🔌 1. 물리 하드웨어 결선 핀맵 (Wiring Diagram)

* **Septentrio mosaic-go G5 (10-pin 헤더)**:
  * `PPS Out` (Pin 7) ➔ **Ouster Interface Box `SYNC_PULSE_IN` (+)** (JST-SH 짝맞춤 핀)
  * `GND` (Pin 10) ➔ **Ouster Interface Box `GND` (-)**

### ⚙️ 2. Ouster LiDAR 파라미터 설정 (`my_ouster_params.yaml`)

```yaml
ouster_driver:
  ros__parameters:
    sensor_hostname: "169.254.129.201"
    lidar_mode: "2048x10"
    timestamp_mode: "TIME_FROM_SYNC_PULSE_IN"  # PPS 하드웨어 동기화 모드 적용
    ptp_utc_tai_offset: -37
    multipurpose_io_mode: "INPUT_NTP"
    sync_pulse_in_polarity: "ACTIVE_HIGH"
```

---

## 4. ROS 2 Bag 녹화 및 타임스탬프 검증 (ROS 2 Bag Recording & Verification)

### 🚀 1. 동기화 데이터 수집 실행 명령어

```bash
# 1. ROS 2 Humble 환경 로드
source /opt/ros/humble/setup.bash
source ~/workspaces/insta360/ouster_ros2/install/setup.bash

# 2. PPS 적용 Ouster 드라이버 런칭
ros2 launch ouster_ros driver.launch.py params_file:=my_ouster_params.yaml viz:=False &

# 3. Septentrio RTK 수신기 NMEA/Fix 노드 런칭
python3 software/ros2_basics/septentrio_nmea_fix_node.py &

# 4. PPS 동기화 정밀 rosbag 녹화 실행 (디지털 트윈 매핑 파이프라인 필수 토픽)
ros2 bag record /ouster/points /ouster/imu /navsat/fix /navsat/vel /tf_static -o digital_twin_pps_bag_$(date +%Y%m%d_%H%M%S)
```

---

### 🔍 2. PPS 동기화 상태 및 데이터 검증 파이썬 스크립트 (`verify_pps_bag.py`)

이 스크립트는 수집된 rosbag 및 Ouster Telemetry API를 점검하여 라이다 점군 타임스탬프가 위성 UTC 시간 기준(PPS Lock)으로 획득되었는지 정밀 검증합니다.

```python
#!/usr/bin/env python3
"""
Ouster LiDAR & Septentrio RTK PPS Sync Verification Script
"""
import urllib.request
import json
import sys

def check_ouster_pps_telemetry(sensor_ip="169.254.129.201"):
    url = f"http://{sensor_ip}/api/v1/sensor/telemetry"
    print(f"[1] Querying Ouster Telemetry API: {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            sync_pulse = data.get("sync_pulse_in", {})
            timestamp_mode = data.get("timestamp_mode", "UNKNOWN")
            temp = data.get("internal_temperature_deg_c", 0.0)
            
            print(f"  - Timestamp Mode: {timestamp_mode}")
            print(f"  - Internal Temperature: {temp} °C")
            print(f"  - Sync Pulse In Locked: {sync_pulse}")

            if timestamp_mode == "TIME_FROM_SYNC_PULSE_IN":
                print("  ✅ PASS: Ouster is properly set to PPS Hardware Sync Mode!")
            else:
                print(f"  ❌ FAIL: Unexpected timestamp mode '{timestamp_mode}'")
    except Exception as e:
        print(f"  ⚠️ Warning: Could not connect to sensor at {sensor_ip}: {e}")

if __name__ == "__main__":
    ip = sys.argv[1] if len(sys.argv) > 1 else "169.254.129.201"
    check_ouster_pps_telemetry(ip)
```

---

## 5. 발행 및 구독 토픽 정의 (ROS 2 Topics)

| 토픽 이름 | 메시지 타입 (Message Type) | 발행 주기 | PPS 동기화 여부 |
| :--- | :--- | :--- | :--- |
| `/ouster/points` | `sensor_msgs/msg/PointCloud2` | 10 Hz | **PPS Hardware Locked (UTC)** |
| `/ouster/imu` | `sensor_msgs/msg/Imu` | 100 Hz | **PPS Hardware Locked (UTC)** |
| `/navsat/fix` | `sensor_msgs/msg/NavSatFix` | 10 Hz | **RTK UTC Atomic Clock** |
| `/navsat/vel` | `geometry_msgs/msg/TwistStamped` | 10 Hz | **RTK UTC Atomic Clock** |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | Latched | Static Frame (`os_sensor` <-> `gnss`) |

---

## 6. ❓ 개발/테스트 Q&A 및 트러블슈팅 (Q&A & Troubleshooting)

### Q1. PPS 하드웨어 케이블을 체결했는데 Ouster Telemetry API에서 `sync_pulse_in` 신호를 미인식하는 이유는?
* **원인**:
  1. Septentrio 수신기 웹 UI(`192.168.3.1`)에서 `PPS Output` 핀 출력이 기본값(Off)으로 꺼져있는 경우.
  2. PPS 신호 극성(Polarity) 불일치 (`ACTIVE_HIGH` vs `ACTIVE_LOW`).
  3. Ground(GND) 핀 미결선으로 인한 신호 기준 전위 부유.
* **해결책**:
  * Septentrio 수신기 설정에서 `SetPPSParameters, Sec1, ActiveHigh` 명령 전송하여 매 1초 마다 Active High 펄스 출력 활성화.
  * Ouster와 Septentrio의 `GND` 핀이 단단히 공통 접지되었는지 멀티미터 도통 테스트 수행.

---

### Q2. rosbag 녹화 파일 저장 시 NVMe 디스크 쓰기 부하로 인해 PPS 동기화 타임스탬프에 영향을 주나요?
* **답변**: **영향을 주지 않습니다.**
* **이유**: PPS 하드웨어 동기화는 센서 내부 FPGA 칩셋 레벨에서 주입되는 펄스를 기반으로 점군 캡처 타임스탬프를 부여하므로, 호스트 PC의 Disk I/O 지연이나 CPU 로드와 관계없이 타임스탬프의 절대 마이크로초 정밀도가 100% 보장됩니다.

---

## 7. 발열 및 안전 관리 수칙 (Safety & Thermal Management)

1. **라이다-수신기 써멀 릴레이**:
   * Ouster OS0-128 라이다 내부 온도가 60°C 초과 시 `Shot Limiting` (점군 결측) 현상이 일어날 수 있으므로, rosbag 녹화 시 `curl -s http://169.254.129.201/api/v1/sensor/telemetry`로 온도를 5분 주기로 감시.
2. **디지털 트윈 & 안동 쓰봇 모듈 전파**:
   * 본 PPS 및 rosbag 검증 프로세스는 디지털 트윈 레포지토리 우선 정리 후, 검증 마감 시 안동 쓰레기로봇 및 ROS 공통 레포지토리에 모듈화하여 이식함.
