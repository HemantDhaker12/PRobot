from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ReindexRequest(BaseModel):
    repository_id: Optional[UUID] = Field(None, description="Database UUID of the repository")
    full_name: Optional[str] = Field(None, description="Slug name of the GitHub repository (e.g. 'owner/repo')")
