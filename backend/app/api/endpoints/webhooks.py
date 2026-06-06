import logging
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.repositories.webhook_event_repo import webhook_event_repo
from app.utils.helpers import verify_github_signature

router = APIRouter()


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
):
    """
    FastAPI endpoint that listens to GitHub repository webhook notifications.
    Validates payload integrity using HMAC-SHA256 signature checks.
    Saves event metadata and enqueues asynchronous event router jobs.
    """
    logging.info("Webhook endpoint entered")

    # 1. Fetch raw request body for signature verification
    body_bytes = await request.body()
    logging.info(f"Received webhook: Event={x_github_event}, Delivery={x_github_delivery}")

    # 2. Verify signature authenticity
    logging.info(f"Starting webhook signature verification for delivery ID: {x_github_delivery}")
    is_valid = verify_github_signature(body_bytes, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET)
    logging.info(f"Webhook signature verification result for delivery ID {x_github_delivery}: {is_valid}")
    if not is_valid:
        logging.warning(f"Signature verification failed for delivery ID: {x_github_delivery}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature hash.",
        )

    # 3. Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logging.error(f"Malformed JSON in webhook request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must be valid JSON.",
        )

    # 4. Check for duplicate webhook delivery to prevent reprocessing
    existing_event = webhook_event_repo.get_by_delivery_id(db, x_github_delivery)
    if existing_event:
        logging.info(f"Webhook event with delivery ID {x_github_delivery} already received. Skipping.")
        response_data = {
            "success": True,
            "message": "Event already registered.",
            "event_id": str(existing_event.id),
        }
        logging.info(f"Webhook endpoint returning duplicate response: {response_data}")
        return response_data

    # 5. Save the WebhookEvent to database in 'pending' status
    event_data = {
        "delivery_id": x_github_delivery,
        "event_type": x_github_event,
        "payload": payload,
        "status": "pending",
    }
    logging.info(f"Writing webhook event to database for delivery ID: {x_github_delivery}")
    db_event = webhook_event_repo.create(db, obj_in=event_data)
    logging.info(f"Webhook event written to database successfully (ID: {db_event.id})")

    # 6. Dispatch Celery task for background execution
    try:
        from app.workers.tasks import process_webhook_event

        logging.info(f"Dispatching Celery task for webhook delivery ID: {x_github_delivery}")
        process_webhook_event.delay(str(db_event.id))
        logging.info(f"Enqueued Celery task for webhook delivery ID: {x_github_delivery} successfully")
    except Exception as e:
        logging.error(f"Failed to enqueue Celery task: {str(e)}")
        db_event.status = "failed"
        db_event.error_message = f"Celery enqueue error: {str(e)}"
        db.commit()

    response_data = {
        "success": True,
        "message": "Event enqueued for processing.",
        "event_id": str(db_event.id),
    }
    logging.info(f"Webhook endpoint returning response: {response_data}")
    return response_data
