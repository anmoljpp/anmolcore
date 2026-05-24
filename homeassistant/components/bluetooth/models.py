from __future__ import annotations

from typing import TypeAlias
"""Models for bluetooth."""

from collections.abc import Callable
from enum import Enum

from home_assistant_bluetooth import BluetoothServiceInfoBleak

BluetoothChange = Enum("BluetoothChange", "ADVERTISEMENT")
BluetoothCallback: TypeAlias = Callable[[BluetoothServiceInfoBleak, BluetoothChange], None]
ProcessAdvertisementCallback: TypeAlias = Callable[[BluetoothServiceInfoBleak], bool]
