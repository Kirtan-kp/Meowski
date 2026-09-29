def build_context(documents: list[dict]) -> str:

    if not documents:
        return ""

    context_parts = []
    source_number = 1

    for document in documents:

        content = document.get("page_content" , "").strip()

        if not content:
            continue

        metadata = document.get("metadata", {}) or {}
        filename = metadata.get("source_filename") or metadata.get("filename") or metadata.get("source") or "unknown"
        page = metadata.get("page")
        if isinstance(page, int):
            page = page + 1
        section = metadata.get("section") or metadata.get("heading")
        chunk_index = metadata.get("chunk_index")

        location = [f"Document: {filename}"]
        if page is not None:
            location.append(f"Page: {page}")
        if section:
            location.append(f"Section: {section}")
        if chunk_index is not None:
            location.append(f"Chunk: {chunk_index}")

        context_parts.append(f"[Source {source_number}]\n" + " | ".join(location) + f"\n{content}")
        source_number += 1

    return "\n\n".join(context_parts)