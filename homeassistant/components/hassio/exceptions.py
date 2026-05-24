"""Exceptions for the Hassio integration."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError


class HassioNotReadyError(HomeAssistantError):
    """Raised when Hassio data is not yet available."""
