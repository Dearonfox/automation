from dataclasses import dataclass
from pathlib import Path

import chromadb

from app.explain import SensorDeviation
from app.rag.embedding import HashEmbedding
from app.rag.knowledge import KnowledgeCase, load_knowledge_cases


@dataclass(frozen=True)
class RetrievedCase:
    case_id: str
    title: str
    distance: float
    document: str


class KnowledgeStore:
    def __init__(self, path: Path = Path("chroma_data"), collection_name: str = "operator_cases"):
        self.embedding = HashEmbedding()
        self.client = chromadb.PersistentClient(path=str(path))
        self.collection = self.client.get_or_create_collection(
            collection_name, metadata={"hnsw:space": "cosine"}
        )

    def index(self, cases: list[KnowledgeCase] | None = None) -> int:
        resolved = cases or load_knowledge_cases()
        documents = [case.document for case in resolved]
        self.collection.upsert(
            ids=[case.case_id for case in resolved],
            documents=documents,
            embeddings=self.embedding.embed(documents),
            metadatas=[{"title": case.title, "synthetic": True} for case in resolved],
        )
        return len(resolved)

    def search(self, deviations: list[SensorDeviation], *, limit: int = 3) -> list[RetrievedCase]:
        if not deviations:
            raise ValueError("At least one sensor deviation is required")
        if limit < 1:
            raise ValueError("limit must be at least 1")
        query = " ".join(
            f"{item.sensor} 편차 {item.z_score:.2f} 표준편차" for item in deviations
        )
        result = self.collection.query(
            query_embeddings=self.embedding.embed([query]),
            n_results=min(limit, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        return [
            RetrievedCase(
                case_id=case_id,
                title=str(metadata["title"]),
                distance=float(distance),
                document=document,
            )
            for case_id, document, metadata, distance in zip(
                ids, documents, metadatas, distances, strict=True
            )
        ]
