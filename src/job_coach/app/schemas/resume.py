import datetime

from pydantic import BaseModel


class ResumeRead(BaseModel):
    id: int
    user_id: int
    filename: str
    content_type: str
    status: str
    raw_text: str | None = None
    uploaded_at: datetime.datetime

    model_config = {"from_attributes": True}
