"""Settings with a fixed set of values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SettingsGroup
from .const import TIME_ZONES
from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity


@dataclass(frozen=True, kw_only=True)
class PulsarNixieSelectDescription(SelectEntityDescription):
    group: SettingsGroup
    field: str
    # option -> the value of the clock
    values: dict[str, Any]


SELECTS: tuple[PulsarNixieSelectDescription, ...] = (
    PulsarNixieSelectDescription(
        key="time_zone",
        group=SettingsGroup.TIME,
        field="time_zone",
        values={label: time_zone for time_zone, label in TIME_ZONES.items()},
    ),
    PulsarNixieSelectDescription(
        key="hour_format",
        group=SettingsGroup.TIME,
        field="24h_format",
        values={"12h": 0, "24h": 1},
    ),
    PulsarNixieSelectDescription(
        key="date_format",
        group=SettingsGroup.DISPLAY,
        field="display_date",
        values={"off": 0, "dd_mm": 1, "mm_dd": 2},
    ),
    PulsarNixieSelectDescription(
        key="temperature_unit",
        group=SettingsGroup.DISPLAY,
        field="display_temp",
        values={"off": 0, "celsius": 1, "fahrenheit": 2},
    ),
    PulsarNixieSelectDescription(
        key="pressure_unit",
        group=SettingsGroup.DISPLAY,
        field="display_press",
        values={"off": 0, "mbar": 1, "mmhg": 2, "inhg": 3},
    ),
    PulsarNixieSelectDescription(
        key="show_every",
        group=SettingsGroup.DISPLAY,
        field="trans_freq",
        values={"30s": 0, "1min": 1, "2min": 2, "5min": 3, "10min": 4, "20min": 5, "30min": 6},
    ),
    PulsarNixieSelectDescription(
        key="nixie_effect",
        group=SettingsGroup.DISPLAY,
        field="trans_effect",
        values={"none": 0, "shift_left": 1, "shift_right": 2, "flip_all": 3, "flip_sequence": 4},
    ),
    PulsarNixieSelectDescription(
        key="digit_effect",
        group=SettingsGroup.DISPLAY,
        field="digit_effect",
        values={"none": 0, "flip_all": 1, "flip_sequence": 2},
    ),
    PulsarNixieSelectDescription(
        key="dot_mode",
        group=SettingsGroup.DISPLAY,
        field="dot_mode",
        values={"off": 0, "on": 1, "blink": 2},
    ),
    PulsarNixieSelectDescription(
        key="cathode_protection_digit",
        group=SettingsGroup.REPAIR,
        field="repair_dig_num",
        values={"all": 7, "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5},
    ),
    PulsarNixieSelectDescription(
        key="cathode_protection_value",
        group=SettingsGroup.REPAIR,
        field="repair_val",
        values={"all": 10} | {str(value): value for value in range(10)},
    ),
    PulsarNixieSelectDescription(
        key="cathode_protection_period",
        group=SettingsGroup.REPAIR,
        field="repair_period",
        values={
            "1min": 60_000,
            "5min": 300_000,
            "10min": 600_000,
            "30min": 1_800_000,
            "1h": 3_600_000,
            "6h": 21_600_000,
            "12h": 43_200_000,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(PulsarNixieSelect(entry.runtime_data, description) for description in SELECTS)


class PulsarNixieSelect(PulsarNixieEntity, SelectEntity):
    entity_description: PulsarNixieSelectDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: PulsarNixieCoordinator, description: PulsarNixieSelectDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_options = list(description.values)

    @property
    def current_option(self) -> str | None:
        description = self.entity_description
        value = self.coordinator.setting(description.group, description.field)
        return next((option for option, option_value in description.values.items() if option_value == value), None)

    async def async_select_option(self, option: str) -> None:
        description = self.entity_description
        await self.coordinator.async_save(description.group, {description.field: description.values[option]})
