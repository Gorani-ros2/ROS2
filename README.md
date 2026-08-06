# ROS2 기술 레퍼런스

ROS2 관련 기술을 기술별로 정리하는 지식 베이스.

## 구조

- [`hardware/`](hardware/README.md) — 물리 장비(센서, 구동부, 로봇암, 연산 하드웨어)
- [`software/`](software/README.md) — 소프트웨어 계층(센서퓨전, 통신 프로토콜, 자율주행
  로직, 앱/모델, ROS2 기초)
- [`tracking/`](tracking/README.md) — 이 지식을 이용한 실제 기술 검증·테스트 진행상황
  (목표/이슈/상태 기록)
- [`templates/`](templates/) — 새 하드웨어/소프트웨어 문서 작성 시 복사해서 쓰는 템플릿

## 새 문서 추가하는 법

- 새 장비 모델을 문서화할 때: `templates/hardware-doc-template.md`를 해당 카테고리
  폴더로 복사 → 파일명을 `제조사-모델명-kebab-case.md`로 변경 → 내용 채움
- 새 소프트웨어 주제를 문서화할 때: `templates/software-doc-template.md`를 해당
  카테고리 폴더로 복사 → 파일명을 `주제-kebab-case.md`로 변경 → 내용 채움
