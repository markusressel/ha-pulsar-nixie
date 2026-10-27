"""A clock with the settings read from a real one."""

from collections.abc import Generator
from copy import deepcopy
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.pulsar_nixie.const import DOMAIN

HOST = "192.168.2.170"
URL = f"http://{HOST}"

CLOCK: dict[str, dict[str, Any]] = {
    "/get-time": {"time_zone": "CET-1CEST,M3.5.0,M10.5.0/3", "24h_format": 1},
    "/get-settings": {
        "night_from": "22:00",
        "night_to": "07:00",
        "night_hv_off": 0,
        "digit_effect": 2,
        "trans_effect": 3,
        "trans_freq": 0,
        "display_date": 1,
        "dot_mode": 0,
        "beep_mode": 1,
        "display_temp": 1,
        "temp_corr": 0,
        "display_press": 0,
        "display_hum": 0,
        "nix_dot_eff": 0,
    },
    "/get-led-settings": {"led_brightness": 255, "led_nght_brght": 100, "led_color": "#ff0000", "led_mode": 3},
    "/get-timer-settings": {"timer_mode": 0, "timer_hours": 0, "timer_min": 0, "timer_sec": 0, "timer_alarm": 0},
    "/get-repair-settings": {"repair_mode": 0, "repair_dig_num": 0, "repair_val": 0, "repair_period": 60000},
    "/get-version": {"version": "6c3sq-1.2.0"},
    "/get-network-settings": {"wifi_mode": 1, "ssid": "home", "ssid_list": ["home"], "hostname": "nixie-clock"},
    "/api/sensors": {
        "temperature": 25.0,
        "humidity": 35.8,
        "pressure": 1014.2,
        "sensor": "BME280",
        "rssi": -68,
        "uptime": 2477,
        "version": "6c3sq-1.4.0",
    },
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None]:
    yield


@pytest.fixture
def clock(aioclient_mock: AiohttpClientMocker) -> dict[str, dict[str, Any]]:
    """The clock's settings: change them to change what it reports."""
    settings = deepcopy(CLOCK)
    mock_clock(aioclient_mock, settings)
    return settings


def mock_clock(aioclient_mock: AiohttpClientMocker, settings: dict[str, dict[str, Any] | None]) -> None:
    """Answers with the settings, a path set to None is not found (like on firmware without it)."""
    for path, value in settings.items():
        if value is None:
            aioclient_mock.get(f"{URL}{path}", status=404)
        else:
            aioclient_mock.get(f"{URL}{path}", json=value)
    for path in ("/save-time", "/save-settings", "/save-led-settings", "/save-timer-settings", "/save-repair-settings"):
        aioclient_mock.post(f"{URL}{path}")


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, unique_id=HOST, title="nixie-clock", data={"host": HOST})


def saved_forms(aioclient_mock: AiohttpClientMocker, path: str) -> list[dict[str, str]]:
    return [data for method, url, data, _ in aioclient_mock.mock_calls if method == "POST" and url.path == path]
