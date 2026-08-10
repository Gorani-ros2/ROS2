# Ouster OS0-128

## 정의
Ouster OS0-128은 128채널의 초광각(Super-Wide FOV) 3D 라이다 센서로, 2048x10Hz 회전 스캔 모드를 지원하며 Ethernet 기반 UDP 데이터 전송 및 ROS 2 Humble 디스트로를 지원합니다.

## 데이터시트
- **채널 수**: 128 채널
- **수평 해상도 (Columns)**: 512, 1024, 2048 (기본 2048x10Hz 모드)
- **스캔 속도**: 10 Hz / 20 Hz (기본 10Hz = 600 RPM)
- **시야각 (FOV)**: 수직 90° / 수평 360°
- **통신 인터페이스**: Ethernet (UDP/TCP)
- **실시간 Telemetry API**: `http://<sensor_hostname>/api/v1/sensor/telemetry`

## 통신 및 ROS 2 토픽 정의
- **드라이버 설정**: `my_ouster_params.yaml` (`lidar_mode: "2048x10"`, `timestamp_mode: "TIME_FROM_ROS_TIME"`)
- **발행 토픽**:
  - `/ouster/points` (`sensor_msgs/msg/PointCloud2`, QoS: **`Best Effort`**)
  - `/ouster/imu` (`sensor_msgs/msg/Imu`)
  - `/ouster/lidar_packets` (`ouster_sensor_msgs/msg/PacketMsg`)

## RViz2 시각화 필수 설정
1. **Global Options > Fixed Frame**: `os_sensor` 또는 `os_lidar`
2. **PointCloud2 > Topic**: `/ouster/points`
3. **PointCloud2 > Topic > Reliability Policy**: **`Best Effort`** (SensorData QoS 호환에 필수)

---

## 🌡️ 과열 보호 및 써멀 동작 메커니즘 (Thermal Protection Mechanism)

### 1. 센서 과열 단계별 동작
Ouster 라이다 내부 펌웨어에는 하드웨어 파손 방지를 위해 2단계 열 보호 시스템이 탑재되어 있습니다:

- **1단계: 레이저 출력 제한 (`Shot Limiting`) — 약 60°C 부근**
  - 회전 모터는 설정된 10Hz 속도를 그대로 유지하지만, 발열 억제를 위해 레이저 발광 소자가 부분적으로 전원을 꺼뜨립니다.
  - **현상**: 모터는 돌고 있으나, 점군(Point Cloud) 데이터 중간중간에 데이터가 누락되어 **이빨이 빠진 것처럼 빈 공간이 듬성듬성 발생**합니다.
- **2단계: 써멀 셧다운 (`Thermal Shutdown / OVER_TEMP`) — 약 75°C~80°C 이상**
  - 센서 소자 탄화 방지를 위해 **레이저 발광을 100% 강제 차단**하고 보호 모드로 진입합니다.
  - **현상**: 점군(Point Cloud) 데이터 출력이 **0%가 되어 아예 나오지 않습니다 (완전 먹통 상태)**.
  - **상태 확인**: `http://<sensor_ip>/api/v1/sensor/telemetry` 조회 시 `"thermal_status": "OVER_TEMP"` 출력.

---

### 2. 호스트 PC(노트북) 과열과 센서 과열의 차이점

| 구분 | 센서(Ouster) 과열 | 호스트 PC(노트북) 과열 |
| :--- | :--- | :--- |
| **원인** | 라이다 직사광선 노출 및 통풍 부족 | 노트북 CPU 쓰로틀링 (Thermal Throttling) |
| **영향** | 센서 레이저 샷 차단 및 셧다운 | 고속 UDP 수신 버퍼 오버플로우로 인한 패킷 유실 (Kernel UDP Packet Drop) |
| **증상** | 점군 듬성듬성 결측 또는 아예 안 나옴 | 라이다는 데이터를 정상 송신하나, **노트북 수신 실패로 rosbag 녹화 파일에 구멍(손실) 발생** |
| **진단 명령어** | Telemetry API (`internal_temperature_deg_c`) | `sudo dmesg -T \| grep -iE "thermal\|throttle"` |
