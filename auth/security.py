import secrets
import random

# API Key Generation
def generate_api_key() -> str:
    """Generates a secure, URL-safe API key."""
    return secrets.token_urlsafe(32)

# Verification Code Generation
def generate_verification_code(length: int = 6) -> str:
    """Generates a random numerical verification code of a given length."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])