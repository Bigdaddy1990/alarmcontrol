
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
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
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import event as ha_event

from .const import (
    DEFAULTS,
    DOMAIN,
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

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([AlarmControl(hass, entry)], update_before_add=False)


@dataclass
class _Config:
    name: str
    instant: list[str]
    delayed: list[str]
    persons: list[str]
    safe_zones: list[str]
    use_window: bool
    t_start: datetime | None
    t_end: datetime | None
    exit_delay: int
    entry_delay: int
    duration: int
    cooldown: int
    cameras: list[str]
    send_snapshot: bool
    snapshot_path: str
    notify_services: list[str]
    persistent: bool
    lights: list[str]
    brightness: int
    sirens: list[str]
    switches: list[str]
    scenes: list[str]
    scripts: list[str]
    media_players: list[str]


class AlarmControl(AlarmControlPanelEntity):
    _attr_has_entity_name = True
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.options.get("name", DEFAULTS["name"])
        self._state = STATE_ALARM_DISARMED
        self._unsubs: list[callable] = []
        self._cooldown_until: float = 0.0

    @property
    def state(self) -> str | None:
        return self._state

    async def async_added_to_hass(self) -> None:
        await self._rebind()

    async def async_will_remove_from_hass(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()

    # --- Arm/Disarm API ---
    async def async_alarm_disarm(self, code: str | None = None) -> None:
        self._set_state(STATE_ALARM_DISARMED)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._arm_with_exit_delay(STATE_ALARM_ARMED_AWAY)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._arm_with_exit_delay(STATE_ALARM_ARMED_NIGHT)

    # --- Core ---
    async def _arm_with_exit_delay(self, target_state: str) -> None:
        cfg = self._cfg()
        if cfg.exit_delay > 0:
            self._set_state(STATE_ALARM_ARMING)
            await asyncio.sleep(cfg.exit_delay)
        self._set_state(target_state)

    def _cfg(self) -> _Config:
        opt = {**DEFAULTS, **self.entry.options}
        t_start = ha_event.parse_time(opt.get(CONF_TIME_START)) if opt.get(CONF_TIME_START) else None
        t_end = ha_event.parse_time(opt.get(CONF_TIME_END)) if opt.get(CONF_TIME_END) else None
        return _Config(
            name=opt["name"],
            instant=list(opt.get(CONF_INSTANT, [])),
            delayed=list(opt.get(CONF_DELAYED, [])),
            persons=list(opt.get(CONF_PERSONS, [])),
            safe_zones=list(opt.get(CONF_SAFE_ZONES, [])),
            use_window=bool(opt.get(CONF_USE_WINDOW, False)),
            t_start=t_start,
            t_end=t_end,
            exit_delay=int(opt.get(CONF_EXIT)),
            entry_delay=int(opt.get(CONF_ENTRY)),
            duration=int(opt.get(CONF_DURATION)),
            cooldown=int(opt.get(CONF_COOLDOWN)),
            cameras=list(opt.get(CONF_CAMERAS, [])),
            send_snapshot=bool(opt.get(CONF_SEND_SNAPSHOT)),
            snapshot_path=str(opt.get(CONF_SNAPSHOT_PATH)),
            notify_services=list(opt.get(CONF_NOTIFY_SERVICES, [])),
            persistent=bool(opt.get(CONF_PERSISTENT)),
            lights=list(opt.get(CONF_LIGHTS, [])),
            brightness=int(opt.get(CONF_BRIGHTNESS)),
            sirens=list(opt.get(CONF_SIRENS, [])),
            switches=list(opt.get(CONF_SWITCHES, [])),
            scenes=list(opt.get(CONF_SCENES, [])),
            scripts=list(opt.get(CONF_SCRIPTS, [])),
            media_players=list(opt.get(CONF_MEDIA_PLAYERS, [])),
        )

    async def _rebind(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()

        cfg = self._cfg()

        if cfg.instant:
            self._unsubs.append(
                async_track_state_change_event(self.hass, cfg.instant, self._on_instant)
            )
        if cfg.delayed:
            self._unsubs.append(
                async_track_state_change_event(self.hass, cfg.delayed, self._on_delayed)
            )
        if cfg.persons:
            self._unsubs.append(
                async_track_state_change_event(self.hass, cfg.persons, self._on_person_change)
            )
        if cfg.use_window and cfg.t_start and cfg.t_end:
            self._unsubs.append(
                async_track_time_change(
                    self.hass, self._on_time_start, hour=cfg.t_start.hour, minute=cfg.t_start.minute, second=0
                )
            )
            self._unsubs.append(
                async_track_time_change(
                    self.hass, self._on_time_end, hour=cfg.t_end.hour, minute=cfg.t_end.minute, second=0
                )
            )

    # --- Event handler ---
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
        # unscharf: jemand in Safe-Zone/home
        if cfg.persons and self._any_person_in_safe_zone(cfg):
            await self.async_alarm_disarm()
        # scharf: alle weg
        elif cfg.persons and self._all_persons_away(cfg):
            await self.async_alarm_arm_away()

    async def _on_time_start(self, now: datetime) -> None:
        cfg = self._cfg()
        if cfg.use_window:
            await self.async_alarm_arm_night()

    async def _on_time_end(self, now: datetime) -> None:
        cfg = self._cfg()
        if cfg.use_window:
            await self.async_alarm_disarm()

    # --- Helpers ---
    def _armed(self) -> bool:
        return self._state in (STATE_ALARM_ARMING, STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_NIGHT)

    def _any_person_in_safe_zone(self, cfg: _Config) -> bool:
        zones = {"home"} | {z.split(".", 1)[1] for z in cfg.safe_zones}
        for eid in cfg.persons:
            st: State | None = self.hass.states.get(eid)
            if st and st.state in zones:
                return True
        return False

    def _all_persons_away(self, cfg: _Config) -> bool:
        if not cfg.persons:
            return False
        zones = {"home"} | {z.split(".", 1)[1] for z in cfg.safe_zones}
        for eid in cfg.persons:
            st: State | None = self.hass.states.get(eid)
            if not st or st.state in zones:
                return False
        return True

    def _set_state(self, new_state: str) -> None:
        if self._state != new_state:
            self._state = new_state
            self.async_write_ha_state()

    async def _trigger_alarm(self, source: State | None) -> None:
        loop = asyncio.get_running_loop()
        now = loop.time()
        cfg = self._cfg()
        if now < self._cooldown_until:
            _LOGGER.debug("cooldown active; skip")
            return

        self._set_state(STATE_ALARM_TRIGGERED)
        await self._run_actions(source, cfg)

        await asyncio.sleep(cfg.duration)
        await self._devices_off(cfg)

        # bleibt „armed_*“
        if self._state == STATE_ALARM_TRIGGERED:
            self._set_state(STATE_ALARM_DISARMED)

        self._cooldown_until = loop.time() + cfg.cooldown

    async def _run_actions(self, source: State | None, cfg: _Config) -> None:
        # Szenen
        if cfg.scenes:
            await self.hass.services.async_call("scene", "turn_on", {ATTR_ENTITY_ID: cfg.scenes}, blocking=False)

        # Lichter
        if cfg.lights:
            data = {ATTR_ENTITY_ID: cfg.lights}
            if cfg.brightness:
                data["brightness"] = cfg.brightness
            await self.hass.services.async_call("light", "turn_on", data, blocking=False)

        # Sirenen
        if cfg.sirens:
            data = {ATTR_ENTITY_ID: cfg.sirens}
            if cfg.duration:
                data["duration"] = cfg.duration
            await self.hass.services.async_call("siren", "turn_on", data, blocking=False)

        # Schalter
        if cfg.switches:
            await self.hass.services.async_call("switch", "turn_on", {ATTR_ENTITY_ID: cfg.switches}, blocking=False)

        # Skripte
        if cfg.scripts:
            await self.hass.services.async_call("script", "turn_on", {ATTR_ENTITY_ID: cfg.scripts}, blocking=False)

        # Snapshot
        snapshot_local = None
        if cfg.send_snapshot and cfg.cameras:
            cam = cfg.cameras[0]
            Path(cfg.snapshot_path).mkdir(parents=True, exist_ok=True)
            filename = f"{cfg.snapshot_path}/alarm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            await self.hass.services.async_call(
                "camera", "snapshot", {"entity_id": cam, "filename": filename}, blocking=True
            )
            snapshot_local = "/local" + filename[7:] if filename.startswith("/config/www") else filename

        # Notify
        msg = f"ALARM — {source.entity_id if source else 'unbekannt'} — {datetime.now().isoformat(timespec='seconds')}"
        for svc in cfg.notify_services:
            domain, service = svc.split(".", 1)
            data: dict[str, Any] = {"message": msg}
            if snapshot_local:
                data["data"] = {"image": snapshot_local}
            await self.hass.services.async_call(domain, service, data, blocking=False)

        # Persistent
        if cfg.persistent:
            body = msg + (f"\nBild: {snapshot_local}" if snapshot_local else "")
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {"title": "ALARM", "message": body},
                blocking=False,
            )

    async def _devices_off(self, cfg: _Config) -> None:
        if cfg.lights:
            await self.hass.services.async_call("light", "turn_off", {ATTR_ENTITY_ID: cfg.lights}, blocking=False)
        if cfg.sirens:
            await self.hass.services.async_call("siren", "turn_off", {ATTR_ENTITY_ID: cfg.sirens}, blocking=False)
