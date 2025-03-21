"""
Home Assistant integration for Tuya sensors.
This integration uses the tuya-connector-python library to poll sensor data.
"""
import logging
from datetime import timedelta
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import (
    CONF_API_KEY,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

DOMAIN = "tuya_sensors"
_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]
MIN_SCAN_INTERVAL = timedelta(seconds=30)
DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)

# Custom constants
CONF_API_SECRET = "api_secret"
CONF_DEVICE_IDS = "device_ids"
CONF_INCLUDE_SENSORS = "include_sensors"
CONF_EXCLUDE_SENSORS = "exclude_sensors"

# Configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_API_SECRET): cv.string,
                vol.Required(CONF_DEVICE_IDS): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_INCLUDE_SENSORS, default=[]): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_EXCLUDE_SENSORS, default=[]): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_REGION, default="us"): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(cv.time_period, vol.Clamp(min=MIN_SCAN_INTERVAL)),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Tuya Sensors component."""
    if DOMAIN not in config:
        return True
        
    conf = config[DOMAIN]
    api_key = conf[CONF_API_KEY]
    api_secret = conf[CONF_API_SECRET]
    device_ids = conf[CONF_DEVICE_IDS]
    include_sensors = conf[CONF_INCLUDE_SENSORS]
    exclude_sensors = conf[CONF_EXCLUDE_SENSORS]
    region = conf[CONF_REGION]
    scan_interval = conf[CONF_SCAN_INTERVAL]
    
    hass.data[DOMAIN] = {
        "api_key": api_key,
        "api_secret": api_secret,
        "device_ids": device_ids,
        "include_sensors": include_sensors,
        "exclude_sensors": exclude_sensors,
        "region": region,
        "scan_interval": scan_interval,
    }
    
    # Setup integration-wide data
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    return True

# Add these new functions for config flow support
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tuya from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok