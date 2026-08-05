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
- [`docs/`](docs/) — 이 레포 구조의 설계 spec과 실행 plan

## 프로젝트 태그 범례

문서의 "적용 프로젝트" 섹션에서 아래 이름을 사용한다.

| 태그 | 프로젝트 | devlog |
|---|---|---|
| 안동 | CARO-Brain (쓰레기로봇 RaaS) | `Gorani-ros2/caro-brain-devlog` (private) |
| sci논문 | 과수원 zero-shot 자율주행 논문 | `Gorani-ros2/sci_second` (private) |
| 디지털트윈 | dt-phenotyping | `Gorani-ros2/dt-phenotyping-devlog` (private) |

## 새 문서 추가하는 법

- 새 장비 모델을 문서화할 때: `templates/hardware-doc-template.md`를 해당 카테고리
  폴더로 복사 → 파일명을 `제조사-모델명-kebab-case.md`로 변경 → 내용 채움
- 새 소프트웨어 주제를 문서화할 때: `templates/software-doc-template.md`를 해당
  카테고리 폴더로 복사 → 파일명을 `주제-kebab-case.md`로 변경 → 내용 채움
