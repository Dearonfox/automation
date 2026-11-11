# automation

**Verify every change before it reaches production.**

`automation`은 반도체 제조 설비의 레시피 변경을 생산 적용 전에 분석하고 검증하는
시스템입니다. 이 저장소의 모든 문서와 데이터는 **가상 시나리오 기반**이며 실제 팹
데이터나 내부 정보를 사용하지 않습니다. 시스템은 승인 권고까지만 수행하며 최종 승인은
항상 사람이 내립니다.

## 현재 구현 범위 (Phase 1)

- FastAPI 애플리케이션과 `/health`, `/api/v1/health` 엔드포인트
- 환경 변수 기반 설정 및 커밋되지 않는 `.env`
- LLM provider 추상화와 API 키가 필요 없는 결정적 `MockLLM`
- pytest 및 ruff 기본 설정

큐는 Phase 5에서 **arq**를 사용합니다. asyncio 기반 FastAPI/LangGraph 흐름과 자연스럽게
통합되고 작업 함수를 단순하게 테스트할 수 있기 때문입니다.

아직 Diff/규칙 엔진, RAG, LangGraph, 큐/worker, Slack/n8n 및 Docker Compose 통합은
구현하지 않았으며 이후 Phase에서 순서대로 추가합니다.

## 실행

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

```bash
pytest
ruff check .
```

