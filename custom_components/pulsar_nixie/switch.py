"""Settings that are on or off."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SettingsGroup
from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity


@dataclass(frozen=True, kw_only=True)
class PulsarNixieSwitchDescription(SwitchEntityDescription):
    group: SettingsGroup
    field: str


SWITCHES: tuple[PulsarNixieSwitchDescription, ...] = (
    PulsarNixieSwitchDescription(
        key="hour_beep",
        group=SettingsGroup.DISPLAY,
        field="beep_mode",
        entity_category=EntityCategory.CONFIG,
    ),
    PulsarNixieSwitchDescription(
        key="show_humidity",
        group=SettingsGroup.DISPLAY,
        field="display_hum",
        entity_category=EntityCategory.CONFIG,
    ),
    PulsarNixieSwitchDescription(
        key="timer",
        group=SettingsGroup.TIMER,
        field="timer_mode",
    ),
    PulsarNixieSwitchDescription(
        key="timer_alarm",
        group=SettingsGroup.TIMER,
        field="timer_alarm",
        entity_category=EntityCategory.CONFIG,
    ),
    PulsarNixieSwitchDescription(
        key="cathode_protection",
        group=SettingsGroup.REPAIR,
        field="repair_mode",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(PulsarNixieSwitch(entry.runtime_data, description) for description in SWITCHES)


class PulsarNixieSwitch(PulsarNixieEntity, SwitchEntity):
    entity_description: PulsarNixieSwitchDescription

    def __init__(self, coordinator: PulsarNixieCoordinator, description: PulsarNixieSwitchDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        description = self.entity_description
        return self.coordinator.setting(description.group, description.field) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._save(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._save(0)

    async def _save(self, value: int) -> None:
        description = self.entity_description
        await self.coordinator.async_save(description.group, {description.field: value})
