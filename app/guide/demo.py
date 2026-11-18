import argparse
import json
from pathlib import Path

from app.data import load_secom, prepare_chronological_split
from app.explain import explain_sample
from app.guide import GuideService
from app.llm import create_llm
from app.rag import KnowledgeStore


async def build_demo(chroma_path: Path) -> dict[str, object]:
    prepared = prepare_chronological_split(load_secom())
    anomaly_positions = prepared.y_test[prepared.y_test == 1].index
    if anomaly_positions.empty:
        raise ValueError("The test split has no labeled anomaly for the demo")
    sample_index = anomaly_positions[0]
    normal_reference = prepared.x_train.loc[prepared.y_train.to_numpy() == -1]
    deviations = explain_sample(normal_reference, prepared.x_test.loc[sample_index], top_n=5)
    store = KnowledgeStore(chroma_path)
    indexed = store.index()
    cases = store.search(deviations, limit=3)
    guide = await GuideService(create_llm()).generate(deviations, cases)
    return {
        "sample_index": int(sample_index),
        "indexed_cases": indexed,
        "top_deviations": [item.__dict__ for item in deviations],
        "retrieved_cases": [
            {"case_id": case.case_id, "title": case.title, "distance": case.distance}
            for case in cases
        ],
        "guide": guide.model_dump(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline operator guide demo")
    parser.add_argument("--chroma-path", type=Path, default=Path("chroma_data"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/operator_guide_demo.json"))
    args = parser.parse_args()
    coroutine = build_demo(args.chroma_path)
    try:
        coroutine.send(None)
    except StopIteration as completed:
        result = completed.value
    else:
        coroutine.close()
        raise RuntimeError("Configured provider requires an async runtime")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
