"""The readings of the clock's sensors (the ones of its monitor page)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory, UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity


@dataclass(frozen=True, kw_only=True)
class PulsarNixieSensorDescription(SensorEntityDescription):
    # the name of the reading in the clock's answer
    field: str


SENSORS: tuple[PulsarNixieSensorDescription, ...] = (
    PulsarNixieSensorDescription(
        key="temperature",
        field="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PulsarNixieSensorDescription(
        key="humidity",
        field="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PulsarNixieSensorDescription(
        key="pressure",
        field="pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    PulsarNixieSensorDescription(
        key="wifi_signal",
        field="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities(PulsarNixieSensor(entry.runtime_data, description) for description in SENSORS)


class PulsarNixieSensor(PulsarNixieEntity, SensorEntity):
    entity_description: PulsarNixieSensorDescription

    def __init__(self, coordinator: PulsarNixieCoordinator, description: PulsarNixieSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        # firmware without the monitor page (before 1.4.0) has no sensor readings
        return super().available and self.coordinator.data.sensors is not None

    @property
    def native_value(self) -> float | None:
        sensors = self.coordinator.data.sensors
        return None if sensors is None else sensors.get(self.entity_description.field)
