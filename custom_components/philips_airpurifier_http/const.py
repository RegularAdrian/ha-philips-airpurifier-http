"""Constants for Philips Air Purifier HTTP."""

from datetime import timedelta

DOMAIN = "philips_airpurifier_http"

CONF_ALLERGY_MODE = "allergy_mode"
CONF_LIGHT_CONTROL = "light_control"
CONF_POLLING_INTERVAL = "polling_interval"
CONF_SLEEP_SPEED = "sleep_speed"
CONF_TIMEOUT = "timeout"

DEFAULT_NAME = "Philips Air Purifier"
DEFAULT_POLLING_INTERVAL = 120
DEFAULT_TIMEOUT = 30
MIN_POLLING_INTERVAL = 30

DEFAULT_SCAN_INTERVAL = timedelta(seconds=DEFAULT_POLLING_INTERVAL)

PRESET_NORMAL = "normal"
PRESET_SLEEP = "sleep"
PRESET_SPEED_1 = "speed_1"
PRESET_SPEED_2 = "speed_2"
PRESET_SPEED_3 = "speed_3"
PRESET_TURBO = "turbo"
PRESET_ALLERGY = "allergy"
PRESET_BACTERIA = "bacteria_virus"
