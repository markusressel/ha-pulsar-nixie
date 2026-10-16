"""Adds a clock by its host, or discovered by zeroconf."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import PulsarNixieClient, PulsarNixieError, PulsarNixieState
from .const import DOMAIN, MODEL


class PulsarNixieConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    _discovered_host: str
    _discovered_title: str

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            self._async_abort_entries_match({CONF_HOST: host})
            try:
                state = await self._read_clock(host)
            except PulsarNixieError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(_unique_id(state, host))
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(title=_title(state), data={CONF_HOST: host})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        """
        The clock announces a plain "_http._tcp" service named after its hostname ("nixie" unless renamed), so the
        manifest only matches that name: whether it is a Pulsar clock is checked through its API.
        """
        host = str(discovery_info.ip_address)
        self._async_abort_entries_match({CONF_HOST: host})
        try:
            state = await self._read_clock(host)
        except PulsarNixieError:
            return self.async_abort(reason="cannot_connect")

        # a known clock with a new address
        await self.async_set_unique_id(_unique_id(state, host))
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._discovered_host = host
        self._discovered_title = _title(state)
        self.context["title_placeholders"] = {"name": self._discovered_title}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=self._discovered_title, data={CONF_HOST: self._discovered_host})
        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._discovered_title, "host": self._discovered_host},
        )

    async def _read_clock(self, host: str) -> PulsarNixieState:
        return await PulsarNixieClient(async_get_clientsession(self.hass), host).get_state()


def _unique_id(state: PulsarNixieState, host: str) -> str:
    # the clock reports neither a serial number nor its MAC address, the hostname is what identifies it on the network
    return (state.hostname or host).lower()


def _title(state: PulsarNixieState) -> str:
    return state.hostname or MODEL
