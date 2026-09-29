# 6axis

## 개념

6자유도(6-DOF) 다관절 로봇암(협동로봇)의 하드웨어 사양, 인터페이스 핀맵, 물리 설치 가이드 및 ROS 2 / 비전 기반 제어 문서와 지식베이스를 관리합니다.

## 이 폴더의 문서 및 데이터셋

- [`duco-gcr-910.md`](duco-gcr-910.md) — **Duco (Siasun) GCR5-910 / GCR7-910 6축 협동로봇 및 비전 기반 제어 가이드**
  - 물리 사양, LAN1 기가비트 이더넷 결선, 툴 플랜지 8핀 커넥터, EIO/SIO 안전 결선, 설치 체크리스트
  - ROS 2 Humble (`duco_ros_driver`), MoveIt 2 기구학 연동, 1-Click 즉시 검증 명령어 모음
  - 실전 비전 제어 5단계 로드맵 (물리 연결 $\rightarrow$ 드라이버 $\rightarrow$ MoveIt $\rightarrow$ 핸드-아이 캘리브레이션 $\rightarrow$ 비전 서보잉)
- [`duco_910_rag_dataset.xlsx`](duco_910_rag_dataset.xlsx) — **1,063건 Duco-910 전문 RAG 데이터셋 및 하드웨어 세팅 시트**
  - Sheet 1: `Duco910_RAG_KnowledgeBase` (1,063건 Q&A: API, ROS 2, 하드웨어, MoveIt, 비전 제어, 트러블슈팅, 소프트웨어 가이드 세팅)
  - Sheet 2: `Hardware_Setup_Guide` (8대 섹션 하드웨어 결선, 핀아웃, 주의사항, 커미셔닝 체크리스트)
  - Sheet 3: `Overview_and_Statistics` (도메인 통계 및 시스템 메타데이터)
