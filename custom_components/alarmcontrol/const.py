
from __future__ import annotations

DOMAIN: str = "alarmcontrol"
PLATFORMS: list[str] = ["alarm_control_panel"]

CONF_NAME = "name"
CONF_INSTANT = "instant_sensors"
CONF_DELAYED = "delayed_sensors"
CONF_PERSONS = "persons"
CONF_SAFE_ZONES = "safe_zones"
CONF_USE_WINDOW = "use_time_window"
CONF_TIME_START = "arm_time_start"
CONF_TIME_END = "arm_time_end"
CONF_EXIT = "exit_delay"
CONF_ENTRY = "entry_delay"
CONF_DURATION = "alarm_duration"
CONF_COOLDOWN = "retrigger_cooldown"
CONF_CAMERAS = "cameras"
CONF_SEND_SNAPSHOT = "send_snapshot"
CONF_SNAPSHOT_PATH = "snapshot_path"

CONF_NOTIFY_SERVICES = "notify_services"
CONF_PERSISTENT = "persistent_enable"
CONF_LIGHTS = "lights"
CONF_BRIGHTNESS = "light_brightness"
CONF_SIRENS = "sirens"
CONF_SWITCHES = "switches"
CONF_SCENES = "scenes"
CONF_SCRIPTS = "scripts"
CONF_MEDIA_PLAYERS = "media_players"

DEFAULTS = {
    CONF_NAME: "Alarm Control",
    CONF_USE_WINDOW: False,
    CONF_TIME_START: "22:00:00",
    CONF_TIME_END: "06:00:00",
    CONF_EXIT: 30,
    CONF_ENTRY: 15,
    CONF_DURATION: 300,
    CONF_COOLDOWN: 60,
    CONF_SEND_SNAPSHOT: True,
    CONF_SNAPSHOT_PATH: "/config/www/snapshots",
    CONF_NOTIFY_SERVICES: [],
    CONF_PERSISTENT: True,
    CONF_BRIGHTNESS: 255,
}
