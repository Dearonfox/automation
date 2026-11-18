import argparse
from pathlib import Path

from app.rag.store import KnowledgeStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Index synthetic operator cases in Chroma")
    parser.add_argument("--path", type=Path, default=Path("chroma_data"))
    args = parser.parse_args()
    count = KnowledgeStore(args.path).index()
    print(f"Indexed {count} synthetic cases in {args.path}")


if __name__ == "__main__":
    main()
