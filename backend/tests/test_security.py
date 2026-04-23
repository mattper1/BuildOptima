import pytest
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_hash_password_produces_different_hash_each_time():
    h1 = hash_password("secret123")
    h2 = hash_password("secret123")
    assert h1 != h2


def test_verify_password_correct_password_returns_true():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong_password_returns_false():
    hashed = hash_password("secret123")
    assert verify_password("wrongpass", hashed) is False


def test_create_access_token_decode_returns_sub():
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_create_refresh_token_decode_returns_sub():
    token = create_refresh_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_decode_token_invalid_token_raises():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token")
    assert exc_info.value.status_code == 401
