"""Sets the clock to Home Assistant's time."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PulsarNixieSyncTimeButton(entry.runtime_data)])


class PulsarNixieSyncTimeButton(PulsarNixieEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: PulsarNixieCoordinator) -> None:
        super().__init__(coordinator, "sync_time")

    async def async_press(self) -> None:
        await self.coordinator.async_sync_time()
