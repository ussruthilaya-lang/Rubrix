import json
import numpy as np
import faiss

print("=" * 40)
print("T-06: Building FAISS index")
print("=" * 40)

# Load embeddings
embeddings = np.load("data/rubric_embeddings.npy")
print(f"✓ embeddings loaded — shape: {embeddings.shape}")

# Load rubric metadata
with open("data/rubric.json", encoding="utf-8") as f:
    rubric = json.load(f)
print(f"✓ rubric loaded — {len(rubric)} criteria")

# Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings.astype(np.float32))
print(f"✓ FAISS IndexFlatL2 built — {index.ntotal} vectors indexed")
print(f"  dimension: {dimension}")

# Save index
faiss.write_index(index, "data/rubric.index")
print("✓ index saved to data/rubric.index")

# Save metadata (maps index position back to criterion)
meta = [{"index": i, "id": c["id"], "name": c["name"], "description": c["description"]} for i, c in enumerate(rubric)]
with open("data/rubric_meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)
print("✓ metadata saved to data/rubric_meta.json")

# Smoke test — query with a known phrase
print("\n→ smoke test: querying 'evaluation methodology'...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
query = model.encode(["evaluation methodology"]).astype(np.float32)
distances, indices = index.search(query, k=3)

print("  top 3 matches:")
for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
    c = rubric[idx]
    print(f"  rank {rank+1}: {c['id']} — {c['name']} (dist={dist:.4f})")

print("\n✓ expected rank 1: C07 — Evaluation methodology")
print("=" * 40)
print("✓ T-06 complete — FAISS index ready")
print("=" * 40)