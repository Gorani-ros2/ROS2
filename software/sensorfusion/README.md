# sensorfusion

## 개요

3D 라이다, 파노라마 카메라, IMU, GPS 등 이종 센서 간의 시스템 타임스탬프 기반 시간 동기화(`TIME_FROM_ROS_TIME`), 센서 데이터 동시 수집 파이프라인, 공간 캘리브레이션 및 점군-이미지 퓨전 기술을 다룹니다.

## 문서 목록

- [`insta360_sync/`](insta360_sync/) — 위 문서의 실행 스크립트(`sync_record.py`, `run.sh`)와 라이다 드라이버 설정(`my_ouster_params.yaml`)
- [`screw_vision/`](screw_vision/README.md) — D405 기반 나사 검출(제로샷 튜닝 기록 `d405_zero_shot_tuning_history.md` 포함)
- [라이다 & Insta360 동시 제어 및 시간 동기화](lidar-insta360-sync-record.md) — Ouster OS0-128과 Insta360 360도 카메라의 통합 시분할/연속 녹화, ROS 2 시간 동기화 오프셋 산출, PCAP 수집 및 과열 보호 통합 관리 기술

## 관련 하드웨어

- [`hardware/vision_sensors/lidar/`](../../hardware/vision_sensors/lidar/README.md)
- [`hardware/vision_sensors/camera/`](../../hardware/vision_sensors/camera/README.md)

## 이 폴더의 문서

이 카테고리의 개별 소프트웨어 주제 문서는 `templates/software-doc-template.md`를 복사해서
`주제-kebab-case.md` 형식으로 이 폴더에 추가한다.

