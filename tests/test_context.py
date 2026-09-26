from app.rag.context import build_context

def test_build_context_adds_source_markers():

    documents = [
        {
            "page_content": "Kirtan built a RAG chatbot.",
            "metadata": {"file_id": "file_1"}
        },
        {
            "page_content": "The project uses Qdrant.",
            "metadata": {"file_id": "file_2"}
        }
    ]

    context = build_context(documents)
    assert "【Source 1】" in context
    assert "【Source 2】" in context
    assert "Kirtan built a RAG chatbot." in context
    assert "The project uses Qdrant." in context

def test_build_context_preserves_document_order():

    documents = [
        {
            "page_content": "First document.",
            "metadata": {}
        },
        {
            "page_content": "Second document.",
            "metadata": {}
        }
    ]

    context = build_context(documents)
    assert context.index("First document.") < context.index("Second document.")

def test_build_context_skips_empty_content():

    documents = [
        {
            "page_content": "",
            "metadata": {}
        },
        {
            "page_content": "Valid document.",
            "metadata": {}
        }
    ]

    context = build_context(documents)

    assert "【Source 1】" in context
    assert "Valid document." in context
    assert context.count("【Source】") == 1

def test_build_context_empty_documents():

    assert build_context([]) == ""