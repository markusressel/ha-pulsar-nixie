"""The start and end of the night (the night brightness of the LED light)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SettingsGroup
from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity


@dataclass(frozen=True, kw_only=True)
class PulsarNixieTimeDescription(TimeEntityDescription):
    field: str


TIMES: tuple[PulsarNixieTimeDescription, ...] = (
    PulsarNixieTimeDescription(key="night_from", field="night_from", entity_category=EntityCategory.CONFIG),
    PulsarNixieTimeDescription(key="night_to", field="night_to", entity_category=EntityCategory.CONFIG),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(PulsarNixieTime(entry.runtime_data, description) for description in TIMES)


class PulsarNixieTime(PulsarNixieEntity, TimeEntity):
    entity_description: PulsarNixieTimeDescription

    def __init__(self, coordinator: PulsarNixieCoordinator, description: PulsarNixieTimeDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> time:
        # "HH:MM"
        return time.fromisoformat(self.coordinator.setting(SettingsGroup.DISPLAY, self.entity_description.field))

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_save(
            SettingsGroup.DISPLAY, {self.entity_description.field: value.strftime("%H:%M")}
        )
