from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core.config import SECRET_KEY
from core.security import ALGORITHM, create_access_token, hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    password = "test-password-123"
    first = hash_password(password)
    second = hash_password(password)
    assert first != password
    assert first != second
    assert verify_password(password, first)
    assert not verify_password("wrong-password", first)


@pytest.mark.parametrize("duration", [None, timedelta(minutes=5)])
def test_token_subject_expiration_and_input_preserved(duration):
    data = {"sub": "alex@example.com"}
    before = datetime.now(timezone.utc).timestamp()
    token = create_access_token(data, expires_delta=duration)
    after = datetime.now(timezone.utc).timestamp()
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    seconds = (duration or timedelta(minutes=30)).total_seconds()
    assert payload["sub"] == data["sub"]
    assert before + seconds - 1 <= payload["exp"] <= after + seconds
    assert data == {"sub": "alex@example.com"}
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "another-test-key-at-least-32-characters", algorithms=[ALGORITHM])


def test_expired_token_is_rejected():
    token = create_access_token({"sub": "alex@example.com"}, timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
