from pydantic import BaseModel

class Source(BaseModel):
    content : str
    metadata : dict

class RetrievalResponse(BaseModel):
    answer : str
    sources : list[Source]
    mode : str = "portfolio"