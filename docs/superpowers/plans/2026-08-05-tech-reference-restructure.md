# ROS2 기술 레퍼런스 레포 재구조화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `Gorani-ros2/ROS2` 레포를 hardware/software/tracking 카테고리 구조의 기술 레퍼런스
지식 베이스로 재구성한다 (안동/sci논문/디지털트윈 세 프로젝트가 공유하는 ROS2 관련 기술 정리).

**Architecture:** 순수 마크다운 문서 구조. 코드는 포함하지 않는다. 각 폴더는 정해진 템플릿을
따르는 `README.md` 스텁으로 스캐폴딩하고, 실제 장비/소프트웨어 문서는 이후 작업하면서
채워나간다. 이번 계획의 산출물은 "골격 + 재사용 템플릿"이지 실제 기술 콘텐츠가 아니다.

**Tech Stack:** Markdown, Git/GitHub CLI (`gh`). 이 저장소는 코드베이스가 아니라 문서
저장소이므로, 아래 각 태스크의 "테스트"는 pytest 같은 자동 테스트가 아니라 파일 존재/구조를
`find`·`grep`으로 확인하는 검증 단계다.

## Global Constraints

- 이 레포는 **public**이다. 실제 소스코드(스니펫 포함)는 절대 넣지 않는다.
- 안동 컨소시엄 미확정 협의 내용, sci논문 미게재 실험 데이터·예비 결과는 넣지 않는다.
- 폴더명은 `lower_snake_case`, 특수문자 없음.
- 하드웨어 모델 문서 파일명: `제조사-모델명-kebab-case.md` (날짜 없음).
- 소프트웨어 문서 파일명: 주제 기반 `kebab-case.md` (날짜 없음, living doc).
- `tracking/status/` 문서 파일명: `YYMMDD_주제-kebab-case.md`.
- 로컬 경로: `C:\claude\r&d\ROS2`. 원격: `https://github.com/Gorani-ros2/ROS2` (public, 이미
  clone되어 있고 로컬 git identity 설정 완료 — `user.name=Gorani-ros2`,
  `user.email=overtime3131@gmail.com`).
- 참고 spec: `docs/superpowers/specs/2026-08-05-tech-reference-restructure-design.md`
  (이미 커밋됨, commit `6a0f75d`).
- 각 태스크는 완료 후 반드시 `git commit`한다. `git push`는 마지막 태스크(Task 5)에서만,
  사용자 확인 후 실행한다 — 그 전 태스크들은 로컬 커밋만 한다.

---

### Task 1: 루트 README + 재사용 템플릿

**Files:**
- Modify: `README.md` (레포 루트, 기존 3년 전 메모 전체 교체)
- Create: `templates/hardware-doc-template.md`
- Create: `templates/software-doc-template.md`

**Interfaces:**
- Consumes: spec의 "공개 범위 원칙", "폴더 구조", "문서 템플릿" 섹션
- Produces: 이후 모든 태스크가 링크할 루트 인덱스, 이후 모델/소프트웨어 문서 작성 시 복사해
  쓸 템플릿 2종

- [ ] **Step 1: 루트 README.md 교체**

기존 내용(3년 전 메모)은 Task 3에서 `software/ros2_basics/README.md`로 이관되므로 여기서는
완전히 새 내용으로 덮어쓴다.

```bash
cat > "C:/claude/r&d/ROS2/README.md" <<'EOF'
# ROS2 기술 레퍼런스

안동(CARO-Brain), sci논문(과수원 zero-shot 자율주행), 디지털트윈(dt-phenotyping) 세
프로젝트가 공유하는 ROS2 관련 기술을 기술별로 정리하는 지식 베이스.

## 공개 범위 원칙

이 레포는 public이다. 아래 기준을 항상 따른다.

- **담는 것**: 장비 스펙/데이터시트, 개념 설명, 실행 명령어, 아키텍처(다이어그램), 통신
  프로토콜 정의, 공식 발표/게재된 내용
- **담지 않는 것**: 실제 소스코드(스니펫 포함), 안동 컨소시엄 미확정 협의 내용, sci논문
  미게재 실험 데이터·예비 결과
- 프로젝트 적용 예시는 "어떤 파라미터로 썼는지"까지만 적고, 그 이상의 프로젝트 고유
  의사결정 배경은 각 프로젝트 devlog로 링크만 건다 (코드가 필요해지면 이 레포와 별도로
  코드 전용 레포를 새로 판다)

## 구조

- [`hardware/`](hardware/README.md) — 물리 장비(센서, 구동부, 로봇암, 연산 하드웨어)
- [`software/`](software/README.md) — 소프트웨어 계층(센서퓨전, 통신 프로토콜, 자율주행
  로직, 앱/모델, ROS2 기초)
- [`tracking/`](tracking/README.md) — 이 지식을 이용한 실제 기술 검증·테스트 진행상황
  (목표/이슈/상태 기록)
- [`templates/`](templates/) — 새 하드웨어/소프트웨어 문서 작성 시 복사해서 쓰는 템플릿

## 프로젝트 태그 범례

문서의 "적용 프로젝트" 섹션에서 아래 이름을 사용한다.

| 태그 | 프로젝트 | devlog |
|---|---|---|
| 안동 | CARO-Brain (쓰레기로봇 RaaS) | `Gorani-ros2/caro-brain-devlog` (private) |
| sci논문 | 과수원 zero-shot 자율주행 논문 | `Gorani-ros2/sci_second` (private) |
| 디지털트윈 | dt-phenotyping | `Gorani-ros2/dt-phenotyping-devlog` (private) |

## 새 문서 추가하는 법

- 새 장비 모델을 문서화할 때: `templates/hardware-doc-template.md`를 해당 카테고리
  폴더로 복사 → 파일명을 `제조사-모델명.md`로 변경 → 내용 채움
- 새 소프트웨어 주제를 문서화할 때: `templates/software-doc-template.md`를 해당
  카테고리 폴더로 복사 → 파일명을 `주제-kebab-case.md`로 변경 → 내용 채움
EOF
```

- [ ] **Step 2: 하드웨어 문서 템플릿 생성**

```bash
cat > "C:/claude/r&d/ROS2/templates/hardware-doc-template.md" <<'EOF'
# <제조사 모델명>

## 정의

## 데이터시트

핵심 스펙 요약 표 + 원본 데이터시트(PDF) 링크. 원본 PDF는 이 문서와 같은 폴더에 함께 보관한다.

## 적용 프로젝트

- 안동(CARO-Brain):
- sci논문:
- 디지털트윈:

## 실행 방법

## 실행 명령어

## 테스트 방법

## 통신 정의

인터페이스(USB/Ethernet/CAN/Serial), 프로토콜, ROS2 토픽/메시지 타입, 데이터 포맷.
EOF
```

- [ ] **Step 3: 소프트웨어 문서 템플릿 생성**

```bash
cat > "C:/claude/r&d/ROS2/templates/software-doc-template.md" <<'EOF'
# <주제>

## 개요

## 관련 하드웨어

(hardware/ 아래 관련 문서로 링크)

## 아키텍처 / 데이터 흐름

```mermaid
flowchart LR
    A[TODO] --> B[TODO]
```

## 설정 방법

## 사용 예시 / 명령어

## 적용 프로젝트

- 안동(CARO-Brain):
- sci논문:
- 디지털트윈:
EOF
```

- [ ] **Step 4: 생성 확인**

Run:
```bash
find "C:/claude/r&d/ROS2" -maxdepth 2 -name "*.md" | sort
```
Expected:
```
C:/claude/r&d/ROS2/README.md
C:/claude/r&d/ROS2/templates/hardware-doc-template.md
C:/claude/r&d/ROS2/templates/software-doc-template.md
```

- [ ] **Step 5: Commit**

```bash
cd "C:/claude/r&d/ROS2"
git add README.md templates/
git commit -m "Rewrite root README as tech-reference index, add doc templates"
```

---

### Task 2: hardware/ 트리 스캐폴딩

**Files:**
- Create: `hardware/README.md`
- Create: `hardware/vision_sensors/README.md`
- Create: `hardware/vision_sensors/lidar/README.md`
- Create: `hardware/vision_sensors/camera/README.md`
- Create: `hardware/vision_sensors/camera/depth_camera/README.md`
- Create: `hardware/vision_sensors/camera/streaming_camera/README.md`
- Create: `hardware/vision_sensors/camera/surround_camera/README.md`
- Create: `hardware/driving_part/README.md`
- Create: `hardware/driving_part/caterpillar/README.md`
- Create: `hardware/driving_part/4_wheel/README.md`
- Create: `hardware/support_sensors/README.md`
- Create: `hardware/support_sensors/radar/README.md`
- Create: `hardware/support_sensors/ultrasonic/README.md`
- Create: `hardware/support_sensors/gps_rtk/README.md`
- Create: `hardware/support_sensors/router/README.md`
- Create: `hardware/robotarm/README.md`
- Create: `hardware/robotarm/6axis/README.md`
- Create: `hardware/robotarm/3axis/README.md`
- Create: `hardware/compute/README.md`

**Interfaces:**
- Consumes: `templates/hardware-doc-template.md`(Task 1), spec의 폴더 구조
- Produces: 향후 각 카테고리에 모델 문서(`제조사-모델명.md`)를 추가할 자리

- [ ] **Step 1: 상위 인덱스(hardware/README.md, vision_sensors/README.md 등) 생성**

```bash
cd "C:/claude/r&d/ROS2"

cat > hardware/README.md <<'EOF'
# hardware

물리 장비 문서. 각 하위 카테고리 폴더에 공통 개념 `README.md`와 개별 모델 문서
(`제조사-모델명.md`)가 들어간다.

- [`vision_sensors/`](vision_sensors/README.md) — 라이다, 카메라(뎁스/스트리밍/서라운드)
- [`driving_part/`](driving_part/README.md) — 궤도(caterpillar), 4륜
- [`support_sensors/`](support_sensors/README.md) — 레이더, 초음파, GPS/RTK, 라우터
- [`robotarm/`](robotarm/README.md) — 6축, 3축 로봇암
- [`compute/README.md`](compute/README.md) — 엣지PC, GPU노트북, Jetson 등 연산 하드웨어
EOF

cat > hardware/vision_sensors/README.md <<'EOF'
# vision_sensors

- [`lidar/`](lidar/README.md)
- [`camera/`](camera/README.md) — [`depth_camera/`](camera/depth_camera/README.md),
  [`streaming_camera/`](camera/streaming_camera/README.md),
  [`surround_camera/`](camera/surround_camera/README.md)
EOF

cat > hardware/driving_part/README.md <<'EOF'
# driving_part

- [`caterpillar/`](caterpillar/README.md) — 궤도(무한궤도) 주행체
- [`4_wheel/`](4_wheel/README.md) — 4륜 주행체
EOF

cat > hardware/support_sensors/README.md <<'EOF'
# support_sensors

- [`radar/`](radar/README.md)
- [`ultrasonic/`](ultrasonic/README.md)
- [`gps_rtk/`](gps_rtk/README.md)
- [`router/`](router/README.md)
EOF

cat > hardware/robotarm/README.md <<'EOF'
# robotarm

- [`6axis/`](6axis/README.md)
- [`3axis/`](3axis/README.md)
EOF
```

- [ ] **Step 2: 개별 카테고리 개념 스텁(공통 템플릿) 생성**

아래 12개 폴더는 전부 동일한 형태의 "공통 개념" 스텁을 쓴다. 카테고리명만 바꿔서 반복 생성한다.

```bash
cd "C:/claude/r&d/ROS2"

write_concept_stub() {
  local dir="$1"
  local title="$2"
  mkdir -p "$dir"
  cat > "$dir/README.md" <<EOF
# ${title}

## 개념

(작성 예정 — 이 기술을 실제로 다루는 프로젝트가 생기면 채운다)

## 이 폴더의 문서

이 카테고리의 개별 장비 모델 문서는 \`templates/hardware-doc-template.md\`를 복사해서
\`제조사-모델명.md\` 형식으로 이 폴더에 추가한다.
EOF
}

write_concept_stub "hardware/vision_sensors/lidar" "lidar"
write_concept_stub "hardware/vision_sensors/camera" "camera"
write_concept_stub "hardware/vision_sensors/camera/depth_camera" "depth_camera"
write_concept_stub "hardware/vision_sensors/camera/streaming_camera" "streaming_camera"
write_concept_stub "hardware/vision_sensors/camera/surround_camera" "surround_camera"
write_concept_stub "hardware/driving_part/caterpillar" "caterpillar"
write_concept_stub "hardware/driving_part/4_wheel" "4_wheel"
write_concept_stub "hardware/support_sensors/radar" "radar"
write_concept_stub "hardware/support_sensors/ultrasonic" "ultrasonic"
write_concept_stub "hardware/support_sensors/gps_rtk" "gps_rtk"
write_concept_stub "hardware/support_sensors/router" "router"
write_concept_stub "hardware/robotarm/6axis" "6axis"
write_concept_stub "hardware/robotarm/3axis" "3axis"
write_concept_stub "hardware/compute" "compute"
```

- [ ] **Step 3: 생성 확인**

Run:
```bash
find "C:/claude/r&d/ROS2/hardware" -name "README.md" | sort | wc -l
```
Expected: `19`

Run:
```bash
find "C:/claude/r&d/ROS2/hardware" -name "README.md" | sort
```
Expected: 19줄, 위 Files 목록의 `hardware/` 하위 19개 경로와 정확히 일치.

- [ ] **Step 4: Commit**

```bash
cd "C:/claude/r&d/ROS2"
git add hardware/
git commit -m "Scaffold hardware/ category tree with concept stub READMEs"
```

---

### Task 3: software/ 트리 스캐폴딩 (+ 레거시 README 이관)

**Files:**
- Create: `software/README.md`
- Create: `software/sensorfusion/README.md`
- Create: `software/protocol/README.md`
- Create: `software/autonomy/README.md`
- Create: `software/app_model/README.md`
- Create: `software/ros2_basics/README.md` (레거시 루트 README 내용을 소프트웨어 템플릿
  형식으로 재정리한 실제 콘텐츠 — 스텁이 아님)

**Interfaces:**
- Consumes: `templates/software-doc-template.md`(Task 1), 레거시 루트 README 원문(아래
  Step 2에 원문 그대로 포함)
- Produces: 소프트웨어 카테고리 4개 스텁 + ros2_basics 실제 콘텐츠 1건

- [ ] **Step 1: software/README.md 및 4개 카테고리 스텁 생성**

```bash
cd "C:/claude/r&d/ROS2"

cat > software/README.md <<'EOF'
# software

- [`sensorfusion/`](sensorfusion/README.md) — 센서 통합(라이다-카메라-보조센서), PPS
  시간동기화, 로봇암-뎁스카메라 연동, 구동부-센서 연동
- [`protocol/`](protocol/README.md) — 서버↔엣지PC, 엣지PC↔로봇암, 엣지PC↔구동부 통신
  프로토콜
- [`autonomy/`](autonomy/README.md) — SLAM·경로계획·VLM거시판단+라이다미시제어 등
  자율주행 로직
- [`app_model/`](app_model/README.md) — 설치 프로그램, VLA/LLM/VLM 스펙·사용법
- [`ros2_basics/`](ros2_basics/README.md) — 패키지 생성/빌드/워크스페이스, 통신구조 등
  ROS2 자체 기초
EOF

write_topic_stub() {
  local dir="$1"
  local title="$2"
  mkdir -p "$dir"
  cat > "$dir/README.md" <<EOF
# ${title}

## 개요

(작성 예정 — 이 기술을 실제로 다루는 프로젝트가 생기면 채운다. 새 세부 문서를 추가할 때는
\`templates/software-doc-template.md\`를 복사해서 \`주제-kebab-case.md\`로 이 폴더에
추가한다.)

## 관련 하드웨어

## 아키텍처 / 데이터 흐름

## 설정 방법

## 사용 예시 / 명령어

## 적용 프로젝트
EOF
}

write_topic_stub "software/sensorfusion" "sensorfusion"
write_topic_stub "software/protocol" "protocol"
write_topic_stub "software/autonomy" "autonomy"
write_topic_stub "software/app_model" "app_model"
```

- [ ] **Step 2: 레거시 루트 README 내용을 ros2_basics로 이관**

레거시 원문(재구조화 전 루트 `README.md`, git 이력 `f4e669f`/`bcb6b97`에 보존됨):

```bash
mkdir -p "C:/claude/r&d/ROS2/software/ros2_basics"
cat > "C:/claude/r&d/ROS2/software/ros2_basics/README.md" <<'EOF'
# ros2_basics

패키지 생성, 빌드, 워크스페이스 구조 등 ROS2 자체의 기초. 특정 하드웨어나 다른 소프트웨어
주제(sensorfusion/protocol/autonomy/app_model)에 속하지 않는 내용을 여기 모은다.

## 개요

- ROS2 패키지 생성: 빌드는 워크스페이스에서, 패키지 생성은 소스 안에서 한다. 생성한
  패키지를 불러오려면 빌드된 bash를 source해야 한다.
- 코드를 바꿀 때마다 빌드를 다시 해야 한다 — 패키지를 새로 만들 때도 마찬가지고, bash도
  다시 불러와야 한다. symlink를 사용하면 bash를 다시 불러오지 않아도 되는 방법이 있다
  (추후 정리).
- ROS2에서는 C++로 작성된 패키지에는 `ament_cmake`를, Python으로 작성된 패키지에는
  `ament_python`을 사용하는 것이 관례다.
- 메시지 빌드 기능은 `ament_python`에는 없다. 그래서 메시지를 만들 때는 `ament_cmake`를
  사용한다.

## 관련 하드웨어

(해당 없음 — ROS2 자체 기초)

## 아키텍처 / 데이터 흐름

### setup.bash vs local_setup.bash

- `setup.bash`: 현재 터미널 세션뿐 아니라 향후에 열릴 모든 터미널 세션에서 ROS2 환경을
  설정한다. 즉 현재 환경뿐 아니라 시스템 전체에 영향을 미친다.
- `local_setup.bash`: 현재 터미널 세션에만 영향을 미친다. 다른 터미널에서 ROS2를 쓰려면
  해당 터미널에서도 이 스크립트를 실행해야 한다.

## 설정 방법

(작성 예정)

## 사용 예시 / 명령어

(작성 예정)

## 적용 프로젝트

- 안동(CARO-Brain): ROS2 공통 기반
- sci논문: ROS2 공통 기반
- 디지털트윈: ROS2 공통 기반
EOF
```

- [ ] **Step 3: 생성 확인**

Run:
```bash
find "C:/claude/r&d/ROS2/software" -name "README.md" | sort
```
Expected:
```
C:/claude/r&d/ROS2/software/README.md
C:/claude/r&d/ROS2/software/app_model/README.md
C:/claude/r&d/ROS2/software/autonomy/README.md
C:/claude/r&d/ROS2/software/protocol/README.md
C:/claude/r&d/ROS2/software/ros2_basics/README.md
C:/claude/r&d/ROS2/software/sensorfusion/README.md
```

Run:
```bash
grep -c "ament_cmake" "C:/claude/r&d/ROS2/software/ros2_basics/README.md"
```
Expected: `2` (레거시 내용이 정상적으로 이관되었는지 확인)

- [ ] **Step 4: Commit**

```bash
cd "C:/claude/r&d/ROS2"
git add software/
git commit -m "Scaffold software/ category tree, migrate legacy README into ros2_basics"
```

---

### Task 4: tracking/ 스캐폴딩

**Files:**
- Create: `tracking/README.md`
- Create: `tracking/goal/README.md`
- Create: `tracking/issues/README.md`
- Create: `tracking/status/260805_레포-재구조화.md`

**Interfaces:**
- Consumes: spec의 "tracking 운영 방식" 섹션
- Produces: 목표/이슈 살아있는 표, 첫 status 기록(이번 재구조화 자체를 기록)

- [ ] **Step 1: tracking/README.md, goal/README.md, issues/README.md 생성**

```bash
cd "C:/claude/r&d/ROS2"
mkdir -p tracking/goal tracking/issues tracking/status

cat > tracking/README.md <<'EOF'
# tracking

이 지식 베이스에 정리된 기술을 **실제로 검증·테스트하는 진행상황**을 추적한다 (문서화
자체의 진행상황이 아니다).

- [`goal/README.md`](goal/README.md) — 목표와 해야 할 일 (살아있는 단일 표)
- [`issues/README.md`](issues/README.md) — 검증·테스트 중 발견한 이슈 (살아있는 단일 표)
- `status/` — 날짜별 진행상황 기록(`YYMMDD_주제.md`). 두괄식(맨 위에 요약 먼저)으로 쓰고,
  벤치마크/검증 결과와 씽크빅 사항은 강조 표시한다. 전문가 검토도 여기 포함한다.
EOF

cat > tracking/goal/README.md <<'EOF'
# goal

| 목표 | 상태 | 관련 카테고리 |
|---|---|---|
| ROS2 레포 재구조화 (hardware/software/tracking) | 완료 | - |
EOF

cat > tracking/issues/README.md <<'EOF'
# issues

| 이슈 | 발견일 | 상태 | 관련 문서 |
|---|---|---|---|
EOF
```

- [ ] **Step 2: 첫 status 기록 작성 (이번 재구조화 자체)**

```bash
cat > "C:/claude/r&d/ROS2/tracking/status/260805_레포-재구조화.md" <<'EOF'
# 260805 레포 재구조화

**요약**: 2023년부터 비정형 메모 수준이었던 `ROS2` 레포를 안동/sci논문/디지털트윈 세
프로젝트가 공유하는 기술 레퍼런스 지식 베이스로 재구조화했다. hardware/software/tracking
3개 최상위 카테고리로 나누고, 각 카테고리에 문서 템플릿과 개념 스텁을 스캐폴딩했다.
실제 장비/소프트웨어 콘텐츠는 아직 비어 있고, 앞으로 각 기술을 실제로 다룰 때 채워나간다.

## 배경

세 프로젝트 모두 ROS2 기반이며 주행체/로봇 제어, 라이다, 뎁스카메라, 자율주행 등에서
기술이 크게 겹친다. 프로젝트별로 흩어진 기술 지식을 기술별로 한곳에 모으기 위해 시작함.

## 진행 내용

- 폴더 구조: `hardware/`(vision_sensors, driving_part, support_sensors, robotarm,
  compute), `software/`(sensorfusion, protocol, autonomy, app_model, ros2_basics),
  `tracking/`(goal, issues, status) 확정
- 공개 범위 원칙 확정: public 유지, 실제 코드·컨소시엄 미확정 협의·논문 미게재 결과는 제외
- 문서 템플릿 2종(`templates/hardware-doc-template.md`,
  `templates/software-doc-template.md`) 작성
- 레거시 루트 README(3년 전 ROS2 입문 메모)를 `software/ros2_basics/README.md`로 이관

## 다음 단계

각 프로젝트에서 실제로 쓰는 장비/소프트웨어부터 순서대로 문서화한다(예: 안동에서 쓰는
라이다 모델부터 `hardware/vision_sensors/lidar/`에 추가).
EOF
```

- [ ] **Step 3: 생성 확인**

Run:
```bash
find "C:/claude/r&d/ROS2/tracking" -type f | sort
```
Expected:
```
C:/claude/r&d/ROS2/tracking/README.md
C:/claude/r&d/ROS2/tracking/goal/README.md
C:/claude/r&d/ROS2/tracking/issues/README.md
C:/claude/r&d/ROS2/tracking/status/260805_레포-재구조화.md
```

- [ ] **Step 4: Commit**

```bash
cd "C:/claude/r&d/ROS2"
git add tracking/
git commit -m "Scaffold tracking/ with goal/issues tables and first status entry"
```

---

### Task 5: 전체 구조 검증 + 원격 반영

**Files:** (읽기/검증만, 신규 파일 없음)

**Interfaces:**
- Consumes: Task 1~4의 전체 산출물
- Produces: 검증된 최종 구조, (사용자 승인 시) 원격 push

- [ ] **Step 1: 전체 트리와 spec 대조**

Run:
```bash
cd "C:/claude/r&d/ROS2"
find . -path ./.git -prune -o -type f -name "*.md" -print | sort
```
Expected: spec(`docs/superpowers/specs/2026-08-05-tech-reference-restructure-design.md`)의
"폴더 구조" 섹션에 있는 모든 경로 + Task 1의 `templates/` 2건 + `docs/superpowers/` 하위
spec·plan 파일이 빠짐없이 나온다. 스펙에 없는 파일이 섞여 있으면 안 된다.

- [ ] **Step 2: 커밋 로그 확인**

Run:
```bash
git log --oneline -6
```
Expected: Task 1~4의 커밋 4개 + spec 커밋(`6a0f75d`) + 기존 `Update README.md`/
`Initial commit` 이 순서대로 보인다.

- [ ] **Step 3: 사용자 확인 후 원격 push**

이 저장소는 public이며 push는 원격에 즉시 반영되는 작업이므로, 실행자는 push 전에 반드시
사용자에게 "로컬 커밋 4~5개를 `Gorani-ros2/ROS2`(public) 원격에 push해도 되는지" 확인한다.
승인 시:

```bash
cd "C:/claude/r&d/ROS2"
git push origin main
```

Expected: `main -> main` 정상 push, 에러 없음.
