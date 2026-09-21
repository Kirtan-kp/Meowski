from datetime import datetime
from pydantic import BaseModel, Field


class CreatePreferenceRequest(BaseModel):

    user_id: str = Field(
        min_length=1,
        max_length=100,
    )

    key: str = Field(
        min_length=1,
        max_length=100,
    )

    value: str = Field(
        min_length=1,
        max_length=500,
    )


class PreferenceResponse(BaseModel):

    id: str
    user_id: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime