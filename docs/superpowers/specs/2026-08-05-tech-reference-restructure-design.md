# ROS2 레포: 기술 레퍼런스 재구성 설계

## 배경 및 목적

`Gorani-ros2/ROS2` 레포는 2023년부터 존재했으나 정리 안 된 메모 수준의 README 하나만 있는
상태였다. 안동(CARO-Brain), sci논문(과수원 zero-shot 자율주행), 디지털트윈(dt-phenotyping)
세 프로젝트가 모두 ROS2 기반이며, 주행체/로봇 제어, 라이다, 뎁스카메라, 자율주행 등에서
기술이 크게 겹친다. 이 레포를 **세 프로젝트가 공유하는 ROS2 관련 기술 지식 베이스**로
재구성하여, 프로젝트별로 흩어진 기술 지식(하드웨어 스펙, 통신 프로토콜, 자율주행 로직 등)을
기술별로 한곳에 모은다.

## 산출물 성격

이 레포는 "엔지니어링 개발 프로젝트"도 아니고 "단일 원고 완성형"도 아닌, **지속적으로
누적되는 기술 참고 문서(레퍼런스) + 그 기술을 검증/테스트하는 진행상황 기록**이다. 기존
devlog 컨벤션(reference/journal/planning/reviews/correspondence/issues)을 그대로
복사하지 않고, 기술 카테고리 중심 구조로 새로 설계한다.

## 공개 범위 원칙 (Public 레포 안전장치)

레포는 public으로 유지한다. 안동(정부 R&D 컨소시엄 과제)과 sci논문(학술 논문 프로젝트)은
각각 별도의 공개 리스크가 있어, 다음 원칙을 루트 README.md에 명문화하여 매번 판단하지 않고
이 기준을 따른다.

- **담는 것**: 장비 스펙/데이터시트, 개념 설명, 실행 명령어, 아키텍처(다이어그램), 통신
  프로토콜 정의, 공식 발표/게재된 내용
- **담지 않는 것**: 실제 소스코드(스니펫 포함 — 코드가 필요해지면 이 레포와 별도로
  코드 전용 레포를 새로 판다), 안동 컨소시엄 미확정 협의 내용, sci논문 미게재 실험
  데이터·예비 결과
- 프로젝트 적용 예시는 "어떤 파라미터로 썼는지"까지만 적고, 그 이상의 프로젝트 고유
  의사결정 배경은 각 프로젝트 devlog로 링크만 걸고 내용을 복제하지 않는다
  (caro-brain-devlog, sci_second, dt-phenotyping-devlog — 모두 private)

## 폴더 구조

```
ROS2/
├── README.md                          # 인덱스: 목적, 공개범위 원칙, 카테고리 설명, 프로젝트 태그 범례
├── hardware/
│   ├── vision_sensors/
│   │   ├── lidar/
│   │   │   ├── README.md              # 라이다 공통 개념
│   │   │   └── <제조사-모델명>.md
│   │   └── camera/
│   │       ├── README.md              # 카메라 공통 개념(캘리브레이션 등)
│   │       ├── depth_camera/<모델>.md
│   │       ├── streaming_camera/<모델>.md
│   │       └── surround_camera/<모델>.md
│   ├── driving_part/
│   │   ├── caterpillar/<모델>.md
│   │   └── 4_wheel/<모델>.md
│   ├── support_sensors/
│   │   ├── radar/<모델>.md
│   │   ├── ultrasonic/<모델>.md
│   │   ├── gps_rtk/<모델>.md
│   │   └── router/<모델>.md
│   ├── robotarm/
│   │   ├── 6axis/<모델>.md
│   │   └── 3axis/<모델>.md
│   └── compute/                       # 엣지PC·GPU노트북·Jetson 등 연산 하드웨어
│       └── <모델>.md
├── software/
│   ├── sensorfusion/                  # 센서 통합, PPS 시간동기화, 로봇암-뎁스카메라 연동, 구동부-센서 연동
│   ├── protocol/                      # 서버↔엣지PC, 엣지PC↔로봇암, 엣지PC↔구동부 통신 프로토콜
│   ├── autonomy/                      # SLAM·경로계획·VLM거시판단+라이다미시제어 등 자율주행 로직
│   ├── app_model/                     # 설치 프로그램, VLA/LLM/VLM 스펙·사용법
│   └── ros2_basics/                   # 패키지 생성/빌드/워크스페이스, 통신구조 등 ROS2 자체 기초
└── tracking/
    ├── goal/                          # 목표와 할 일 (living README, 표)
    ├── issues/                        # 기술 검증·테스트 중 발견한 이슈 (living README, 표)
    └── status/                        # 날짜별 진행상황 기록 (YYMMDD_주제.md)
```

카테고리는 필요에 따라 계속 추가될 수 있다(software 하위 특히, 사용자 확정: "3개+a"). 처음부터
완벽할 필요 없이 작업하면서 구조를 조정해나간다 (사용자 확정: "일단 그렇게 짜놓자. 하면서
수정해나갈꺼야").

`ros2_basics/`는 설계 검토 중 발견한 gap을 메우기 위해 추가한 "+a" 카테고리다 — 패키지
생성/빌드/워크스페이스/통신구조 같은 ROS2 자체의 기초 지식은 특정 하드웨어나 개별 소프트웨어
주제(sensorfusion/protocol/autonomy/app_model)에 속하지 않는다. 기존 레포 루트에 있던
비정형 메모(README.md, 패키지 생성·빌드·setup.bash·ament_cmake 관련 내용)는 이 폴더로
이관하여 위 템플릿 형식으로 재정리한다.

## 문서 템플릿

### 하드웨어 leaf 문서 (`<제조사-모델명>.md`)

```markdown
# <제조사 모델명>

## 정의
## 데이터시트          (핵심 스펙 표 + 원본 PDF 링크, 원본은 같은 폴더에 보관)
## 적용 프로젝트        (안동/sci논문/디지털트윈 — 어디서 어떤 파라미터로 쓰는지)
## 실행 방법            (드라이버 설치, ROS2 패키지 설치/빌드)
## 실행 명령어          (cheat sheet)
## 테스트 방법          (정상 동작 확인)
## 통신 정의            (인터페이스, 프로토콜, ROS2 토픽/메시지 타입, 데이터 포맷)
```

각 기술 카테고리 폴더에는 개별 모델 문서와 별도로 `README.md`를 두어 그 기술군의 공통
개념(예: 라이다라면 포인트클라우드, ROS2 공통 처리 방식)을 설명한다.

### 소프트웨어 문서 (`sensorfusion/`, `protocol/`, `autonomy/`, `app_model/` 하위)

```markdown
# <주제>

## 개요
## 관련 하드웨어        (hardware/ 문서로 링크)
## 아키텍처 / 데이터 흐름 (mermaid 다이어그램)
## 설정 방법
## 사용 예시 / 명령어
## 적용 프로젝트
```

## tracking 운영 방식

- `goal/README.md`, `issues/README.md`: 각각 살아있는 단일 표로 관리
  (목표|상태|관련 카테고리 / 이슈|발견일|상태|관련 문서 링크)
- `status/`: 날짜별 개별 파일. 기존 저장소(안동, dt-phenotyping)와 동일한 컨벤션 재사용 —
  두괄식 구조(맨 위 스토리라인 요약 먼저), 벤치마크/검증 결과와 씽크빅 사항은 강조 표시,
  전문가 검토도 이 폴더에 포함
- tracking이 추적하는 대상은 **이 지식을 이용한 실제 기술 검증·테스트 진행상황**이다
  (문서화 진행상황이 아니라, 예: "lidar-camera 캘리브레이션 정확도 검증" 같은 실제 검증
  작업의 목표/이슈/결과)

## 네이밍 컨벤션

- 폴더명: `lower_snake_case`, 특수문자 없음 (`app&model` → `app_model`로 변경)
- 하드웨어 모델 문서: `제조사-모델명-kebab-case.md` (날짜 없음, 예: `ouster-os1-64.md`)
- 소프트웨어 문서: 주제 기반 `kebab-case.md` (날짜 없음, living doc)
- tracking/status 문서: `YYMMDD_주제-kebab-case.md`

## 로컬 경로

`C:\claude\r&d\ROS2` (기존 프로젝트들과 동일한 `C:\claude\r&d\<project>` 컨벤션)
