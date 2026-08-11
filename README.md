# ROS2 기술 레퍼런스

ROS2 및 센서 융합 시스템 관련 기술을 체계적으로 정리하는 통합 지식 베이스 레포지토리.

---

## 📢 최근 핵심 업데이트 내역 (Latest Updates)

### 📌 2026-08-11: Septentrio RTK GNSS & 안테나 통합 완료 및 펌웨어 v1.1.0 업그레이드
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

