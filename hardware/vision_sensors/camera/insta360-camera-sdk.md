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

---

## ❓ 자주 묻는 질문 및 실전 기술 Q&A

### Q1. Insta360 파일 다운로드 시 `http_tunnel_client.cpp: write to socket` 메세지가 멈추고 `Ctrl+C`도 차단되는 이유와 대처법은?

**현상 설명**:
`./run.sh --download` 또는 `sync_record.py` 실행 후 대용량 비디오(1GB 이상) 다운로드 중 `http_tunnel_client.cpp:0086: write to socket: ...` 출력이 1.05GB 부근에서 완전히 멈추고(Freeze), `Ctrl+C`를 입력해도 `[Signal] Interrupted by user (signal 2). Stopping process...`만 지속되며 프로세스가 종료되지 않음.

**원인 분석**:
1. **USB Bulk Transfer HTTP 소켓 버퍼 락**: Insta360 C++ SDK의 HTTP 터널 클라이언트(`http_tunnel_client.cpp`)는 USB 전송 속도 지연 또는 카메라 SD 카드 읽기 병목 발생 시 소켓 쓰기 버퍼가 꽉 찬 상태(Socket Buffer Overflow)에서 Sync Blocking 상태로 락이 걸립니다.
2. **SIGINT Ignore 이관 데드락**: 상위 파이썬 스크립트에서 `SIGINT`를 `SIG_IGN`(무시) 설정한 후 다운로드 프로세스를 호출할 경우, `Ctrl+C` 키 입력 시 C++ SDK 신호 포착 로그만 찍히고 시스템 콜 블로킹을 탈출하지 못합니다.
3. **SDK 내부 300초(5분) 무응답 소켓 타임아웃**: C++ SDK(`HttpTunnelService`) 내부에 300초(5분) 타임아웃 타이머가 내장되어 있어, 소켓 멈춤 시점(`10:41:05`)부터 정확히 5분 후(`10:46:05`)에 `[Download] Download failed!` 및 `HttpTunnelService:: begin close serveice` 로그를 남기고 자동 타임아웃 종료됩니다.

**실전 해결 방안**:
1. **다른 터미널에서 강제 종료 (Emergency Kill)**:
   ```bash
   killall -9 insta360_control python3
   ```
2. **`--no-download` 옵션 적용**:
   대용량 비디오 녹화 시 자동 다운로드를 비활성화하고 카메라 SD 카드 직결 복사 방식을 활용합니다.
   ```bash
   python3 sync_record.py --record --res 4K --fps 30 --no-download
   ```

---

### Q2. 녹화 중간에 카메라가 스스로 멈추는지 진단하는 명령어와 원인은?

**1. 실시간 진단 명령어**:
```bash
./run.sh --status
```
실행 시 카메라 접속 유무, 배터리 잔량, SD 카드 용량 및 현재 녹화 동작 중 여부(`CaptureCurrentStatus`)를 즉시 출력합니다.

**2. 녹화 중작 주요 원인**:
- **8K/5.7K 인코딩 과열 셧다운**: DSP 온도가 올라가 카메라가 자동 정지됨. (해결: 4K@30fps 권장)
- **SD 카드 쓰기 속도 부족**: V30 규격 미달 시 레코딩 튕김. (해결: U3/V30 SD 카드 사용)
