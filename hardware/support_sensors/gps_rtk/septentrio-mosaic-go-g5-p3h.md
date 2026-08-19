# Septentrio mosaic-go G5 P3 / P3H 수신기

> **작성 일자**: 2026-08-11  
> **작성 장비**: `knu laptop` (KNU 노트북 PC)  
> **작성 AI**: Antigravity (Google DeepMind Team)  
> **파일명 규격**: `septentrio-mosaic-go-g5-p3h.md`

---

## 📌 Executive Abstract (상세 요약 및 초록)
본 문서는 **Septentrio mosaic-go G5 P3/P3H Evaluation Kit** RTK GNSS 수신기의 하드웨어 사양, 인터페이스 핀맵, 펌웨어 업그레이드, ROS 2 연동 및 실전 문답을 망라한 통합 기술 레퍼런스입니다. 

2026-08-11 진행된 실전 검증에서는 구 펌웨어(v1.0.0)에서 발생하던 ROSaic C++ 드라이버(`septentrio_gnss_driver`)의 SBF 명령어 구문 에러를 수신기 플래시 메모리에 최신 공식 펌웨어 **v1.1.0**(`mosaic-G5 P3H-1.1.0.suf`)을 파이썬 스크립트로 직접 라이팅하여 100% 완벽 해결하였습니다. 

그 결과 ROS 2 Humble 환경에서 4개 위성군(GPS+GLONASS+BeiDou+Galileo, `service: 15`)을 결합한 3D 위치 및 오차 분산 행렬 데이터가 표준 토픽 **`/navsat/fix`** (`sensor_msgs/msg/NavSatFix`)로 정상 수신됨을 실증하였습니다. 또한 사용자 질문 13종(전력계산, 핀맵, 수신기 방향 무관성, PPS 결선, NavSatFix 수치 해석, configure_rx 파라미터 원리, /tf_static QoS, 펌웨어 업그레이드 보고서, 국토지리정보원 NGII NTRIP 1cm RTK 연동가이드 등)을 축약 없이 풍부한 기술 디테일로 수록하였습니다.

---

## 📌 개요 및 정의

Septentrio mosaic-go G5는 mosaic-G5 P3™ (단일 안테나 초고정밀 RTK) 및 mosaic-G5 P3H™ (이중 안테나 서브 디그리 Heading 지원) 수신기 모듈을 탑재한 평가 키트(Evaluation Kit)입니다.


드론, 로봇, 자율주행 모빌리티 등 센티미터급 정밀 위치 측정 및 방위각 측정이 필요한 로봇 시스템을 위한 고정밀 멀티 밴드 GNSS 수신기입니다.

> 📄 **원본 데이터시트 PDF**: [`septentrio-mosaic-go-g5-p3h.pdf`](septentrio-mosaic-go-g5-p3h.pdf)

---

## 🔗 관련 소프트웨어 및 센서 십자 링크 (Cross-Links)
* 📡 **체결 3중 대역 안테나**: [`Tallysman TW7972 안테나`](tallysman-tw7972-antenna.md)
* 💻 **통합 ROS 2 NGII NTRIP RTK 브릿지 노드**: [`septentrio_ngii_ntrip_bridge.md`](../../../software/ros2_basics/septentrio_ngii_ntrip_bridge.md)
* ⏱️ **하드웨어 PPS 동기화 및 Bag 검증**: [`lidar-rtk-pps-sync-bag.md`](../../../software/sensorfusion/lidar-rtk-pps-sync-bag.md)
* 🌐 **RTK MQTT DB 연동 브릿지**: [`rtk-mqtt-db-bridge.md`](../../../software/protocol/rtk-mqtt-db-bridge.md)
* 📹 **라이다-카메라-GNSS 동기화 녹화**: [`lidar-insta360-sync-record.md`](../../../software/sensorfusion/lidar-insta360-sync-record.md)
* 🌐 **4G LTE 라우터 (NTRIP 연동)**: [`Teltonika RUT241 라우터`](../router/teltonika-rut241.md)


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

---

### Q10. 동일한 안테나 위치에서도 분산 행렬(Covariance Matrix) 수치가 계속 변하는 이유는?
* **원인**: 약 20,000km 상공에서 이동하는 위성의 기하학적 배치(DOP 지수), 대기층(전離層/대기권) 신호 지연 및 굴절 오차, 주변 건물 반사파(Multipath), 위성 신호 세기(C/N0)가 1초마다 동적으로 변하기 때문입니다.
* Septentrio 수신기 내부의 칼만 필터(Kalman Filter)가 1Hz 매 초마다 실시간 신호 품질을 평가하여 오차 범위($\sigma_x, \sigma_y, \sigma_z$)를 동적으로 재계산합니다.

---

### Q11. 현재 출력되는 `/navsat/fix` 데이터는 RTK 보정 데이터가 포함된 것인가요?
* **아닙니다 (Standalone Multi-GNSS 3D Fix 상태).**
* 현재 `status.status` 값은 `0` (`STATUS_FIX`)으로, RTK 보정 없이 4개 위성군(GPS, GLONASS, BeiDou, Galileo)의 위성 신호만을 이용해 위치를 잡은 **단독 측위 상태 (오차 약 1.5m ~ 4m)**입니다.
* 인터넷(NTRIP)을 통해 국토지리정보원 보정 신호를 입력하면 `status.status`가 `2` (`STATUS_GBAS_FIX` / RTK Fixed)로 변경되며 **1cm ~ 2cm 센티미터 급 정밀도**로 고정됩니다.

---

### Q12. 국토지리정보원(NGII) 최신 보정 데이터(NTRIP) 연동 접속 정보 및 포털 변경 내역은?
* **개요**: 국토지리정보원은 전국 상시관측소 데이터를 기반으로 무료 RTK 보정 신호(RTCM 3.x)를 인터넷(NTRIP 프로토콜)으로 제공합니다.
* **1단계: GNSS 서비스 포털 회원가입 및 ID 확인**
  * **통합 포털 웹사이트**: **[`https://geodesy.ngii.go.kr/portal/main`](https://geodesy.ngii.go.kr/portal/main)** (기존 `gnss.ngii.go.kr`에서 최신 통합 포털로 변경)
  * 포털 로그인 후 **'측위보정정보(네트워크 RTK)'** 메뉴에서 서비스 이용 ID 생성/확인.
* **2단계: 최신 NTRIP 접속 정보**
  * **주소 (Caster / Host)**: **`rts1.ngii.go.kr`** (VRS 최신 주소 / FKP 사용 시 `rts2.ngii.go.kr`, 또는 IP `211.175.76.10`)
  * **포트 (Port)**: **`2101`**
  * **마운트포인트 (Mountpoint)**: **`VRS-RTCM32`** (권장: GPS+GLONASS+BeiDou+Galileo 4개 위성군) 또는 `VRS-RTCM30`
  * **ID / Password**: GNSS 포털 발급 아이디 / **`ngii`** (RTK 서비스 전용 공통 비밀번호)

---

### Q13. 펌웨어 업그레이드(v1.1.0) 진행 절차 및 적용 결과는?
* **사용 파일**: `sub_sensors` 폴더 내 `mosaic-G5 P3H_fwp_1.1.0.zip` 압축 해제 ➔ `mosaic-G5 P3H-1.1.0.suf`
* **업그레이드 절차**:
  1. 수신기에 시리얼 명령 `exeResetReceiver, Upgrade, none` 전송하여 업그레이드 부트로더 모드 진입
  2. 수신기가 `Ready for SUF download` 응답 출력 후, 2.95MB 용량의 `.suf` 파일 바이너리 스트리밍 송신
  3. 수신기 내부 플래시 메모리 프로그래밍 및 CRC 무결성 검증 (`SUF fully processed`) 후 자동 재부팅
* **최종 결과**: 펌웨어 v1.1.0 정식 적용 완료. 구 펌웨어 경고 메시지 완전 소멸 및 ROS 2 `septentrio_gnss_driver` SBF 파싱 100% 정상 가동.

---

### Q14. mosaic-go G5 평가키트에 RJ45 랜포트가 없는데 필드 로봇 하드웨어 연결은 어떻게 구성하나요?
* **하드웨어 인터페이스**: mosaic-go G5 평가키트에는 RJ45 포트가 없으며 **USB-C 포트**가 5V 전원 공급 + USB-Ethernet(`192.168.3.1`) + NMEA 시리얼 통신을 단일 케이블로 통합 제공합니다.
* **필드 로봇 온보드 연결 아키텍처**:
  * **RUT241 LTE 라우터 ➔ 엣지 PC (노트북/Jetson)**: LAN 케이블 연결 (무선 LTE 인터넷 공급).
  * **mosaic-go G5 수신기 ➔ 엣지 PC (노트북/Jetson)**: USB-C 케이블 연결 (전원 공급 및 USB 가상 이더넷 `192.168.3.1` 형성).
  * **동작 원리**: 수신기는 USB-C가 형성한 가상 이더넷망을 통해 엣지 PC 및 RUT241 라우터를 경유하여 국토지리정보원(`rts1.ngii.go.kr`)에 접속합니다.

---

### Q15. 라우터 자체 NTRIP 모드 (방식 A) vs 수신기 자체 NTRIP 모드 (방식 B) 비교 및 최적 선택은?
* **방식 A (라우터 처리)**: RUT241 라우터 웹페이지(`192.168.1.1`)에 계정을 등록하여 라우터가 보정 데이터를 다운로드받아 수신기로 전달.
* **방식 B (수신기 처리 - 강력 추천)**: RUT241은 단순 무선 인터넷 통로 역할만 대어주고, mosaic-go G5 수신기 웹페이지(`192.168.3.1`)에서 계정을 등록하여 수신기가 직접 국토지리정보원에 접속.
* **방식 B 선택 이유**: 야외 노지에서 LTE 신호 순간 단절 시 수신기 펌웨어가 5초 이내 자동 재접속(Auto-Reconnect)하여 RTK Fixed 상태를 완벽 복구하며, 수신기 단일 웹 화면에서 위성 SNR과 보정속도, 1cm 오차를 한눈에 관찰할 수 있어 모니터링 및 안전성이 가장 뛰어납니다.

---

### Q16. 방식 B를 쓸 때 mosaic-go G5 수신기가 안 필요한가요?
* **반드시 필요합니다!** RUT241 라우터는 위성 안테나 칩이 없는 무선 통신 기기이므로 위성 전파를 전혀 수신하지 못합니다.
* mosaic-go G5 수신기가 Tallysman 안테나로 우주 상공 2만 km의 위성 전파(GPS/GLONASS/BeiDou/Galileo)를 수신하고, 라우터가 준 보정 데이터(RTCM3)를 수신기 내부 칩셋에서 결합해야만 1cm 정밀 위치가 계산됩니다.

---

### Q17. 위성 신호 수신과 RTK 보정 데이터 수신의 결정적 차이 및 실내/실외 동작 원리는?
* **위성 신호 (전파)**: 상공 2만 km의 인공위성이 쏘는 라디오 전파. **인터넷 0% 전혀 불필요**. 안테나로 수신. 콘크리트 실내 천장을 뚫지 못함.
* **RTK 보정 데이터 (RTCM3)**: 지상 기준국 데이터. **인터넷 100% 필수**. RUT241 LTE망으로 수신.
* **실내 테스트 실패 원인 분석**: 실내에서는 인터넷이 되므로 보정 데이터는 수신되나, 위성 전파가 콘크리트에 막혀 0개 수신되므로 연산 불가능(`NO_FIX`). 안테나를 실외(창문 밖 또는 하늘이 보이는 곳)로 배치해야 1cm RTK Fixed가 고정됩니다.

---

### Q18. 방식 B 적용 시 Teltonika RUT241 라우터의 최종 역할은?
* RUT241 라우터는 센서 연산이나 복잡한 파싱을 하지 않고, 오직 무선 LTE 인터넷 공급, NGII 보정 통로 통과, 관제 서버 DB로의 MQTT 텔레메트리 데이터 전송만을 수행하는 **안정적인 무선 데이터 통신 허브(Gateway)** 역할을 수행합니다.

---

### Q19. Septentrio 수신기 단독 위성 수신 테스트 4단계 수칙 (시리얼 포트 판독 및 ROS 2 드라이버 구동 방법)?

* **개요**: RTK 보정 데이터(NTRIP) 입력 전, 수신기 자체가 우주 인공위성 전파 신호를 정상 수신하고 표준 위치 토픽(`/navsat/fix`)을 발행하는지 검증합니다.
* **상세 테스트 4단계 수칙**:
  1. **1단계: 시리얼 통신 포트(`/dev/ttyACM*`) 판독 및 권한 확인**:
     * `ls -l /dev/ttyACM*` 명령어로 수신기 포트 조회.
     * 모자이크 G5 수신기는 플래싱/제어 포트(`/dev/ttyACM0`)와 실제 NMEA 위치 통신 포트(**`/dev/ttyACM1`**)로 분리 인식되므로 NMEA 통신 포트 경로인 **`/dev/ttyACM1`**을 지정해야 합니다.
  2. **2단계: ROS 2 Humble 실행 환경 로드 (Prerequisite)**:
     * `source /opt/ros/humble/setup.bash` 실행하여 `rclpy` 및 ROS 2 메시지 환경 탑재.
  3. **3단계: 통합 RTK 수신기 드라이버 노드 실행**:
     * `python3 ~/workspaces/insta360/software/ros2_basics/septentrio_ngii_ntrip_bridge.py` 실행.
  4. **4단계: 표준 위치 토픽 `/navsat/fix` 단독 3D 측위 수신 검증**:
     * 새 터미널에서 `ros2 topic echo /navsat/fix` 실행하여 위도, 경도, 고도 수치 및 `status.status: 0` (`STATUS_FIX` / 단독 3D 측위) 수신 확인.

---

### Q20. Septentrio 웹 UI (`http://192.168.3.1`) 접속 시 라우터(`192.168.1.x`) 및 라이다(`169.254.x.x`) 서브넷 충돌 해결 방법은?

* **원인**: 노트북 랜카드가 `192.168.1.x` 라우터 대역만 쥐고 있어 3.x 대역인 수신기 웹서버 접속 패킷을 보낼 길을 찾지 못함.
* **해결책**: 기본 `eno1` 프로필은 순수 일반용으로 유지하고, 전용 개발 프로필(**`robot_dev`**)을 생성하여 보조 IP 주소(`192.168.3.100/24`)를 추가 등록(IP Subnet Aliasing)함으로써 수동 프로필 교체 없이 라우터 인터넷 + RTK 웹 UI(`192.168.3.1`) + Ouster 라이다(`169.254.129.201`)를 100% 동시에 가동.

> [!NOTE]
> **전용 개발 프로필 (`robot_dev`) 1줄 생성 명령**:
> `nmcli connection add type ethernet con-name "robot_dev" ifname eno1 ipv4.method auto +ipv4.addresses "192.168.3.100/24, 169.254.129.100/16" && nmcli connection up "robot_dev"`

---

### Q21. 기본 `eno1` 상태에서도 위성 위치 토픽이 들어오나요? RTK 1cm 고정을 위해 `192.168.3.1`이 필수인 이유는?

> [!IMPORTANT]
> **위성 토픽 수신 vs RTK 1cm 보정의 네트워크 요구사항 차이 (필수 숙지!)**

1. **단독 3D 측위 (`status.status: 0`, 오차 ~1.5m)**:
   * USB-C 케이블(시리얼 포트 `/dev/ttyACM1`)을 타고 읽어오는 시리얼 통신이므로, 랜선 프로필이 기본 `eno1`이든 랜선을 뽑아두었든 **USB 케이블만 연결되어 있으면 `/navsat/fix` 위치 토픽은 100% 수신**됩니다.
2. **RTK 1cm 고정 측위 (`status.status: 2`, 오차 ~1cm)**:
   * 수신기가 웹 UI(`http://192.168.3.1`)에 저장된 계정으로 국토지리정보원(`rts1.ngii.go.kr`)에 접속하고 LTE 보정 데이터(RTCM3)를 가져오기 위해서는 **`192.168.3.1` 가상 이더넷 통로가 반드시 연결되어 있어야 가동**됩니다.

* **요약**: 단독 측위 토픽 수신은 기본 `eno1`에서도 항상 가능하며, **1cm 센티미터 급 RTK 고정을 사용할 때만 `robot_dev` 프로필을 활성화하여 `192.168.3.1` 가상 이더넷 통로를 열어두면 됩니다.**

---

### Q22. 위치를 옮기지 않았는데 `status.status`가 `0`에서 `2`(`STATUS_GBAS_FIX`)로 승격된 결정적 이유는?

> [!TIP]
> **수신기 USB 시리얼 포트 RTCM3 입력 디코딩 활성화 세팅 검증 완료!**

* **원인 분석**: Septentrio 수신기의 USB 시리얼 포트(`/dev/ttyACM1`)로 국토지리정보원 RTCM3 보정데이터 바이트가 전달되더라도, 수신기 내부 칩셋이 이를 디코딩하도록 명령(`sdio, USB1, auto, RTCMv3`)이 전송되지 않으면 보정데이터를 무시하고 `status.status: 0` (단독 측위) 상태를 유지합니다.
* **해결 및 검증**: [`septentrio_ngii_ntrip_bridge.py`](../../../software/ros2_basics/septentrio_ngii_ntrip_bridge.py) 노드 초기화 시 `sdio, USB1, auto, RTCMv3` 명령어를 송신하도록 보완한 직후, 수신기 내부 칩셋이 RTCM3 보정데이터를 즉시 해석하여 **`status.status: 2` (`STATUS_GBAS_FIX` / RTK Fixed)로 실시간 승격**되었습니다.




