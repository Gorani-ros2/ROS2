# 라이다 & Insta360 동시 제어 및 시간 동기화 (LiDAR & Camera Synchronized Controller)

> **작성 일자**: 2026-08-11  
> **작성 장비**: `knu laptop` (KNU 노트북 PC)  
> **작성 AI**: Antigravity (Google DeepMind Team)  
> **파일명 규격**: `lidar-insta360-sync-record.md`

---

## 📌 Executive Abstract (상세 요약 및 초록)
본 문서는 Ouster OS0-128 3D 라이다, Insta360 360도 카메라, Septentrio RTK 수신기 멀티 센서 융합 시스템의 동시 제어 아키텍처, 파이썬 동기화 녹화 스크립트(`sync_record.py`), ROS 2 오프셋 동기화 및 다중 센서 고온 발열 방지 수칙을 다룹니다.

---

## 1. 개요 및 정의

Ouster OS0-128 3D 라이다와 Insta360 360도 파노라마 카메라의 이종(Heterogeneous) 센서를 통합하여 **시분할/연속 동시 녹화**, **스틸 샷 동시 캡처**, **ROS 2 타임스탬프 동기화**, **원천 PCAP 수집** 및 **시스템 최대 온도 변화 대응 관리**를 수행하는 통합 동시 제어 기술입니다.


---

## 관련 하드웨어

- [Ouster OS0-128 3D 라이다](../../hardware/vision_sensors/lidar/ouster-os0-128.md)
- [Insta360 파노라마 카메라 (Camera SDK)](../../hardware/vision_sensors/camera/insta360-camera-sdk.md)
- [Septentrio mosaic-go G5 P3H RTK 수신기](../../hardware/support_sensors/gps_rtk/septentrio-mosaic-go-g5-p3h.md)


---

## 아키텍처 / 데이터 흐름

```mermaid
flowchart TD
    CLI[sync_record.py 스크립트 실행] --> ConfigCam[1. Insta360 해상도/FPS 설정: ./run.sh --set-res 4K 30]
    ConfigCam --> LaunchLidar[2. Ouster ROS 2 드라이버 런칭: driver.launch.py]
    LaunchLidar --> CheckTopics[3. ROS 2 토픽 활성화 검증: /ouster/points, /ouster/imu]
    CheckTopics --> QueryMeta[4. 라이다 메타데이터 획득 및 metadata.json 저장]
    
    QueryMeta --> ModeBranch{동작 모드 선택}
    
    ModeBranch -- "--record / --record-time" --> StartCamRec[5. 카메라 녹화 시작: ./run.sh --start-only]
    StartCamRec --> MarkCamTime[t_cam_start_unix 측정]
    MarkCamTime --> StartBagRec[6. rosbag record 백그라운드 프로세스 생성]
    StartBagRec --> MarkBagTime[t_bag_start_unix 측정]
    MarkBagTime --> GenSyncJson[7. sync_info.json 타임스탬프 오프셋 계산 및 저장]
    GenSyncJson --> OptionPCAP[8. 옵션: tcpdump PCAP 패킷 수집]
    
    OptionPCAP --> WaitStop[9. 녹화 진행 / 지정 시간 대기]
    WaitStop --> SignalStop[10. 녹화 종료 시그널 전달]
    
    SignalStop --> StopPCAP[PCAP tcpdump 안전 종료]
    StopPCAP --> StopBag[rosbag 인덱스 마감 및 저장]
    StopBag --> StopCamRec[카메라 녹화 종료 시그널 전달: ./run.sh --stop]
    StopCamRec --> DownloadMP4[카메라 MP4/INSP 파일 로컬 저장소 다운로드]
    DownloadMP4 --> StopLidar[라이다 노드 안전 종료]

    ModeBranch -- "--photo" --> TakePhoto[1. 카메라 사진 촬영: ./run.sh --take-photo]
    TakePhoto --> GrabPCD[2. /ouster/points 1프레임 캡처 및 .pcd 파일 저장]
    GrabPCD --> DownloadJPG[3. 카메라 JPG/INSP 다운로드]
    DownloadJPG --> StopLidar
```

---

## 타임스탬프 시간 동기화 메커니즘 (Time Synchronization)

1. **라이다 타임스탬프**: Ouster 드라이버 설정 `timestamp_mode: "TIME_FROM_ROS_TIME"`에 따라 시스템 호스트 시간 기반 ROS 2 헤더 타임스탬프가 부여됩니다.
2. **카메라 타임스탬프 오프셋 산출**:
   - 카메라 녹화 명령 수신 직후 Unix timestamp(`t_cam_start_unix`)를 생성합니다.
   - rosbag 프로세스 런칭 직후 Unix timestamp(`t_bag_start_unix`)를 생성합니다.
   - **동기화 오프셋**: `cam_to_bag_offset_sec = t_bag_start_unix - t_cam_start_unix`
   - 이 데이터는 `sync_info.json`에 저장되어 이종 미디어 후처리 시 비디오 프레임과 점군(Point Cloud) 간의 정확한 시각을 매칭합니다.

```json
{
  "camera_fps": 30,
  "lidar_hz": 10,
  "points_topic": "/ouster/points",
  "camera_frame_period_ms": 33.33,
  "lidar_scan_period_ms": 100.0,
  "camera_frames_per_lidar_scan": 3.0,
  "t_cam_start_unix": 1723365000.123,
  "t_bag_start_unix": 1723365000.456,
  "cam_to_bag_offset_sec": 0.333
}
```

---

## 🌡️ 시스템 최대 온도 변화 및 써멀 통합 관리 (Max Temperature & Thermal Management)

동시 제어 시 하드웨어(LiDAR, Camera, Host PC) 전체의 **복합 열부하**를 사전에 관리해야 합니다.

### 1. 센서 및 호스트 단계별 과열 한계치

| 컴포넌트 | 과열 단계 / 현상 | 한계 온도 | 영향 및 시스템 반응 |
| :--- | :--- | :--- | :--- |
| **Ouster OS0-128 LiDAR** | **Shot Limiting (1단계)** | 약 60°C 부근 | 레이저 샷 부분 강제 OFF → 점군 듬성듬성 결측 (이빨 빠짐 현상) |
| | **Thermal Shutdown (2단계)** | 약 75°C~80°C | 레이저 100% 강제 차단 → `OVER_TEMP` 상태 및 데이터 수신 0% |
| **Insta360 Camera** | **Auto-Shutdown Protection** | 내부 DSP 70°C 이상 | 고해상도(8K) 인코딩 발열로 자동 녹화 중단 및 카메라 셧다운 |
| **Host PC (노트북)** | **CPU Thermal Throttling** | CPU 코어 85°C 이상 | CPU 성능 저하로 인한 커널 UDP Socket Buffer Overflow → **rosbag 결측 발생** |

### 2. 열 부하 진단 및 모니터링 명령어
- **LiDAR 온도 조회**: `curl -s http://<sensor_ip>/api/v1/sensor/telemetry | jq .internal_temperature_deg_c`
- **Host PC CPU 쓰로틀링 진단**: `sudo dmesg -T | grep -iE "thermal|throttle"`

### 3. 과열 방지 및 시스템 최적화 방안
- **포인트 클라우드 Hz Throttle**: `--lidar-hz 5` 옵션을 적용하여 `/ouster/points` 데이터를 5Hz로 리샘플링하여 Host PC의 커널 UDP 버퍼 처리 및 NVMe 쓰기 부하를 50% 절감.
- **카메라 해상도 최적화**: 8K 대신 **4K @ 30fps**를 사용하여 Insta360 인코딩 프로세서 발열을 제어.

---

## 사용 예시 및 실행 명령어

### 1. 지정 시간(예: 10초) 동안 동시 녹화
```bash
python3 sync_record.py.bak --record-time --duration 10 --res 4K --fps 30
```

### 2. 수동 종료(ENTER키 입력) 시까지 연속 동시 녹화
```bash
python3 sync_record.py.bak --record --res 4K --fps 30
```

### 3. 라이다 스로틀링(5Hz) 및 원천 PCAP 패킷 백업 포함 동시 녹화
```bash
python3 sync_record.py.bak --record-time --duration 20 --lidar-hz 5 --pcap
```

### 4. 1프레임 시분할 동시 스틸 샷 (Photo + PCD 캡처)
```bash
python3 sync_record.py.bak --photo
```
