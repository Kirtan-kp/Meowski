from pydantic import BaseModel


class UsageResponse(BaseModel):
    questions_left: int          # rough estimate of how many more questions fit in the tightest budget
    fraction: float              # 0..1 share of that budget still available (drives the meter)
    resets_in: int | None = None  # seconds until a question is possible again, when none are left
    limited_by: str              # which budget is tightest: hourly, session_hourly, daily, session_daily, provider_daily
