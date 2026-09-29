from pydantic import BaseModel

class HealthResponse(BaseModel):
    status : str
    environment : str
    dependencies: dict[str, str]