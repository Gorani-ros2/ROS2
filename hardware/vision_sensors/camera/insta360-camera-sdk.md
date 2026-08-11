# Insta360 파노라마 카메라 (Insta360 Camera SDK)

## 정의

Insta360 카메라(X3, X4 등)는 Dual Fisheye 렌즈 기반의 360도 전방위 파노라마 미디어(사진 및 비디오) 수집 장치입니다. Linux 환경에서 제공되는 **Insta360 Camera SDK** (C++ API / Python Wrapper) 및 제어 스크립트를 통해 카메라 설정 변경, 동시 비디오 녹화/정지, 스틸 샷 캡처 및 미디어 파일 자동 다운로드를 수행합니다.

---

## 데이터시트 및 핵심 스펙

| 항목 | 사양 |
| :--- | :--- |
| **렌즈 및 FOV** | Dual Fisheye Lenses, 360° × 360° Full Panorama |
| **비디오 해상도 & FPS** | 8K @ 30fps, 5.7K @ 60fps/30fps, 4K @ 60fps/30fps |
| **사진 해상도** | 72MP (11968×5984), 18MP (5952×2976) 파노라마 RAW/JPG |
| **인터페이스** | USB 3.0 / USB-C Direct Connection (Linux Host) |
| **SDK 버전** | Linux CameraSDK v2.1.1 / MediaSDK v3.1.1 |
| **작동 온도** | -20°C ~ 40°C |
| **발열 및 과열 특성** | 8K/5.7K 연속 비디오 인코딩 시 내부 DSP 온도가 급상승할 수 있으며, 4K@30fps 설정 시 열 안정성 및 긴 녹화 유지력을 제공함. |

---

## 제어 방법 및 제어 명령어

Insta360 카메라는 C++ Camera SDK 기반의 실행 바이너리 및 CLI 래퍼 스크립트(`./run.sh` 또는 `sync_record.py`)를 통해 통신하고 제어합니다.

### 1. 카메라 해상도 및 프레임레이트 설정
```bash
./run.sh --set-res <RESOLUTION> <FPS>
# 예시: 4K @ 30fps 설정
./run.sh --set-res 4K 30
```

### 2. 비디오 녹화 제어 (Start / Stop)
```bash
# 비디오 녹화 시작 (Start Only)
./run.sh --start-only

# 비디오 녹화 정지 및 생성된 미디어 URL 조회 (Stop)
./run.sh --stop
```

### 3. 사진 캡처 (Photo Capture)
```bash
# 파노라마 스틸 샷 1회 캡처
./run.sh --take-photo
```

### 4. 미디어 파일 다운로드 (Download)
카메라 내부 스토리지/메모리에 저장된 MP4/INSP 파일 URL을 호스트 PC 로컬 저장소로 전송합니다.
```bash
./run.sh --download <REMOTE_MEDIA_URL> <LOCAL_SAVE_PATH>
# 예시
./run.sh --download /DCIM/Camera01/VID_20260811.mp4 ~/bags/VID_20260811.mp4
```

---

## 🌡️ 온도 제어 및 과열 대응 (Thermal Behavior & Management)

### 1. 카메라 발열 특성
- **DSP 인코딩 발열**: 360도 전방위 영상을 realtime 8K/5.7K H.265로 인코딩할 때 카메라 내부 프로세서의 발열이 심하게 발생합니다.
- **자동 과열 보호 (Thermal Throttling / Auto-Shutdown)**:
  - 임계 온도 초과 시 안전을 위해 녹화가 자동 중지되거나 카메라 전원이 OFF 됩니다.
  - 연속 센서 수집 및 로보틱스 기록 환경에서는 **4K @ 30fps** 설정을 권장하여 고발열을 방지합니다.

### 2. 라이다/호스트 PC와의 열 분리 방안
- 통풍이 잘되는 위치에 설치하며 라이다 배기열이 카메라 렌즈/본체로 직접 전달되지 않도록 거리를 유지합니다.

---

## 통신 정의 및 ROS 2 활용 (Communication & Usage in ROS 2)

- **인터페이스**: USB 3.0 Bulk Transfer
- **데이터 흐름**:
  ```text
  Insta360 Camera (Dual Fisheye)
    └─ USB 3.0 Interface
        └─ Linux CameraSDK (C++/Python)
            └─ HTTP/SDK Command Controller (run.sh / sync_record.py)
                └─ Local Storage (MP4 / INSP Files) & ROS 2 Time-Sync Metadata
  ```
- **로보틱스 및 센서퓨전 활용**:
  - 360도 비주얼 오도메트리(Omnidirectional Visual Odometry) 및 전방위 서라운드 매핑
  - 3D 라이다 포인트 클라우드(PointCloud2)와의 텍스처 매핑 및 3D 점군-이미지 퓨전
  - 자율주행 기록(rosbag)과 결합된 전방위 비주얼 모니터링
