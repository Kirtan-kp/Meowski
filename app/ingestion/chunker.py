from dataclasses import dataclass

@dataclass               #used to create datastore class which dont require to specify function like __init__, repr(),eq()
class TextChunk:         #directly a class is made with the given parameters
    text : str
    chunk_index : int

class TextChunker:

    def __init__(self , chunk_size : int = 500 , chunk_overlap : int = 50):

        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0"
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative"
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self , text : str) -> list[str]:

        if not text or not text.strip():
            return []

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        chunks = []

        current_chunk = ""

        for paragraph in paragraphs:
            if not current_chunk:
                current_chunk = paragraph
                continue

            candidate = (current_chunk + "\n\n" + paragraph)

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate

            else:
                chunks.append(current_chunk)
                overlap = current_chunk[-self.chunk_overlap:]

                current_chunk = (overlap + "\n\n" + paragraph)

        if current_chunk:
            chunks.append(current_chunk)

        return chunks