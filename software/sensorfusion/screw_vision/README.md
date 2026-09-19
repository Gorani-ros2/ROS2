# 🔩 Duco-910 M3 / M4 나사 인식 및 3D 피킹 비전 파이프라인

본 워크스페이스는 Duco-910(GCR5/7-910) 협동로봇의 비전 기반 나사 체결/픽앤플레이스 작업을 위해 **M3 및 M4 나사를 실시간으로 정밀 식별하고 3D 피킹 좌표를 생성**하는 2-Track 비전 시스템입니다.

---

## 📌 1. M3 vs M4 나사 물리 규격 및 식별 기준

| 구분 | M3 나사 규격 | M4 나사 규격 | 비고 (식별 기준) |
| :--- | :--- | :--- | :--- |
| **나사산 호칭 직경 (Thread Body)** | **$3.0\text{ mm}$** | **$4.0\text{ mm}$** | 누워있는 나사 측정 기준 ($\Delta = 1.0\text{ mm}$) |
| **렌치볼트 머리 직경 (DIN 912 SHCS)** | **$5.5\text{ mm}$** ($5.32 \sim 5.50$) | **$7.0\text{ mm}$** ($6.78 \sim 7.00$) | 직립 나사 측정 기준 ($\Delta = 1.5\text{ mm}$) |
| **둥근머리 직경 (DIN 7985 Pan)** | **$5.6\text{ mm}$** ($5.30 \sim 5.60$) | **$8.0\text{ mm}$** ($7.64 \sim 8.00$) | 직립 나사 측정 기준 ($\Delta = 2.4\text{ mm}$) |
| **육각머리 대변 거리 (DIN 933 Hex)** | **$5.5\text{ mm}$** | **$7.0\text{ mm}$** | 스패너 체결면 폭 ($\Delta = 1.5\text{ mm}$) |
| **나사 피치 (Pitch)** | $0.5\text{ mm}$ | $0.7\text{ mm}$ | 표준 미터 보통 나사 |

> 💡 **핵심 원리**: 카메라 작업 거리($Z = 150\text{ mm}$)에서 M3 머리($\approx 5.5\text{ mm}$)와 M4 머리($\approx 7.0\text{ mm}$)는 약 $1.5 \sim 2.4\text{ mm}$의 뚜렷한 직경 차이를 보이므로, **카메라 기하학 역변환($D_{\text{mm}} = \frac{D_{\text{px}} \cdot Z}{f_x}$)**을 통해 별도 학습 없이도 100% 구분 가능합니다.

---

## 🛠️ 2. 하드웨어 환경 세팅 수칙 (금속 난반사 방지)

1. **검정 무광 실리콘 패드/트레이 사용**:
   - 금속 나사는 표면 반사율이 높으므로, 흰색 바닥보다 **검정색 무광 제전 패드** 위에 놓았을 때 대비(Contrast)가 극대화됩니다.
2. **확산 조명 (Diffuse Ring Light) 권장**:
   - 직접 점광원 LED를 비추면 나사 머리에 강한 흰색 하이라이트(Glare)가 발생하여 십자/육각 홈이 뭉개집니다. 원형 링 조명이나 반투명 디퓨저 판을 적용해야 합니다.
3. **권장 작업 거리 (Inspection Height)**:
   - Eye-in-Hand 카메라 기준 트레이 상단 **$Z = 100 \sim 150\text{ mm}$** 거리 권장 (해상도당 약 $0.15\text{ mm/pixel}$ 확보).

---

## 🚀 3. 실행 방법 (2-Track 아키텍처)

### Track 1. [학습 불필요] Zero-Shot 기하학 검출기 즉시 실행
별도의 딥러닝 학습 데이터 없이, 지금 당장 연결된 카메라로 M3/M4 나사를 자동 분류하고 치수를 화면에 띄웁니다:

```bash
cd /home/knu/workspaces/screw_vision

# 1-Click 실행 (카메라 0번, 높이 150mm 기준)
python3 screw_geometric_detector.py --camera 0 --distance 150.0

# 핫키 조작:
#   '+' / '-' : 카메라 높이 Z를 5mm 단위로 실시간 미세조정
#   's'       : 현재 감지된 프레임 스크린샷 캡처
#   'q'       : 종료
```

---

### Track 2. [딥러닝 고도화] YOLO11 커스텀 모델 파이프라인

#### Step 1: 자동 라벨링 데이터셋 수집 (5분 컷)
트레이 위에 M3와 M4 나사를 흩뿌려 두고 실행하면, Track 1의 기하 검출기가 자동으로 바운딩 박스를 찾아 YOLO `.txt` 라벨을 생성합니다:

```bash
# 자동 캡처 모드 (나사를 조금씩 섞어가며 50~100장 수집)
python3 auto_dataset_collector.py --camera 0 --distance 150.0 --auto-interval 1.5

# 조작: [SPACE] 수동 1장 캡처, [A] 자동 인터벌 캡처 토글, [Q] 완료
```

#### Step 2: RTX 5070 GPU 초고속 파인튜닝 (약 5분 소요)
수집된 데이터셋으로 사전학습된 `yolo11n.pt`를 파인튜닝합니다:

```bash
python3 train_yolo_screw.py --epochs 50 --batch 16 --imgsz 640 --device 0
```
> 학습 완료 시 `screw_runs/screw_m3_m4/weights/best.pt` 가 생성됩니다.

---

### 4. ROS 2 드라이버 연동 노드 실행 (Duco-910 피킹 연계)

ROS 2 Humble 환경에서 나사 검출 결과를 로봇 피킹 토픽으로 실시간 브로드캐스팅합니다:

```bash
# 터미널 1: 기하학 모드로 ROS 2 노드 기동
cd /home/knu/workspaces/screw_vision
source /opt/ros/humble/setup.bash
python3 screw_detector_ros2_node.py --ros-args -p mode:=geometric -p camera_device:=0 -p distance_mm:=150.0

# 터미널 2: 1-Click 피킹 좌표 수신 확인
source /opt/ros/humble/setup.bash
ros2 topic echo /screw_detection/poses --once
```

발행 토픽:
- `/screw_detection/poses` (`geometry_msgs/msg/PoseArray`): 카메라 기준 각 나사의 3D 위치 $(X, Y, Z)$ 및 회전 쿼터니언 $(q_x, q_y, q_z, q_w)$
- `/screw_detection/debug_image` (`sensor_msgs/msg/Image`): RViz / rqt 실시간 오버레이 화면
