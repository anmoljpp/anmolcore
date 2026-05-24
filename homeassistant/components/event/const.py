"""Provides the constants needed for the component."""

from __future__ import annotations

from enum import StrEnum

DOMAIN = "event"
ATTR_EVENT_TYPE = "event_type"
ATTR_EVENT_TYPES = "event_types"


class DoorbellEventType(StrEnum):
    """Standard event types for doorbell device class."""

    RING = "ring"
