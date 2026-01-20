"""
Proof of Concept: Sentence Transformers embedding generation
Validates: Model downloads and generates embeddings
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import time

print("✓ Loading model...")
start = time.time()
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
load_time = time.time() - start
print(f"  Model loaded in {load_time:.2f}s")

print("\n✓ Generating embeddings...")
texts = [
    "How do I store memories in the database?",
    "What is the best way to save data?",
    "Python programming tutorial",
]

start = time.time()
embeddings = model.encode(texts, show_progress_bar=False)
embed_time = time.time() - start

print(f"  Generated {len(embeddings)} embeddings in {embed_time:.2f}s")
print(f"  Embedding dimensions: {embeddings.shape[1]}")

# Test similarity
print("\n✓ Testing similarity...")
from sklearn.metrics.pairwise import cosine_similarity

similarities = cosine_similarity([embeddings[0]], embeddings)[0]
print(f"  Query: '{texts[0]}'")
for i, (text, sim) in enumerate(zip(texts, similarities)):
    print(f"    {i+1}. {text[:40]:40s} | Similarity: {sim:.3f}")

if similarities[1] > 0.5:
    print("\n✅ Embedding test passed! Semantically similar texts detected.")
else:
    print("\n⚠️  Warning: Similarity lower than expected")
