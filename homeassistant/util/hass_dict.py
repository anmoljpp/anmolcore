"""Implementation for HassDict and custom HassKey types.

Custom for type checking. See stub file.
"""


from __future__ import annotations


class HassKey(str):
    """Generic Hass key type.

    At runtime this is a generic subclass of str.
    """

    __slots__ = ()

    def __class_getitem__(cls, params: object) -> type:
        """Allow subscript for type checking."""
        return cls


class HassEntryKey(str):
    """Key type for integrations with config entries.

    At runtime this is a generic subclass of str.
    """

    __slots__ = ()

    def __class_getitem__(cls, params: object) -> type:
        """Allow subscript for type checking."""
        return cls


HassDict = dict
