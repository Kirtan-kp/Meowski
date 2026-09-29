import re
from threading import Lock
from langchain_community.retrievers import BM25Retriever


def _tokenize(text: str) -> list[str]:
    # Default BM25 tokenizer is text.split(): "Docker," != "docker". Lowercase and strip punctuation.
    return re.findall(r"\w+", text.lower())


class BM25IndexService:

    def __init__(self):
        self._indexes = {}
        self._locks = {}

    def _get_lock(self, cache_key):
        if cache_key not in self._locks:
            self._locks[cache_key] = Lock()

        return self._locks[cache_key]

    def get_or_create(
        self,
        cache_key: str,
        loader,
        k: int
    ):
        if cache_key in self._indexes:
            retriever = self._indexes[cache_key]
            retriever.k = k
            return retriever

        lock = self._get_lock(cache_key)

        with lock:
            if cache_key in self._indexes:
                retriever = self._indexes[cache_key]
                retriever.k = k
                return retriever

            documents = loader()

            if not documents:
                return None

            retriever = BM25Retriever.from_documents(documents, preprocess_func=_tokenize)
            retriever.k = k

            self._indexes[cache_key] = retriever

            return retriever

    def invalidate(self, cache_key):
        self._indexes.pop(cache_key, None)

    def invalidate_session(
        self,
        user_id: str,
        session_id: str
    ):
        self.invalidate(
            self.session_cache_key(user_id, session_id)
        )
        self.invalidate(
            self.portfolio_session_cache_key(user_id, session_id)
        )

    @staticmethod
    def session_cache_key(
        user_id: str,
        session_id: str
    ):
        return f"session:{user_id}:{session_id}"

    @staticmethod
    def portfolio_session_cache_key(user_id, session_id):
        return f"portfolio+session:{user_id}:{session_id}"

    @staticmethod
    def portfolio_cache_key():
        return "portfolio"