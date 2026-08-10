# lidar

## 개념

Ouster 등 3D/2D 라이다 센서의 회전 스캔 제어, 수평 해상도(Columns) 및 빔 채널 매개변수 설정, Ethernet UDP/TCP 데이터 수신, HTTP Telemetry 센서 상태 쿼리, 과열 보호(Thermal Protection: 1단계 Shot Limiting / 2단계 Thermal Shutdown) 및 ROS 2 Topic/QoS(`Best Effort`) 제어 기술을 다룹니다.

## 문서 목록

- [Ouster OS0-128](ouster-os0-128.md) — 128채널 3D 라이다 스펙, 통신 정의, 써멀 동작 메커니즘 및 호스트 CPU 쓰로틀링 진단법

## 이 폴더의 문서

이 카테고리의 개별 장비 모델 문서는 `templates/hardware-doc-template.md`를 복사해서
`제조사-모델명-kebab-case.md` 형식으로 이 폴더에 추가한다.
