import pytest

from app.ingestion.validators import validate_file


def test_pdf_extension_requires_pdf_signature():
    with pytest.raises(ValueError, match="content does not match"):
        validate_file("document.pdf", 10, b"not a pdf")


def test_docx_extension_requires_zip_signature():
    with pytest.raises(ValueError, match="content does not match"):
        validate_file("document.docx", 10, b"not a docx")


def test_text_must_be_utf8():
    with pytest.raises(ValueError, match="UTF-8"):
        validate_file("document.txt", 2, b"\xff\xfe")
