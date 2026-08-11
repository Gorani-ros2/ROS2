# 🤖 AGENTS.md — AI Agent Collaboration & Operating Guidelines

Welcome AI Agent! You are working on the **ROS 2 & Multi-Sensor System Knowledge Base** repository (`Gorani-ros2/ROS2`).

This repository is actively managed across multiple development machines (`knu laptop`, `knu desktop`) by human developers paired with AI assistants.

---

## 📌 Critical Directives for Every AI Assistant Working on This Repo

When assisting the user or making edits to this repository, you MUST strictly adhere to the following rules:

### 1. 📖 Comprehensive & Rich Technical Detail Requirement
- **NEVER summarize briefly** or skip technical explanations.
- When the user asks questions or resolves hardware/software issues, write out the complete, rich technical background, error root causes, parameters, formulas, commands, and firmware upgrade procedures in detail.

### 2. 📁 Multi-Location Categorization (`hardware/` & `software/`)
- Place hardware specs, pinouts, power calculations, antenna guidelines in `hardware/`.
- Place ROS 2 drivers, topics, parsing nodes, thermal safety, and synchronization architecture in `software/`.
- **Duplication is explicitly allowed and required**: If information touches both hardware and software, record the detailed Q&A and documentation in **all relevant places** without omission.

### 3. 📢 Mandatory Root `README.md` Update
- Every session that modifies documentation, code, or hardware configuration MUST update the **`📢 최근 핵심 업데이트 내역 (Latest Updates)`** section in the root [`README.md`](README.md).
- Always include: Date, Host Machine (`knu laptop` vs `knu desktop`), summary of changes, and clickable file links.

### 4. 💻 Environment Audit Logging
- Every session MUST create or update a tracking log under `tracking/YYYY-MM-DD-environment-audit.md`.
- State the machine identifier (`knu laptop`), OS, AI model identity, local raw resource paths (e.g. `/home/knu/workspaces/sensors/sub_sensors`), and affected file list.

### 5. 🔄 Seamless Continuation Protocol for Next AI / Session
- Always record current completion status and upcoming tasks (e.g. Teltonika RUT241 LTE Router NTRIP Client B-mode, Ouster LiDAR PPS time sync) in the docs and tracking files so that **any other AI on another computer can `git pull` and immediately pick up where you left off**.
