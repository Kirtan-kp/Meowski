from pathlib import Path
import io
import zipfile

from pypdf import PdfReader

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_DOCX_UNCOMPRESSED_SIZE = 5 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 1000


def validate_file(filename: str, file_size: int, file_bytes: bytes | None = None) -> str:
    extension = Path(filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type : {extension} , upload pdf txt docx file only")

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds the 10 MB limit.")

    if file_bytes is None:
        return extension

    if extension == ".pdf":
        if not file_bytes.startswith(b"%PDF"):
            raise ValueError("File content does not match the PDF extension.")
        try:
            pages = len(PdfReader(io.BytesIO(file_bytes)).pages)
        except Exception as exc:
            raise ValueError("Invalid PDF file.") from exc
        if pages > settings.max_upload_pages:
            raise ValueError(f"PDF exceeds the {settings.max_upload_pages} page limit.")

    elif extension == ".docx":
        if not file_bytes.startswith(b"PK"):
            raise ValueError("File content does not match the DOCX extension.")
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                members = archive.infolist()
                if len(members) > MAX_ARCHIVE_MEMBERS:
                    raise ValueError("DOCX contains too many archive entries.")
                total_uncompressed = sum(item.file_size for item in members)
                if total_uncompressed > MAX_DOCX_UNCOMPRESSED_SIZE:
                    raise ValueError("DOCX contains too much uncompressed content.")
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("Invalid DOCX file.")
        except zipfile.BadZipFile as exc:
            raise ValueError("Invalid DOCX file.") from exc

    elif extension == ".txt":
        if len(file_bytes) > settings.max_upload_text_chars * 4:
            raise ValueError(f"Text file exceeds the {settings.max_upload_text_chars} character limit.")
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Text files must be valid UTF-8.") from exc
        if len(text) > settings.max_upload_text_chars:
            raise ValueError(f"Text file exceeds the {settings.max_upload_text_chars} character limit.")

    return extension
