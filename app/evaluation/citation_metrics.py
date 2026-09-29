import re

SOURCE_PATTERN = re.compile(r"\[Source\s+(\d+)\]")

def extract_citations(answer: str) -> list[int]:
    return [
        int(number)
        for number in SOURCE_PATTERN.findall(answer)
    ]


def calculate_citation_presence(answer: str) -> float:
    """
    Returns 1.0 if the answer contains at least one citation,
    otherwise 0.0.
    """

    return 1.0 if extract_citations(answer) else 0.0


def calculate_citation_validity(
    answer: str,
    source_count: int
) -> float:
    """
    Measures whether cited source numbers actually exist.
    """

    citations = extract_citations(answer)

    if not citations:
        return 0.0

    valid = [
        citation
        for citation in citations
        if 1 <= citation <= source_count
    ]

    return len(valid) / len(citations)


def calculate_expected_citation_recall(
    answer: str,
    retrieved_documents,
    expected_chunk_indices: list[int]
) -> float:
    """
    Measures whether the answer cites sources corresponding
    to the expected supporting chunks.

    This is intentionally conservative: a cited source must map
    directly to an expected chunk index.
    """

    citations = extract_citations(answer)

    if not citations or not expected_chunk_indices:
        return 0.0

    expected = set(expected_chunk_indices)

    cited_chunk_indices = set()

    for citation in citations:
        source_index = citation - 1

        if 0 <= source_index < len(retrieved_documents):
            document = retrieved_documents[source_index]

            if isinstance(document, dict):
                metadata = document.get("metadata", {})
            else:
                metadata = document.metadata

            chunk_index = metadata.get("chunk_index")

            if chunk_index is not None:
                cited_chunk_indices.add(chunk_index)

    return len(cited_chunk_indices & expected) / len(expected)