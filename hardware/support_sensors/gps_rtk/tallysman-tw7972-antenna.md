# Tallysman Accutenna® TW7972 3중 대역 GNSS 안테나

## 정의

Tallysman TW7972는 GPS L1/L2/L5, GLONASS G1/G2/G3, BeiDou B1/B2, Galileo E1/E5a+b 및 L-band 보정 신호를 수신하는 고정밀 3중 대역(Triple Band) Accutenna® 안테나입니다. 셀룰러 700MHz 고출력 신호 간섭 및 상호변조를 방지하며, 정밀 농업, 자율주행 로봇 차량 추적, RTK 베이스/로버 시스템에 적용됩니다.

- **원본 데이터시트 PDF**: [`tallysman-tw7972-antenna.pdf`](tallysman-tw7972-antenna.pdf)

---

## 데이터시트 및 핵심 스펙

### 1. 지원 주파수 대역 및 수신 신호
- **대역 1 (L2/L5/E5/B2)**: 1164 MHz ~ 1254 MHz
- **대역 2 (L1/E1/B1/G1/L-Band)**: 1525 MHz ~ 1606 MHz
- **지원 위성 신호**:
  - **GPS**: L1, L2, L5
  - **GLONASS**: G1, G2, G3
  - **BeiDou**: B1, B2
  - **Galileo**: E1, E5a, E5b
  - **L-band Correction Services**

### 2. 안테나 앰프 및 LNA 성능

| 항목 | 사양 |
| :--- | :--- |
| **패치 아키텍처** | Circular, Dual Feed, Dual Stacked Patch |
| **LNA 증폭 이득 (Gain)** | **32 dB (typical)** |
| **LNA 잡음 지수 (Noise Figure)** | **2.5 dB (typical @ 25°C)** |
| **Axial Ratio @ Zenith** | L1/E1/L-Band: < 1 dB / L2/L5/G1/G2: < 1.5~2 dB |
| **편파 (Polarization)** | RHCP (우회전 편파) |
| **VSWR** | < 1.5:1 (typical), 1.8:1 (max) |
| **대역 외 차단 (Rejection)** | < 1050 MHz (> 45 dB), > 1730 MHz (> 40 dB) |

### 3. 전기적 사양
- **공급 전압 범위**: **+2.5 VDC ~ +16 VDC** (공급 전압 변동에 불변 성능 유지)
- **소모 전류**: **24 mA (typical @ 25°C)**, 25 mA (max @ 75°C)
- **ESD 보호**: 15 KV (Air discharge)

### 4. 기계적 & 환경 사양
- **크기**: 외경 **69 mm (dia) × 높이 22 mm (H)**
- **무게**: **180 g**
- **외하우징 재질**: Radome: EXL9330, Base: Zamak White Metal
- **장착 방식 (Attachment)**: **자석 장착 (Magnetic Mount)** + 하부 4개 스크루 홀 (#6x32, 4mm 깊이)
- **동작 온도**: **-40°C ~ +85°C**
- **내환경 규격**: **IP69K (완전 방수/고압 세척 대응)**, RoHS, REACH, RED 준수
- **내충격 & 내진동**: 수직축 50 G, 기타 축 30 G / MIL-STD-810D 진동 규격 검증

---

## RTK 수신기 연동 및 장착 팁

1. **Septentrio mosaic-go G5 연동**: 수신기의 안테나 RF 포트에 SMA 커넥터로 직결합니다.
2. **Ground Plane 효과**: 100mm 이상 직경의 금속 지판(Ground Plane) 상단에 안테나 자석 부착 시 최고의 Zenith 이득 및 멀티패스 억제 성능을 발휘합니다.
3. **이중 안테나 Heading 배치**: P3H 모듈 사용 시 2개의 TW7972 안테나를 로봇 차량 이동축 방향으로 1m 이상 이격 배치하여 직렬 연결합니다.
