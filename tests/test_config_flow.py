from ipaddress import ip_address

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.pulsar_nixie.const import DOMAIN

from .conftest import HOST, URL


async def test_adds_the_clock_named_after_its_hostname(hass: HomeAssistant, clock) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": f" {HOST} "})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "nixie-clock"
    assert result["data"] == {"host": HOST}
    assert result["result"].unique_id == "nixie-clock"


async def test_unreachable_clock(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{URL}/get-time", exc=TimeoutError)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": HOST})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


def _announcement(host: str = HOST) -> ZeroconfServiceInfo:
    # what the clock announces: a plain HTTP service named after its hostname, without TXT records
    return ZeroconfServiceInfo(
        ip_address=ip_address(host),
        ip_addresses=[ip_address(host)],
        port=80,
        hostname="nixie-clock.local.",
        type="_http._tcp.local.",
        name="nixie-clock._http._tcp.local.",
        properties={},
    )


async def test_discovered_clock_is_added_after_confirmation(hass: HomeAssistant, clock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_announcement()
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "nixie-clock"
    assert result["data"] == {"host": HOST}


async def test_discovery_updates_the_address_of_a_known_clock(hass: HomeAssistant, aioclient_mock, clock) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="nixie-clock", data={"host": "192.168.2.99"})
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_announcement()
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data == {"host": HOST}


async def test_discovery_of_a_configured_address_is_ignored(hass: HomeAssistant, aioclient_mock) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=HOST, data={"host": HOST}).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_announcement()
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert aioclient_mock.call_count == 0


async def test_discovered_device_without_the_clock_api_is_ignored(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Another device named "nixie...": the manifest can only match the name."""
    aioclient_mock.get(f"{URL}/get-time", status=404)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_announcement()
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"
