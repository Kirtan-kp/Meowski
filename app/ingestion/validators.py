from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf" , ".txt" , ".docx"}  #set

MAX_FILE_SIZE = 10*1024*1024  # 10 mb

def validate_file(filename : str , file_size : int) -> None:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type : {extension} , upload pdf txt docx file only")

    if file_size>MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds the 10 mb limit.")

    return extension