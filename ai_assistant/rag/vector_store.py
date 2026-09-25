import os
import json
import math
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
STORE_PATH = "data/vector_store.json"


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two vectors."""
    if len(v1) != len(v2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class SimpleVectorStore:
    """Persistent local Vector Store with native Python Cosine Similarity search."""
    
    def __init__(self, file_path: str = STORE_PATH):
        self.file_path = file_path
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        self.load()

    def load(self) -> None:
        """Loads index from disk."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading vector store file: {str(e)}")
                self.data = {}
        else:
            self.data = {}

    def save(self) -> None:
        """Saves index to disk."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving vector store file: {str(e)}")

    def add_lecture_chunks(self, lecture_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        """Indexes a set of chunks and their embedding vectors for a lecture."""
        self.data[lecture_id] = [
            {"chunk": chunk, "embedding": emb}
            for chunk, emb in zip(chunks, embeddings)
        ]
        self.save()

    def is_lecture_indexed(self, lecture_id: str) -> bool:
        """Checks if a lecture has already been vectorized and indexed."""
        return lecture_id in self.data and len(self.data[lecture_id]) > 0

    def query(self, lecture_id: str, query_emb: List[float], top_k: int = 3) -> List[str]:
        """Queries the store for the top K most similar lecture chunks."""
        if lecture_id not in self.data:
            return []

        scored_chunks = []
        for item in self.data[lecture_id]:
            sim = cosine_similarity(query_emb, item["embedding"])
            scored_chunks.append((item["chunk"], sim))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored_chunks[:top_k]]


# Singleton vector store instance
vector_store = SimpleVectorStore()
