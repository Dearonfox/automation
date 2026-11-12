# automation

**Detect, explain, and verify process anomalies before they become yield loss.**

`automation`은 반도체 공정 센서 데이터에서 이상 가능성을 탐지하고 원인 변수를 설명한 뒤,
유사 사례를 바탕으로 조치 가이드를 제안하는 사람 중심 의사결정 지원 시스템입니다.
**공개 데이터셋 기반 프로젝트**이며 실제 팹 데이터나 내부 정보는 사용하지 않습니다.
조치는 자동 실행하지 않으며 최종 판단은 항상 사람이 내립니다.

## 데이터셋 출처

> McCann, M. & Johnston, A. (2008). SECOM [Dataset]. UCI Machine Learning Repository. [https://doi.org/10.24432/C54305](https://doi.org/10.24432/C54305). (CC BY 4.0)

원본 데이터는 자동으로 내려받지 않습니다. `data/raw/`에 `secom.data`와
`secom_labels.data`를 직접 배치해야 하며 두 파일은 Git에서 제외됩니다.

## Step 1 구현 범위

- FastAPI 설정, 헬스체크, LLM provider 추상화와 기본 `MockLLM` 유지
- UCI SECOM 피처·라벨 로딩 및 타임스탬프 파싱
- 타임스탬프 정렬 후 앞 80%/뒤 20% 순차 분할
- 학습 구간만 사용한 저분산·전체 결측 피처 제거 및 중앙값 대치
- 재현 가능한 EDA JSON 요약

아직 SPC/ML 탐지와 성능 비교, 원인 변수 추출, RAG, 조치 가이드, Slack 알림은 구현하지
않았습니다. LangGraph, 큐, 모델 라우팅은 현재 범위 밖이며 확장 계획에만 포함됩니다.

## 설치 및 실행

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m app.data.eda
pytest
ruff check .
uvicorn app.main:app --reload
```

EDA 결과는 `artifacts/eda_summary.json`에 기록됩니다. 성능 수치는 Step 2~3에서 실제 실행한
결과만 문서화합니다.

## 확장 계획

대규모·장시간 분석이 필요해질 경우 LangGraph 기반 오케스트레이션, Redis 큐 및 위험도별
모델 라우팅을 검토합니다. 현재 구현에는 포함하지 않습니다.
