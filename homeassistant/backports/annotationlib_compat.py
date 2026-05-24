"""Compatibility shim for annotationlib (Python 3.14+).

On Python 3.12, annotationlib doesn't exist. We provide a minimal
implementation using inspect.get_annotations() that covers the usage
patterns in Home Assistant.
"""

from __future__ import annotations

import enum
import inspect
import sys

if sys.version_info >= (3, 14):
    from annotationlib import Format, get_annotations
else:

    class Format(enum.IntEnum):
        """Annotation format enum compatible with annotationlib.Format."""

        VALUE = 1
        FORWARDREF = 2
        STRING = 3

    def get_annotations(
        obj: type, *, format: Format = Format.VALUE  # noqa: A002
    ) -> dict[str, object]:
        """Get annotations for a class, compatible with annotationlib.get_annotations.

        On Python < 3.14, uses inspect.get_annotations() which handles
        forward references as strings when eval_str=False.
        """
        return inspect.get_annotations(obj, eval_str=False)
