from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PullRequestResponse(BaseModel):
    id: UUID
    repository_id: UUID
    number: int
    title: str
    body: Optional[str]
    state: str
    html_url: str
    is_draft: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
