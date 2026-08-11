# 🤖 AGENTS.md — AI Agent Collaboration & Central Knowledge Hub Protocol

Welcome AI Agent! You are working on the **ROS 2 & Multi-Sensor System Knowledge Base** repository (`Gorani-ros2/ROS2`).

This repository serves as the **Central Core Technology Hub** for all application projects, including:
- **Andong Robot Project** (안동 로봇 프로젝트)
- **Phenotyping Project** (피노타이핑 응용 프로젝트)
- **Paper & Thesis Repositories** (논문 및 기술 연구 레포지토리)

---

## 📌 Critical Directives for Every AI Assistant Working on This Repo

When assisting the user or making edits to this repository, you MUST strictly adhere to the following rules:

### 1. 🌐 Central Knowledge Hub & Cross-Repository Synchronization Rule
- Treat this repository as the **primary reusable technology vault**.
- When working on application repositories (Andong Robot, Phenotyping, Research Papers), any verified sensor driver, parsing node, hardware pinout, or sync script MUST be uploaded back into this ROS 2 repository following standard templates for long-term reusability.
- Conversely, when building application projects, pull drivers and setup guides directly from this ROS 2 knowledge base.

### 2. 🔗 Mandatory Bidirectional Cross-Linking Rule
- Every hardware document under `hardware/` MUST include relative markdown links to its corresponding software driver, ROS 2 node, and synchronization documents under `software/`.
- Every software document under `software/` MUST include relative markdown links to its corresponding hardware sensors, antennas, and interface documents under `hardware/`.
- Ensure seamless navigation so that anyone reading a document can switch back and forth between hardware specs and software code with 1 click.

### 3. 📐 Standardized Document Structure & Writing Order
- All new and updated documentation MUST use the templates in `templates/` and follow a strict, unified section hierarchy:
  - **Hardware Docs (`templates/hardware-doc-template.md`)**:
    1. Title `# [제조사] [모델명] [장비 카테고리]`
    2. `## 1. 개요 및 주요 특징`
    3. `## 2. 🔗 관련 소프트웨어 및 센서 십자 링크` (Bidirectional Links)
    4. `## 3. 하드웨어 기술 사양 (표)`
    5. `## 4. 핀맵 및 커넥터 가이드`
    6. `## 5. 물리적 설치 및 배치 3대 수칙`
    7. `## 6. ROS 2 드라이버 및 토픽 연동`
    8. `## 7. ❓ 자주 묻는 질문 및 실전 기술 Q&A`
    9. `## 8. 펌웨어 및 변경 이력`
  - **Software Docs (`templates/software-doc-template.md`)**:
    1. Title `# [소프트웨어/모듈명] [주제 및 기능 정의]`
    2. `## 1. 개요 및 파이프라인 (Mermaid 흐름도)`
    3. `## 2. 🔗 관련 하드웨어 장비 문서 십자 링크` (Bidirectional Links)
    4. `## 3. 필수 환경 및 패키지 의존성`
    5. `## 4. 소스코드 및 구동 가이드`
    6. `## 5. 발행 및 구독 토픽 정의 (표)`
    7. `## 6. ❓ 개발/테스트 Q&A 및 트러블슈팅`
    8. `## 7. 발열 및 안전 관리 수칙`

### 4. 📖 Comprehensive & Rich Technical Detail Requirement
- **NEVER summarize briefly** or skip technical explanations.
- When the user asks questions or resolves hardware/software issues, write out the complete, rich technical background, error root causes, parameters, formulas, commands, and firmware upgrade procedures in detail inside the Q&A section of the document.

### 5. 📁 Multi-Location Categorization (`hardware/` & `software/`)
- Place hardware specs, pinouts, power calculations, antenna guidelines in `hardware/`.
- Place ROS 2 drivers, topics, parsing nodes, thermal safety, and synchronization architecture in `software/`.
- **Duplication is explicitly allowed and required**: If information touches both hardware and software, record the detailed Q&A and documentation in **all relevant places** without omission.

### 6. 📢 Mandatory Root `README.md` Update
- Every session that modifies documentation, code, or hardware configuration MUST update the **`📢 최근 핵심 업데이트 내역 (Latest Updates)`** section in the root [`README.md`](README.md).
- Always include: Date, Host Machine (`knu laptop` vs `knu desktop`), local source folder path, summary of changes, and clickable file links.

### 7. 💻 Environment Audit Logging
- Every session MUST create or update a tracking log under `tracking/YYYY-MM-DD-environment-audit.md`.
- State the machine identifier (`knu laptop`), OS, AI model identity, local raw resource paths (e.g. `/home/knu/workspaces/sensors/sub_sensors`), and affected file list.

### 8. 🔄 Seamless Continuation Protocol for Next AI / Session
- Always record current completion status and upcoming tasks (e.g. Teltonika RUT241 LTE Router NTRIP Client B-mode, Ouster LiDAR PPS time sync) in the docs and tracking files so that **any other AI on another computer can `git pull` and immediately pick up where you left off**.
