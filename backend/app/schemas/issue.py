from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class IssueResponse(BaseModel):
    id: UUID
    repository_id: UUID
    number: int
    title: str
    body: Optional[str]
    state: str
    html_url: str
    is_duplicate: bool
    duplicate_of_id: Optional[UUID]
    labels: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
