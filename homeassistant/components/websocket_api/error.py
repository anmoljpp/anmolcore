"""WebSocket API related errors."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError


class Disconnect(HomeAssistantError):
    """Disconnect the current session."""
