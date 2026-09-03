import asyncio
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.providers.groq import GroqLLM
from openai import AsyncOpenAI
from app.rag.prompt import RAG_PROMPT
from app.rag.chain import create_rag_chain
from app.rag.response import build_rag_response
from tests.evaluation_dataset import EVALUATION_DATASET
from ragas.llms import llm_factory
from app.core.config import settings
from ragas.metrics.collections import Faithfulness,AnswerRelevancy,ContextPrecision
from langchain_core.documents import Document
from ragas.embeddings import embedding_factory

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

documents = [
    Document(
        page_content="Kirtan built an anime face generation project.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "doc_1",
            "filename": "test.txt",
            "chunk_index": 0
        }
    ),
    Document(
        page_content="Kirtan worked on machine learning and computer vision.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "doc_1",
            "filename": "test.txt",
            "chunk_index": 1
        }
    ),
    Document(
        page_content="Kirtan developed a license plate recognition system.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "doc_1",
            "filename": "test.txt",
            "chunk_index": 2
        }
    ),
    Document(
        page_content="Kirtan enjoys playing video games.",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1",
            "document_id": "doc_1",
            "filename": "test.txt",
            "chunk_index": 3
        }
    )
]

vector_store.add_documents(documents)

llm = GroqLLM()

ragas_client = AsyncOpenAI(api_key = settings.llm_api_key , base_url = "https://api.groq.com/openai/v1")
 
ragas_llm = llm_factory(model = settings.llm_model , provider = "openai" , client = ragas_client , adapter = "instructor")

ragas_embeddings = embedding_factory(provider = "huggingface" , model = settings.embedding_model , interface = "modern")

retriever = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , k = 10 , top_n = 3 , search_type = "mmr" , 
                                      filter = user_filter)

rag_chain = create_rag_chain(retriever = retriever , llm = llm.llm , prompt = RAG_PROMPT)

faithfulness_metric = Faithfulness(llm = ragas_llm)

answer_relevancy_metric = AnswerRelevancy(llm = ragas_llm , embeddings = ragas_embeddings)

context_precision_metric = ContextPrecision(llm = ragas_llm)

async def evaluate_question(question , reference):

    result = rag_chain.invoke(question)
    response = build_rag_response(result)
    contexts = [
        source.content
        for source in response.sources
    ]

    faithfulness_result = await faithfulness_metric.ascore(user_input = question , response = response.answer , retrieved_contexts = contexts)

    answer_relevancy_result = await answer_relevancy_metric.ascore(user_input = question , response =  response.answer)

    context_precision_result = await context_precision_metric.ascore(user_input = question , retrieved_contexts = contexts , reference = reference)

    return (response , faithfulness_result , answer_relevancy_result , context_precision_result)


async def main():

    total_faithfulness = 0.0
    total_answer_relevancy = 0.0
    total_context_precision = 0.0

    count = len(EVALUATION_DATASET)
    print("\n================ RAGAS EVALUATION ================\n")
    for item in EVALUATION_DATASET:

        question = item["question"]

        (
            response,
            faithfulness,
            answer_relevancy,
            context_precision
        ) = await evaluate_question(question, item["reference"])

        total_faithfulness += faithfulness.value
        total_answer_relevancy += answer_relevancy.value
        total_context_precision += context_precision.value

        print(f"QUESTION: {question}")

        print("\nANSWER:")
        print(response.answer)

        print("\nRETRIEVED CONTEXTS:")

        for source in response.sources:
            print(f"- {source.content}")

        print(
            f"\nFaithfulness: "
            f"{faithfulness.value:.2f}"
        )

        print(
            f"Answer Relevancy: "
            f"{answer_relevancy.value:.2f}"
        )

        print(
            f"Context Precision: "
            f"{context_precision.value:.2f}"
        )

        print("\n" + "-" * 55)

    print("\n================ AVERAGE =================\n")

    print(
        f"Average Faithfulness: "
        f"{total_faithfulness / count:.2f}"
    )

    print(
        f"Average Answer Relevancy: "
        f"{total_answer_relevancy / count:.2f}"
    )

    print(
        f"Average Context Precision: "
        f"{total_context_precision / count:.2f}"
    )

    print(
        "\n=======================================================\n"
    )


if __name__ == "__main__":

    asyncio.run(main())