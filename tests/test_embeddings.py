from app.services.embedding_service import EmbeddingService

embedding_service = EmbeddingService()

# text = "I built a machine learning project."

# vector = embedding_service.embed_text(text)

# print("Vector length:", len(vector))
# print("First 10 values:", vector[:10])
texts = [
    "I built a machine learning project.",
    "I developed an artificial intelligence application.",
    "I cooked pasta for dinner."
]

vectors = embedding_service.embed_documents(texts)

print("Number of vectors:", len(vectors))

for vector in vectors:
    print("Dimension:", len(vector))