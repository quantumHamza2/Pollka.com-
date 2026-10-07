"""Versioned PBKDF2 password storage, using only the Python standard library."""
import hashlib
import hmac
import secrets

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"

def verify_password(password, stored):
    if not stored.startswith("pbkdf2_sha256$"):
        # Compatibility only: caller upgrades legacy plaintext after successful login.
        return hmac.compare_digest(password.encode(), stored.encode())
    try:
        _, rounds, salt, expected = stored.split("$")
        iterations = int(rounds)
        if iterations != 600000: return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False
