import base64
import hashlib
import hmac
import json
import time

import pytest

from agriment_shared.auth import (
    JWT_SECRET_KEY,
    InvalidToken,
    decode_access_token,
    split_bearer,
)


def _b64(d: dict) -> bytes:
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=")


def _make_token(sub="user-123", exp_delta=3600, alg="HS256", secret=None) -> str:
    header = {"alg": alg, "typ": "JWT"}
    payload = {"sub": sub, "exp": time.time() + exp_delta} if exp_delta is not None else {"sub": sub}
    h, p = _b64(header), _b64(payload)
    signed = h + b"." + p
    key = (secret or JWT_SECRET_KEY).encode()
    sig = hmac.new(key, signed, hashlib.sha256).digest()
    return (signed + b"." + base64.urlsafe_b64encode(sig).rstrip(b"=")).decode()


def test_valid_token_returns_subject():
    assert decode_access_token(_make_token(sub="farmer-42")) == "farmer-42"


def test_expired_token_rejected():
    with pytest.raises(InvalidToken):
        decode_access_token(_make_token(exp_delta=-10))


def test_wrong_signature_rejected():
    with pytest.raises(InvalidToken):
        decode_access_token(_make_token(secret="not-the-real-secret"))


def test_wrong_algorithm_rejected():
    with pytest.raises(InvalidToken):
        decode_access_token(_make_token(alg="none"))


def test_missing_subject_rejected():
    with pytest.raises(InvalidToken):
        decode_access_token(_make_token(sub=""))


def test_malformed_token_rejected():
    with pytest.raises(InvalidToken):
        decode_access_token("not-a-jwt")


def test_split_bearer_valid():
    assert split_bearer("Bearer abc.def.ghi") == "abc.def.ghi"


def test_split_bearer_case_insensitive_scheme():
    assert split_bearer("bearer abc.def.ghi") == "abc.def.ghi"


@pytest.mark.parametrize("header", [None, "", "abc.def.ghi", "Basic abc"])
def test_split_bearer_invalid(header):
    assert split_bearer(header) is None
