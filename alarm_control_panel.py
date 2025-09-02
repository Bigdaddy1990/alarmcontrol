from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelEntityFeature,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import event as ha_event, template as ha_template
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)

from .const import (
    DEFAULTS,
    DOMAIN,
    CONF_NAME,
    CONF_ARMED_HELPER, CONF_MANUAL_ARM_SWITCH,
    CONF_AUTO_ARM_ALL_AWAY, CONF_AUTO_DISARM_ANY_HOME,
    CONF_PERSONS, CONF_SAFE_ZONES, CONF_ARM_SCHEDULE_ENABLE, CONF_TIME_START, CONF_TIME_END,
    CONF_EXIT, CONF_ENTRY, CONF_DURATION, CONF_COOLDOWN,
    CONF_INSTANT, CONF_DELAYED,
    CONF_CAMERAS, CONF_SEND_SNAPSHOT, CONF_SNAPSHOT_PATH,
    CONF_NOTIFY_SERVICES_CSV, CONF_NOTIFY_TITLE, CONF_NOTIFY_MESSAGE, CONF_PERSISTENT,
    CONF_LIGHTS, CONF_BRIGHTNESS, CONF_SIRENS, CONF_MEDIA_PLAYERS, CONF_MEDIA_ALARM_URL, CONF_MEDIA_VOLUME, CONF_SWITCHES, CONF_SCENES, CONF_SCRIPTS, CONF_NOTIFY_TARGETS, CONF_NOTIFY_LEGACY_CSV, CONF_TTS_ENTITIES, CONF_TTS_LANGUAGE, CONF_TTS_MESSAGE, ATTR_LAST_TRIGGER, ATTR_LAST_SNAPSHOT, ATTR_COOLDOWN_UNTIL, SERVICE_GENERATE_DASHBOARD, DASHBOARD_FILENAME_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([AlarmControl(hass, entry)], update_before_add=False)


@dataclass
class _Config:
    name: str
    # control
    armed_helper: str | None
    manual_arm_switch: str | None
    # logic
    auto_arm_all_away: bool
    auto_disarm_any_home: bool
    persons: list[str]
    safe_zones: list[str]
    arm_schedule_enable: bool
    t_start: time | None
    t_end: time | None
    # timers
    exit_delay: int
    entry_delay: int
    duration: int
    cooldown: int
    # sensors
    instant: list[str]
    delayed: list[str]
    cameras: list[str]
    # notify
    send_snapshot: bool
    snapshot_path: str
    notify_services_csv: str
    notify_title: str
    notify_message: str
    persistent: bool
    # devices
    lights: list[str]
    brightness: int
    sirens: list[str]
    media_players: list[str]
    media_alarm_url: str
    media_volume: float
    switches: list[str]
    scenes: list[str]
    scripts: list[str]
    # notify/tts
    notify_targets: list[str]
    notify_legacy_csv: str
    tts_entities: list[str]
    tts_language: str
    tts_message: str


class AlarmControl(AlarmControlPanelEntity):
    _attr_has_entity_name = True
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.options.get(CONF_NAME, DEFAULTS[CONF_NAME])
        self._state = STATE_ALARM_DISARMED
        self._attr_code_arm_required = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "manufacturer": "alarmcontrol",
            "model": "Alarm Control Virtual",
            "name": self._attr_name,
        }
        self._last_trigger: str | None = None
        self._last_snapshot: str | None = None
        self._unsubs: list[callable] = []
        self._cooldown_until: float = 0.0

    @property
    def state(self) -> str | None:
        return self._state

        async def async_added_to_hass(self) -> None:

    async def async_will_remove_from_hass(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()

    # ---- Arm/Disarm API ----
    async def async_alarm_disarm(self, code: str | None = None) -> None:
        self._set_state(STATE_ALARM_DISARMED)
        cfg = self._cfg()
        if cfg.armed_helper:
            await self.hass.services.async_call("input_boolean", "turn_off", {"entity_id": cfg.armed_helper}, blocking=False)
        await self._devices_off(cfg)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._arm_with_exit_delay(STATE_ALARM_ARMED_AWAY)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._arm_with_exit_delay(STATE_ALARM_ARMED_NIGHT)

    async def _arm_with_exit_delay(self, target_state: str) -> None:
        cfg = self._cfg()
        if cfg.exit_delay > 0:
            self._set_state(STATE_ALARM_ARMING)
            await asyncio.sleep(cfg.exit_delay)
        self._set_state(target_state)
        if cfg.armed_helper:
            await self.hass.services.async_call("input_boolean", "turn_on", {"entity_id": cfg.armed_helper}, blocking=False)

    # ---- Config ----
    def _cfg(self) -> _Config:
        opt = {**DEFAULTS, **self.entry.options}
        t_start = ha_event.parse_time(opt.get(CONF_TIME_START)) if opt.get(CONF_TIME_START) else None
        t_end = ha_event.parse_time(opt.get(CONF_TIME_END)) if opt.get(CONF_TIME_END) else None
        return _Config(
            name=opt.get(CONF_NAME, DEFAULTS[CONF_NAME]),
            armed_helper=opt.get(CONF_ARMED_HELPER),
            manual_arm_switch=opt.get(CONF_MANUAL_ARM_SWITCH),
            auto_arm_all_away=bool(opt.get(CONF_AUTO_ARM_ALL_AWAY, True)),
            auto_disarm_any_home=bool(opt.get(CONF_AUTO_DISARM_ANY_HOME, True)),
            persons=list(opt.get(CONF_PERSONS, [])),
                safe_zones=list(opt.get(CONF_SAFE_ZONES, [])),
            arm_schedule_enable=bool(opt.get(CONF_ARM_SCHEDULE_ENABLE, False)),
            t_start=t_start,
            t_end=t_end,
            exit_delay=int(opt.get(CONF_EXIT)),
            entry_delay=int(opt.get(CONF_ENTRY)),
            duration=int(opt.get(CONF_DURATION)),
            cooldown=int(opt.get(CONF_COOLDOWN)),
            instant=list(opt.get(CONF_INSTANT, [])),
            delayed=list(opt.get(CONF_DELAYED, [])),
            cameras=list(opt.get(CONF_CAMERAS, [])),
            send_snapshot=bool(opt.get(CONF_SEND_SNAPSHOT)),
            snapshot_path=str(opt.get(CONF_SNAPSHOT_PATH)),
            notify_services_csv=str(opt.get(CONF_NOTIFY_SERVICES_CSV)),
            notify_title=str(opt.get(CONF_NOTIFY_TITLE)),
            notify_message=str(opt.get(CONF_NOTIFY_MESSAGE)),
            persistent=bool(opt.get(CONF_PERSISTENT)),
            lights=list(opt.get(CONF_LIGHTS, [])),
            brightness=int(opt.get(CONF_BRIGHTNESS)),
            sirens=list(opt.get(CONF_SIRENS, [])),
            media_players=list(opt.get(CONF_MEDIA_PLAYERS, [])),
                media_alarm_url=str(opt.get(CONF_MEDIA_ALARM_URL, "")),
                media_volume=float(opt.get(CONF_MEDIA_VOLUME, 0.6)),
            switches=list(opt.get(CONF_SWITCHES, [])),
            scenes=list(opt.get(CONF_SCENES, [])),
            scripts=list(opt.get(CONF_SCRIPTS, [])),
            notify_targets=list(opt.get(CONF_NOTIFY_TARGETS, [])),
            notify_legacy_csv=str(opt.get(CONF_NOTIFY_LEGACY_CSV, "")),
            tts_entities=list(opt.get(CONF_TTS_ENTITIES, [])),
            tts_language=str(opt.get(CONF_TTS_LANGUAGE, "")),
            tts_message=str(opt.get(CONF_TTS_MESSAGE, "")),
        )

    async def _rebind(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()

        cfg = self._cfg()

        if cfg.armed_helper:
            self._unsubs.append(async_track_state_change_event(self.hass, [cfg.armed_helper], self._on_helper))
        if cfg.manual_arm_switch:
            self._unsubs.append(async_track_state_change_event(self.hass, [cfg.manual_arm_switch], self._on_manual_switch))

        if cfg.instant:
            self._unsubs.append(async_track_state_change_event(self.hass, cfg.instant, self._on_instant))
        if cfg.delayed:
            self._unsubs.append(async_track_state_change_event(self.hass, cfg.delayed, self._on_delayed))

        if cfg.persons:
            self._unsubs.append(async_track_state_change_event(self.hass, cfg.persons, self._on_person_change))

        if cfg.arm_schedule_enable and cfg.t_start and cfg.t_end:
            self._unsubs.append(async_track_time_change(self.hass, self._on_time_start, hour=cfg.t_start.hour, minute=cfg.t_start.minute, second=0))
            self._unsubs.append(async_track_time_change(self.hass, self._on_time_end, hour=cfg.t_end.hour, minute=cfg.t_end.minute, second=0))

    # ---- Handlers ----
    async def _on_helper(self, event) -> None:
        new = event.data.get("new_state")
        if not new:
            return
        if new.state == "on":
            await self.async_alarm_arm_away()
        elif new.state == "off":
            await self.async_alarm_disarm()

    async def _on_manual_switch(self, event) -> None:
        new = event.data.get("new_state")
        old = event.data.get("old_state")
        if not new:
            return
        if old and old.state == "off" and new.state == "on":
            await self.async_alarm_arm_away()
        elif old and old.state == "on" and new.state == "off":
            await self.async_alarm_disarm()

    async def _on_instant(self, event) -> None:
        if not self._armed():
            return
        new = event.data.get("new_state")
        if new and new.state == STATE_ON:
            await self._trigger_alarm(source=new)

    async def _on_delayed(self, event) -> None:
        if not self._armed():
            return
        new = event.data.get("new_state")
        if new and new.state == STATE_ON:
            cfg = self._cfg()
            if cfg.entry_delay > 0:
                await asyncio.sleep(cfg.entry_delay)
                if not self._armed():
                    return
            await self._trigger_alarm(source=new)

    async def _on_person_change(self, event) -> None:
        cfg = self._cfg()
        if cfg.auto_disarm_any_home and self._any_person_home(cfg):
            await self.async_alarm_disarm()
        elif cfg.auto_arm_all_away and self._all_persons_away(cfg):
            await self.async_alarm_arm_away()

    async def _on_time_start(self, now: datetime) -> None:
        cfg = self._cfg()
        if cfg.arm_schedule_enable:
            await self.async_alarm_arm_night()

    async def _on_time_end(self, now: datetime) -> None:
        cfg = self._cfg()
        if cfg.arm_schedule_enable:
            await self.async_alarm_disarm()

    # ---- Helpers ----
    def _armed(self) -> bool:
        return self._state in (STATE_ALARM_ARMING, STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_NIGHT)

    def _any_person_home(self, cfg: _Config) -> bool:
        # home or in any safe zone
        zones = {'home'} | {z.split('.',1)[1] for z in cfg.safe_zones}
        for eid in cfg.persons:
            st: State | None = self.hass.states.get(eid)
            if st and st.state in zones:
                return True
        return False

    def _all_persons_away(self, cfg: _Config) -> bool:
        zones = {'home'} | {z.split('.',1)[1] for z in cfg.safe_zones}
        if not cfg.persons:
            return False
        for eid in cfg.persons:
            st: State | None = self.hass.states.get(eid)
            if not st or st.state in zones:
                return False
        return True

    def _set_state(self, new_state: str) -> None:
        if self._state != new_state:
            self._state = new_state
            self.async_write_ha_state()

    # ---- Alarm pipeline ----
    async def _trigger_alarm(self, source: State | None) -> None:
        loop = asyncio.get_running_loop()
        now = loop.time()
        cfg = self._cfg()
        if now < self._cooldown_until:
            _LOGGER.debug("cooldown active; skip")
            return

        self._set_state(STATE_ALARM_TRIGGERED)
        if source:
            self._last_trigger = source.entity_id
        await self._run_actions(source, cfg)

        await asyncio.sleep(cfg.duration)
        await self._devices_off(cfg)

        if self._state == STATE_ALARM_TRIGGERED:
            self._set_state(STATE_ALARM_ARMED_AWAY)

        self._cooldown_until = loop.time() + cfg.cooldown

    async def _run_actions(self, source: State | None, cfg: _Config) -> None:
        if cfg.scenes:
            await self.hass.services.async_call("scene", "turn_on", {ATTR_ENTITY_ID: cfg.scenes}, blocking=False)

        if cfg.lights:
            data = {ATTR_ENTITY_ID: cfg.lights}
            if cfg.brightness:
                data["brightness"] = cfg.brightness
            await self.hass.services.async_call("light", "turn_on", data, blocking=False)

        if cfg.sirens:
            data = {ATTR_ENTITY_ID: cfg.sirens}
            if cfg.duration:
                data["duration"] = cfg.duration
            await self.hass.services.async_call("siren", "turn_on", data, blocking=False)

        if cfg.switches:
            await self.hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: cfg.switches}, blocking=False)

        if cfg.scripts:
            await self.hass.services.async_call("script", "turn_on", {ATTR_ENTITY_ID: cfg.scripts}, blocking=False)

        snapshot_local = None
        if cfg.send_snapshot and cfg.cameras:
            cam = cfg.cameras[0]
            Path(cfg.snapshot_path).mkdir(parents=True, exist_ok=True)
            filename = f"{cfg.snapshot_path}/alarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            await self.hass.services.async_call("camera", "snapshot", {"entity_id": cam, "filename": filename}, blocking=True)
            snapshot_local = "/local" + filename[7:] if filename.startswith("/config/www") else filename
            self._last_snapshot = snapshot_local

        services = [s.strip() for s in (cfg.notify_services_csv or "").split(",") if s.strip()]

        ctx = {
            "now": datetime.now,
            "source_entity": source.entity_id if source else None,
            "snapshot": snapshot_local,
        }
        title_t = ha_template.Template(cfg.notify_title, self.hass)
        msg_t = ha_template.Template(cfg.notify_message, self.hass)
        title = title_t.async_render(ctx, parse_result=False) if isinstance(cfg.notify_title, str) else "ALARM"
        message = msg_t.async_render(ctx, parse_result=False) if isinstance(cfg.notify_message, str) else "Alarm"

        notify_targets = cfg.notify_targets or []
        # New notify entity API
        if self.hass.services.has_service("notify", "send_message") and notify_targets:
            data: dict[str, Any] = {"message": message, "title": title}
            if snapshot_local:
                data["data"] = {"image": snapshot_local}
            await self.hass.services.async_call("notify", "send_message", {"entity_id": notify_targets, **data}, blocking=False)
        # Legacy notify services fallback
        for svc in services:
            if "." not in svc:
                continue
            domain, service = svc.split(".", 1)
            data: dict[str, Any] = {"message": message, "title": title}
            if snapshot_local:
                data["data"] = {"image": snapshot_local}
            await self.hass.services.async_call(domain, service, data, blocking=False)

        if cfg.persistent:
            body = message + (f"\nBild: {snapshot_local}" if snapshot_local else "")
            await self.hass.services.async_call("persistent_notification", "create", {"title": title, "message": body}, blocking=False)

    async def _devices_off(self, cfg: _Config) -> None:
        if cfg.lights:
            await self.hass.services.async_call("light", "turn_off", {ATTR_ENTITY_ID: cfg.lights}, blocking=False)
        if cfg.sirens:
            await self.hass.services.async_call("siren", "turn_off", {ATTR_ENTITY_ID: cfg.sirens}, blocking=False)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {
            ATTR_LAST_TRIGGER: self._last_trigger,
            ATTR_LAST_SNAPSHOT: self._last_snapshot,
            ATTR_COOLDOWN_UNTIL: self._cooldown_until,
        }
