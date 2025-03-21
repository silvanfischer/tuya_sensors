# Define the configuration flow for Tuya integration
# File: custom_components/tuya_sensors/config_flow.py

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
import homeassistant.helpers.config_validation as cv

# Define schema constants
DOMAIN = "tuya_sensors"
CONF_API_SECRET = "api_secret"
CONF_REGION = "region"
CONF_DEVICE_IDS = "device_ids"
CONF_INCLUDE_SENSORS = "include_sensors"
CONF_EXCLUDE_SENSORS = "exclude_sensors"

# Region options
REGIONS = ["us", "eu", "cn", "in"]

# Common sensor types that might be available
COMMON_SENSORS = [
    "temp_current",
    "humidity",
    "power",
    "current",
    "voltage",
    "countdown",
    "battery",
    "switch",
    "motion",
    "brightness"
]

class TuyaSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tuya Sensors integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Process device IDs as a list
            device_ids = [id.strip() for id in user_input[CONF_DEVICE_IDS].split(",") if id.strip()]
            user_input[CONF_DEVICE_IDS] = device_ids

            # Create entry
            return self.async_create_entry(
                title=f"Tuya Cloud ({user_input[CONF_REGION]})",
                data=user_input,
            )

        # Show form for credentials
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_API_SECRET): str,
                vol.Required(CONF_DEVICE_IDS): str,
                vol.Required(CONF_REGION, default="us"): vol.In(REGIONS),
                vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=300)
                ),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return TuyaOptionsFlowHandler(config_entry)


class TuyaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Tuya integration options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.sensor_options = {s: s for s in COMMON_SENSORS}

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            # Update the options
            device_ids = [id.strip() for id in user_input[CONF_DEVICE_IDS].split(",") if id.strip()]
            user_input[CONF_DEVICE_IDS] = device_ids
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, 60))
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=300)),
                vol.Required(CONF_DEVICE_IDS, default=", ".join(data.get(CONF_DEVICE_IDS, ""))): str,
                vol.Optional(
                    CONF_INCLUDE_SENSORS,
                    default=options.get(CONF_INCLUDE_SENSORS, data.get(CONF_INCLUDE_SENSORS, []))
                ): cv.multi_select(self.sensor_options),
                vol.Optional(
                    CONF_EXCLUDE_SENSORS,
                    default=options.get(CONF_EXCLUDE_SENSORS, data.get(CONF_EXCLUDE_SENSORS, []))
                ): cv.multi_select(self.sensor_options),
            }),
            errors=errors,
        )