"""Typing Helpers for Home Assistant."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, Never, TypeAlias

import voluptuous as vol

GPSType: TypeAlias = tuple[float, float]
ConfigType: TypeAlias = dict[str, Any]
DiscoveryInfoType: TypeAlias = dict[str, Any]
ServiceDataType: TypeAlias = dict[str, Any]
StateType: TypeAlias = str | int | float | None
TemplateVarsType: TypeAlias = Mapping[str, Any] | None
NoEventData: TypeAlias = Mapping[str, Never]
VolSchemaType: TypeAlias = vol.Schema | vol.All | vol.Any
VolDictType: TypeAlias = dict[str | vol.Marker, Any]

# Custom type for recorder Queries
QueryType: TypeAlias = Any


class UndefinedType(Enum):
    """Singleton type for use with not set sentinel values."""

    _singleton = 0


UNDEFINED = UndefinedType._singleton  # noqa: SLF001
