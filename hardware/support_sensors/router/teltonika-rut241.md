# Teltonika RUT241 산업용 4G LTE 라우터

## 정의

Teltonika RUT241은 4G LTE (Cat 4), 3G, 2G 셀룰러 통신 및 Wi-Fi 4(802.11b/g/n), Dual Ethernet, eSIM™ SGP.22를 지원하는 컴팩트형 산업용 엣지 라우터입니다. 로봇 온보드 네트워크 구획, 원격 관제(RMS), VPN 릴레이, 산업용 Modbus/MQTT 게이트웨이 및 통신 장애 시 자동 Failover를 제공합니다.

- **원본 데이터시트 PDF**: [`teltonika-rut241.pdf`](teltonika-rut241.pdf)

---

## 데이터시트 및 핵심 스펙

### 1. 셀룰러 및 통신 속도

| 통신 모듈 | 다운링크 (DL) / 업링크 (UL) 속도 | 비고 |
| :--- | :--- | :--- |
| **4G LTE (Cat 4)** | **최대 150 Mbps DL / 50 Mbps UL** | 3GPP Rel 10/11 준수 |
| **3G** | 최대 21 Mbps DL / 5.76 Mbps UL | |
| **2G** | 최대 236.8 kbps DL / 236.8 kbps UL | |

- **SIM 슬롯 구성**:
  - **1x Physical Mini SIM (2FF)** 슬롯 (1.8 V / 3 V 외부 슬롯)
  - **1x eSIM™ (Consumer 타입)**: 최대 7개 프로필 저장 지원
- **SIM Auto-Switch (자동 전환)**: 신호 약화, 데이터 한계 초과, 로밍, 네트워크 연결 실패 시 물리 SIM ↔ eSIM 간 자동 전환.

### 2. 무선 Wi-Fi 네트워크
- **Wi-Fi 표준**: 802.11b/g/n (Wi-Fi 4), 2.4 GHz
- **동작 모드**: Access Point (AP), Station (STA)
- **Wi-Fi 보안**: WPA2-Enterprise, WPA2-PSK, WPA3-SAE, WPA3-EAP, OWE, EAP-TLS (PKCS#12 인증서)
- **동시 접속자 수**: **최대 50대 장치 동시 연결 지원**
- **무선 기능**: Wireless Mesh (802.11s), Fast Roaming (802.11r), Relayd, QR 코드 Wi-Fi 접속 기능

### 3. 이더넷 (Ethernet) 및 입출력 (I/O)
- **이더넷 포트**:
  - **1x WAN 포트**: 10/100 Mbps (IEEE 802.3, Auto MDI/MDIX)
  - **1x LAN 포트**: 10/100 Mbps (IEEE 802.3, Auto MDI/MDIX)
- **디지털 I/O (4-pin 전원 커넥터 연동)**:
  - **1x Digital Input**: 0 ~ 6 V (Logic Low), 8 ~ 30 V (Logic High)
  - **1x Digital Output**: Open Collector, 최대 30 V, 300 mA

### 4. 프로세서, 메모리 및 RutOS
- **CPU**: Mediatek 580 MHz (MIPS 24KEc)
- **RAM / Flash**: **128 MB DDR2 RAM / 16 MB SPI Flash**
- **운영체제**: **RutOS (OpenWrt 기반 Linux OS)**, C/C++/Lua/Busybox SDK 제공

### 5. 네트워크, 보안 & VPN
- **라우팅 & 프로토콜**: Static, Dynamic (BGP, OSPF v2, RIP, EIGRP), Policy Based Routing, VRRP, DHCP, DDNS
- **VPN 지원**: **OpenVPN (27종 암호화)**, **IPsec (14종 암호화)**, **WireGuard**, GRE, PPTP, L2TP, ZeroTier, DMVPN, SSTP
- **산업용 게이트웨이**: Modbus TCP (Server/Client), MQTT Broker/Publisher, OPC UA, DNP3, DLMS/COSEM
- **공격 방지 & 방화벽**: DDOS/SYN Flood 방지, Port Scan 방지, Port Forwarding, DMZ, NAT

### 6. 전기적 & 물리적 사양
- **전원 커넥터**: 4-pin industrial DC power socket
- **입력 전압 범위**: **9 VDC ~ 30 VDC** (역극성 보호, >31 VDC 10us 서지 보호)
- **패시브 PoE 수전**: LAN1 포트를 통한 패시브 PoE 수전 지원 (Mode B, 9 ~ 30 VDC)
- **소비 전력**: **최대 < 6.5 W**
- **안테나 커넥터**: **2x SMA (LTE 전용)**, **1x RP-SMA (Wi-Fi 전용)**
- **외하우징**: 알루미늄 하우징, 플라스틱 패널
- **크기 & 무게**: **83 x 25 x 74 mm / 125 g**
- **동작 온도**: **-40°C ~ +75°C** (습도 10% ~ 90% non-condensing, IP30 등급)
- **인증**: KC (한국 방송통신기자재 인증), CE, FCC, UKCA, IC, E-mark, CB, UL/CSA 준수

---

## 로봇 온보드 네트워크 구축 가이드

1. **로봇 서브넷 구획**:
   - RUT241 LAN 포트 및 Wi-Fi AP를 로봇 전용 서브넷(`192.168.1.0/24`)으로 설정.
   - Ouster 라이다, Insta360 제어 PC, RTK 수신기, 로봇암 통신 장비를 동일 서브넷으로 구성.
2. **원격 관제 브리지**:
   - WireGuard 또는 OpenVPN을 RUT241 내부에서 실행하여 로봇 외부 관제 서버로 관제 데이터(ROS 2 데이터) 전송.
3. **네트워크 백업 및 자동 복구**:
   - `Ping Reboot` 및 `Wget Reboot` 설정을 통해 LTE 통신 손실 시 라우터 자동 재부팅 및 복구 실행.
