from datetime import datetime

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import URL, saved_forms


@pytest.fixture
async def setup(hass: HomeAssistant, clock, config_entry: MockConfigEntry) -> MockConfigEntry:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


async def test_entities_show_the_settings_of_the_clock(hass: HomeAssistant, setup) -> None:
    assert hass.states.get("select.nixie_clock_time_zone").state == "(GMT+01:00) Berlin, Copenhagen, Paris, Prague, Rome"
    assert hass.states.get("select.nixie_clock_hour_format").state == "24h"
    assert hass.states.get("select.nixie_clock_nixie_effect").state == "flip_all"
    assert hass.states.get("select.nixie_clock_cathode_protection_period").state == "1min"
    assert hass.states.get("switch.nixie_clock_hour_beep").state == "on"
    assert hass.states.get("switch.nixie_clock_humidity").state == "off"
    assert hass.states.get("number.nixie_clock_led_night_brightness").state == "100"
    assert hass.states.get("time.nixie_clock_night_from").state == "22:00:00"

    led = hass.states.get("light.nixie_clock_led_backlight")
    assert led.state == "on"
    assert led.attributes["effect"] == "Rainbow"
    assert led.attributes["brightness"] == 255
    assert led.attributes["rgb_color"] == (255, 0, 0)


async def test_a_change_saves_its_whole_group(
    hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker
) -> None:
    await hass.services.async_call(
        "select", "select_option", {ATTR_ENTITY_ID: "select.nixie_clock_dot_mode", "option": "blink"}, blocking=True
    )

    assert saved_forms(aioclient_mock, "/save-settings") == [
        {
            "night_from": "22:00",
            "night_to": "07:00",
            "display_date": "1",
            "display_temp": "1",
            "temp_corr": "0",
            "display_press": "0",
            "display_hum": "0",
            "trans_freq": "0",
            "trans_effect": "3",
            "digit_effect": "2",
            "dot_mode": "2",
            "beep_mode": "1",
        }
    ]
    assert hass.states.get("select.nixie_clock_dot_mode").state == "blink"


async def test_consecutive_changes_keep_each_other(
    hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker
) -> None:
    await hass.services.async_call(
        "switch", "turn_on", {ATTR_ENTITY_ID: "switch.nixie_clock_humidity"}, blocking=True
    )
    await hass.services.async_call(
        "time", "set_value", {ATTR_ENTITY_ID: "time.nixie_clock_night_to", "time": "06:30:00"}, blocking=True
    )

    last = saved_forms(aioclient_mock, "/save-settings")[-1]
    assert last["display_hum"] == "1"
    assert last["night_to"] == "06:30"


async def test_saving_the_time_settings_sets_the_time(
    hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker, freezer: FrozenDateTimeFactory
) -> None:
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to(datetime.fromisoformat("2026-10-16T21:05:09+02:00"))

    await hass.services.async_call("button", "press", {ATTR_ENTITY_ID: "button.nixie_clock_sync_time"}, blocking=True)

    assert saved_forms(aioclient_mock, "/save-time") == [
        {
            "time_zone": "CET-1CEST,M3.5.0,M10.5.0/3",
            "24h_format": "1",
            "hours": "21",
            "minutes": "5",
            "seconds": "9",
            "year": "2026",
            "month": "10",
            "day": "16",
        }
    ]


async def test_led_turns_on_with_the_mode_it_had(
    hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker
) -> None:
    await hass.services.async_call("light", "turn_off", {ATTR_ENTITY_ID: "light.nixie_clock_led_backlight"}, blocking=True)
    assert hass.states.get("light.nixie_clock_led_backlight").state == "off"

    await hass.services.async_call("light", "turn_on", {ATTR_ENTITY_ID: "light.nixie_clock_led_backlight"}, blocking=True)

    assert [form["led_mode"] for form in saved_forms(aioclient_mock, "/save-led-settings")] == ["0", "3"]


async def test_led_color_ends_an_effect_without_color(
    hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker
) -> None:
    await hass.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: "light.nixie_clock_led_backlight", "rgb_color": (0, 128, 255), "brightness": 100},
        blocking=True,
    )

    assert saved_forms(aioclient_mock, "/save-led-settings") == [
        {"led_brightness": "100", "led_nght_brght": "100", "led_mode": "1", "led_color": "#0080ff"}
    ]
    assert hass.states.get("light.nixie_clock_led_backlight").attributes["effect"] == "Static color"


async def test_led_effect(hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker) -> None:
    await hass.services.async_call(
        "light", "turn_on", {ATTR_ENTITY_ID: "light.nixie_clock_led_backlight", "effect": "Fade"}, blocking=True
    )

    assert saved_forms(aioclient_mock, "/save-led-settings")[-1]["led_mode"] == "4"


async def test_failed_save_is_reported(hass: HomeAssistant, setup, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.post(f"{URL}/save-timer-settings", status=500)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: "switch.nixie_clock_timer"}, blocking=True)

    assert hass.states.get("switch.nixie_clock_timer").state == "off"
