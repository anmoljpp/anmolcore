"""Implementation for EventType.

Custom for type checking. See stub file.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class EventType(str):
    """Custom type for Event.event_type.

    At runtime this is a generic subclass of str.
    """

    __slots__ = ()

    def __class_getitem__(cls, params: object) -> type:
        """Allow subscript for type checking."""
        return cls
