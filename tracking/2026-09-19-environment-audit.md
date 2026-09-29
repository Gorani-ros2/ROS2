# 📋 Environment Audit Log — 2026-09-19

- **Date**: 2026-09-19
- **Host Machine**: `knu laptop` (Linux Ubuntu 22.04 LTS / ROS 2 Humble)
- **AI Assistant**: Antigravity (Google DeepMind Team)
- **Target Workspace**: `/home/knu/workspaces/insta360` (`Gorani-ros2/ROS2`)
- **Robot Workspace**: `/home/knu/workspaces/duco_ros2_control_ws`
- **Vision Workspace**: `/home/knu/workspaces/screw_vision`

---

## 🔍 System Environment State & Audit

### 1. Active Hardware & Ports
- **Duco-910 (GCR5-910 / GCR7-910) 6축 협동로봇**: 컨트롤 캐비닛 전면 LAN1 기가비트 이더넷 직결 (`192.168.1.10:7003`)
- **Intel RealSense D405 초근접 RGB-D 카메라**: USB 3.0 포트 직결 (측정 범위 7cm ~ 50cm, 서브밀리미터 정밀도)
- **유선 랜카드 (`eno1`)**: NetworkManager 통합 프로파일 `robot_dev` 활성화
- **무선 랜카드 (`wlp3s0`)**: 인터넷 전용 접속 유지 (`172.30.1.41/24`, Gateway: `172.30.1.254`)

---

## 🛠️ Summary of Diagnosed & Resolved Issues

### 1. 네트워크 IP 충돌 방지 및 `robot_dev` 단일 프로파일 통합
- **문제**: 라우터, 라이다, 로봇암 등 다수의 하드웨어를 연동하면서 각 서브넷이 뒤섞이고 인터넷 경로와 충돌하는 현상 발생.
- **해결**:
  - `eno1`의 기존 하드웨어 전용 프로파일인 **`robot_dev`**에 듀코 로봇 서브넷(`192.168.1.100/24`)을 추가.
  - `robot_dev` 하나로 3대 디바이스 서브넷(`192.168.3.100/24`, `169.254.129.100/16`, `192.168.1.100/24`)을 완전 공존.
  - 인터넷(Wi-Fi) 기본 게이트웨이 무결성 100% 보존.
- **검증 실측치**:
  - Ping RTT: **`0.260 ms`** (패킷 손실 0%)
  - RPC 7003 포트: **`Connection succeeded`**

### 2. ROS 2 빌드 경로 심볼릭 링크 복구 및 드라이버 재빌드
- **문제**: 이전 빌드 경로(`/home/knu/ros2_control_ws`)의 CMake 캐시로 인해 현재 경로(`/home/knu/workspaces/duco_ros2_control_ws`)에서 빌드 및 소싱 에러 발생.
- **해결**:
  - 하위 호환 심볼릭 링크 생성: `ln -s /home/knu/workspaces/duco_ros2_control_ws /home/knu/ros2_control_ws`
  - `duco_msg`, `duco_ros_driver`, `robot_control` 클린 재빌드 완료.
- **실기 전환 검증**:
  - `DucoRobotStatus` 노드 구동 시: `Switches to ros-controller successfully` 확인.

### 3. 티칭 인터페이스 조그 회전 중 정지 원인 분석 및 가이드
- **현상**: 티칭 펜던트로 모터를 하나씩 돌려보는데 자꾸 경보음과 함께 멈춤.
- **원인 및 조치**:
  1. **직교(Base/XYZ) 모드 특이점**: 관절 모드(`Joint / J1~J6`)로 변경하여 개별 모터 독립 회전 유도.
  2. **스텝(Step) 인칭 모드**: 이동 방식을 `Continuous(연속)`로 변경.
  3. **충돌 감지 민감도**: 가감속 관성 토크로 인한 오작동 방지를 위해 충돌 감지 민감도를 `1단계(최저)`로 낮춤.
  4. **관절별 가동 범위**: J1~J6 소프트웨어 안전 리미트 $\pm 175^\circ$ 및 J2-J3 자체 간섭 영역 확인.

### 4. M3 / M4 나사 3D 인식 파이프라인 구축 (D405 + 검은색 나사 모드)
- Intel RealSense D405 서브밀리미터 전용 검출기(`screw_detector_d405.py`) 개발.
- 흑색 산화피막 나사의 빛 흡수 특성을 고려하여 **반전 이진화(`THRESH_BINARY_INV`) 기반 검은 나사 모드** 및 실시간 핫키(`[B]`, `[T]`, `[G]`) 탑재.
- YOLO11 고속 학습 및 ROS 2 피킹 포즈 발행 노드 완비.

---

## 📌 Current Milestone & Next Action
- **로봇 하드웨어 및 ROS 2 통신 링크 검증 완료**: 로봇 가동 일시 일시정지(Hold).
- **다음 포커스**: Intel RealSense D405 카메라를 이용한 책상 위 M3/M4 검은 나사 3D 정밀 계측 및 비전 인식 검증으로 전환.
