from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

# Salt allows us to have different "namespaces" for signatures
SIGNER_SALT = "order.guest_access"


def sign_order_id(order_id: int) -> str:
    signer = TimestampSigner(salt=SIGNER_SALT)
    # Fix: explicitly cast int to str
    return signer.sign(str(order_id))


def unsign_order_id(token: str, max_age_seconds: int = 86400) -> int | None:
    """
    Returns order_id if token is valid and not expired (default 24h).
    Returns None if invalid.
    """
    signer = TimestampSigner(salt=SIGNER_SALT)
    try:
        # unsign returns string "123", convert to int
        value = signer.unsign(token, max_age=max_age_seconds)
        return int(value)
    except (BadSignature, SignatureExpired, ValueError):
        return None
