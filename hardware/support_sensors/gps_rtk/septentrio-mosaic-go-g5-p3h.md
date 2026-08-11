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

## ❓ 자주 묻는 질문 및 실전 연결 Q&A (Receiver Setup Q&A)

### Q1. 수신기 본체의 유심 슬롯처럼 생긴 구멍과 마이크로 USB처럼 생긴 포트의 정체는?
- **A**: 유심 슬롯 모양은 **MicroSD 카드 슬롯**으로 단독 SBF/NMEA 데이터 백업 로깅용입니다. 마이크로 USB처럼 보이는 단자는 **USB-C 포트**로, 노트북과 연결하여 [전원 5V + NMEA 통신 + 웹 UI(`http://192.168.3.1`)] 접속에 사용됩니다.

### Q2. 동봉된 USB A-to-C 케이블 대신 USB C-to-C 케이블을 써도 전력이 부족하지 않나요?
- **A**: **둘 다 전력이 넉넉하게 작동합니다.** 수신기 본체+안테나 소모 전력은 최대 **1.5W~1.8W**인 반면, 가장 기본 USB A-to-C 포트도 2.5W(5V 0.5A) 이상을 공급하므로 전혀 전력 부족이 발생하지 않습니다.

### Q3. 동봉된 JST 6-pin open ended (4선: 빨, 검, 노, 파) 케이블의 핀맵과 용도는?
- **A**: Pixhawk/PX4 오토파일럿이나 외부 MCU 직결 전용 시리얼+전원 케이블입니다.
  - 🔴 **Red**: `V_IN` (+5V 전원 입력)
  - 🖤 **Black**: `GND` (공통 접지)
  - 🟡 **Yellow**: `TXD1` (COM1 3.3V LVTTL 시리얼 데이터 송신)
  - 🔵 **Blue**: `RXD1` (COM1 3.3V LVTTL 시리얼 데이터 수신)
  *(노트북 USB 연결 시에는 미사용)*

### Q4. 수신기 본체(mosaic-go G5)를 뒤집어놓거나 비스듬히 놓아도 되나요?
- **A**: **방향/기울기에 상관없이 100% 정상 작동합니다.** 신호 수신의 주체는 외부 안테나이며, 본체 내부 칩셋은 방향의 영향을 받지 않습니다.

### Q5. Ouster OS0-128 라이다와 PPS 시각 동기화를 하려면 어떻게 결선하나요?
- **A**: Septentrio 10-pin 헤더의 `PPS` 핀 ➔ Ouster Interface Box `SYNC_PULSE_IN` (+), Septentrio `GND` 핀 ➔ Ouster Interface Box `GND` (-)에 연결하여 마이크로초 단위 절대시각 동기화를 수행합니다.
