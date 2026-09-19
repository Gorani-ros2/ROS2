# 🔩 Duco-910 M3 / M4 나사 인식 및 3D 피킹 비전 파이프라인

본 워크스페이스는 Duco-910(GCR5/7-910) 협동로봇의 비전 기반 나사 체결/픽앤플레이스 작업을 위해 **M3 및 M4 나사(검은색 산화피막 볼트 및 은색 금속 볼트)를 실시간으로 정밀 식별하고 3D 피킹 좌표를 생성**하는 2-Track 비전 시스템입니다.

---

## 📌 1. M3 vs M4 나사 물리 규격 및 식별 기준

| 구분 | M3 나사 규격 | M4 나사 규격 | 판별 치수 차이 ($\Delta$) | 비고 (식별 기준) |
| :--- | :--- | :--- | :---: | :--- |
| **렌치볼트 머리 직경 (DIN 912 SHCS)** | **$5.5\text{ mm}$** ($5.32 \sim 5.50$) | **$7.0\text{ mm}$** ($6.78 \sim 7.00$) | **$\mathbf{1.5\text{ mm}}$** | 직립 상태 시 머리 외경 측정 |
| **둥근머리 직경 (DIN 7985 Pan)** | **$5.6\text{ mm}$** ($5.30 \sim 5.60$) | **$8.0\text{ mm}$** ($7.64 \sim 8.00$) | **$\mathbf{2.4\text{ mm}}$** | 십자/일자 둥근머리 볼트 |
| **육각머리 대변 거리 (DIN 933 Hex)** | **$5.5\text{ mm}$** | **$7.0\text{ mm}$** | **$\mathbf{1.5\text{ mm}}$** | 스패너 체결면 대변 거리 |
| **나사산 호칭 직경 (Thread Body)** | **$3.0\text{ mm}$** | **$4.0\text{ mm}$** | **$\mathbf{1.0\text{ mm}}$** | 누워있는 나사 바디 두께 측정 |
| **나사 피치 (Pitch)** | $0.5\text{ mm}$ | $0.7\text{ mm}$ | - | 표준 미터 보통 나사 |

> 💡 **핵심 원리**: 카메라 작업 거리($Z = 70 \sim 150\text{ mm}$)에서 M3 머리($\approx 5.5\text{ mm}$)와 M4 머리($\approx 7.0\text{ mm}$)는 약 $1.5 \sim 2.4\text{ mm}$의 뚜렷한 직경 차이를 보이므로, **카메라 기하학 역변환($D_{\text{mm}} = \frac{D_{\text{px}} \cdot Z}{f_x}$)**을 통해 별도 학습 없이도 100% 구분 가능합니다.

---

## 🛠️ 2. 하드웨어 환경 세팅 수칙 (나사 색상별 배경 가이드)

### 2.1 검은색 나사 (Black Oxide / Carbon Steel) — **강력 추천**
* **배경 패드**: **흰색 A4 용지, 밝은 회색 패드, 연녹색 커팅 매트 (⭕)**
* **장점**: 검은색 나사는 빛을 흡수하므로 은색 나사와 같은 표면 난반사(Glare)가 거의 없어 외곽 윤곽선(Contour)이 훨씬 더 깨끗하게 검출됩니다.
* **소프트웨어 모드**: `BLACK SCREW (White/Light BG)` (반전 이진화 `THRESH_BINARY_INV` 자동 적용).

### 2.2 은색 나사 (Stainless Steel / Nickel Plated)
* **배경 패드**: 검정색 무광 제전 패드.
* **조명**: 원형 링 조명 또는 디퓨저를 사용하여 나사 머리 핫스팟 억제.
* **소프트웨어 모드**: `SILVER SCREW (Dark BG)` (`[B]` 키로 전환).

---

## 🚀 3. 실전 실행 방법 (카메라별 가이드)

### Option A. [추천] Intel RealSense D405 전용 초정밀 3D 검출 (로봇 불필요)
D405는 측정 범위 **7cm ~ 50cm** (서브밀리미터 $0.1\text{ mm}$급 정밀도)를 지원하므로, 나사 표면까지의 실제 깊이($Z$)를 센서가 직접 측정합니다.

```bash
# 1. D405 인식 확인 (1줄)
rs-enumerate-devices -s

# 2. 실시간 3D 나사 검출기 + 웹 텔레메트리 허브 실행
cd /home/knu/workspaces/screw_vision
python3 screw_detector_d405.py
```

* **1-Click 자가 검증 수단 (Self-Verification)**:
  - **웹 브라우저 뷰어**: [`http://localhost:5000`](http://localhost:5000) (실시간 RGB-D 스트림, 이진화 마스크, M3/M4 검출 개수, 실시간 3D 좌표 표, 임계값 슬라이더)
  - **데스크톱 GUI 창**: `DISPLAY=:0` 모니터에 OpenCV 윈도우 즉시 표시
* **화면 출력**:
  - M3 나사(초록색), M4 나사(주황색), 측정 생크 직경($d$), 머리 직경($D$), 길이($L$), 회전 각도($^\circ$), 카메라 좌표계 실제 3D 좌표 `3D: [X, Y, Z] mm` 표시
* **단축키 (GUI 및 웹 제어)**:
  - `[B]`: 검은 나사 모드(밝은 배경) $\leftrightarrow$ 은색 나사 모드(어두운 배경) 토글
  - `[T]` / `[G]`: 이진화 임계값(Threshold) $+5$ / $-5$ 미세조정
  - `[S]`: 실시간 스냅샷 및 주석 저장, `[Q]`: 종료

---

### Option B. 일반 USB 웹캠 / V4L2 카메라 기하학 검출기
```bash
cd /home/knu/workspaces/screw_vision
python3 screw_geometric_detector.py --camera 0 --distance 150.0
```

---

### Option C. YOLO11 커스텀 모델 파이프라인 (자동 라벨링 + RTX 5070 GPU 학습)

1. **자동 라벨링 데이터셋 수집 (5분)**:
   ```bash
   python3 auto_dataset_collector.py --camera 0 --distance 150.0 --auto-interval 1.5
   ```
2. **RTX 5070 Laptop GPU 고속 파인튜닝 (5분)**:
   ```bash
   python3 train_yolo_screw.py --epochs 50 --batch 16 --imgsz 640 --device 0
   ```
   > 완료 시 `screw_runs/screw_m3_m4/weights/best.pt` 생성.

---

### Option D. ROS 2 드라이버 연동 노드 실행 (Duco-910 3D 피킹)

```bash
# 터미널 1: ROS 2 노드 실행
source /opt/ros/humble/setup.bash
python3 /home/knu/workspaces/screw_vision/screw_detector_ros2_node.py \
    --ros-args -p mode:=geometric -p camera_device:=0 -p distance_mm:=150.0

# 터미널 2: 1-Click 피킹 좌표 수신 확인 (geometry_msgs/PoseArray)
ros2 topic echo /screw_detection/poses --once
```
