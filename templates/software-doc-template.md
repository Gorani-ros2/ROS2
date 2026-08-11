# 💻 [소프트웨어/모듈명] [주제 및 기능 정의]

## 1. 개요 및 파이프라인 (Overview & Pipeline)
* **목적**: 시스템 연동, 동기화, 센서 파싱 노드 기능 정의
* **시스템 아키텍처 흐름도**:
```mermaid
flowchart LR
    A[하드웨어 센서] -->|시리얼/NMEA| B[ROS 2 파서 노드]
    B -->|sensor_msgs/NavSatFix| C[ROS 2 토픽 /fix]
```

---

## 2. 🔗 관련 하드웨어 장비 문서 십자 링크 (Cross-Links)
* **연동 GNSS 수신기**: `[Septentrio mosaic-go G5 P3H](../../hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md)`
* **연동 안테나**: `[Tallysman TW7972 안테나](../../hardware/support_sensors/gps_rtk/tallysman-tw7972-antenna.md)`
* **연동 3D 라이다**: `[Ouster OS0-128 라이다](../../hardware/vision_sensors/lidar/ouster-os0-128.md)`

---

## 3. 필수 환경 및 패키지 의존성 (Prerequisites & Dependencies)
* **ROS 2 버전**: ROS 2 Humble Hawksbill (Ubuntu 22.04 LTS)
* **필수 라이브러리 및 APT 패키지**:
  * `python3-serial` / `pyserial`
  * `ros-humble-nmea-msgs`

---

## 4. 소스코드 및 구동 가이드 (Source Code & Execution)

### 🚀 1줄 실행 명령어
```bash
python3 software/ros2_basics/node_name.py
```

### ⚙️ 주요 매개변수 (ROS 2 Parameters)
* `port`: 시리얼 포트 경로 (기본값: `/dev/ttyACM0`)
* `baud`: 통신 보레이트 (기본값: `115200`)

---

## 5. 발행 및 구독 토픽 정의 (ROS 2 Topics)

| 토픽 이름 | 메시지 타입 (Message Type) | 발행 주기 (Hz) | 설명 (Description) |
| :--- | :--- | :--- | :--- |
| `/fix` | `sensor_msgs/msg/NavSatFix` | 1 Hz ~ 10 Hz | WGS84 위도, 경도, 고도 및 3D 오차 분산 행렬 |
| `/fix/velocity` | `geometry_msgs/msg/TwistStamped` | 1 Hz ~ 10 Hz | 3D 지상 이동 속도 |

---

## 6. ❓ 개발/테스트 Q&A 및 트러블슈팅 (Q&A & Troubleshooting)

### Q1. [개발 및 구동 중 발생한 이슈/질문]?
* **증상**: 에러 메시지 및 수신 불량 현상
* **원인**: 기술적 근본 원인 분석
* **해결책**: 적용된 코드 수정 및 설정 조치 내용

---

## 7. 발열 및 안전 관리 수칙 (Safety & Thermal Management)
* **동시 구동 시 전력/발열 관리**: CPU 핫스팟 모니터링 및 쿨링 대책
