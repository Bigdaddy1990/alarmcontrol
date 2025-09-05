
from __future__ import annotations

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, SERVICE_GENERATE_DASHBOARD, DASHBOARD_FILENAME_DEFAULT

ISSUE_ID_DASHBOARD = "dashboard_missing"


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict | None
) -> RepairsFlow:
    if issue_id == ISSUE_ID_DASHBOARD:
        return DashboardRepairFlow(hass)
    raise data_entry_flow.AbortFlow("unknown_issue")


class DashboardRepairFlow(RepairsFlow):
    """Fix flow: generate a YAML dashboard and show next steps."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_step_init(self, user_input: dict | None = None) -> data_entry_flow.FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict | None = None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            # Call service to generate dashboard
            await self.hass.services.async_call(
                DOMAIN, SERVICE_GENERATE_DASHBOARD, {"filename": DASHBOARD_FILENAME_DEFAULT}, blocking=True
            )
            # Remove issue after success
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_ID_DASHBOARD)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))
