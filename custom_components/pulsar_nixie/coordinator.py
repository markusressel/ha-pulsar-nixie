"""Polls the clock, and saves changed settings."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PulsarNixieClient, PulsarNixieError, PulsarNixieState, SettingsGroup
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type PulsarNixieConfigEntry = ConfigEntry[PulsarNixieCoordinator]


class PulsarNixieCoordinator(DataUpdateCoordinator[PulsarNixieState]):
    """The clock doesn't report changes by itself, so its settings are polled."""

    config_entry: PulsarNixieConfigEntry

    def __init__(self, hass: HomeAssistant, entry: PulsarNixieConfigEntry, client: PulsarNixieClient) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.client = client
        # a change is saved by sending its whole group, so changes must not overlap: the second would undo the first
        self._save_lock = asyncio.Lock()

    async def _async_update_data(self) -> PulsarNixieState:
        try:
            return await self.client.get_state()
        except PulsarNixieError as err:
            raise UpdateFailed(str(err)) from err

    def setting(self, group: SettingsGroup, field: str) -> Any:
        return self.data.settings[group][field]

    async def async_save(self, group: SettingsGroup, changes: dict[str, Any]) -> None:
        """Changes settings of a group, keeping its other settings as they are."""
        async with self._save_lock:
            values = self.data.settings[group] | changes
            try:
                # saving the time zone or format also sets the time: use Home Assistant's, like the browser's
                await self.client.save(group, values, now=dt_util.now())
            except PulsarNixieError as err:
                raise HomeAssistantError(f"Saving the settings of the clock failed: {err}") from err
            # the clock only reports changes when polled
            self.data.settings[group] = values
            self.async_set_updated_data(self.data)

    async def async_sync_time(self) -> None:
        """Sets the clock to Home Assistant's time (saving the time settings as they are)."""
        await self.async_save(SettingsGroup.TIME, {})
