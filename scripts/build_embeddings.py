import json
import numpy as np
from sentence_transformers import SentenceTransformer

print("=" * 40)
print("T-05: Building rubric embeddings")
print("=" * 40)

# Load rubric
with open("data/rubric.json", encoding="utf-8") as f:
    rubric = json.load(f)
print(f"✓ rubric loaded — {len(rubric)} criteria")

# Load model
print("→ loading model: all-MiniLM-L6-v2")
print("  (first run downloads ~90MB — wait for it)")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✓ model loaded")

# Embed all criterion descriptions
print("→ embedding 20 criteria...")
descriptions = [c["description"] for c in rubric]
embeddings = model.encode(descriptions, show_progress_bar=True)

print(f"✓ embeddings shape: {embeddings.shape}")
print(f"✓ expected shape:   (20, 384)")

# Verify unit vectors
norms = np.linalg.norm(embeddings, axis=1)
print(f"✓ mean norm: {norms.mean():.4f} (should be close to 1.0)")

# Save embeddings
np.save("data/rubric_embeddings.npy", embeddings)
print("✓ saved to data/rubric_embeddings.npy")
print("=" * 40)
print("✓ T-05 complete — ready to build FAISS index")
print("=" * 40)