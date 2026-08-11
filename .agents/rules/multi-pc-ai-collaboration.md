# 🤖 다중 PC & AI 협업 가이드라인 (Multi-PC & Multi-AI Collaboration Rules)

본 레포지토리(`Gorani-ros2/ROS2`)는 여러 노트북(`knu laptop`) 및 데스크톱(`knu desktop`) PC 환경에서 다양한 AI 어시스턴트(Antigravity 등)가 협업하여 지식을 작성하고 유지보수하는 공간입니다.

이 레포지토리를 작업하는 **모든 AI 어시스턴트는 반드시 아래 5대 협업 규칙을 철저히 준수**해야 합니다.

---

## 📜 AI 필수 준수 5대 수칙 (Mandatory AI Rules)

### 1. 📝 사용자 질의응답 및 해결 답변의 100% 상세 문서화 (Rich Detail Rule)
* 사용자와 주고받은 모든 질의응답(Q&A), 에러 원인 분석, 펌웨어 업그레이드 절차, 파라미터 의미, 명령어를 절대 함축하거나 생략하지 말고 **풍부하고 정밀한 기술적 디테일**로 문서화한다.

### 2. 🗂️ Hardware 및 Software 다중 관련 카테고리 중복 수록 허용 (Cross-Referencing Rule)
* 센서 사양, 핀맵, 전력, 물리 배치 등은 `hardware/` 하위 문서에 작성한다.
* 드라이버, ROS 2 토픽, 파싱 노드, 동기화 스크립트 등은 `software/` 하위 문서에 작성한다.
* 하드웨어와 소프트웨어 양쪽에 관련된 주제일 경우, **내용이 중복되더라도 상관없이 관련 있는 모든 카테고리 문서에 빠짐없이 상세히 작성**한다.

### 3. 📢 루트 `README.md` 최신 업데이트 섹션 필히 반영 (Root README Mandate)
* 작업이 완료될 때마다 반드시 레포지토리 최상위 [`README.md`](../../README.md)의 **`📢 최근 핵심 업데이트 내역 (Latest Updates)`** 섹션을 업데이트한다.
* 업데이트 내역에는 **[작업 일자], [수행 개발 장비 구분 (예: knu laptop / knu desktop)], [작업 내용 요약], [수정/생성된 문서 링크]**를 빠짐없이 기재한다.

### 4. 💻 개발 환경 및 AI 이력 트래킹 리포트 저장 (Environment Audit Rule)
* 매 작업 시 [`tracking/YYYY-MM-DD-environment-audit.md`](../../tracking/) 리포트 파일을 작성하여 깃에 커밋한다.
* 리포트에는 **호스트 장비 구분(`knu laptop` 등), OS 정보, 작업 수행 AI 이름, 로컬 원본 작업 폴더 경로, 손댄 파일 내역**을 명확히 밝힌다.

### 5. 🔄 다른 AI가 즉시 작업을 이어받을 수 있는 완벽한 연속성 보장 (Seamless Continuation)
* 작업 종료 시 현재 완료된 상태, 미해결 이슈, 다음 예정 작업(예: Teltonika RUT241 LTE 라우터 유심 도착 후 NTRIP 방법 B 세팅, 라이다 PPS 시간 동기화 결선 등)을 문서에 명확히 남겨, **다른 PC나 다른 AI가 `git pull`을 받아 이 레포지토리를 열었을 때 바로 이전맥락을 이해하고 작업을 이어갈 수 있도록** 구성한다.
