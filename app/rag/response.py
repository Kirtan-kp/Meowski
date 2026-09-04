from app.schemas.retrieval import RetrievalResponse,Source

def build_rag_response(result) -> RetrievalResponse:

    sources = [Source(content = document["page_content"] , metadata = document["metadata"]) for document in result["documents"]]

    return RetrievalResponse(answer = result["answer"] , sources = sources)