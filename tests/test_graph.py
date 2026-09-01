from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.providers.groq import GroqLLM
from app.rag.prompt import RAG_PROMPT
from app.graph.graph import create_rag_graph
from app.rag.response import build_rag_response

vector_store = QdrantVectorStore(embedding_dimension = 384)

user_filter = Filter(
    must=[
        FieldCondition(
            key="metadata.user_id",
            match=MatchValue(value="user_1")
        ),
        FieldCondition(
            key="metadata.session_id",
            match=MatchValue(value="session_1")
        )
    ]
)

llm = GroqLLM()

retriever = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , k = 10 , 
                                      top_n = 3 , search_type = "mmr" , filter = user_filter)

rag_graph = create_rag_graph(retriever = retriever , llm = llm.llm , prompt = RAG_PROMPT)

questions = ["What projects has Kirtan worked on?" , "Which one involved computer vision?" , "What was the purpose of that project?"]

config = {"configurable" : {"thread_id" : "test_session_1"}}

for question in questions:
    result = rag_graph.invoke({"question" : question , "retry_count" : 0} , config = config)

    response = build_rag_response(result)

    print("\nQUESTION:")
    print(question)

    print("\nREWRITTEN QUESTION:")
    print(result.get("rewritten_question", "None"))

    print("\nANSWER:")
    print(response.answer)

    print("\nSOURCES:")

    for source in response.sources:

        print("\nCONTENT:")
        print(source.content)

        print("\nMETADATA:")
        print(source.metadata)