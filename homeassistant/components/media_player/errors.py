"""Errors for the Media Player component."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError


class MediaPlayerException(HomeAssistantError):
    """Base class for Media Player exceptions."""


class BrowseError(MediaPlayerException):
    """Error while browsing."""


class SearchError(MediaPlayerException):
    """Error while searching."""
