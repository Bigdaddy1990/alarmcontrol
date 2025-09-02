from __future__ import annotations

DOMAIN: str = "alarmcontrol"
PLATFORMS: list[str] = ["alarm_control_panel"]

# Blueprint-aligned option keys
CONF_NAME = "name"
CONF_ARMED_HELPER = "armed_helper_entity"
CONF_MANUAL_ARM_SWITCH = "manual_arm_switch_entity"

CONF_AUTO_ARM_ALL_AWAY = "auto_arm_all_away"
CONF_AUTO_DISARM_ANY_HOME = "auto_disarm_on_any_home"
CONF_PERSONS = "persons"
CONF_SAFE_ZONES = "safe_zones"
CONF_ARM_SCHEDULE_ENABLE = "arm_schedule_enable"
CONF_TIME_START = "arm_time_start"
CONF_TIME_END = "arm_time_end"

CONF_EXIT = "exit_delay"
CONF_ENTRY = "entry_delay"
CONF_DURATION = "alarm_duration"
CONF_COOLDOWN = "retrigger_cooldown"

CONF_INSTANT = "instant_sensors"
CONF_DELAYED = "delayed_sensors"

CONF_CAMERAS = "camera_entities"
CONF_SEND_SNAPSHOT = "send_snapshot"
CONF_SNAPSHOT_PATH = "snapshot_path"

CONF_NOTIFY_SERVICES_CSV = "notify_services_csv"
CONF_NOTIFY_TITLE = "notify_title"
CONF_NOTIFY_MESSAGE = "notify_message"
CONF_PERSISTENT = "persistent_enable"

CONF_LIGHTS = "lights"
CONF_BRIGHTNESS = "light_brightness"
CONF_SIRENS = "sirens"
CONF_MEDIA_PLAYERS = "media_players"
CONF_SWITCHES = "switches"
CONF_SCENES = "scenes"
CONF_SCRIPTS = "scripts"

CONF_MEDIA_ALARM_URL = "media_alarm_url"
CONF_MEDIA_VOLUME = "media_volume"

DEFAULTS = {
    CONF_NAME: "Alarm Control",
    CONF_AUTO_ARM_ALL_AWAY: True,
    CONF_AUTO_DISARM_ANY_HOME: True,
    CONF_ARM_SCHEDULE_ENABLE: False,
    CONF_TIME_START: "22:00:00",
    CONF_TIME_END: "06:00:00",
    CONF_EXIT: 30,
    CONF_ENTRY: 15,
    CONF_DURATION: 300,
    CONF_COOLDOWN: 60,
    CONF_SEND_SNAPSHOT: True,
    CONF_SNAPSHOT_PATH: "/config/www/snapshots",
    CONF_NOTIFY_SERVICES_CSV: "notify.persistent_notification",
    CONF_NOTIFY_TITLE: "ALARM",
    CONF_NOTIFY_MESSAGE: "{{ now().strftime('%Y-%m-%d %H:%M:%S') }} — Alarm von {{ source_entity if source_entity else 'unbekannt' }}",
    CONF_PERSISTENT: True,
    CONF_BRIGHTNESS: 255,
}

CONF_NOTIFY_TARGETS = "notify_targets"  # list of notify.* entities for notify.send_message
CONF_NOTIFY_LEGACY_CSV = "notify_services_csv"  # keep for legacy services
CONF_TTS_ENTITIES = "tts_entities"  # list of tts.* entities to use with tts.speak
CONF_TTS_LANGUAGE = "tts_language"
CONF_TTS_MESSAGE = "tts_message"

ATTR_LAST_TRIGGER = "last_trigger_entity"
ATTR_LAST_SNAPSHOT = "last_snapshot_url"
ATTR_COOLDOWN_UNTIL = "cooldown_until"

SERVICE_GENERATE_DASHBOARD = "generate_dashboard"
DASHBOARD_FILENAME_DEFAULT = "/config/www/alarmcontrol_dashboard.yaml"
