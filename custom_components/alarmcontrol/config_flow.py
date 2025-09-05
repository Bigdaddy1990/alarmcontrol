from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import selector
from homeassistant.data_entry_flow import section

from .const import (
    DOMAIN, DEFAULTS,
    CONF_NAME as C_NAME,
    CONF_ARMED_HELPER, CONF_MANUAL_ARM_SWITCH,
    CONF_AUTO_ARM_ALL_AWAY, CONF_AUTO_DISARM_ANY_HOME,
    CONF_PERSONS, CONF_SAFE_ZONES, CONF_ARM_SCHEDULE_ENABLE, CONF_TIME_START, CONF_TIME_END,
    CONF_EXIT, CONF_ENTRY, CONF_DURATION, CONF_COOLDOWN,
    CONF_INSTANT, CONF_DELAYED,
    CONF_CAMERAS, CONF_SEND_SNAPSHOT, CONF_SNAPSHOT_PATH,
    CONF_NOTIFY_SERVICES_CSV, CONF_NOTIFY_TITLE, CONF_NOTIFY_MESSAGE, CONF_PERSISTENT,
    CONF_LIGHTS, CONF_BRIGHTNESS, CONF_SIRENS, CONF_MEDIA_PLAYERS, CONF_MEDIA_ALARM_URL, CONF_MEDIA_VOLUME, CONF_SWITCHES, CONF_SCENES, CONF_SCRIPTS, CONF_NOTIFY_TARGETS, CONF_NOTIFY_LEGACY_CSV, CONF_TTS_ENTITIES, CONF_TTS_LANGUAGE, CONF_TTS_MESSAGE,
, DASHBOARD_FILENAME_DEFAULT, SERVICE_GENERATE_DASHBOARD)

STEP_USER = "user"
STEP_OPTIONS_MAIN = "options_main"
STEP_OPTIONS_ACTIONS = "options_actions"


def _select(hass: HomeAssistant, domain: str, multiple: bool = True, DASHBOARD_FILENAME_DEFAULT, SERVICE_GENERATE_DASHBOARD) -> dict[str, Any]:
    return selector({"entity": {"domain": domain, "multiple": multiple}}, DASHBOARD_FILENAME_DEFAULT, SERVICE_GENERATE_DASHBOARD)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 0

        STEP_OPTIONS_ASSISTANT = "options_assistant"

        async def async_step_options(self, user_input: dict[str, Any] | None = None):
            return await self.async_step_options_main()

        async def async_step_options_actions(self, user_input: dict[str, Any] | None = None):
            if user_input is not None:
                self.options = {**self.options, **user_input}
                return await self.async_step_options_assistant()

            schema = vol.Schema(
                {
                    vol.Optional(CONF_NOTIFY_SERVICES_CSV, default=self.options.get(CONF_NOTIFY_SERVICES_CSV, DEFAULTS[CONF_NOTIFY_SERVICES_CSV])): selector({"text": {}}),
                    vol.Optional(CONF_NOTIFY_TITLE, default=self.options.get(CONF_NOTIFY_TITLE, DEFAULTS[CONF_NOTIFY_TITLE])): selector({"text": {}}),
                    vol.Optional(CONF_NOTIFY_MESSAGE, default=self.options.get(CONF_NOTIFY_MESSAGE, DEFAULTS[CONF_NOTIFY_MESSAGE])): selector({"text": {"multiline": True}}),
                    vol.Optional(CONF_PERSISTENT, default=self.options.get(CONF_PERSISTENT, DEFAULTS[CONF_PERSISTENT])): selector({"boolean": {}}),
                }
            )
            return self.async_show_form(step_id=STEP_OPTIONS_ACTIONS, data_schema=schema)

        async def async_step_options_assistant(self, user_input: dict[str, Any] | None = None):
            if user_input is not None:
                # perform actions
                create_snap = user_input.get("create_snapshot_folder", False)
                gen_dash = user_input.get("generate_dashboard", False)
                snap_path = self.options.get("snapshot_path", DEFAULTS.get("snapshot_path", "/config/www/snapshots"))
                if create_snap:
                    from pathlib import Path
                    Path(snap_path).mkdir(parents=True, exist_ok=True)
                if gen_dash:
                    await self.hass.services.async_call(DOMAIN, SERVICE_GENERATE_DASHBOARD, {"filename": DASHBOARD_FILENAME_DEFAULT}, blocking=True)
                return self.async_create_entry(title="", data={}, options=self.options)

            schema = vol.Schema({
                vol.Optional("create_snapshot_folder", default=False): selector({"boolean": {}}),
                vol.Optional("generate_dashboard", default=True): selector({"boolean": {}}),
            })
            return self.async_show_form(step_id=STEP_OPTIONS_ASSISTANT, data_schema=schema)

