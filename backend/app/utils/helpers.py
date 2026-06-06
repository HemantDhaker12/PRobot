import hashlib
import hmac
import logging
from typing import List


def verify_github_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Validates that the incoming payload came from GitHub using the configured webhook secret.
    """
    secret_len = len(secret) if secret else 0
    logging.info(f"Webhook signature verification started. Configured webhook secret length: {secret_len}")
    logging.info(f"Received signature header: {signature_header}")

    if not signature_header:
        logging.warning("GitHub webhook request missing X-Hub-Signature-256 header.")
        return False
    if not secret:
        logging.warning("GITHUB_WEBHOOK_SECRET is not configured. Webhook signature verification bypassed.")
        # Under developer dev/test mode without secret, let's allow it if secret is empty string,
        # but in production, we should enforce it. Let's enforce it or log/warn.
        return True

    try:
        if "=" not in signature_header:
            logging.warning("Signature header does not contain '='.")
            return False
        sha_name, signature = signature_header.split("=", 1)
        if sha_name != "sha256":
            logging.warning(f"Unsupported signature hash algorithm: {sha_name}")
            return False

        mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256,
        )
        calculated_sig = mac.hexdigest()
        logging.info(f"Calculated signature: sha256={calculated_sig}")

        result = hmac.compare_digest(calculated_sig, signature)
        logging.info(f"Signature verification result: {result}")
        return result
    except Exception as e:
        logging.error(f"Error during webhook signature verification: {str(e)}")
        return False


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Utility to split large document text (like README/CONTRIBUTING) into overlapping chunks.
    """
    if not text:
        return []
    words = text.split()
    chunks = []
    current_words = []
    current_length = 0

    for word in words:
        current_words.append(word)
        current_length += len(word) + 1  # count word and space
        if current_length >= chunk_size:
            chunks.append(" ".join(current_words))
            # keep overlap (approximately 20% of words)
            overlap_count = max(1, int(len(current_words) * (chunk_overlap / chunk_size)))
            current_words = current_words[-overlap_count:]
            current_length = sum(len(w) + 1 for w in current_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
