def get_chunk_index(document):
    return document.metadata.get("chunk_index")


def calculate_recall(retrieved, relevant):
    retrieved_indices = {get_chunk_index(document) for document in retrieved}
    relevant = set(relevant)

    if not relevant:
        return 0.0

    return len(retrieved_indices & relevant) / len(relevant)


def calculate_precision(retrieved, relevant):
    retrieved_indices = {get_chunk_index(document) for document in retrieved}
    relevant = set(relevant)

    if not retrieved_indices:
        return 0.0

    return len(retrieved_indices & relevant) / len(retrieved_indices)


def calculate_mrr(retrieved, relevant):
    relevant = set(relevant)

    for rank, document in enumerate(retrieved, start=1):
        chunk_index = get_chunk_index(document)

        if chunk_index in relevant:
            return 1.0 / rank

    return 0.0