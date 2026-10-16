"""Client for the local HTTP API of the Pulsar nixie clock (the API behind its configuration page)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

import aiohttp

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class SettingsGroup(StrEnum):
    """A group of settings, read and saved together (one form on the configuration page)."""

    TIME = "time"
    DISPLAY = "settings"
    LED = "led-settings"
    TIMER = "timer-settings"
    REPAIR = "repair-settings"

    @property
    def read_path(self) -> str:
        return f"/get-{self.value}"

    @property
    def save_path(self) -> str:
        return f"/save-{self.value}"


# The fields each group saves. The clock returns more in some groups (e.g. "nix_dot_eff" in the display settings,
# which its configuration page doesn't offer), those are never sent.
SAVED_FIELDS: dict[SettingsGroup, tuple[str, ...]] = {
    SettingsGroup.TIME: ("time_zone", "24h_format"),
    SettingsGroup.DISPLAY: (
        "night_from",
        "night_to",
        "display_date",
        "display_temp",
        "temp_corr",
        "display_press",
        "display_hum",
        "trans_freq",
        "trans_effect",
        "digit_effect",
        "dot_mode",
        "beep_mode",
    ),
    SettingsGroup.LED: ("led_brightness", "led_nght_brght", "led_mode", "led_color"),
    SettingsGroup.TIMER: ("timer_mode", "timer_alarm", "timer_hours", "timer_min", "timer_sec"),
    SettingsGroup.REPAIR: ("repair_mode", "repair_dig_num", "repair_val", "repair_period"),
}


class PulsarNixieError(Exception):
    """The clock could not be reached or answered with an error."""


@dataclass
class PulsarNixieState:
    """Everything the clock reports: the settings by group, and its firmware version."""

    settings: dict[SettingsGroup, dict[str, Any]]
    version: str
    hostname: str | None


class PulsarNixieClient:
    """
    Reads and saves the settings of the clock.

    The clock's small web server handles one request at a time ("Connection: close"), so requests are sent one after
    the other.
    """

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._base_url = f"http://{host}"
        self._lock = asyncio.Lock()

    async def get_state(self) -> PulsarNixieState:
        async with self._lock:
            settings = {group: await self._get(group.read_path) for group in SettingsGroup}
            version = await self._get("/get-version")
            # only the hostname is used: the network settings also contain the Wi-Fi in reach
            network = await self._get("/get-network-settings")
        return PulsarNixieState(settings=settings, version=version["version"], hostname=network.get("hostname"))

    async def get_version(self) -> str:
        async with self._lock:
            return (await self._get("/get-version"))["version"]

    async def save(self, group: SettingsGroup, values: dict[str, Any], now: datetime | None = None) -> None:
        """
        Saves a whole group: the clock's configuration page always sends all fields of a group.

        :param values: the values of all fields of the group (see SAVED_FIELDS)
        :param now: for the time settings, the time to set the clock to (the configuration page sends the browser's)
        """
        missing = set(SAVED_FIELDS[group]) - values.keys()
        if missing:
            raise ValueError(f"Missing fields for {group}: {sorted(missing)}")
        form = {field: _form_value(values[field]) for field in SAVED_FIELDS[group]}
        if group is SettingsGroup.TIME:
            if now is None:
                raise ValueError("Saving the time settings also sets the time, it is required")
            form |= {
                "hours": str(now.hour),
                "minutes": str(now.minute),
                "seconds": str(now.second),
                "year": str(now.year),
                "month": str(now.month),
                "day": str(now.day),
            }
        async with self._lock:
            await self._post(group.save_path, form)

    async def _get(self, path: str) -> dict[str, Any]:
        try:
            async with self._session.get(self._base_url + path, timeout=REQUEST_TIMEOUT) as response:
                response.raise_for_status()
                # the clock sends JSON without a JSON content type
                return await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise PulsarNixieError(f"Reading {path} failed: {err}") from err

    async def _post(self, path: str, form: dict[str, str]) -> None:
        try:
            async with self._session.post(self._base_url + path, data=form, timeout=REQUEST_TIMEOUT) as response:
                response.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise PulsarNixieError(f"Saving {path} failed: {err}") from err


def _form_value(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
