"""Numeric settings."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SettingsGroup
from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity


@dataclass(frozen=True, kw_only=True)
class PulsarNixieNumberDescription(NumberEntityDescription):
    group: SettingsGroup
    field: str


NUMBERS: tuple[PulsarNixieNumberDescription, ...] = (
    PulsarNixieNumberDescription(
        # in the unit the temperature is shown in (see the temperature unit)
        key="temperature_correction",
        group=SettingsGroup.DISPLAY,
        field="temp_corr",
        native_min_value=-10,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    PulsarNixieNumberDescription(
        # the day brightness is the brightness of the LED light
        key="led_night_brightness",
        group=SettingsGroup.LED,
        field="led_nght_brght",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        entity_category=EntityCategory.CONFIG,
    ),
    PulsarNixieNumberDescription(
        key="timer_hours",
        group=SettingsGroup.TIMER,
        field="timer_hours",
        native_min_value=0,
        native_max_value=23,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        mode=NumberMode.BOX,
    ),
    PulsarNixieNumberDescription(
        key="timer_minutes",
        group=SettingsGroup.TIMER,
        field="timer_min",
        native_min_value=0,
        native_max_value=59,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
    ),
    PulsarNixieNumberDescription(
        key="timer_seconds",
        group=SettingsGroup.TIMER,
        field="timer_sec",
        native_min_value=0,
        native_max_value=59,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.BOX,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(PulsarNixieNumber(entry.runtime_data, description) for description in NUMBERS)


class PulsarNixieNumber(PulsarNixieEntity, NumberEntity):
    entity_description: PulsarNixieNumberDescription

    def __init__(self, coordinator: PulsarNixieCoordinator, description: PulsarNixieNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float:
        description = self.entity_description
        return self.coordinator.setting(description.group, description.field)

    async def async_set_native_value(self, value: float) -> None:
        description = self.entity_description
        await self.coordinator.async_save(description.group, {description.field: int(value)})
