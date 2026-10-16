from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
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
    assert result["result"].unique_id == HOST


async def test_unreachable_clock(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(f"{URL}/get-time", exc=TimeoutError)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": HOST})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
