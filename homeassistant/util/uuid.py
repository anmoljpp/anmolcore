"""Helpers to generate uuids."""

from __future__ import annotations

from random import getrandbits


def random_uuid_hex() -> str:
    """Generate a random UUID hex.

    This uuid should not be used for cryptographically secure
    operations.
    """
    return f"{getrandbits(32 * 4):032x}"
