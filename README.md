# ROS2 기술 레퍼런스

ROS2 및 센서 융합 시스템 관련 기술을 체계적으로 정리하는 통합 지식 베이스 레포지토리.

---

## 📢 최근 핵심 업데이트 내역 (Latest Updates)

### 📌 2026-09-29: 로봇 카메라 실시간 영상 스트리밍 지연 진단 및 WebRTC 기본 프로토콜 채택
- **작업 수행 개발 장비**: `knu laptop` (KNU 노트북 PC / AI: Claude Code)
- **핵심 수행 작업**:
  1. **RTSP/HLS/WebRTC 구간별 지연 실측**: 카메라 캡처(~26ms), 네트워크 RTT(~10ms), RTSP 단발 지연(82ms), HLS(3.35초, 배제), WebRTC(최저)로 병목이 코덱/네트워크가 아니라 전송 프로토콜·클라이언트 버퍼링임을 규명.
  2. **중계서버 MediaMTX v1.11.3 → v1.21.1 업그레이드**: 1년 7개월 미갱신 상태에서 발생하던 WebRTC 코덱 payload type 충돌 버그(`bluenviron/mediamtx#4394`) 해결.
  3. **낮은 fps(10fps)가 재생 클라이언트 버퍼링을 시간 단위로 증폭시키는 현상 확인**: 30fps 전환으로 동일 측정 기준 지연 ~220ms → ~83ms 개선.
  4. **관제(언리얼) 영상 수신 기본 프로토콜을 WebRTC로 확정**, RTSP는 백업/범용 테스트용으로 유지.
- **관련 문서**:
  * [`software/protocol/robot-camera-webrtc-streaming.md`](software/protocol/robot-camera-webrtc-streaming.md) — 프로토콜 비교, 트러블슈팅 Q&A
  * [`synology-server-roadmap/video_streaming_latency_investigation.md`](https://github.com/Gorani-ros2/synology-server-roadmap/blob/main/video_streaming_latency_investigation.md) — 전체 실측 진단 스토리라인 (별도 레포)

### 📌 2026-09-29: 원격 텔레오퍼레이션 영상·제어 실시간성 레퍼런스 추가
- **작업 수행 개발 장비**: `knu desktop` (AI: Claude Code)
- 카메라→인코딩→네트워크→서버→관제 파이프라인의 glass-to-glass 지연 예산 분해, RTSP/HLS
  vs WebRTC 버퍼링 구조 차이와 "RTSP 2초 지연"의 흔한 원인(클라이언트 기본 버퍼값) 정리.
- MQTT가 실시간성을 사양으로 보장하지 않는 구조적 이유(head-of-line blocking, QoS 왕복,
  꼬리 지연)와, 로봇 제어 채널에서 이를 흡수하는 설계 패턴(연속/단발 명령 분리, 워치독,
  시퀀스 번호, twist_mux/Nav2 액션 브리지) 정리.
- 무선 WAN(LTE 등)에서 CGNAT를 통과하는 프로토콜별 방식 비교(MQTT/WebRTC/ROS2 DDS/Zenoh),
  VPN(WireGuard/OpenVPN) 도입이 영상 실시간성에 미치는 영향과 실패 조건(터널 처리량 부족,
  TCP-over-TCP, MTU 조각화) 정리.
- 원격 건설기계 실증 연표·제어 방식 3분류, ETH Zurich HEAP 논문의 "100ms 영상 지연" 재현성
  검토(논문만으로는 재현 불가, XIMEA 공개 파이프라인으로 보강) 포함.
- **관련 문서**:
  * [`software/protocol/teleoperation-video-control-latency.md`](software/protocol/teleoperation-video-control-latency.md) — 원격 영상·제어 실시간성 종합 레퍼런스
  * [`hardware/support_sensors/router/teltonika-rut241.md`](hardware/support_sensors/router/teltonika-rut241.md) — VPN 오버헤드·원격 관제 구성 절 갱신

### 📌 2026-08-24: 산업용 PoE/RTSP 카메라 폼팩터 비교 및 IP67~68급 자작 하우징 설계 가이드 추가
- **작업 수행 개발 장비**: `knu desktop` (AI: Claude Code)
- 완제품형(Bullet/Dome/Block)·분리형(Remote Head)·보드/박스카메라형 세 폼팩터의 대표 제품
  스펙(RTSP/ONVIF·전력·크기·작동온도·방수등급) 대조표 정리.
- 보드/박스카메라 채택 시 필요한 3D프린트 IP67~IP68급 자작 하우징 설계 체크리스트(소재·O링
  실링·광학창·방수 RJ45·압력균등 벤트·컨포멀코팅) 정리.
- **관련 문서**: [`hardware/vision_sensors/camera/streaming_camera/industrial-poe-rtsp-camera-form-factors.md`](hardware/vision_sensors/camera/streaming_camera/industrial-poe-rtsp-camera-form-factors.md)

### 📌 2026-08-21: Insta360 대용량 추출 멈춤(Freeze) 및 Ctrl+C 데드락 원인 규명, CLI 스크립트(`sync_record.py`) 예외 처리 및 문서화
- **작업 수행 개발 장비**: `knu laptop` (KNU 노트북 PC / AI: Antigravity)
- **핵심 수행 작업**:
  1. **Insta360 SDK 대용량 다운로드 멈춤 및 SIGINT 데드락 원인 분석**:
     - 8K/5.7K 1GB 이상 비디오 파일 USB HTTP 터널 다운로드 중 소켓 쓰기 버퍼 오버플로우(`http_tunnel_client.cpp:0086 write to socket: ...`) 블로킹 현상 원인 규명.
     - 파이썬 스크립트 `finally` 블록의 `SIGINT` = `SIG_IGN` 설정으로 인해 하위 바이너리가 `Ctrl+C` 무시 상태를 상속받아 멈추는 데드락 원인 파악.
  2. **`sync_record.py` 스크립트 개선 및 `--no-download` 옵션 추가**:
     - 다운로드 시 `signal.signal(signal.SIGINT, signal.SIG_DFL)` 복구 및 Ctrl+C 중단 예외 처리 추가.
     - 대용량 비디오 자동 다운로드를 스킵할 수 있는 `--no-download` 옵션 신설.
  3. **트러블슈팅 및 긴급 복구 Q&A 문서화**:
     - `killall -9 insta360_control python3` 강제 종료 명령어 및 SD 카드 직결 전송 가이드 수록.
  4. **카메라 녹화 중작 실시간 진단 기능 문서화**:
     - `./run.sh --status` CLI 명령어로 녹화 튕김/과열 셧다운 여부 실시간 조회 수칙 수록.
- **관련 문서**:
  * [`software/sensorfusion/lidar-insta360-sync-record.md`](software/sensorfusion/lidar-insta360-sync-record.md) — 동시 제어 스크립트 트러블슈팅 Q&A
  * [`hardware/vision_sensors/camera/insta360-camera-sdk.md`](hardware/vision_sensors/camera/insta360-camera-sdk.md) — Insta360 SDK 소켓 버퍼 락 Q&A
  * [`tracking/2026-08-21-environment-audit.md`](tracking/2026-08-21-environment-audit.md) — 2026-08-21 개발 환경 및 Audit 이력 리포트

### 📌 2026-08-18: RTK+라우터 NGII 보정, MQTT-DB 서버 연동, 라이다-RTK PPS 동기화 및 ROS2 Bag 유지 검증 (디지털 트윈)
- **작업 수행 개발 장비**: `knu laptop` (KNU 노트북 PC / AI: Antigravity)
- **핵심 수행 작업 4종**:
  1. **RTK+RUT241 라라우터 국토지리정보원(NGII) NTRIP 연동**: `rts1.ngii.go.kr:2101` (`VRS-RTCM34`, 계정 `<NGII_ID>`) 보정 데이터 수신 및 `sdio, USB1, auto, RTCMv3` 시리얼 주입을 통한 `status.status: 2` (RTK Fixed, 1cm 정밀도) 실시간 융합 승격 실증 및 통합 노드([`septentrio_ngii_ntrip_bridge.py`](software/ros2_basics/septentrio_ngii_ntrip_bridge.py)) 구동 검증.
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


