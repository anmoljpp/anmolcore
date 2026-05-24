"""Define SignalTypes for dispatcher."""


from __future__ import annotations

class _SignalTypeBase(str):
    """Generic base class for SignalType."""

    __slots__ = ()


class SignalType(_SignalTypeBase[*_Ts]):
    """Generic string class for signal to improve typing."""

    __slots__ = ()


class SignalTypeFormat(_SignalTypeBase[*_Ts]):
    """Generic string class for signal. Requires call to 'format' before use."""

    __slots__ = ()
