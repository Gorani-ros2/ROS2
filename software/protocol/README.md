# protocol

## 개요

로봇 원격 영상·제어에 쓰이는 통신 프로토콜(RTSP/WebRTC/HLS, MQTT, DDS, VPN) 자체의
특성(지연·신뢰성·NAT 통과)을 다루는 카테고리. 새 세부 문서를 추가할 때는
`templates/software-doc-template.md`를 복사해서 `주제-kebab-case.md`로 이 폴더에
추가한다.

## 문서 목록

- [`rtk-mqtt-db-bridge.md`](rtk-mqtt-db-bridge.md) — RTK 텔레메트리를 MQTT로 서버 DB에
  적재하는 파이프라인.
- [`teleoperation-video-control-latency.md`](teleoperation-video-control-latency.md) —
  원격 영상(RTSP/HLS/WebRTC)·제어(MQTT/ROS2 DDS) 실시간성. 지연 예산 분해, MQTT의 구조적
  비실시간성과 보완 설계 패턴, 무선 WAN에서의 NAT 통과·VPN 영향, 원격 건설기계·ETH HEAP
  논문 벤치마크.

## 관련 하드웨어

- [`hardware/support_sensors/router/teltonika-rut241.md`](../../hardware/support_sensors/router/teltonika-rut241.md)
  — 4G LTE 라우터, VPN(WireGuard/OpenVPN) 종단 구성.

## 아키텍처 / 데이터 흐름

## 설정 방법

## 사용 예시 / 명령어
