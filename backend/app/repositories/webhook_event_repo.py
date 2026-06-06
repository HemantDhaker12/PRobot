from typing import Optional
from sqlalchemy.orm import Session
from app.models.webhook_event import WebhookEvent
from app.repositories.base import CRUDBase


class WebhookEventRepository(CRUDBase[WebhookEvent]):
    def get_by_delivery_id(self, db: Session, delivery_id: str) -> Optional[WebhookEvent]:
        """
        Fetch a webhook event record by GitHub's delivery ID.
        """
        return db.query(self.model).filter(self.model.delivery_id == delivery_id).first()


webhook_event_repo = WebhookEventRepository(WebhookEvent)
