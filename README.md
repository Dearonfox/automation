# automation

## Operator 중심 Step 3 조정

프로젝트의 중심은 작업자가 이상 알림을 확인하고 점검 내용을 기록·보고하며,
미처리 사항을 다음 근무자에게 전달하도록 지원하는 것입니다.
ML 비교는 참고 평가로 유지하며 운영 모델을 자동 선정하지 않습니다.

- 첫 화면: 미확인 알림, 점검 중, 보고 초안 준비, 인계 대상 건수
- 가상 알림 3건: 확인 → 점검 체크리스트 → 관찰 기록 → 보고 초안 준비
- 필수 확인 항목과 관찰 내용·보고 대상이 없으면 초안 준비 차단
- 기록 수정 후 보고 초안 재검토, 시간별 작업 이력 및 인수인계 텍스트 다운로드
- 브라우저 localStorage 저장: 서버 DB, 실제 보고 전송, 사용자 인증, 승인 기능은 미구현

가상 업무 데이터는 SECOM의 실제 설비·교대·작업 이력이 아닙니다.
체크리스트는 실제 팹 표준작업서가 아닌 데모용 절차입니다.
이전의 가상 센서 점수 차트와 원인 순위는 제거했습니다.
실제 모델 비교 수치는 접힌 참고 패널에 표시하며 실시간 값은 아닙니다.

실행: `uvicorn app.main:app --reload` 후 `http://127.0.0.1:8000/` 접속.
가상 알림을 선택해 확인, 필수 항목 입력, 초안 준비, 새로고침 후 기록 복원,
인수인계 다운로드 순으로 데모를 진행합니다.

**Detect, explain, and verify process anomalies before they become yield loss.**

`automation`은 반도체 공정 센서 데이터에서 이상 가능성을 탐지하고 원인 변수를 설명한 뒤,
유사 사례를 바탕으로 조치 가이드를 제안하는 사람 중심 의사결정 지원 시스템입니다.
**공개 데이터셋 기반 프로젝트**이며 실제 팹 데이터나 내부 정보는 사용하지 않습니다.
조치는 자동 실행하지 않으며 최종 판단은 항상 사람이 내립니다.

## 문제 정의와 접근

Operator가 공정 이상 알림을 확인할 때 센서 데이터, 분석 근거, 과거 참고 사례가 흩어져
있으면 점검 누락과 인수인계 공백이 생길 수 있습니다. 이 프로젝트는 시간순 데이터 분할로
SPC와 ML 이상 탐지를 비교하고, 익명 센서 편차와 가상 유사 사례를 찾아 점검·보고 초안을
만든 뒤, 작업자의 확인 상태와 이력을 저장하는 하나의 업무 흐름으로 구성했습니다.

## 데이터셋 출처

> McCann, M. & Johnston, A. (2008). SECOM [Dataset]. UCI Machine Learning Repository. [https://doi.org/10.24432/C54305](https://doi.org/10.24432/C54305). (CC BY 4.0)

원본 데이터는 자동으로 내려받지 않습니다. `data/raw/`에 `secom.data`와
`secom_labels.data`를 직접 배치해야 하며 두 파일은 Git에서 제외됩니다.

## 구현한 것 (Step 1~5)

- FastAPI 설정, 헬스체크, LLM provider 추상화와 기본 `MockLLM` 유지
- UCI SECOM 피처·라벨 로딩 및 타임스탬프 파싱
- 타임스탬프 정렬 후 앞 80%/뒤 20% 순차 분할
- 학습 구간만 사용한 저분산·전체 결측 피처 제거 및 중앙값 대치
- 재현 가능한 EDA JSON 요약
- 학습 구간의 정상 샘플만으로 적합하는 센서별 평균±3σ SPC baseline
- precision, recall, F1, 오탐률 및 confusion matrix 항목 평가
- 비지도 `IsolationForest`, `OneClassSVM`과 지도 `RandomForest` 비교
- 학습 구간 내부의 시간순 검증 구간으로 RandomForest 판정 임계값 보정
- 실제 업무용 콘솔 형태의 반응형 웹 대시보드 (`/`)
- 정상 학습 구간 대비 절대 z-score 기반 상위 센서 편차 추출
- 가상 Operator 점검 사례 15건과 Chroma 로컬 검색
- 외부 모델 다운로드가 없는 결정적 해시 임베딩
- 고정 JSON 스키마의 점검·보고 초안과 기본 `MockLLM`
- `POST /api/v1/analyze` 실제 분석 API와 결과 조회 API
- SQLite 분석 이력과 작업자 상태 전이 기록
- 실제 SECOM 테스트 샘플을 실행하는 Operator 대시보드
- 이상 판정 시 선택적으로 전송하는 Slack Incoming Webhook

Slack은 n8n보다 설정과 실행 경로가 단순한 Incoming Webhook을 선택했습니다. URL이 설정되지
않으면 알림을 건너뛰므로 API 키 없이 전체 파이프라인과 테스트가 동작합니다.

## 아직 구현하지 않은 것

- Slack 확인/반려 버튼과 Slack 서명 검증
- 사용자 인증·권한 관리와 실제 담당자 계정 연동
- 실제 팹 표준작업서, 설비 제어, 생산 중단·재개 승인
- 운영 모델 자동 재학습과 모델·데이터 드리프트 감시
- LangGraph, 큐, 모델 라우팅

## Step 4: Operator 점검·보고 초안

익명 센서의 물리적 의미나 고장 원인을 추정하지 않습니다. 상위 편차 센서와 가상 유사
사례를 근거로 확인할 항목과 보고 초안을 만들며, 설비 조작이나 생산 재개를 지시하지
않습니다. 출력의 `requires_human_confirmation`은 항상 `true`여야 하고 검색된 사례 ID가
출력 근거와 정확히 일치하지 않으면 실패합니다.

`data/knowledge/`의 15개 문서는 모두 가상 사례입니다. Chroma에는 외부 임베딩 모델 대신
결정적 로컬 해시 벡터를 명시적으로 전달하므로 API 키와 모델 다운로드가 필요 없습니다.

## Step 5: API와 작업 이력

- `POST /api/v1/analyze`: 테스트 행 번호 또는 전처리된 468개 센서 맵 분석
- `GET /api/v1/analyses/{id}`: 분석 결과와 작업 이력 조회
- `POST /api/v1/analyses/{id}/actions`: 확인·보고 초안·기록 확인·반려 상태 기록

모든 분석은 `review_required`로 시작합니다. `confirmed`는 기록 확인 완료 상태이며 생산 재개나
설비 조작을 승인하지 않습니다. 모든 API 응답에 `does_not_authorize_production: true`를
포함합니다. SQLite 경로는 `DATABASE_PATH`, Chroma 경로는 `CHROMA_PATH`, 선택적 Slack
Webhook은 `SLACK_WEBHOOK_URL`로 설정합니다.

## Baseline vs ML 실제 성능 비교

실제 SECOM 테스트 구간 314건에서 실행한 결과입니다. 이상 샘플은 양성(`1`)으로
평가했으며 테스트 구간은 모델 적합이나 임계값 선택에 사용하지 않았습니다.

| 모델 | Precision | Recall | F1 | 오탐률 |
|---|---:|---:|---:|---:|
| SPC 평균±3σ | 0.0519 | 0.9412 | 0.0985 | 0.9832 |
| IsolationForest | 0.0323 | 0.1176 | 0.0506 | 0.2020 |
| OneClassSVM | 0.0000 | 0.0000 | 0.0000 | 0.0774 |
| RandomForest | 0.1333 | 0.1176 | 0.1250 | 0.0438 |

센서 468개 중 하나라도 관리한계를 벗어나면 이상으로 판정하는 보수적인 규칙이라 recall은
높지만 다중 센서 비교의 영향으로 오탐률이 매우 높습니다. RandomForest는 F1과 오탐률을
개선했지만 재현율이 낮아 실제 운영 수준에는 미달합니다. OneClassSVM은 이 설정에서 실제
이상을 탐지하지 못했으며, 이 실패 결과도 그대로 기록했습니다.

## 설치 및 실행

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m app.data.eda
python -m app.evaluation.baseline
python -m app.evaluation.compare
python -m app.rag.indexer
python -m app.guide.demo
pytest
ruff check .
uvicorn app.main:app --reload
```

서버 실행 후 `http://127.0.0.1:8000/`에서 대시보드를, `/docs`에서 API 문서를 확인할 수
있습니다. 대시보드의 작업 기록은 가상 데모이며, 모델 참고 패널은 실제 Step 3 비교 결과입니다.
브라우저 기록은 다른 기기와 공유되지 않으며 저장 공간 삭제 시 사라집니다.
실제 분석 결과와 상태 이력은 SQLite에 저장됩니다. 대시보드의 “샘플 분석 실행”은 공개
테스트 구간의 실제 이상 라벨이면서 RandomForest가 이상으로 판정한 샘플 `1363`을 사용합니다.

EDA 결과는 `artifacts/eda_summary.json`, SPC 결과는 `artifacts/spc_baseline_metrics.json`,
전체 비교 결과는 `artifacts/model_comparison.json`에 기록됩니다. 위 성능 수치는 모두 실제
실행 결과입니다.

Step 4 데모 결과는 `artifacts/operator_guide_demo.json`에 기록됩니다. 데모는 테스트 구간의
첫 번째 이상 라벨 샘플을 사용하며 실제 팹 조치나 표준작업서가 아닙니다.

## 한계

- UCI SECOM은 실제 SK하이닉스 팹 데이터가 아니며 센서 의미가 익명화돼 있습니다.
- RandomForest 재현율은 0.1176으로 실제 이상 17건 중 2건만 탐지했습니다.
- SPC는 재현율이 높지만 오탐률이 0.9832여서 운영 경보로 사용하기 어렵습니다.
- 가상 사례와 체크리스트는 실제 현장 표준작업서가 아닙니다.
- 로컬 해시 임베딩은 오프라인 재현성을 위한 간단한 검색 기준이며 의미 검색 품질에 한계가 있습니다.
- SQLite와 단일 프로세스 모델 캐시는 로컬 데모용이며 다중 사용자 운영 구성이 아닙니다.

## 확장 계획

대규모·장시간 분석이 필요해질 경우 Redis 큐와 비동기 worker, 모델·데이터 드리프트 감시,
실제 인증·권한 관리, 승인된 표준작업서 연동을 검토합니다.
