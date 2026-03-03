from jose import jwt

from app.core.security import ALGORITHM, SECRET_KEY, decode_token


def test_token_signed_with_old_fallback_key_is_invalid():
    legacy_key = "your-super-secret-key-change-in-production-2024"
    token = jwt.encode({"sub": "legacy-user", "role": "individual"}, legacy_key, algorithm=ALGORITHM)
    decoded = decode_token(token)
    assert decoded is None


def test_token_signed_with_current_secret_is_valid():
    token = jwt.encode({"sub": "current-user", "role": "individual"}, SECRET_KEY, algorithm=ALGORITHM)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "current-user"
