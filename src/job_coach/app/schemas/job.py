import datetime

from pydantic import BaseModel


class JobCreate(BaseModel):
    company: str
    position: str
    position_number: str | None = None
    status: str = "Applied"
    url: str | None = None
    notes: str | None = None


class JobUpdate(BaseModel):
    company: str | None = None
    position: str | None = None
    position_number: str | None = None
    status: str | None = None
    url: str | None = None
    notes: str | None = None


class JobRead(BaseModel):
    id: int
    user_id: int
    company: str
    position: str
    position_number: str | None = None
    status: str
    url: str | None
    notes: str | None
    applied_at: datetime.datetime

    model_config = {"from_attributes": True}
