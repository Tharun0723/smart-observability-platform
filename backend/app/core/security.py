
import hashlib
import hmac
import secrets


def generate_collector_secret() -> str:
    """
    Generate a strong random secret for a registered collector.
    The plaintext secret should be shown only once.
    """
    return secrets.token_urlsafe(32)


def hash_collector_secret(secret: str) -> str:
    """
    Store a SHA-256 hash instead of the original secret.
    """
    if not isinstance(secret, str) or not secret:
        raise ValueError("Collector secret cannot be empty")

    return hashlib.sha256(
        secret.encode("utf-8")
    ).hexdigest()


def verify_collector_secret(
    secret: str,
    stored_hash: str
) -> bool:
    """
    Verify a supplied secret without storing or logging plaintext.
    """
    if (
        not isinstance(secret, str)
        or not secret
        or not isinstance(stored_hash, str)
        or not stored_hash
    ):
        return False

    calculated_hash = hash_collector_secret(secret)

    return hmac.compare_digest(
        calculated_hash.encode("ascii"),
        stored_hash.encode("utf-8")
    )

def verify_admin_api_key(provided_key: str | None) -> bool:
    """
    Verify an administrator API key using constant-time comparison.
    Fail closed if no administrator key is configured.
    """
    from app.core.config import settings

    configured_key = settings.admin_api_key

    if (
        not isinstance(provided_key, str)
        or not provided_key
        or not configured_key
    ):
        return False

    return hmac.compare_digest(provided_key, configured_key)