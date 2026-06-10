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


def test_long_password_does_not_crash_and_roundtrips():
    pw = "a" * 200
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    # Both hash and verify truncate to 72 bytes, so the first 72 bytes of the long
    # password will verify correctly. A different truncated prefix won't.
    assert verify_password("a" * 199, h) is True  # Truncated to 72 bytes -> same hash domain
    assert verify_password("a" * 71, h) is False  # Only 71 bytes, different from first 72
