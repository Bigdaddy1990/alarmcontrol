
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import selector

from .const import (
    DOMAIN,
    DEFAULTS,
    CONF_INSTANT,
    CONF_DELAYED,
    CONF_PERSONS,
    CONF_SAFE_ZONES,
    CONF_USE_WINDOW,
    CONF_TIME_START,
    CONF_TIME_END,
    CONF_EXIT,
    CONF_ENTRY,
    CONF_DURATION,
    CONF_COOLDOWN,
    CONF_CAMERAS,
    CONF_SEND_SNAPSHOT,
    CONF_SNAPSHOT_PATH,
    CONF_NOTIFY_SERVICES,
    CONF_PERSISTENT,
    CONF_LIGHTS,
    CONF_BRIGHTNESS,
    CONF_SIRENS,
    CONF_SWITCHES,
    CONF_SCENES,
    CONF_SCRIPTS,
    CONF_MEDIA_PLAYERS,
)

STEP_USER = "user"
STEP_OPTIONS_MAIN = "options_main"
STEP_OPTIONS_ACTIONS = "options_actions"


def _select(hass: HomeAssistant, domain: str, multiple: bool = True) -> dict[str, Any]:
    return selector({"entity": {"domain": domain, "multiple": multiple}})


def _gather_notify_services(hass: HomeAssistant) -> list[str]:
    services = hass.services.async_services().get("notify", {})
    return sorted([f"notify.{name}" for name in services.keys()])


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            title = user_input.get(CONF_NAME) or DEFAULTS[CONF_NAME]
            return self.async_create_entry(title=title, data={}, options=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULTS[CONF_NAME]): str,
                vol.Required(CONF_INSTANT, default=[]): _select(self.hass, "binary_sensor"),
                vol.Required(CONF_DELAYED, default=[]): _select(self.hass, "binary_sensor"),
                vol.Optional(CONF_CAMERAS, default=[]): _select(self.hass, "camera"),
                vol.Optional(CONF_PERSONS, default=[]): selector({"entity": {"domain": "person", "multiple": True}}),
                vol.Optional(CONF_SAFE_ZONES, default=[]): selector({"entity": {"domain": "zone", "multiple": True}}),
                vol.Optional(CONF_USE_WINDOW, default=DEFAULTS[CONF_USE_WINDOW]): selector({"boolean": {}}),
                vol.Optional(CONF_TIME_START, default=DEFAULTS[CONF_TIME_START]): selector({"time": {}}),
                vol.Optional(CONF_TIME_END, default=DEFAULTS[CONF_TIME_END]): selector({"time": {}}),
                vol.Optional(CONF_EXIT, default=DEFAULTS[CONF_EXIT]): selector({"number": {"min": 0, "max": 600, "unit_of_measurement": "s"}}),
                vol.Optional(CONF_ENTRY, default=DEFAULTS[CONF_ENTRY]): selector({"number": {"min": 0, "max": 600, "unit_of_measurement": "s"}}),
                vol.Optional(CONF_DURATION, default=DEFAULTS[CONF_DURATION]): selector({"number": {"min": 10, "max": 3600, "unit_of_measurement": "s"}}),
                vol.Optional(CONF_COOLDOWN, default=DEFAULTS[CONF_COOLDOWN]): selector({"number": {"min": 0, "max": 3600, "unit_of_measurement": "s"}}),
            }
        )
        return self.async_show_form(step_id=STEP_USER, data_schema=schema)

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_options_main()

    async def async_step_options_main(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.options = {**self.options, **user_input}
            return await self.async_step_options_actions()

        schema = vol.Schema(
            {
                vol.Optional(CONF_LIGHTS, default=self.options.get(CONF_LIGHTS, [])): _select(self.hass, "light"),
                vol.Optional(CONF_BRIGHTNESS, default=self.options.get(CONF_BRIGHTNESS, DEFAULTS[CONF_BRIGHTNESS])): selector({"number": {"min": 1, "max": 255}}),
                vol.Optional(CONF_SIRENS, default=self.options.get(CONF_SIRENS, [])): _select(self.hass, "siren"),
                vol.Optional(CONF_SWITCHES, default=self.options.get(CONF_SWITCHES, [])): _select(self.hass, "switch"),
                vol.Optional(CONF_SCENES, default=self.options.get(CONF_SCENES, [])): _select(self.hass, "scene"),
                vol.Optional(CONF_SCRIPTS, default=self.options.get(CONF_SCRIPTS, [])): _select(self.hass, "script"),
                vol.Optional(CONF_MEDIA_PLAYERS, default=self.options.get(CONF_MEDIA_PLAYERS, [])): _select(self.hass, "media_player"),
                vol.Optional(CONF_SEND_SNAPSHOT, default=self.options.get(CONF_SEND_SNAPSHOT, DEFAULTS[CONF_SEND_SNAPSHOT])): selector({"boolean": {}}),
                vol.Optional(CONF_SNAPSHOT_PATH, default=self.options.get(CONF_SNAPSHOT_PATH, DEFAULTS[CONF_SNAPSHOT_PATH])): selector({"text": {}}),
            }
        )
        return self.async_show_form(step_id=STEP_OPTIONS_MAIN, data_schema=schema)

    async def async_step_options_actions(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self.options = {**self.options, **user_input}
            return self.async_create_entry(title="", data={}, options=self.options)

        notify_choices = _gather_notify_services(self.hass)
        schema = vol.Schema(
            {
                vol.Optional(CONF_NOTIFY_SERVICES, default=self.options.get(CONF_NOTIFY_SERVICES, [])): selector(
                    {"select": {"multiple": True, "options": notify_choices}}
                ),
                vol.Optional(CONF_PERSISTENT, default=self.options.get(CONF_PERSISTENT, DEFAULTS[CONF_PERSISTENT])): selector({"boolean": {}}),
            }
        )
        return self.async_show_form(step_id=STEP_OPTIONS_ACTIONS, data_schema=schema)
