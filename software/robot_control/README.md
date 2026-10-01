# robot_control

## 개요

로봇팔(6축 협동로봇 Duco GCR5-910)을 비전으로 유도해 제어하는 코드와 문서. 카메라 쪽 인식(나사 검출)은
[`../sensorfusion/screw_vision/`](../sensorfusion/screw_vision/README.md)에 있고, 이 폴더는 로봇팔 구동과
그 둘을 잇는 파이프라인을 다룬다.

## 파일

| 파일 | 내용 |
|---|---|
| [`duco_vision_servoing_pipeline.md`](duco_vision_servoing_pipeline.md) | 비전 서보잉 파이프라인 전체 설명·이슈 분석·트레이드오프 |
| `duco_controller.py` | Duco C++ API(libDucoCobotAPI)를 파이썬 ctypes로 감싼 제어 브리지 |
| `duco_bridge.cpp` | 위 브리지의 C++ 측 |
| `duco_pipeline.py` | 비전 유도 제어 파이프라인 (영점화, 순회, 접근·후퇴) |
| `duco_named_poses.json` | 이름 붙인 로봇팔 자세 목록 |
| `d405_10mm_clearance_verification.png` | D405 10mm 이격 검증 사진 |

## 관련 하드웨어

- [`hardware/robotarm/6axis/duco-gcr-910.md`](../../hardware/robotarm/6axis/duco-gcr-910.md)
