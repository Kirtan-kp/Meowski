from app.ingestion.chunker import TextChunker

text = """
My name is Kirtan. I am interested in artificial intelligence.

I have worked on machine learning and computer vision projects.

I built an anime face generation project using deep learning.

I also worked on a license plate recognition system.
"""

chunker = TextChunker(chunk_size=100 , chunk_overlap=20)

chunks = chunker.chunk(text)

print(chunks)

for index, chunk in enumerate(chunks):

    print(f"\n--- Chunk {index} ---")
    print(chunk)