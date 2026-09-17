from app.graph.nodes import generate_node


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return "Generated answer"


class FakeCache:
    def __init__(self, cached_answer=None):
        self.cached_answer = cached_answer
        self.set_calls = 0

    def get(self, **kwargs):
        return self.cached_answer

    def set(self, **kwargs):
        self.set_calls += 1


class FakeCacheService:
    def __init__(self, cache):
        self.cache = cache

    def get(self, **kwargs):
        return self.cache.get(**kwargs)

    def set(self, **kwargs):
        self.cache.set(**kwargs)


class FakePrompt:
    def __or__(self, llm):
        return FakeChain(llm)


class FakeChain:
    def __init__(self, llm):
        self.llm = llm

    def __or__(self, parser):
        return self

    def invoke(self, data):
        return self.llm.invoke(data)


def create_state():
    return {
        "question": "What does Kirtan work on?",
        "documents": [
            {
                "page_content": "Kirtan works on AI and machine learning.",
                "metadata": {
                    "scope": "portfolio",
                    "file_id": "file_1",
                },
            }
        ],
        "retry_count": 0,
        "chat_history": [],
        "user_id": "user_1",
        "session_id": "session_1",
    }


def test_generate_node_calls_llm_on_cache_miss(monkeypatch):

    fake_llm = FakeLLM()
    fake_cache = FakeCache(cached_answer=None)

    monkeypatch.setattr(
        "app.graph.nodes.LLMCacheService",
        lambda: FakeCacheService(fake_cache),
    )

    result = generate_node(
        state=create_state(),
        prompt=FakePrompt(),
        llm=fake_llm,
    )

    assert result["answer"] == "Generated answer"
    assert fake_llm.calls == 1
    assert fake_cache.set_calls == 1


def test_generate_node_skips_llm_on_cache_hit(monkeypatch):

    fake_llm = FakeLLM()
    fake_cache = FakeCache(cached_answer="Cached answer")

    monkeypatch.setattr(
        "app.graph.nodes.LLMCacheService",
        lambda: FakeCacheService(fake_cache),
    )

    result = generate_node(
        state=create_state(),
        prompt=FakePrompt(),
        llm=fake_llm,
    )

    assert result["answer"] == "Cached answer"
    assert fake_llm.calls == 0
    assert fake_cache.set_calls == 0