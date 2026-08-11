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

## ❓ 자주 묻는 질문 및 실전 연결 Q&A (Receiver Setup & Installation Q&A)

### Q1. 수신기 본체 단면에 있는 유심 슬롯처럼 생긴 구멍과 마이크로 USB처럼 생긴 포트의 정확한 정체와 용도는 무엇인가요?
- **답변**:
  - **유심처럼 생긴 슬롯 ➔ MicroSD 카드 슬롯**:
    - 유심(SIM) 카드가 아니라 **MicroSD 메모리 카드 슬롯**입니다.
    - Septentrio 수신기에는 자체 데이터 로깅(Logging) 기능이 내장되어 있습니다. PC나 노트북 연결 없이 수신기 단독으로 위치 데이터, 위성 궤도 정보, SBF(Septentrio Binary Format) 바이너리 및 NMEA 로그를 MicroSD 카드에 실시간 백업 기록할 때 사용합니다. (노트북 연동 테스트 시에는 미사용 가능)
  - **마이크로 USB처럼 생긴 단자 ➔ USB-C (USB 2.0 High Speed) 포트**:
    - 표준 **USB-C 포트**입니다.
    - 노트북과 연결할 때 **[① 5V DC 전원 공급 + ② NMEA 시리얼 위치 데이터 통신 + ③ 웹 브라우저 대시보드 UI(`http://192.168.3.1`) 접속 통신]**을 단 하나의 케이블로 통합 처리하는 핵심 포트입니다.

### Q2. 동봉되어 있던 케이블이 USB A-to-C 케이블인데, 노트북의 C 포트에 직접 연결하기 위해 USB C-to-C 케이블을 써도 전력이 부족하거나 문제가 생기지 않나요?
- **답변**:
  - **C-to-C 케이블을 써도 100% 아무 문제 없이 완벽하게 작동합니다.**
  - **상세 전력 분석**:
    - Septentrio mosaic-go G5 수신기 본체 소모 전력: 약 0.59W (typ) ~ 1.06W (max)
    - Tallysman 활성 안테나 LNA 앰프 전원 소모량: 약 0.5W ~ 0.75W
    - ➔ **본체 + 안테나 합산 전체 필요 전력: 약 1.5W ~ 1.8W (5V DC 기준 약 300mA~360mA)**
  - **USB 포트 전력 공급 능력**:
    - 가장 구형인 USB 2.0 Type-A 포트 규격 최소 출력: 5V / 0.5A = **2.5W**
    - 최근 노트북 USB Type-C 포트 기본 출력: 5V / 3.0A = **15W** (PD 미적용 시에도 최소 7.5W~15W)
  - **결론**: 수신기가 필요한 전력(1.8W max)보다 USB 포트가 공급해 주는 전력(2.5W~15W)이 훨씬 넉넉하므로, A-to-C 케이블과 C-to-C 케이블 모두 안심하고 사용하셔도 됩니다.

### Q3. 동봉되어 있던 JST 6-pin open ended 케이블(4개 와이어: 빨강, 검정, 노랑, 파랑)의 정확한 핀맵과 용도는 무엇인가요?
- **답변**:
  - **용도**: Pixhawk, PX4 등 드론/로봇의 오토파일럿 제어기 또는 외부 MCU(Arduino, STM32, Jetson)에 수신기를 시리얼(UART1/COM1)로 하드웨어 직결할 때 사용하는 시리얼 데이터 + 전원 공급 케이블입니다.
  - **4선 핀맵 (Pinout)**:
    - 🔴 **빨강 (Red)**: `V_IN` (+5V DC 외부 전원 공급 입력)
    - 🖤 **검정 (Black)**: `GND` (공통 그라운드 / 접지)
    - 🟡 **노랑 (Yellow)**: `TXD1` (COM1 3.3V LVTTL 시리얼 데이터 송신 — 수신기 ➔ 외부 제어기)
    - 🔵 **파랑 (Blue)**: `RXD1` (COM1 3.3V LVTTL 시리얼 데이터 수신 — 외부 제어기 ➔ 수신기)
  - **노트북 연결 시 사용 여부**: 노트북 USB-C 포트로 연결할 때는 USB 케이블에서 전원과 통신이 한 번에 공급되므로 이 JST 6-pin 케이블은 꽂지 않고 비워둡니다.

### Q4. 수신기 본체(mosaic-go G5)의 배치 방향이나 기울기(뒤집어 놓기, 비스듬히 놓기)가 위치 정밀도에 영향을 주나요?
- **답변**:
  - **수신기 본체의 방향이나 기울기는 위치 정밀도에 0.001%도 영향을 주지 않습니다.**
  - **이유**: 위성 신호를 정밀하게 수신하고 지향성을 가지는 주체는 케이블로 외부 연결된 **Tallysman 안테나**입니다. 수신기 본체(mosaic-go G5) 내부에는 안테나 소자가 없으며, 연산을 수행하는 칩셋과 기판, 그리고 알루미늄 보호 케이스로 구성되어 있습니다.
  - 따라서 수신기 본체는 거꾸로 뒤집어 놓거나, 옆으로 세워두거나, 제어함 내부에 대각선으로 고정해 두어도 100% 동일하게 정상 작동합니다.

### Q5. Ouster OS0-128 3D 라이다와 Septentrio 수신기 간에 PPS 하드웨어 시각 동기화를 수행하려면 어떻게 물리적으로 결선해야 하나요?
- **답변**:
  - **동기화 목적**: 호스트 PC 시계의 유연성/지연과 무관하게, RTK 위성 시계(UTC)의 마이크로초(µs) 정밀도 파형에 라이다 3D 점군(Point Cloud) 타임스탬프를 강제 고정하여 라이다-RTK 센서퓨전 및 SLAM 오차를 제로화합니다.
  - **물리 결선 방법**:
    - Septentrio 측면 10-pin 헤더의 **`PPS` (Pulse Per Second 1Hz 파형) 핀** ➔ Ouster Interface Box의 **`SYNC_PULSE_IN` (+)** 핀에 연결.
    - Septentrio 10-pin 헤더의 **`GND` (접지) 핀** ➔ Ouster Interface Box의 **`GND` / `SYNC_PULSE_IN` (-)** 핀에 연결.
  - **라이다 드라이버 설정**: Ouster `my_ouster_params.yaml` 파일에서 `timestamp_mode: "TIME_FROM_SYNC_PULSE_IN"` 및 `sync_pulse_in_polarity: "ACTIVE_HIGH"`로 설정하면 동기화가 완료됩니다.
