# 📋 Environment Audit Log — 2026-08-21

- **Date**: 2026-08-21
- **Host Machine**: `knu laptop` (Linux / Ubuntu ROS 2 Humble)
- **AI Assistant**: Antigravity (Google DeepMind Team)
- **Target Workspace**: `/home/knu/workspaces/insta360` (`Gorani-ros2/ROS2`)

---

## 🔍 System Environment State & Audit

### 1. Active Hardware & Ports
- **Insta360 Camera**: USB-C connection (`/dev/bus/usb`, Camera SDK v2.1.1 HTTP tunnel)
- **Ouster OS0-128 LiDAR**: Ethernet (`169.254.129.201`, UDP packets)
- **Septentrio mosaic-go G5 P3H RTK**: USB-C (`/dev/ttyACM1` serial + `192.168.3.1` web)

### 2. Affected Files & Artifacts
1. [`sync_record.py`](file:///home/knu/workspaces/insta360/sync_record.py)
   - Backup: [`sync_record.py.bak_20260821`](file:///home/knu/workspaces/insta360/sync_record.py.bak_20260821)
   - Added `--no-download` flag.
   - Restored `SIGINT` signal handler before download loop to allow Ctrl+C cancellation during socket download.
2. [`software/sensorfusion/lidar-insta360-sync-record.md`](file:///home/knu/workspaces/insta360/software/sensorfusion/lidar-insta360-sync-record.md)
   - Added Q&A section explaining Insta360 HTTP socket stall root cause, Ctrl+C SIG_IGN deadlock, emergency kill command (`killall -9 insta360_control python3`), and `--no-download` workflow.
3. [`hardware/vision_sensors/camera/insta360-camera-sdk.md`](file:///home/knu/workspaces/insta360/hardware/vision_sensors/camera/insta360-camera-sdk.md)
   - Updated Q&A section with USB Bulk Transfer socket lock diagnosis and remediation.
4. [`README.md`](file:///home/knu/workspaces/insta360/README.md)
   - Added 2026-08-21 entry in "최근 핵심 업데이트 내역".

---

## 🛠️ Summary of Diagnosed Issue
- **Symptom**: Downloading large video file (~1.05 GB) via `./run.sh --download` (`insta360_control`) froze at `http_tunnel_client.cpp:0086 write to socket: ...` and ignored `Ctrl+C`.
- **Root Cause**:
  1. USB Bulk transfer socket buffer full on large files (1GB+) in Insta360 C++ SDK.
  2. Parent Python process set `SIGINT` = `SIG_IGN` during cleanup, causing `insta360_control` to inherit SIGINT ignore and deadlock on blocking socket I/O.
  3. Insta360 C++ SDK (`HttpTunnelService`) internal 300-second (5-minute) timeout expired at 10:46:05 (from 10:41:05 freeze), triggering `[Download] Download failed!` and auto-cleanup.
- **Resolution**:
  - Provided immediate terminal kill command: `killall -9 insta360_control python3`.
  - Added `--no-download` option to skip automatic USB downloading for large 8K/5.7K recordings.
  - Restored `SIGINT` handling in `sync_record.py` during download phase.
  - Documented `./run.sh --status` CLI diagnostic command to detect mid-recording camera stops and thermal drops.
