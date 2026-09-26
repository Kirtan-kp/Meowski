from typing import Any


def calculate_answer_correctness(
    answer: str,
    reference_answer: str,
    llm
) -> float:
    prompt = f"""
You are evaluating the correctness of a RAG answer.

Question:
{{question}}

Reference answer:
{{reference_answer}}

Generated answer:
{{answer}}

Score the generated answer from 0 to 1.

1.0 = fully correct and consistent with the reference answer.
0.5 = partially correct but missing important information.
0.0 = incorrect or contradicts the reference answer.

Return ONLY the numeric score.
""".format(
        question="{question}",
        reference_answer=reference_answer,
        answer=answer
    )

    result = llm.invoke(prompt)

    try:
        score = float(str(result).strip())
    except ValueError:
        return 0.0

    return max(0.0, min(1.0, score))


# def calculate_keyword_correctness(
#     answer: str,
#     reference_answer: str
# ) -> float:
#     """
#     Lightweight deterministic correctness signal.

#     This is not a semantic correctness metric.
#     It measures overlap between meaningful reference terms
#     and the generated answer.
#     """

#     reference_words = {
#         word.lower().strip(".,:;!?()[]")
#         for word in reference_answer.split()
#         if len(word) > 3
#     }

#     answer_words = {
#         word.lower().strip(".,:;!?()[]")
#         for word in answer.split()
#         if len(word) > 3
#     }

#     if not reference_words:
#         return 0.0

#     return len(reference_words & answer_words) / len(reference_words)

def calculate_keyword_correctness(answer, reference_answer):
    """Lightweight deterministic correctness signal."""

    reference_words = {
        word.lower().strip(".,:;!?()[]{}")
        for word in reference_answer.split()
        if len(word) > 3
    }

    answer_words = {
        word.lower().strip(".,:;!?()[]{}")
        for word in answer.split()
        if len(word) > 3
    }

    if not reference_words:
        return 0.0

    return len(reference_words & answer_words) / len(reference_words)