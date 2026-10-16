"""The LED backlight of the tubes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SettingsGroup
from .coordinator import PulsarNixieConfigEntry, PulsarNixieCoordinator
from .entity import PulsarNixieEntity

LED_MODE_OFF = 0
LED_MODE_STATIC = 1
LED_MODE_FADE = 4

# effect -> LED mode of the clock
EFFECTS: dict[str, int] = {
    "Static color": LED_MODE_STATIC,
    "Color change": 2,
    "Rainbow": 3,
    "Fade": LED_MODE_FADE,
}
# the modes that show the color, the others pick their colors themselves
MODES_WITH_COLOR = (LED_MODE_STATIC, LED_MODE_FADE)


async def async_setup_entry(
    hass: HomeAssistant, entry: PulsarNixieConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([PulsarNixieLight(entry.runtime_data)])


class PulsarNixieLight(PulsarNixieEntity, LightEntity):
    """
    The LED mode switches it on and off, so turning it on again restores the last mode it was on with.

    Its brightness is the day brightness, the night brightness is a separate number entity.
    """

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(EFFECTS)

    def __init__(self, coordinator: PulsarNixieCoordinator) -> None:
        super().__init__(coordinator, "led")
        self._last_mode = LED_MODE_STATIC
        self._remember_mode()

    @property
    def _mode(self) -> int:
        return self.coordinator.setting(SettingsGroup.LED, "led_mode")

    @property
    def is_on(self) -> bool:
        return self._mode != LED_MODE_OFF

    @property
    def brightness(self) -> int:
        return self.coordinator.setting(SettingsGroup.LED, "led_brightness")

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        # "#rrggbb"
        color = self.coordinator.setting(SettingsGroup.LED, "led_color").lstrip("#")
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

    @property
    def effect(self) -> str | None:
        return next((effect for effect, mode in EFFECTS.items() if mode == self._mode), None)

    async def async_turn_on(self, **kwargs: Any) -> None:
        mode = self._mode if self.is_on else self._last_mode
        if ATTR_EFFECT in kwargs:
            mode = EFFECTS[kwargs[ATTR_EFFECT]]
        elif ATTR_RGB_COLOR in kwargs and mode not in MODES_WITH_COLOR:
            # choosing a color ends an effect that doesn't show it
            mode = LED_MODE_STATIC

        changes: dict[str, Any] = {"led_mode": mode}
        if ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            changes["led_color"] = f"#{red:02x}{green:02x}{blue:02x}"
        if ATTR_BRIGHTNESS in kwargs:
            changes["led_brightness"] = kwargs[ATTR_BRIGHTNESS]
        await self.coordinator.async_save(SettingsGroup.LED, changes)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_save(SettingsGroup.LED, {"led_mode": LED_MODE_OFF})

    @callback
    def _handle_coordinator_update(self) -> None:
        self._remember_mode()
        super()._handle_coordinator_update()

    def _remember_mode(self) -> None:
        if self.is_on:
            self._last_mode = self._mode
