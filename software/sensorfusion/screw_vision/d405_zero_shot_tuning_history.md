# 🔍 Intel RealSense D405 제로샷 나사 비전 개발 및 트러블슈팅 히스토리

본 문서는 **방법 1 (Zero-Shot Precision Geometric Measurement)** 엔진 개발 과정에서 발생한 오인식 및 예외 상황의 기술적 원인과, 이를 해결하기 위해 단계별로 적용한 핵심 알고리즘 수정 내역을 상세히 기록합니다.

---

## 📌 1. 전체 트러블슈팅 요약 표

| 단계 | 발생 증상 (Symptom) | 기술적 근본 원인 (Root Cause) | 적용 해결책 (Resolution) | 비고 |
| :---: | :--- | :--- | :--- | :---: |
| **Phase 1** | `cv2.imshow` 실행 시 GTK/Cocoa 구현 에러로 프로세스 크래시 | `opencv-python-headless 4.12`가 설치되어 GUI 모듈(`highgui`)을 덮어씀 | `pip uninstall -y opencv-python-headless` 실행, GUI 패키지 복원 | 환경 복구 |
| **Phase 2** | 전역 반전 이진화 시 검은 책상 전체가 흰색으로 덮이며 나사가 감춰짐 | 어두운 책상(명도 ~17)이 검은 나사와 동일 명도이며, 외곽 컨투어가 나사를 집어삼킴 | **2단계 계층형 세그멘테이션**: 흰 패드 검출 후 패드 내부 영역에서만 나사 추출 | ROI 격리 |
| **Phase 3** | 나사 폭이 $7\text{ mm}$에서 $13 \sim 14\text{ mm}$로 2배 부풀려져 측정됨 | CLAHE(적응형 대비 균등화)가 흰 완충재에 드리운 미세한 소프트 그림자를 진한 검은색으로 증폭 | 검은 나사 모드에서 **CLAHE 우회**, 가우시안 블러 후 직접 이진화 적용 | 치수 정상화 |
| **Phase 4** | 폼 매트 외곽 경계선 찌꺼기가 전장 $191\text{ mm}$의 거대 나사로 오인식 | 패드와 어두운 책상이 만나는 경계면에 계단형 윤곽선 노이즈 생성 | **형태학적 침식 (Morphological Erosion)**: 폼 패드 마스크를 15px 축소하여 경계 원천 배제 | 경계 노이즈 제거 |
| **Phase 5** | 패드 중앙 원형 관통홀(직경 $\approx 18.6\text{ mm}$)이 나사로 오인식 | 홀 내부의 검은 음영이 나사와 동일한 검은색 객체로 검출됨 | **물리적 면적 필터 ($Area_{\text{mm}^2}$)**: 나사 면적($60 \sim 80\text{ mm}^2$)과 홀 면적($236\text{ mm}^2$) 분리 | 홀 오인식 차단 |
| **Phase 6** | 프로세스 재시작 시 USB 엔드포인트 잠김으로 `wait_for_frames` 타임아웃 | 이전 파이프라인 정지 누락으로 USB 버스 상에서 RealSense 노드가 먹통 | `dev.hardware_reset()` 기반 **USB 자동 하드웨어 리셋 및 재시도 로직** 내장 | 상시 안정성 |

---

## 🛠️ 2. 단계별 세부 원인 분석 및 수정 코드

### 1단계: GUI 크래시 해결 (`opencv-python-headless` 충돌)
* **원인**: 시스템에 `opencv-python-headless 4.12.0.88`, `opencv-contrib-python 4.11.0.86`, `opencv-python 4.10.0.84`가 혼재되어 있었으며, 파이썬 인터프리터가 GUI 창 생성 함수(`cvShowImage`)가 제거된 headless 패키지를 우선 로드함.
* **해결**:
  ```bash
  pip uninstall -y opencv-python-headless
  ```

---

### 2단계: 배경 반전 이진화 삼킴 현상 해결 (2단계 ROI 분리)
* **원인**:
  - 검은색 책상 표면 명도: `~17` (Gray)
  - 검은색 볼트 명도: `~17` (Gray)
  - 흰색 완충 패드 명도: `~142` (Gray)
  - 전역 이미지에 `THRESH_BINARY_INV`를 적용하면 책상 전체가 `255(흰색)`로 바뀌고 흰 패드는 `0(검은색 구멍)`이 됨. `cv2.RETR_EXTERNAL`을 사용하면 책상 전체 외곽선만 잡혀 패드 안의 나사가 외곽선에 먹혀 검출되지 않음.
* **해결 코드 (`screw_detector_d405.py`)**:
  ```python
  # 1. 밝은 영역(흰 완충 패드) 먼저 검출
  pad_mask = (blurred > 70).astype(np.uint8) * 255
  pad_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
  pad_filled = cv2.morphologyEx(pad_mask, cv2.MORPH_CLOSE, pad_kernel)

  # 2. 패드 내부 마스크 안에서만 검은색 나사 추출
  screw_mask = np.zeros_like(gray)
  screw_mask[(blurred < thresh_val) & (pad_filled > 0)] = 255
  ```

---

### 3단계: 그림자 왜곡 현상 제거 (CLAHE 비활성화)
* **원인**:
  - 은색 금속 볼트는 빛 반사(Specular Glare)가 심해 CLAHE(대비 제한 적응형 히스토그램 균등화)가 필수적임.
  - 하지만 **흰색 폼 매트 위의 검은색 산화피막 볼트**의 경우, 주변 조명으로 인해 볼트 주위에 옅은 회색 그림자(명도 ~50-60)가 생김.
  - CLAHE를 거치면서 $8 \times 8$ 타일 국소 대비 증폭으로 인해 이 옅은 그림자가 진한 검은색으로 증폭되어 나사 폭이 $7.0\text{ mm}$에서 $13.6\text{ mm}$로 왜곡됨.
* **해결**:
  - 검은 나사 모드에서는 CLAHE를 적용하지 않고 가우시안 블러 필터링된 원본 그레이스케일에서 직접 임계값을 적용하여 순수 볼트 단면만 추출.

---

### 4단계: 폼 매트 외곽선 및 관통홀 오인식 완벽 차단
* **원인**:
  1. 흰 패드 외곽선과 검은 책상이 만나는 경계선에 픽셀 단절이 발생하여 최대 길이 $191\text{ mm}$의 비정상 컨투어가 생성됨.
  2. 패드 중앙에 뚫린 원형 홀(직경 약 $18.6\text{ mm}$)이 검은색 객체로 인식되어 나사로 오분류됨.
* **해결 알고리즘 (2중 안전 필터)**:
  1. **폼 패드 침식 마스킹**:
     ```python
     # 폼 패드 외곽 윤곽선을 구한 뒤 15픽셀을 깎아내어(침식) 경계선 노이즈 원천 차단
     c_foam = max(pad_cnts, key=cv2.contourArea)
     foam_canvas = np.zeros_like(gray)
     cv2.drawContours(foam_canvas, [c_foam], -1, 255, -1)
     foam_canvas = cv2.erode(foam_canvas, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
     ```
  2. **물리적 면적 역변환 필터 ($Area_{\text{mm}^2}$)**:
     - 카메라 깊이($Z$)와 초점거리($f_x$)를 이용해 픽셀 면적을 실제 $\text{mm}^2$ 단위로 변환:
       $$Area_{\text{mm}^2} = Area_{\text{px}} \times \left(\frac{Z}{f_x}\right)^2$$
     - 실측 면적:
       - **M4 x 20mm 볼트 실측 면적**: **$66 \sim 80\text{ mm}^2$**
       - **중앙 관통홀 실측 면적**: **$236.4\text{ mm}^2$** (원형 직경 $\approx 18.6\text{ mm}$)
       - **이물질/먼지**: **$< 15\text{ mm}^2$**
     - 필터 조건: $20.0\text{ mm}^2 \le Area \le 130.0\text{ mm}^2$ 적용으로 중앙 홀 및 초소형 노이즈 100% 제거.
  3. **ISO 4762 / DIN 912 물리 치수 상한선 검증**:
     ```python
     # M3/M4 규격을 벗어나는 거대 객체 및 극소 객체 기각
     if head_dia_mm > 9.0 or tot_l_mm > 42.0 or tot_l_mm < 6.0:
         continue
     ```

---

## 📊 3. 최종 검증 결과 (7개 M4 볼트 완벽 검출)

* **FPS**: **$30.0\text{ FPS}$** (실시간 유지)
* **검출 개수**: M3 = 0개, **M4 = 7개 (100% 검출, 오인식 0건)**
* **실측 치수 일치도**:
  - 공칭 머리 외경 $7.0\text{ mm}$ $\rightarrow$ 센서 계측 **$6.97 \sim 7.70\text{ mm}$**
  - 공칭 바디 외경 $4.0\text{ mm}$ $\rightarrow$ 센서 계측 **$3.92 \sim 4.43\text{ mm}$**
  - 공칭 전장 $20.0\text{ mm}$ $\rightarrow$ 센서 계측 **$18.3 \sim 19.8\text{ mm}$**
* **자가 검증 수단**: 로컬 웹 텔레메트리 뷰어([`http://localhost:5000`](http://localhost:5000)) 탑재 완료.
