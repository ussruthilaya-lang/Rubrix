import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Module-level globals — loaded once, reused across calls
_model = None
_index = None
_meta = None


def _load_resources():
    global _model, _index, _meta

    if _model is None:
        print("  [retrieval] loading sentence transformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("  [retrieval] model loaded")

    if _index is None:
        _index = faiss.read_index("data/rubric.index")
        print(f"  [retrieval] FAISS index loaded — {_index.ntotal} vectors")

    if _meta is None:
        with open("data/rubric_meta.json", encoding="utf-8") as f:
            _meta = json.load(f)
        print(f"  [retrieval] metadata loaded — {len(_meta)} criteria")


def retrieve_top_k(query_text: str, k: int = 5) -> list:
    """
    Embed query_text and return top-k matching criteria from the rubric.

    Returns a list of dicts:
        [{"rank": 1, "id": "C07", "name": "...", "description": "...", "distance": 0.63}, ...]
    """
    _load_resources()

    print(f"  [retrieval] querying: '{query_text[:60]}...' " if len(query_text) > 60 else f"  [retrieval] querying: '{query_text}'")

    query_vec = _model.encode([query_text]).astype(np.float32)
    distances, indices = _index.search(query_vec, k=k)

    results = []
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
        entry = _meta[idx]
        results.append({
            "rank": rank + 1,
            "id": entry["id"],
            "name": entry["name"],
            "description": entry["description"],
            "distance": round(float(dist), 4)
        })
        print(f"  [retrieval] rank {rank+1}: {entry['id']} — {entry['name']} (dist={dist:.4f})")

    return results


if __name__ == "__main__":
    print("=" * 40)
    print("T-07: Testing retrieval function")
    print("=" * 40)

    test_queries = [
        "baseline comparison",
        "we evaluated using accuracy and F1 score",
        "the dataset contains 10000 samples split 80/20",
        "future research could explore larger models",
        "ethical implications of using patient data"
    ]

    for query in test_queries:
        print(f"\n→ query: '{query}'")
        results = retrieve_top_k(query, k=3)
        print(f"  top match: {results[0]['id']} — {results[0]['name']}")

    print("\n" + "=" * 40)
    print("✓ T-07 complete — retrieval function ready")
    print("=" * 40)