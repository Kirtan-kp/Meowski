def build_context(documents: list[dict]) -> str:

    if not documents:
        return ""

    context_parts = []
    source_number = 1

    for document in documents:

        content = document.get("page_content" , "").strip()

        if not content:
            continue

        context_parts.append(f"【Source {source_number}】\n" f"{content}")
        source_number += 1

    return "\n\n".join(context_parts)