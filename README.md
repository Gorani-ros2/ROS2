# ROS2 기술 레퍼런스

ROS2 및 센서 융합 시스템 관련 기술을 체계적으로 정리하는 통합 지식 베이스 레포지토리.

---

## 📢 최근 핵심 업데이트 내역 (Latest Updates)

### 📌 2026-08-24: 산업용 PoE/RTSP 카메라 폼팩터 비교 및 IP67~68급 자작 하우징 설계 가이드 추가
- **작업 수행 개발 장비**: `knu desktop` (AI: Claude Code)
- 완제품형(Bullet/Dome/Block)·분리형(Remote Head)·보드/박스카메라형 세 폼팩터의 대표 제품
  스펙(RTSP/ONVIF·전력·크기·작동온도·방수등급) 대조표 정리.
- 보드/박스카메라 채택 시 필요한 3D프린트 IP67~IP68급 자작 하우징 설계 체크리스트(소재·O링
  실링·광학창·방수 RJ45·압력균등 벤트·컨포멀코팅) 정리.
- **관련 문서**: [`hardware/vision_sensors/camera/streaming_camera/industrial-poe-rtsp-camera-form-factors.md`](hardware/vision_sensors/camera/streaming_camera/industrial-poe-rtsp-camera-form-factors.md)

### 📌 2026-08-18: RTK+라우터 NGII 보정, MQTT-DB 서버 연동, 라이다-RTK PPS 동기화 및 ROS2 Bag 유지 검증 (디지털 트윈)
- **작업 수행 개발 장비**: `knu laptop` (KNU 노트북 PC / AI: Antigravity)
- **핵심 수행 작업 4종**:
  1. **RTK+RUT241 라라우터 국토지리정보원(NGII) NTRIP 연동**: `rts1.ngii.go.kr:2101` (`VRS-RTCM34`, 계정 `<redacted>`) 보정 데이터 수신 및 `sdio, USB1, auto, RTCMv3` 시리얼 주입을 통한 `status.status: 2` (RTK Fixed, 1cm 정밀도) 실시간 융합 승격 실증 및 통합 노드([`septentrio_ngii_ntrip_bridge.py`](software/ros2_basics/septentrio_ngii_ntrip_bridge.py)) 구동 검증.
  2. **RTK 텔레메트리 MQTT 방식 서버 DB 적재**: ROS 2 `/navsat/fix` 데이터를 JSON 페이로드 규격으로 MQTT 브로커(QoS 1) 발행 및 PostgreSQL / TimescaleDB 공간 테이블 스키마 자동 적재 파이프라인 정립.
  3. **라이다(Ouster OS0-128) & RTK(Septentrio) PPS 하드웨어 동기화**: Septentrio `PPS Out` <-> Ouster `SYNC_PULSE_IN` 물리 결선 및 `timestamp_mode: "TIME_FROM_SYNC_PULSE_IN"` 세팅.
  4. **ROS 2 Bag 녹화 및 PPS 동기화 유지 검증**: rosbag 저장 load 환경에서도 라이다-RTK 타임스탬프 드리프트 방지 및 검증 스크립트 작성 (디지털 트윈 3D 라이다+360 RGB 매핑 핵심 기술).
- **관련 문서**:
  * [`software/ros2_basics/septentrio_ngii_ntrip_bridge.md`](software/ros2_basics/septentrio_ngii_ntrip_bridge.md) — Septentrio NGII NTRIP RTK 통합 드라이버 파이프라인
  * [`software/protocol/rtk-mqtt-db-bridge.md`](software/protocol/rtk-mqtt-db-bridge.md) — RTK Telemetry MQTT 서버 DB 연동 파이프라인
  * [`software/sensorfusion/lidar-rtk-pps-sync-bag.md`](software/sensorfusion/lidar-rtk-pps-sync-bag.md) — Ouster 라이다 & RTK PPS 동기화 및 Bag 검증
  * [`tracking/2026-08-18-environment-audit.md`](tracking/2026-08-18-environment-audit.md) — 2026-08-18 개발 환경 및 Audit 이력 리포트

### 📌 2026-08-14: Teltonika RUT241 LTE 라우터 유심 셀프개통(OMD 등록/IMEI) 및 무선 데이터 테스트 가이드 추가
- **작업 수행 개발 장비**: `knu laptop` (KNU 노트북 PC / AI: Antigravity)
- **자급제 LTE 라우터 유심 등록 이슈 해결**:
  - 스마트폰 셀프개통 서식의 모델명/7자리 일련번호 미존재 이슈 원인 분석 및 해결 방안(통신사 114 OMD 라우터 IMEI 등록, 유심기변, OMD 공통 코드 `OMD 기타 LTE 라우터`/`PTA-TYPE5` 기재) 정리.
- **RUT241 네트워크 무선 데이터 전송 동작 검증 4단계 수칙 수록**:
  - LED 상태등(Power/4G/Signal), PC 접속 및 [fast.com](https://fast.com) 속도 측정, WebUI(`192.168.1.1`) RSRP/SINR 수신 신호 품질 진단, Ping 연속 패킷 테스트 및 APN 수동 설정 가이드 문서화.
- **관련 문서**: [`hardware/support_sensors/router/teltonika-rut241.md`](hardware/support_sensors/router/teltonika-rut241.md)

### 📌 2026-08-11: Septentrio RTK GNSS & 안테나 통합 완료 및 펌웨어 v1.1.0 업그레이드
- **작업 수행 개발 장비**: `knu laptop` (KNU 노트북 PC / AI: Antigravity)
- **로컬 원본 작업 폴더**: `/home/knu/workspaces/sensors/sub_sensors/` (PDF 및 펌웨어 zip 판독/추출)
- **Septentrio mosaic-go G5 P3H 펌웨어 업그레이드**:
  - `sub_sensors` 제공 `mosaic-G5 P3H-1.1.0.suf` 바이너리 수신기 플래시 메모리 라이팅 완료.
  - 구 펌웨어(v1.0.0)의 `[WARN] firmware version 1.0.0` 경고 및 SBF 명령어 구문 에러 100% 해결.
- **ROS 2 Humble 실전 수신 및 파싱 구동**:
  - Septentrio C++ 공식 드라이버(`septentrio_gnss_driver`) 수신 100% 검증 (`/navsat/fix` 4개 위성군 15-service 및 오차 분산 행렬 출력).
  - 수동 파싱 전용 파이썬 노드 제작 완료: [`software/ros2_basics/septentrio_nmea_fix_node.py`](software/ros2_basics/septentrio_nmea_fix_node.py)
- **센서 Q&A 13종 정리 완료**:
  - [`hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md`](hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md): 수신기 포트/전력/JST핀맵/기울기무관성/라이다 PPS 배선/NavSatFix 수치 해석/configure_rx/tf/tf_static/Covariance 변동/Standalone vs RTK/국토지리정보원(NGII) NTRIP 연동가이드/펌웨어 v1.1.0 업그레이드 보고서.
  - [`hardware/support_sensors/gps_rtk/tallysman-tw7972-antenna.md`](hardware/support_sensors/gps_rtk/tallysman-tw7972-antenna.md): `MAIN` 포트 위치, Ground Plane 100mm, 배/등 각도 및 3대 설치 수칙.

### 📌 2026-08-11: Insta360 360도 카메라 & Ouster OS0-128 라이다 센서 융합 동기화
- **Insta360 Camera SDK 통합**: [`hardware/vision_sensors/camera/insta360-camera-sdk.md`](hardware/vision_sensors/camera/insta360-camera-sdk.md)
- **Ouster OS0-128 라이다 제어 & 텔레메트리**: [`hardware/vision_sensors/lidar/ouster-os0-128.md`](hardware/vision_sensors/lidar/ouster-os0-128.md)
- **동시 녹화 & 발열 방지 건축**: [`software/sensorfusion/lidar-insta360-sync-record.md`](software/sensorfusion/lidar-insta360-sync-record.md)

---

## 📁 디렉토리 구조

- [`hardware/`](hardware/README.md) — 물리 장비(라이다, 카메라, GPS/RTK 수신기, 안테나, LTE 라우터)
- [`software/`](software/README.md) — 소프트웨어 계층(센서 융합 동기화, ROS 2 기초 파서 노드)
- [`tracking/`](tracking/README.md) — 이 지식을 이용한 실제 기술 검증·테스트 진행상황
- [`templates/`](templates/) — 새 하드웨어/소프트웨어 문서 작성 템플릿

---

## 📝 문서 작성 및 기여 방법

- 새 장비 모델 문서화: `templates/hardware-doc-template.md` ➔ `hardware/카테고리/제조사-모델명-kebab-case.md`
- 새 소프트웨어 주제 문서화: `templates/software-doc-template.md` ➔ `software/카테고리/주제-kebab-case.md`

---

## 🤖 AI 어시스턴트 필수 협업 수칙 (AI Collaboration Protocol)

다중 PC(`knu laptop`, `knu desktop`) 및 다중 AI 환경에서 작업 연속성을 보장하기 위해 다음 수칙을 **모든 AI가 의무 적용**합니다 ([`AGENTS.md`](AGENTS.md) 참조):

1. **상세 기술 문답 100% 저장**: 사용자의 질문과 해결 답안은 함축 없이 디테일하게 작성.
2. **다중 카테고리 중복 수록 허용**: 내용이 해당되면 `hardware/`와 `software/` 양쪽에 빠짐없이 중복 기재.
3. **루트 README.md 최신화**: 작업 후 `📢 최근 핵심 업데이트 내역` 섹션에 개발 PC, 작업 내역, 링크 필수 업데이트.
4. **환경 Audit 이력 기록**: `tracking/YYYY-MM-DD-environment-audit.md`에 호스트명(`knu laptop`), OS, AI 모델명, 손댄 로컬 폴더 기록.
5. **작업 인수인계 보장**: 다음 AI가 `git pull` 후 즉시 다음 단계(예: RUT241 LTE NTRIP B모드, 라이다 PPS 동기화 등)를 이어받을 수 있게 작업 상태 명시.


