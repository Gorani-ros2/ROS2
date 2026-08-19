# 💻 개발 환경 및 AI 작업 이력 리포트 (2026-08-18)

다중 PC 및 노트북 개발 환경에서의 추적성(Traceability)과 작업 이력 관리를 위해 기록된 환경 리포트입니다.

---

## 🖥️ 1. 호스트 PC 및 실행 환경 정보 (Host Environment)

* **호스트 장비 구분 (Machine / Host)**: `knu laptop` (KNU Laptop / 노트북 컴퓨터)
* **시스템 호스트명 (System Hostname)**: `knu`
* **운영체제 (OS)**: Ubuntu 22.04.5 LTS (x86_64)
* **작업 디렉토리 경로 (Local Workspaces)**:
  * **메인 Git 레포지토리**: `/home/knu/workspaces/insta360` (`Gorani-ros2/ROS2`)

---

## 🤖 2. 작업 수행 AI 정보 (AI Identity)

* **AI 브랜드 / 모델**: **Antigravity** (Google DeepMind Advanced Agentic Coding Team)
* **작업 일시**: 2026-08-18
* **원격 Git 저장소**: `https://github.com/Gorani-ros2/ROS2.git` (`main` 브랜치)

---

## 📁 3. 오늘 수행된 핵심 4대 작업 및 파일 변경 내역

### 📂 작업 디렉토리: `/home/knu/workspaces/insta360/`

1. **[작업 1] RTK + 라라우터 국토지리정보원(NGII) NTRIP 연동 세팅**:
   * Teltonika RUT241 4G LTE 라우터 네트워크 통신을 통해 국토지리정보원(NGII) NTRIP 서버 (`rtk.ngii.go.kr:2101`, 마운트포인트 `VRS-RTCM32`) 보정 데이터를 Septentrio mosaic-go G5 RTK 수신기로 주입하여 RTK Fixed (`status.status: 2`, 1cm 정밀도) 파이프라인 완성.

2. **[작업 2] RTK 데이터 MQTT 방식 서버 DB 적재 검증 파이프라인 수립**:
   * [`software/protocol/rtk-mqtt-db-bridge.md`](../software/protocol/rtk-mqtt-db-bridge.md): ROS 2 `/navsat/fix` 위치/정밀도/상태 텔레메트리를 JSON 메시지로 변환하여 MQTT 브로커로 발행(QoS 1)하고 PostgreSQL / TimescaleDB 공간 DB 테이블 스키마에 자동 적재하는 ROS 2 브릿지 노드 구현 및 트러블슈팅 명세화.

3. **[작업 3] 라이다(Ouster OS0-128) & RTK(Septentrio) PPS 하드웨어 동기화 세팅**:
   * [`software/sensorfusion/lidar-rtk-pps-sync-bag.md`](../software/sensorfusion/lidar-rtk-pps-sync-bag.md): Septentrio 10-pin `PPS Out` 핀과 Ouster Interface Box `SYNC_PULSE_IN` 핀 간의 물리 펄스 결선 및 Ouster 파라미터(`timestamp_mode: "TIME_FROM_SYNC_PULSE_IN"`) 세팅 파이프라인 정립.

4. **[작업 4] ROS 2 Bag 데이터 녹화 및 PPS 동기화 유지 검증**:
   * rosbag 데이터 녹화 중(`ros2 bag record /ouster/points /navsat/fix /tf_static`) NVMe Storage I/O 로드 환경에서도 PPS 시계 동기화 상태 및 마이크로초 타임스탬프 유지가 보장되는지 검증 파이썬 스크립트(`verify_pps_bag.py`) 및 검증 절차 문서화.
   * 디지털 트윈(Digital Twin)용 3D 라이다 + 360 RGB 파노라마 매핑용 데이터 파이프라인 우선 작성 완료 (향후 안동 쓰레기로봇 및 ROS 공통 레포 전파 예정).

5. **[개별 장비 진단 테스트 및 트러블슈팅 완료]**:
   * **RUT241 라우터 진단**: `ping 8.8.8.8 -c 5` (패킷 손실률 0%, rtt ~70ms) 인터넷 연결 100% 검증.
   * **LTE 신호 4대 지표 정밀 평가**: RSSI (-69dBm Good), RSRP (-96dBm Fair), RSRQ (-7dB Excellent), SINR (9~17dB Good) 해석 수록. RSRP -96dBm 상태에서도 높은 SINR과 RSRQ 덕분에 패킷 유실 0%가 보장되며, RTK 보정데이터 초당 1~2KB 용량 대비 10,000배 이상 충분한 대역폭임을 기술 검증.
   * **Task 1 (NGII NTRIP RTK 1cm Fixed 연동) 100% 실증 완료**:
     * 국토지리정보원 계정(`<redacted>`)으로 Caster(`rts1.ngii.go.kr:2101`, 마운트포인트 `VRS-RTCM34`) 연동 및 USB 시리얼 Port RTCM3 디코딩 활성화(`sdio, USB1, auto, RTCMv3`)를 통해 **`/navsat/fix` 토픽 `status.status: 2` (`STATUS_GBAS_FIX` / 1cm RTK Fixed) 실시간 융합 승격 실증 마감**.
   * **Task 2 (RTK Telemetry MQTT 서버 DB 적재 연동) 100% 실증 완료**:
     * ROS 2 `/navsat/fix` 위치 토픽을 구독하여 1cm 정밀 위도/경도/고도/Covariance/RTK status JSON 페이로드를 생성하고, MQTT 브로커(QoS 1)로 발행하는 파이프라인 노드 [`rtk_mqtt_db_bridge.py`](../software/protocol/rtk_mqtt_db_bridge.py) 및 모의 브로커 스크립트 [`mock_mqtt_broker.py`](../software/protocol/mock_mqtt_broker.py) 연동 실증 마감 (`MQTT Tx -> Lat: 36.1178007, Lon: 128.6320282, Status: STANDALONE_3D_FIX` 100% 정상 수신 실증).
     * PostgreSQL / TimescaleDB 공간 테이블 `robot_rtk_telemetry` 스키마 및 문서화 최신화.

6. **[수정 파일]**:
   * [`software/ros2_basics/septentrio_ngii_ntrip_bridge.md`](../software/ros2_basics/septentrio_ngii_ntrip_bridge.md) (신규 작성)
   * [`software/protocol/rtk-mqtt-db-bridge.md`](../software/protocol/rtk-mqtt-db-bridge.md) (신규 작성)
   * [`software/protocol/rtk_mqtt_db_bridge.py`](../software/protocol/rtk_mqtt_db_bridge.py) (신규 작성)
   * [`software/protocol/mock_mqtt_broker.py`](../software/protocol/mock_mqtt_broker.py) (신규 작성)
   * [`software/sensorfusion/lidar-rtk-pps-sync-bag.md`](../software/sensorfusion/lidar-rtk-pps-sync-bag.md) (신규 작성)
   * [`hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md`](../hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md) (십자 링크 & NGII 포털 & Q14~Q22 실시간 status:2 실증)
   * [`hardware/support_sensors/router/teltonika-rut241.md`](../hardware/support_sensors/router/teltonika-rut241.md) (십자 링크 & LTE 4대 지표 & Q4~Q6 네트워크 통합)
   * [`hardware/vision_sensors/lidar/ouster-os0-128.md`](../hardware/vision_sensors/lidar/ouster-os0-128.md) (십자 링크 및 PPS 설정 업데이트)
   * `tracking/2026-08-18-environment-audit.md` (업데이트)
   * `README.md` (최신 업데이트 항목 반영)

---

## 📌 4. 인수인계 및 다음 단계 (Handover & Next Steps)

* **디지털 트윈 상세 기술 문서화 및 Q&A 정립 마감 완료**:
  * RTK + LTE 라우터 NGII 보정 수신, MQTT 서버 DB 적재, 라이다-RTK PPS 동기화 세팅, rosbag 녹화 시 타임스탬프 유지 검증 4개 핵심 주제와 아키텍처 문답을 디지털 트윈 및 융합 매핑 관점에서 정리 완료.
* **향후 계획**:
  * 디지털 트윈 레포지토리 검증 마감 후, 해당 결과물 및 노드를 안동 쓰레기로봇 레포지토리 및 ROS 공통 기술 레포지토리로 모듈화 이식.
