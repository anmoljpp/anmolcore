from __future__ import annotations

from typing import TypeAlias
"""MQTT Discovery data."""

from dataclasses import dataclass

from homeassistant.data_entry_flow import BaseServiceInfo

ReceivePayloadType: TypeAlias = str | bytes | bytearray


@dataclass(slots=True)
class MqttServiceInfo(BaseServiceInfo):
    """Prepared info from mqtt entries."""

    topic: str
    payload: ReceivePayloadType
    qos: int
    retain: bool
    subscribed_topic: str
    timestamp: float
