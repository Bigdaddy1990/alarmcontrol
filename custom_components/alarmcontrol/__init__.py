from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.typing import ConfigType

from .const import DASHBOARD_FILENAME_DEFAULT, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True


def _dashboard_exists(hass: HomeAssistant) -> bool:
    try:
        from pathlib import Path

        return Path(DASHBOARD_FILENAME_DEFAULT).exists()
    except Exception:
        return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Create repairs issue if dashboard is missing
    if not _dashboard_exists(hass):
        ir.async_create_issue(
            hass,
            DOMAIN,
            "dashboard_missing",
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key="dashboard_missing",
        )
    _LOGGER.debug("alarmcontrol setup: %s", entry.entry_id)
    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
