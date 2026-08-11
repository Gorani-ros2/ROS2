# 📑 [제조사] [모델명] [장비 카테고리/타입]

## 1. 개요 및 주요 특징 (Overview & Key Features)
* **장비 정의**: 장비의 핵심 역할 및 적용 분야 요약
* **핵심 기능**:
  * 기능 1: 주요 기능 불릿 설명
  * 기능 2: 주요 기능 불릿 설명
* **원문 데이터시트**: `[PDF 원본 파일명](파일명.pdf)` (반드시 문서와 동일한 폴더에 보관)

---

## 2. 하드웨어 기술 사양 (Hardware Specifications)

| 구분 | 주요 사양 (Specification) | 비고 |
| :--- | :--- | :--- |
| **전원 및 소모 전력** | 전압(V), 전류(mA), 최대 소모 전력(W) | USB / 외부 DC 전원 구분 |
| **통신 인터페이스** | USB-C, RS232, Ethernet, CAN 등 | 데이터/웹UI 포트 구분 |
| **성능 / 정밀도** | 센서 측정 범위, 갱신 주파수(Hz), 오차 정밀도 | |
| **물리 규격 및 커넥터** | 크기(mm), 무게(g), 방수방진(IP등급) | |

---

## 3. 핀맵 및 커넥터 가이드 (Pinout & Connection Diagram)

### 🔌 외부 인터페이스 / 케이블 핀맵
* **전원/시리얼 케이블 핀맵**:
  * 🔴 **Red**: `V_IN` (+5V DC)
  * 🖤 **Black**: `GND` (접지)
  * 🟡 **Yellow**: `TXD` (데이터 송신)
  * 🔵 **Blue**: `RXD` (데이터 수신)

---

## 4. 물리적 설치 및 배치 3대 수칙 (Installation Guidelines)
1. **[수칙 1] 상방 시야 확보**: 가림막 없는 트인 공간 배치
2. **[수칙 2] 수평 평면 유지**: 진동 방지 및 수평 판 부착
3. **[수칙 3] 전자파 간섭 분리**: 고주파 안테나/모터와 일정 거리 유지

---

## 5. ROS 2 드라이버 및 토픽 연동 (ROS 2 Integration)

### 🚀 패키지 실행 명령어
```bash
ros2 run <package_name> <node_name> --ros-args -p device:="/dev/ttyACM0"
```

### 📡 주요 발행 토픽 (Published Topics)
* **`/topic_name`** (`sensor_msgs/msg/NavSatFix`): 실시간 데이터 설명

---

## 6. ❓ 자주 묻는 질문 및 실전 기술 Q&A (Technical Q&A)

### Q1. [사용자 실전 질문 내용]?
* **결론**: 핵심 결론 요약
* **상세 기술 이유**:
  * 원인 분석 및 수치 비교
  * 물리적/소프트웨어적 해결 방안

---

## 7. 펌웨어 및 변경 이력 (Revision & Firmware History)
* **현재 적용 펌웨어**: `v1.x.x`
* **변경 및 트래킹 이력**:
  * `YYYY-MM-DD`: 펌웨어 업그레이드 및 통신 에러 해결 완료 (`knu laptop` / AI: Antigravity)
