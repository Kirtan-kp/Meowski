import asyncio

from app.llm.resilient import ProviderRouter


class FakeProvider:
    def __init__(self, value=None, error=None):
        self.value = value
        self.error = error
        self.calls = 0

    def invoke(self, input, config=None, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.value

    async def ainvoke(self, input, config=None, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.value


class FakeBreaker:
    def __init__(self):
        self.calls = []

    def before_call(self, provider):
        self.calls.append(("before", provider))

    def record_success(self, provider):
        self.calls.append(("success", provider))

    def record_failure(self, provider):
        self.calls.append(("failure", provider))


def test_router_falls_back_after_provider_failure():
    primary = FakeProvider(error=RuntimeError("down"))
    fallback = FakeProvider(value="fallback")
    breaker = FakeBreaker()

    router = ProviderRouter(
        [("groq", primary), ("ollama", fallback)],
        breaker=breaker,
    )

    assert router.invoke("hello") == "fallback"
    assert primary.calls == 1
    assert fallback.calls == 1
    assert ("failure", "groq") in breaker.calls
    assert ("success", "ollama") in breaker.calls


def test_router_async_fallback():
    primary = FakeProvider(error=RuntimeError("down"))
    fallback = FakeProvider(value="fallback")
    router = ProviderRouter(
        [("groq", primary), ("ollama", fallback)],
        breaker=FakeBreaker(),
    )

    assert asyncio.run(router.ainvoke("hello")) == "fallback"
