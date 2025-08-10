import hashlib
import os
import random

__all__ = ["hash_password", "generate_cookie_value"]

def generate_cookie_value(length: int = 16) -> str:
    """
    Generate a random cookie value of specified length using lowercase letters and digits.

    Args:
        length (int): The length of the cookie value to generate (default: 16).

    Returns:
        str: A randomly generated string of the specified length, consisting of lowercase letters and digits.

    Example:
        >>> generate_cookie_value(8)
        'a1b2c3d4'

    Notes:
        Used for session cookies and randomized HTTP headers.
    """
    return ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=length))

def hash_password(password: str) -> str:
    """
    Generate a Tor-compatible hashed password for use with the Tor control protocol.

    Args:
        password (str): Plain text password.

    Returns:
        str: Tor-formatted hashed password string.

    Security:
        Uses SHA-1 as required by the Tor control protocol.
        The output format is "16:<salt><hash>", where both are hex-encoded.

    Example:
        >>> hash_password("secret")
        '16:...'

    Notes:
        The salt is randomly generated for each call.
    """
    # Tor uses a specific salt + hash format
    salt = os.urandom(8)
    h = hashlib.sha1(salt + password.encode()).digest()
    return f"16:{salt.hex().upper()}{h.hex().upper()}"
