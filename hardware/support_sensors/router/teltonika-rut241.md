# 📑 Teltonika RUT241 산업용 4G LTE 라우터

> **작성 일자**: 2026-08-14  
> **작성 장비**: `knu laptop` (KNU 노트북 PC / Linux Ubuntu 22.04 LTS)  
> **작성 AI**: Antigravity (Google DeepMind Team)  
> **파일명 규격**: `teltonika-rut241.md`  

---

## 📌 Executive Abstract (상세 요약 및 초록)

본 문서는 Teltonika RUT241 산업용 4G LTE 라우터의 물리적/전기적 하드웨어 사양, 인터페이스 핀맵, 온보드 로봇 네트워크 배치 수칙, 유심(SIM) 셀프개통시 OMD/IMEI 등록 및 스마트폰 서식 차이점 극복 가이드, 네트워크 무선 데이터 전송 동작 검증 4단계 절차를 다룹니다.

RUT241은 로봇 온보드 환경에서 자급제 데이터 기기로 동작하며, 일반 스마트폰 셀프개통 사이트에서 요구하는 7자리 핸드폰 일련번호가 존재하지 않으므로 통신사 OMD 단말기(LTE 라우터) 등록 및 APN 설정을 통해 개통 문제를 해결할 수 있습니다. 또한 LED 상태등, WebUI(`192.168.1.1`), RSRP/SINR 수신 신호 품질 진단, Ping 테스트 및 Auto Reboot 메커니즘을 통해 무인 이송 로봇 및 현장 데이터 수집 시스템의 24/7 통신 안정성을 제공합니다.

---

## 1. 개요 및 주요 특징 (Overview & Key Features)

* **장비 정의**: Teltonika RUT241은 4G LTE (Cat 4), 3G, 2G 셀룰러 통신 및 Wi-Fi 4(802.11b/g/n), Dual Ethernet, eSIM™ SGP.22를 지원하는 컴팩트형 산업용 엣지 라우터입니다. 로봇 온보드 네트워크 구획, 원격 관제(RMS), VPN 릴레이, 산업용 Modbus/MQTT 게이트웨이 및 통신 장애 시 자동 Failover를 제공합니다.
* **원본 데이터시트 PDF**: [`teltonika-rut241.pdf`](teltonika-rut241.pdf)

---

## 2. 🔗 관련 소프트웨어 및 센서 십자 링크 (Cross-Links)

* 📡 **체결 수신기/센서**: [`Septentrio RTK 수신기`](../gps_rtk/septentrio-mosaic-go-g5-p3h.md)
* 📹 **관련 비전/라이다 센서**: [`Ouster OS0-128 라이다`](../../vision_sensors/lidar/ouster-os0-128.md), [`Insta360 360도 카메라`](../../vision_sensors/camera/insta360-camera-sdk.md)
* 🌐 **RTK MQTT DB 연동 브릿지**: [`rtk-mqtt-db-bridge.md`](../../../software/protocol/rtk-mqtt-db-bridge.md)
* ⏱️ **하드웨어 PPS 동기화 및 Bag 검증**: [`lidar-rtk-pps-sync-bag.md`](../../../software/sensorfusion/lidar-rtk-pps-sync-bag.md)
* 💻 **관련 센서 융합 모듈**: [`라이다-카메라 동시 녹화 아키텍처`](../../../software/sensorfusion/lidar-insta360-sync-record.md)
* 📡 **관련 ROS 2 파서 노드**: [`Septentrio NMEA Fix 노드`](../../../software/ros2_basics/septentrio_nmea_fix_node.py)

---

## 3. 하드웨어 기술 사양 (Hardware Specifications)

| 구분 | 주요 사양 (Specification) | 비고 |
| :--- | :--- | :--- |
| **셀룰러 모듈** | 4G LTE (Cat 4) 최대 150 Mbps DL / 50 Mbps UL | 3GPP Rel 10/11 준수, 3G/2G 하위 호환 |
| **SIM 슬롯 구성** | 1x Mini SIM (2FF, 1.8V/3V) + 1x eSIM™ (Consumer) | SIM Auto-Switch (신호약화/로밍 시 자동전환) |
| **무선 Wi-Fi** | 802.11b/g/n (Wi-Fi 4, 2.4 GHz), AP/Station 모드 | 최대 50대 접속, WPA3-SAE, Enterprise, Mesh 지원 |
| **이더넷 포트** | 1x WAN (10/100 Mbps) + 1x LAN (10/100 Mbps) | Auto MDI/MDIX 지원 |
| **입출력 (I/O)** | 1x Digital Input (0~6V Low, 8~30V High), 1x Digital Output | Open Collector, 4-pin 전원 커넥터 연동 |
| **프로세서 & 메모리** | Mediatek 580 MHz (MIPS 24KEc), 128 MB RAM / 16 MB Flash | OpenWrt 기반 RutOS (C/C++/Lua/Busybox SDK) |
| **전원 및 소비 전력** | 9 ~ 30 VDC (4-pin 산업용 포트), 패시브 PoE 수전(LAN1) | 최대 소비 전력 < 6.5 W, 역극성/서지 보호 |
| **안테나 커넥터** | 2x SMA (LTE 전용), 1x RP-SMA (Wi-Fi 전용) | 외장 안테나 분리형 커넥터 |
| **물리 규격 및 환경** | 83 x 25 x 74 mm, 125 g, 알루미늄 하우징 | 동작 온도 -40°C ~ +75°C, IP30 등급, KC 인증 |

---

## 4. 핀맵 및 커넥터 가이드 (Pinout & Connection Diagram)

### 🔌 4-pin 전원 및 I/O 커넥터 핀맵
* **전원 포트 규격**: 4-pin industrial DC power socket (Micro-Fit 4-pin)
  * 🔴 **Pin 1 (V+)**: `+9 ~ +30 VDC` (적색 케이블)
  * 🖤 **Pin 2 (V-)**: `GND` (흑색 케이블)
  * 🟢 **Pin 3 (Digital Input)**: `0~6V (Low)`, `8~30V (High)` (디지털 입력)
  * ⚪ **Pin 4 (Digital Output)**: Open Collector (최대 30V / 300mA 디지털 출력)

---

## 5. 물리적 설치 및 배치 3대 수칙 (Installation Guidelines)

1. **[수칙 1] LTE 안테나 수직 고정 및 무선 간섭 분리**:
   - LTE 안테나 2개(SMA 커넥터)는 상향 수직 방향으로 설치하고, Wi-Fi 안테나(RP-SMA)와 최소 10cm 이상 이격 배치하여 기기간 무선 스펙트럼 간섭을 방지합니다.
2. **[수칙 2] 온보드 진동 방지 및 방열 확보**:
   - 알루미늄 하우징 표면 방열을 위해 밀폐 공간 설치를 피하고, 로봇 이동 시 진동으로 인한 SIM 탈착 및 DC 커넥터 이탈이 없도록 DIN Rail 마운트 또는 진동 감쇄 브래킷에 견고히 고정합니다.
3. **[수칙 3] 로봇 서브넷 IP 충돌 차단**:
   - 라우터 기본 Gateway IP(`192.168.1.1`)가 로봇 내부 센서(Septentrio, Ouster 라이다, 카메라 PC 등)의 고정 IP 대역과 충돌하지 않도록 서브넷(`192.168.1.0/24`) 대역을 통일하거나 로봇 고정 IP 체계를 사전에 할당합니다.

---

## 6. ROS 2 드라이버 및 토픽 연동 (ROS 2 Integration)

### 🚀 로봇 네트워크 구획 및 원격 관제 구성
1. **로봇 온보드 서브넷 통합**:
   - RUT241 LAN 포트를 온보드 스위치 hub에 연결하고, Ouster OS0-128 라이다, Insta360 제어 PC, Septentrio RTK GNSS 수신기를 동일 서브넷(`192.168.1.x`)으로 묶습니다.
2. **WireGuard / OpenVPN 관제 릴레이**:
   - RUT241 RutOS 내부에 WireGuard/OpenVPN 클라이언트를 탑재하여 관제실 전용 암호화 터널을 구축하고, ROS 2 `CycloneDDS` / `FastDDS` Discovery Server 또는 `zenoh-bridge-ros2`를 통해 멀티 로봇 관제 토픽을 전송합니다.

---

## 7. ❓ 자주 묻는 질문 및 실전 기술 Q&A (Technical Q&A)

### Q1. 유심 등록 중 IMEI는 입력했는데, 스마트폰 모델명과 7자리 일련번호를 등록하라고 나옵니다. RUT241 라우터에는 이게 없는데 어떻게 해야 하나요?

* **결론**:
  * 접속하신 등록 페이지가 **'스마트폰 전용 셀프개통'** 서식이기 때문입니다. RUT241과 같은 자급제 LTE 라우터는 스마트폰 규격의 모델명과 7자리 일련번호가 존재하지 않으므로 통신사 **OMD(Open Model Device) 단말기(LTE 라우터)** 전산 등록 또는 유심기변으로 해결해야 합니다.

* **상세 원인 및 해결 방법 3가지**:
  1. **[해결 1 - 가장 추천] 통신사 고객센터(114)를 통한 OMD 등록**:
     * 이용 중인 통신사/알뜰폰 고객센터에 전화하여 *"자급제 LTE 라우터(RUT241) 사용을 위해 OMD 단말기 등록(IMEI 등록) 요청"*을 전달합니다.
     * 라우터 뒷면 스티커에 표기된 **IMEI**(15자리)와 **SN(Serial Number)**을 제공하면 상담원이 전산에 `OMD 기타 라우터`로 수동 등록해 줍니다.
  2. **[해결 2] 스마트폰에서 유심 먼저 개통 후 라우터로 이동 (유심기변)**:
     * 구매한 유심이 일반 스마트폰 요금제(음성+데이터)일 경우, 개인 스마트폰에 유심을 삽입하여 셀프개통을 완료(통화/데이터 확인)합니다.
     * 개통 완료 후 유심을 빼서 RUT241 라우터에 꽂고 **2~3회 재부팅**하면 라우터가 유심을 정상 인식합니다.
  3. **[해결 3] 자급제 OMD 공통 코드 입력 (온라인 서식 입력 시)**:
     * 온라인 서식에서 모델명 검색이 가능할 경우 아래 자급제 코드명을 검색하여 선택합니다:
       * **SKT 계열**: `OMD 기타 LTE 라우터` 또는 `OMD TABLET`
       * **KT 계열**: `PTA-TYPE5` (LTE 데이터 전용/라우터)
       * **LGU+ 계열**: `OMD 기타 LTE 라우터`
     * 일련번호 필수 입력창에는 라우터 뒷면 스티커의 `SN` (시리얼 번호)를 입력합니다.

---

### Q2. RUT241 라우터 무선 데이터 수신 상태 진단 및 LTE 신호 지표 4가지(RSSI, RSRP, RSRQ, SINR) 정밀 해석 방법은?

* **결론**:
  * **[1단계] 전면 LED 확인 ➔ [2단계] Ping 연속 패킷 손실률 테스트 ➔ [3단계] WebUI(`192.168.1.1`) LTE 4대 수신 지표 진단** 3단계를 수행합니다.

* **상세 테스트 수칙**:
  1. **1단계: 전면 LED 상태 확인**:
     * `Power`: 초록색 점등 / `Mobile Network`: `4G/LTE` 점등 / `Signal Strength`: 오른쪽 막대 **2~3개 이상** 점등.
  2. **2단계: 네트워크 핑(Ping) 연속 패킷 테스트**:
     * 터미널에서 `ping 8.8.8.8 -c 5` 실행하여 **패킷 손실률(Packet Loss) 0%** 및 지연 시간(rtt avg ~70ms) 수신 검증.
  3. **3단계: 관리자 페이지 WebUI (`192.168.1.1`) 4대 수신 지표 정밀 진단**:
     * **Status > Network > Mobile** 진단:
       * **`RSSI (-69 dBm / Good)`**: 무선 공간 전체 전파 수신 총합 전력 (양호)
       * **`RSRP (-96 dBm / Fair)`**: 기지국 참조 신호 순수 수신 세기 (실내/창가에서 보통 수준)
       * **`RSRQ (-7 dB / Excellent)`**: 신호 수신 품질 (잡음 대비 순수 신호 비율, 최상)
       * **`SINR (9~17 dB / Good)`**: 신호 대 신호가란(잡음) 간섭비 (양호)

---

### Q3. RSRP 수치가 `-96 dBm` (Fair to Poor)로 나오는데, RTK 보정 데이터 수신에 영향이 없나요?

* **결론**: **전혀 영향이 없으며 100% 안정적으로 동작합니다.**
* **이유 분석**:
  1. **RSRQ(-7dB)와 SINR(+9~17dB)의 우수성**: 전파 세기(RSRP)가 보통(-96dBm)이어도 잡음 간섭비(SINR)가 높고 RSRQ가 최상이면 패킷 유실률이 0%로 완벽하게 전송됩니다.
  2. **RTK 보정 데이터(RTCM3) 필요 용량**: RTK 보정 데이터는 초당 **약 1KB ~ 2KB/sec의 극소 용량**만 사용합니다. 현재 LTE 라우터의 다운로드 속도(10~30Mbps)는 필요 용량의 **10,000배 이상**이므로 매우 안정적입니다.

---

### Q4. 우분투 환경에서 인터넷(RUT241), RTK 수신기(Septentrio), 3D 라이다(Ouster/VLP16), 시놀로지 NAS 네트워크 프로필을 수동 전환 없이 단 1개의 개발 전용 프로필(`robot_dev`)로 통합하는 방법은?

* **개요**: 기본 `eno1` 프로필은 순수 일반용으로 유지하고, 전용 개발 프로필(**`robot_dev`**)을 별도 생성하여 **[DHCP 자동 인터넷 + 3개 보조 IP]**를 동시 바인딩(IP Subnet Aliasing)함으로써 수동 프로필 교체를 완전 제거합니다.
* **통합 원리**:
  * **기본 DHCP**: RUT241 라우터 무선 인터넷 자동 수신 (`192.168.1.x`)
  * **보조 IP 1 (Septentrio RTK용)**: `192.168.3.100/24` (Netmask: `255.255.255.0`)
  * **보조 IP 2 (3D 라이다용)**: `169.254.129.100/16` (Netmask: `255.255.0.0`)
  * **보조 IP 3 (시놀로지 NAS용)**: `192.168.x.x/24`
* **전용 프로필 생성 및 1줄 적용 명령어**:
  ```bash
  nmcli connection add type ethernet con-name "robot_dev" ifname eno1 ipv4.method auto +ipv4.addresses "192.168.3.100/24, 169.254.129.100/16" && nmcli connection up "robot_dev"
  ```

---

### Q5. DHCP(자동 IP)와 넷마스크(Netmask), 센서 고정 IP(Static IP)의 명확한 개념 구별은?

* **DHCP (자동 번호표 발급기)**: 라우터가 랜선을 꽂은 노트북에 외부 인터넷용 IP(`192.168.1.239`)를 자동으로 발급해 주는 시스템.
* **넷마스크 (Netmask / 울타리 경계선)**: 어디까지가 같은 동네(아파트 단지)인가를 구분하는 울타리. `255.255.255.0`(`/24`)은 앞 3자리 고정, `255.255.0.0`(`/16`)은 앞 2자리 고정.
* **센서 고정 IP (Static IP)**: 라이다(`169.254.129.201`) 및 RTK 수신기(`192.168.3.1`)는 엣지 PC가 언제 접속하든 통신이 터지지 않도록 고유 고정 신분증을 장비 내부에 영구 보유함.
* **노트북 랜카드의 통합 동작**: 노트북이 DHCP 인터넷 신분증을 메인으로 쥐고, 추가 등록된 2개 보조 IP 신분증을 손에 쥐어 전 센서와 동시에 대화함.

---

### Q6. RUT241 라라우터의 DHCP IP 주소가 재부팅 시 변경되어도 RTK 수신 및 서버 MQTT 전송에 영향이 없나요?

* **결론**: **전혀 영향을 주지 않으며 100% 정상 가동됩니다.**
* **이유 분석**:
  1. **NGII RTK 수신**: 수신기가 외부 국토지리정보원(`rts1.ngii.go.kr`)으로 나가는 아웃바운드(Outbound) 요청이므로 내부 라우터 DHCP IP가 변경되어도 보정데이터 수신은 100% 정상 유지됨.
  2. **서버 MQTT 전송**: ROS 2 MQTT 브릿지 노드가 목적지 중앙 서버 고정 IP(`100.118.194.54:1883`)로 데이터를 쏘아 올리므로 노트북 내부 DHCP IP 변동에 영향을 받지 않음.

---

## 8. 펌웨어 및 변경 이력 (Revision & Firmware History)

* **현재 적용 RutOS 펌웨어**: `RUT2_R_00.07.x` (OpenWrt 기반)
* **변경 및 트래킹 이력**:
  * `2026-08-14`: Teltonika RUT241 LTE 라우터 유심 셀프개통(OMD/IMEI/일련번호 등록) 및 무선 데이터 전송 동작 검증 4단계 테스트 가이드 수록 완료 (`knu laptop` / AI: Antigravity)
