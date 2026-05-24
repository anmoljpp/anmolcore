"""Define SignalTypes for dispatcher."""

from __future__ import annotations


class _SignalTypeBase(str):
    """Generic base class for SignalType."""

    __slots__ = ()

    def __class_getitem__(cls, params: object) -> type:
        """Allow subscript for type checking."""
        return cls


class SignalType(_SignalTypeBase):
    """Generic string class for signal to improve typing."""

    __slots__ = ()


class SignalTypeFormat(_SignalTypeBase):
    """Generic string class for signal. Requires call to 'format' before use."""

    __slots__ = ()
