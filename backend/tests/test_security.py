
import pytest

from app.core.security import (
    generate_collector_secret,
    hash_collector_secret,
    verify_collector_secret,
)


def test_generate_collector_secret():
    secret = generate_collector_secret()

    assert isinstance(secret, str)
    assert len(secret) > 20


def test_generated_secrets_are_unique():
    first = generate_collector_secret()
    second = generate_collector_secret()

    assert first != second


def test_secret_is_hashed():
    secret = generate_collector_secret()
    hashed = hash_collector_secret(secret)

    assert hashed != secret
    assert len(hashed) == 64


def test_valid_secret_verification():
    secret = generate_collector_secret()
    hashed = hash_collector_secret(secret)

    assert verify_collector_secret(secret, hashed) is True


def test_invalid_secret_rejected():
    secret = generate_collector_secret()
    hashed = hash_collector_secret(secret)

    assert verify_collector_secret("wrong-secret", hashed) is False


def test_empty_secret_rejected():
    with pytest.raises(ValueError):
        hash_collector_secret("")
