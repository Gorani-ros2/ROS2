# Septentrio mosaic-go G5 P3 / P3H 수신기

## 📌 개요 및 정의

Septentrio mosaic-go G5는 mosaic-G5 P3™ (단일 안테나 초고정밀 RTK) 및 mosaic-G5 P3H™ (이중 안테나 서브 디그리 Heading 지원) 수신기 모듈을 탑재한 평가 키트(Evaluation Kit)입니다.

드론, 로봇, 자율주행 모빌리티 등 센티미터급 정밀 위치 측정 및 방위각 측정이 필요한 로봇 시스템을 위한 고정밀 멀티 밴드 GNSS 수신기입니다.

> 📄 **원본 데이터시트 PDF**: [`septentrio-mosaic-go-g5-p3h.pdf`](septentrio-mosaic-go-g5-p3h.pdf)

---

## 📊 데이터시트 및 핵심 스펙

### 1. GNSS 수신 및 채널 사양
- **하드웨어 채널 수**: **789 채널** (모든 가시 위성 신호 동시 추적)
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

- **RTK 초기화 시간 (Initialization Time)**: **7초 (99.9% 신뢰도)**
- **속도 정밀도 (Velocity Accuracy)**: **3 cm/s**

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

## 🛡️ Septentrio 특허 GNSS+ 기술

1. **LOCK+**: 높은 충격 및 심한 기계적 진동 환경에서도 위성 신호 추적 유지.
2. **APME+**: 건물, 구조물 반사로 인한 멀티패스(Multipath) 에러 자동 추정 및 신호 왜곡 제거.
3. **AIM+**: 강력한 재밍(Jamming) 및 스푸핑(Spoofing) 신호 감지 및 자동 간섭 완화.
4. **IONO+**: 전離층(Ionosphere) 교란 및 섭란 방지 기능.
5. **RAIM+**: 수신기 자율 무결성 감시 기능.

---

## 🔌 인터페이스 및 물리 사양

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
- **물리 규격 & 인증**: 74 x 44 x 11.4 mm / 50 g / -25°C ~ +85°C / CE, FCC, RoHS, KC 인증

---

## 🌐 프로토콜 및 ROS 2 통신 정의

- **지원 프로토콜**: SBF (Septentrio Binary Format), NMEA 0183 (v2.3, v3.03, v4.0), RTCM v3.x (MSM 포함 수신)
- **ROS 2 패키지 연동**: `septentrio_gnss_driver` 또는 `nmea_navsat_driver`
- **발행 토픽**:
  - `/navsat/fix` (`sensor_msgs/msg/NavSatFix`) — 위도, 경도, 고도 및 RTK Status
  - `/navsat/vel` (`geometry_msgs/msg/TwistStamped`) — 3D 이동 속도
  - `/navsat/heading` (`sensor_msgs/msg/Imu` 또는 커스텀 메시지) — 이중 안테나 방위각

---

## ❓ 자주 묻는 질문 및 실전 연결 Q&A (Receiver Setup Q&A)

### Q1. 수신기 본체의 유심 슬롯처럼 생긴 구멍과 마이크로 USB처럼 생긴 포트의 정확한 정체는?
* **유심 슬롯 형태 ➔ MicroSD 카드 슬롯**:
  유심 카드가 아닌 **MicroSD 카드 슬롯**입니다. PC 연결 없이 수신기 단독으로 SBF 바이너리 및 NMEA 로그를 저장할 때 사용합니다.
* **마이크로 USB 형태 ➔ USB-C (USB 2.0 High Speed) 포트**:
  표준 **USB-C 포트**입니다. 노트북 연결 시 **[① 5V 전원 공급 + ② NMEA 위치 통신 + ③ 웹 UI(`http://192.168.3.1`) 접속 통신]**을 단일 케이블로 통합 처리합니다.

---

### Q2. USB A-to-C 케이블 대신 USB C-to-C 케이블을 써도 전력이 부족하지 않나요?
* **결론**: **C-to-C 케이블을 써도 100% 아무 문제 없이 작동합니다.**
* **상세 전력 수치 비교**:
  * **수신기 + 활성 안테나 합산 전력**: **약 1.5W ~ 1.8W max** (5V DC 기준 약 300mA~360mA)
  * **구형 USB 2.0 Type-A 포트 최소 공급 전력**: **2.5W** (5V / 0.5A)
  * **노트북 USB Type-C 포트 기본 공급 전력**: **15W** (5V / 3.0A)
* **분석**: 수신기의 최대 소모 전력(1.8W)보다 모든 USB 포트의 공급 전력(2.5W~15W)이 항상 크기 때문에 A-to-C 및 C-to-C 케이블 모두 100% 안정적입니다.

---

### Q3. 동봉된 JST 6-pin open ended (4선: 빨, 검, 노, 파) 케이블의 핀맵과 용도는?
* **용도**: Pixhawk/PX4 오토파일럿 또는 외부 MCU(Arduino, Jetson) 직결용 시리얼+전원 케이블입니다.
* **4선 핀맵 (Pinout)**:
  * 🔴 **Red**: `V_IN` (+5V DC 외부 전원 공급 입력)
  * 🖤 **Black**: `GND` (공통 그라운드 / 접지)
  * 🟡 **Yellow**: `TXD1` (COM1 3.3V LVTTL 시리얼 데이터 송신)
  * 🔵 **Blue**: `RXD1` (COM1 3.3V LVTTL 시리얼 데이터 수신)
* *(노트북 USB 연결 시에는 미사용)*

---

### Q4. 수신기 본체(mosaic-go G5)의 배치 방향이나 기울기가 정밀도에 영향을 주나요?
* **결론**: **방향이나 기울기는 정밀도에 전혀 영향을 주지 않습니다.**
* **이유**: 신호 수신의 주체는 케이블로 외부 연결된 **Tallysman 안테나**이며, 본체 내부는 연산 칩셋과 알루미늄 케이스로 이루어져 있어 거꾸로 뒤집어놓거나 비스듬히 놓아도 100% 동일하게 작동합니다.

---

### Q5. Ouster OS0-128 3D 라이다와 PPS 하드웨어 시각 동기화 결선 방법은?
* **목적**: 호스트 PC 시계 오차와 무관하게, RTK 위성 시계(UTC) 마이크로초(µs) 정밀도 파형에 라이다 3D 점군 타임스탬프를 강제 고정합니다.
* **물리 결선 방법**:
  * Septentrio 10-pin 헤더 **`PPS` 핀** ➔ Ouster Interface Box **`SYNC_PULSE_IN` (+)**
  * Septentrio 10-pin 헤더 **`GND` 핀** ➔ Ouster Interface Box **`GND` (-)**
* **라이다 설정**: `my_ouster_params.yaml`에 `timestamp_mode: "TIME_FROM_SYNC_PULSE_IN"` 적용.

---

### Q6. ROS 2 `sensor_msgs/msg/NavSatFix` 메세지 각 필드의 상세 의미는?
```yaml
header:
  stamp:
    sec: 1786424850
    nanosec: 975653337
  frame_id: gnss
status:
  status: 0
  service: 15
latitude: 36.11776659406625
longitude: 128.63186570005357
altitude: 141.23728296236337
position_covariance:
- 3.154019355773926
- 0.0
- 0.0
- 0.0
- 21.924036026000977
- 0.0
- 0.0
- 0.0
- 20.45357322692871
position_covariance_type: 3
```
* **`header.stamp`**: 데이터 측정 시각 (Unix 초 단위 `sec` + 나노초 `nanosec`).
* **`header.frame_id`**: 로봇 TF 트리의 수신기 좌표계 이름 (`gnss`).
* **`status.status`**: 측위 상태 구분 지수 (`0` = Standalone 3D Fix, `1` = DGPS, `2` = RTK Float/Fix).
* **`status.service`**: 수신 조합 비트마스크 (`15` = `1(GPS) + 2(GLONASS) + 4(BeiDou) + 8(Galileo)`, 4개 위성군 동시 수신 중).
* **`latitude` / `longitude` / `altitude`**: WGS84 위도($^\circ N$), 경도($^\circ E$), 고도($m$).
* **`position_covariance`**: $3 \times 3$ 위치 오차 분산 행렬 ($\text{m}^2$).
  * 대각 성분: East 오차 분산 $\sigma_x^2 = 3.154$ ($\approx 1.77\text{m}$ 오차), North 오차 분산 $\sigma_y^2 = 21.924$ ($\approx 4.68\text{m}$ 오차), Alt 오차 분산 $\sigma_z^2 = 20.453$ ($\approx 4.52\text{m}$ 오차).
* **`position_covariance_type`**: `3` (`COVARIANCE_TYPE_KNOWN`, Septentrio 칼만 필터가 산출한 정밀 공분산 적용).

---

### Q7. `-p configure_rx:=false` 옵션을 붙였을 때와 안 붙였을 때의 결과가 펌웨어 업데이트 후 똑같아진 이유는?
* **구 펌웨어 (v1.0.0)**: 드라이버 기본값(`configure_rx:=true`)이 펌웨어 v1.0.0에서 지원하지 않는 SBF 명령어를 전송하여 에러가 발생했으나, `configure_rx:=false`로 자동 설정을 건너뛰어 우회 수신했습니다.
* **신규 펌웨어 (v1.1.0)**: 수신기 내부 SBF 명령어 구문 해석기가 최신화되어, `configure_rx:=true`이든 `false`이든 에러 없이 완벽하게 SBF 명령어를 정상 처리하게 되었습니다.

---

### Q8. ROS 2 토픽 `/tf`와 `/tf_static`의 정체와 `echo` 시 데이터가 안 나오는 이유는?
* **`/tf`**: 로봇 이동에 따라 동적으로 변하는 좌표 변환 트리를 담당합니다.
* **`/tf_static`**: 센서 설치 위치 등 고정된 좌표 변환 정보를 담당합니다.
* **데이터 미출력 이유**: `/tf_static`은 메시지를 매초 계속 쏘지 않고 **노드 시작 시 1회만 발행 (`TRANSIENT_LOCAL` QoS)**합니다. 노드 구동 후에 `echo`하면 지나간 메시지를 놓치므로 `ros2 topic echo /tf_static --qos-durability transient_local`로 조회해야 합니다.

---

### Q9. 펌웨어 업그레이드 후 토픽이 `/gpgga`, `/gprmc`에서 `/navsat/fix`로 변경된 이유는?
* **구 펌웨어 (v1.0.0)**: SBF 바이너리 파싱 실패로 드라이버가 텍스트 NMEA 백업 패스스루만 구동하여 NMEA 토픽(`/gpgga`, `/gprmc`)만 내보냈습니다.
* **신규 펌웨어 (v1.1.0)**: SBF 바이너리 수신(`PVTGeodetic`)이 100% 정상화되어 ROS 표준 위치 메시지인 **`/navsat/fix`** (및 `/navsat/poscovgeodetic`)를 파싱 및 직접 내보내게 되었습니다.

