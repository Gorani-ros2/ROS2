# Septentrio mosaic-go G5 P3 / P3H 수신기

## 정의

Septentrio mosaic-go G5는 mosaic-G5 P3™ (단일 안테나 초고정밀 RTK) 및 mosaic-G5 P3H™ (이중 안테나 서브 디그리 Heading 지원) 수신기 모듈을 탑재한 평가 키트(Evaluation Kit)입니다. 드론, 로봇, 자율주행 모빌리티 등 정밀 위치 측정 및 방위각 측정이 필요한 로봇 시스템을 위한 고정밀 멀티 밴드 GNSS 수신기입니다.

- **원본 데이터시트 PDF**: [`septentrio-mosaic-go-g5-p3h.pdf`](septentrio-mosaic-go-g5-p3h.pdf)

---

## 데이터시트 및 핵심 스펙

### 1. GNSS 수신 및 채널 사양
- **하드웨어 채널 수**: 789 채널 (모든 가시 위성 신호 동시 추적)
- **지원 위성 군 (Multiconstellation, Quad-band GNSS)**:
  - **GPS**: L1C/A, L1C, L2C, L2PY, L5
  - **GLONASS**: L1CA, L2CA, L2P, L3 CDMA
  - **BeiDou**: B1I, B1C, B2a, B2I, B2b, B3I
  - **Galileo**: E1, E5a, E5b, E6 (Galileo HAS 및 OSNMA 호환)
  - **QZSS**: L1C/A, L1 C/B, L2C, L5, L6

### 2. 정밀도 (Positioning Accuracy)

| 측정 모드 | 수평 정밀도 (Horizontal) | 수직 정밀도 (Vertical) |
| :--- | :--- | :--- |
| **RTK (센티미터급)** | **0.6 cm + 0.5 ppm** | **1 cm + 1 ppm** |
| **DGNSS** | 0.4 m | 0.7 m |
| **Standalone (단독 측위)** | 1.2 m | 1.9 m |

- **RTK 초기화 시간 (Initialization Time)**: 7초 (99.9% 신뢰도)
- **속도 정밀도 (Velocity Accuracy)**: 3 cm/s

### 3. 이중 안테나 Heading & Attitude 정밀도 (P3H 모듈 전용)

| 안테나 간격 (Separation) | Heading (방위각) 정밀도 | Pitch / Roll 정밀도 |
| :--- | :--- | :--- |
| **1 m** | **0.15°** | **0.25°** |
| **5 m** | **0.03°** | **0.05°** |

### 4. 신호 처리 및 처리 속도
- **최대 업데이트율**: 위치/측위 20 Hz, Raw Measurement 20 Hz (P3 전용)
- **지연 시간 (Latency)**: < 10 ms
- **Fix 획득 시간 (TTFF)**: Cold Start < 35s, Warm Start < 10s, Re-acquisition 1s
- **시간 정밀도**: PPS 해상도 1.4 ns, Event Marker 정확도 < 3 ns

---

## Septentrio 특허 GNSS+ 기술

1. **LOCK+**: 높은 충격 및 심한 기계적 진동 환경에서도 위성 신호 추적 유지.
2. **APME+**: 건물, 구조물 반사로 인한 멀티패스(Multipath) 에러 자동 추정 및 신호 왜곡 제거.
3. **AIM+**: 강력한 재밍(Jamming) 및 스푸핑(Spoofing) 신호 감지 및 자동 간섭 완화.
4. **IONO+**: 전離층(Ionosphere) 교란 및 섭란 방지 기능.
5. **RAIM+**: 수신기 자율 무결성 감시 기능.

---

## 인터페이스 및 물리 사양

- **통신 포트**:
  - **UART 1**: 6-pin JST-GH (LVTTL, 최대 4 Mbps, Pixhawk/PX4 오토파일럿 직결)
  - **UART 2**: 10-pin 100 mil 소켓 (LVTTL, 최대 4 Mbps, 블루투스 모듈 연결)
  - **USB-C**: USB 2.0 High Speed (최대 480 Mbps)
  - **SD 카드 슬롯**: 온보드 데이터 로깅 지원
  - **신호 핀**: Configurable PPS Output (1x), Event Marker Input (1x), User GPIO (1x)
- **전원 및 소모 전력**:
  - **입력 전압**: USB-C 또는 외부 5 VDC
  - **소비 전력**: P3 (0.59W typ / 0.77W max), P3H 이중 안테나 (0.81W typ / 1.06W max)
  - **안테나 바이어스 전압**: 3.0 V ~ 5.5 V (내장 150 mA 전류 제한)
- **물리적 규격**:
  - **크기**: 74 x 44 x 11.4 mm (Casting metal enclosure)
  - **무게**: 50 g
  - **동작 온도**: -25°C ~ +85°C
  - **인증**: CE, FCC, RoHS, WEEE, ISED

---

## 프로토콜 및 ROS 2 통신 정의

- **지원 프로토콜**: SBF (Septentrio Binary Format), NMEA 0183 (v2.3, v3.03, v4.0), RTCM v3.x (MSM 포함 수신)
- **ROS 2 패키지 연동**: `septentrio_gnss_driver` 또는 `nmea_navsat_driver`
- **발행 토픽**:
  - `/navsat/fix` (`sensor_msgs/msg/NavSatFix`) — 위도, 경도, 고도 및 RTK Status
  - `/navsat/vel` (`geometry_msgs/msg/TwistStamped`) — 3D 이동 속도
  - `/navsat/heading` (`sensor_msgs/msg/Imu` 또는 커스텀 메시지) — 이중 안테나 방위각

---

## 🛠️ 실전 하드웨어 구축 및 케이블/배치 가이드 (Q&A 정리)

### 1. 전원 공급 및 케이블 선택 (USB A-to-C vs C-to-C)
- **전력 소모량**: 수신기 본체 + 활성 안테나 합산 전력은 약 **1.5W ~ 1.8W max** (5V DC).
- **케이블 상호 호환성**:
  - 표준 USB 2.0 A-to-C 포트(최소 2.5W 공급) 및 USB C-to-C 포트(15W+ 공급) **모두 100% 전력 넉넉하게 작동**함.
  - PC/노트북 연결 시 전원 공급 + NMEA 데이터 송수신 + 웹 UI(`http://192.168.3.1`) 접속이 단일 USB 케이블로 처리됨.

### 2. JST 6-pin COM1 & Power Open-Ended 케이블 (4선 핀맵)
- **배선 핀맵**:
  - 🔴 **Red**: `V_IN` (+5V 외부 전원 입력)
  - 🖤 **Black**: `GND` (공통 접지)
  - 🟡 **Yellow**: `TXD1` (COM1 3.3V LVTTL 시리얼 데이터 송신)
  - 🔵 **Blue**: `RXD1` (COM1 3.3V LVTTL 시리얼 데이터 수신)
- **사용 지침**: 오토파일럿(Pixhawk/PX4)이나 외부 MCU 직결 전용이며, 노트북 USB 연결 시에는 미사용(연결 불필요).

### 3. 안테나 체결 포트 배치 규칙 (MAIN vs AUX)
- **단일 안테나 수신 시**: 반드시 **`MAIN` 포트**에 체결 (위도, 경도, 고도, RTK, 속도, PPS 전담).
- **이중 안테나 수신 시**: `MAIN` 포트(뒤쪽) + **`AUX` 포트**(앞쪽) 체결 (정지 시 서브 디그리 Heading 방위각 계산용).

### 4. 안테나 설치 장소 및 오리엔테이션
- **방향 (Orientation)**: 안테나 하단 자석/평면(배)이 아래쪽 철판/지면을 향하고, **상단 둥근 돔(등)이 위쪽(하늘)을 똑바로 바라보도록 부착**.
- **위치 (Location)**: 로봇/차량의 상방에 차폐물이 없는 최상단 수평면에 위치하여 멀티패스 반사파 및 신호 왜곡 방지.
- **이중 안테나 이격 거리**: 최소 **30~50cm 이상** (권장 **1m 이상** 이격 시 Heading 오차 0.15° 달성). 수신기 본체와 안테나 간 거리는 케이블 길이 내 자유 배치 가능.

### 5. Ouster OS0-128 3D 라이다 PPS 하드웨어 동기화 연동
- Septentrio 10-pin 헤더의 **`PPS` (1Hz Pulse Per Second) 핀** ➔ Ouster Interface Box의 **`SYNC_PULSE_IN` (+)**에 연결.
- Septentrio **`GND` 핀** ➔ Ouster Interface Box **`GND` (-)**에 연결.
- 마이크로초(µs) 단위로 라이다 점군 타임스탬프와 GNSS 수신기 절대 시각을 강제 고정.

