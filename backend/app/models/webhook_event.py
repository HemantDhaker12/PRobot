from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseUUIDModel


class WebhookEvent(BaseUUIDModel):
    __tablename__ = "webhook_events"

    # delivery_id from X-GitHub-Delivery header
    delivery_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String(30), nullable=False, default="pending")  # pending, processed, failed
    error_message = Column(Text, nullable=True)
