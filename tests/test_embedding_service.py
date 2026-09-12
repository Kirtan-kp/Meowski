from app.services.embedding_service import EmbeddingService


class FakeEmbeddingModel:
    def __init__(self):
        self.query_calls = 0

    def embed_query(self, text):
        self.query_calls += 1
        return [0.1, 0.2, 0.3]


class FakeCache:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ttl_seconds):
        self.data[key] = value


def test_embedding_cache_hit():
    service = EmbeddingService()

    fake_model = FakeEmbeddingModel()

    service.embedding.embedding = fake_model
    service.embedding.cache = FakeCache()

    first = service.embed_text("hello")
    second = service.embed_text("hello")

    assert first == second
    assert fake_model.query_calls == 1


def test_different_texts_are_embedded_separately():
    service = EmbeddingService()

    fake_model = FakeEmbeddingModel()

    service.embedding.embedding = fake_model
    service.embedding.cache = FakeCache()

    service.embed_text("hello")
    service.embed_text("world")

    assert fake_model.query_calls == 2


def test_embed_documents_uses_cache():
    service = EmbeddingService()

    fake_model = FakeEmbeddingModel()

    service.embedding.embedding = fake_model
    service.embedding.cache = FakeCache()

    first = service.embed_documents(["hello", "world"])
    second = service.embed_documents(["hello", "world"])

    assert first == second
    assert fake_model.query_calls == 2