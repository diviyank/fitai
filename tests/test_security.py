from app.security import hash_password, verify_password, new_token


def test_hash_roundtrip_and_reject_wrong():
    h = hash_password("s3cret")
    assert h != "s3cret"
    assert verify_password("s3cret", h) is True
    assert verify_password("wrong", h) is False


def test_new_token_is_unique_and_long():
    a, b = new_token(), new_token()
    assert a != b
    assert len(a) >= 32
