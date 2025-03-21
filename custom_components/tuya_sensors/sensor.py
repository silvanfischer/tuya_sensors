"""Sensor platform for Tuya sensors integration."""
import logging
from datetime import timedelta
import re
import asyncio

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfEnergy,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import DOMAIN, _LOGGER, CONF_INCLUDE_SENSORS, CONF_EXCLUDE_SENSORS

# Mapping of Tuya codes to Home Assistant sensor types
# This is a starting point and can be expanded
SENSOR_TYPES = {
    # Temperature
    "temp_current": {"name": "Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temperature": {"name": "Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp_indoor": {"name": "Indoor Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "Tin": {"name": "Indoor Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "ToutCh1": {"name": "Outdoor Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "temp_outdoor": {"name": "Outdoor Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    
    # Humidity
    "humidity": {"name": "Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "humidity_indoor": {"name": "Indoor Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "Hin": {"name": "Indoor Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "HoutCh1": {"name": "Outdoor Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "humidity_outdoor": {"name": "Outdoor Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    
    # Power
    "cur_power": {"name": "Current Power", "device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT},
    "add_ele": {"name": "Power Consumption", "device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING},
    
    # Voltage/Current
    "cur_voltage": {"name": "Voltage", "device_class": SensorDeviceClass.VOLTAGE, "unit": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT},
    "cur_current": {"name": "Current", "device_class": SensorDeviceClass.CURRENT, "unit": UnitOfElectricCurrent.AMPERE, "state_class": SensorStateClass.MEASUREMENT},
    
    # Battery
    "battery_percentage": {"name": "Battery", "device_class": SensorDeviceClass.BATTERY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
    "battery_state": {"name": "Battery State", "device_class": None, "unit": None, "state_class": None},
    
    # CO2, VOC, PM2.5
    "co2_value": {"name": "CO2", "device_class": SensorDeviceClass.CO2, "unit": "ppm", "state_class": SensorStateClass.MEASUREMENT},
    "pm25_value": {"name": "PM2.5", "device_class": SensorDeviceClass.PM25, "unit": "μg/m³", "state_class": SensorStateClass.MEASUREMENT},
    "voc_value": {"name": "VOC", "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS, "unit": "ppb", "state_class": SensorStateClass.MEASUREMENT},
    
    # Illuminance
    "bright_value": {"name": "Brightness", "device_class": SensorDeviceClass.ILLUMINANCE, "unit": "lx", "state_class": SensorStateClass.MEASUREMENT},
    
    # Pressure
    "pressure": {"name": "Pressure", "device_class": SensorDeviceClass.PRESSURE, "unit": UnitOfPressure.HPA, "state_class": SensorStateClass.MEASUREMENT},
    
    # Generic
    "countdown": {"name": "Countdown", "device_class": SensorDeviceClass.DURATION, "unit": UnitOfTime.SECONDS, "state_class": SensorStateClass.MEASUREMENT},
    "filter_life": {"name": "Filter Life", "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
}

async def async_setup_platform(
    hass,
    config,
    async_add_entities,
    discovery_info = None,
) -> None:
    # Get config from hass.data
    domain_config = hass.data[DOMAIN]
    await _async_setup(hass, domain_config, async_add_entities)

async def async_setup_entry(
    hass,
    entry,
    async_add_entities
) -> None:
    # Get config from hass.data
    domain_config = hass.data[DOMAIN].get(entry.entry_id)
    await _async_setup(hass, domain_config, async_add_entities)

async def _async_setup(
    hass,
    domain_config,
    async_add_entities
) -> None:
    """Set up the Tuya sensor."""
    try:
        from tuya_connector import TuyaOpenAPI, TUYA_LOGGER
    except ImportError:
        _LOGGER.error("Failed to import tuya_connector. Make sure it's installed.")
        return

    # Set up logging for tuya_connector
    TUYA_LOGGER.setLevel(logging.INFO)
    
    api_key = domain_config["api_key"]
    api_secret = domain_config["api_secret"]
    device_ids = domain_config["device_ids"]
    include_sensors = domain_config.get("include_sensors", [])
    exclude_sensors = domain_config.get("exclude_sensors", [])
    region = domain_config["region"]
    scan_interval = domain_config["scan_interval"]

    # Set appropriate endpoint based on region
    endpoint = f"https://openapi.tuya{region}.com"

    # Initialize API connection
    tuya_api = TuyaOpenAPI(
        access_id=api_key,
        access_secret=api_secret,
        endpoint=endpoint
    )
    
    try:
        # Get access token
        response = await hass.async_add_executor_job(tuya_api.connect)
        
        if not response.get("success", False):
            _LOGGER.error("Failed to get access token: %s", response)
            return

        sensor_entities = []
        all_devices = []
        
        # If specific device IDs are provided, use them
        if device_ids:
            for device_id in device_ids:
                try:
                    # Get device info
                    response = await hass.async_add_executor_job(
                        tuya_api.get, f"/v1.0/devices/{device_id}"
                    )
                    
                    if not response.get("success", False):
                        _LOGGER.error("Failed to get device info for %s: %s", device_id, response)
                        continue
                    
                    device_info = response.get("result", {})
                    all_devices.append(device_info)
                except Exception as e:
                    _LOGGER.error("Error processing device %s: %s", device_id, str(e))
        else:
            # If no specific devices are provided, discover all devices
            response = await hass.async_add_executor_job(tuya_api.get, "/v1.0/devices")
            
            if not response.get("success", False):
                _LOGGER.error("Failed to get devices: %s", response)
                return
                
            all_devices = response.get("result", [])
            
        # Process each device to discover sensors
        for device in all_devices:
            device_id = device.get("id")
            device_name = device.get("name", f"Device {device_id}")

            # Create a coordinator for this device
            coordinator = TuyaDataCoordinator(
                hass,
                _LOGGER,
                tuya_api,
                device_id,
                scan_interval
            )
            
            try:
                # Get device status to see what sensors are available
                status_response = await hass.async_add_executor_job(
                    tuya_api.get, f"/v1.0/devices/{device_id}/status"
                )
                
                if not status_response.get("success", False):
                    _LOGGER.warning("Failed to get status for device %s: %s", device_id, status_response)
                    continue
                
                status_data = status_response.get("result", [])
                
                # Get device specification for additional sensor metadata
                specs_response = await hass.async_add_executor_job(
                    tuya_api.get, f"/v1.0/devices/{device_id}/specifications"
                )
                
                spec_data = {}
                if specs_response.get("success", False):
                    specs = specs_response.get("result", {})
                    spec_data = specs.get("status", [])
                
                # Create a map of code to spec for easier lookup
                spec_map = {item.get("code"): item for item in spec_data if "code" in item}
                
                # Process each sensor data point
                for sensor_data in status_data:
                    code = sensor_data.get("code")
                    value = sensor_data.get("value")
                    
                    # Skip if code is None
                    if code is None:
                        continue
                    
                    # Check if this sensor should be included/excluded
                    if include_sensors and code not in include_sensors:
                        continue
                    if code in exclude_sensors:
                        continue
                    
                    # Get sensor type definition from our mapping
                    sensor_type = SENSOR_TYPES.get(code)
                    
                    # If we don't have a predefined type, try to auto-detect
                    if not sensor_type:
                        sensor_type = auto_detect_sensor_type(code, value, spec_map.get(code, {}))
                    
                    # Skip if we still can't determine the sensor type
                    if not sensor_type:
                        _LOGGER.debug("Skipping unknown sensor type: %s with value %s", code, value)
                        continue
                    
                    # Create sensor entity
                    sensor_entity = TuyaSensor(
                        coordinator=coordinator,
                        device_name=device_name,
                        code=code,
                        name=sensor_type["name"],
                        device_class=sensor_type["device_class"],
                        unit=sensor_type["unit"],
                        state_class=sensor_type["state_class"]
                    )
                    
                    sensor_entities.append(sensor_entity)        
            
            except Exception as e:
                _LOGGER.error("Error discovering sensors for device %s: %s", device_id, str(e))
        
        # Add all discovered sensor entities
        if sensor_entities:
            _LOGGER.info("Found %d Tuya sensors", len(sensor_entities))
            async_add_entities(sensor_entities, update_before_add=True)

        else:
            _LOGGER.warning("No compatible sensors found in your Tuya account")
            
    except Exception as e:
        _LOGGER.error("Error setting up Tuya sensors integration: %s", str(e))


def auto_detect_sensor_type(code, value, spec_data):
    """Try to auto-detect sensor type based on code, value and specifications."""
    # Try to detect by code name patterns
    if "temp" in code:
        return {"name": "Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT}
    elif "humidity" in code:
        return {"name": "Humidity", "device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT}
    elif "power" in code or "energy" in code or "electricity" in code:
        if isinstance(value, (int, float)) and value > 1000:  # Likely energy counter
            return {"name": "Energy", "device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING}
        else:
            return {"name": "Power", "device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT}
    elif "voltage" in code:
        return {"name": "Voltage", "device_class": SensorDeviceClass.VOLTAGE, "unit": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT}
    elif "current" in code and not "power" in code:
        return {"name": "Current", "device_class": SensorDeviceClass.CURRENT, "unit": UnitOfElectricCurrent.AMPERE, "state_class": SensorStateClass.MEASUREMENT}
    elif "battery" in code:
        return {"name": "Battery", "device_class": SensorDeviceClass.BATTERY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT}
    elif "co2" in code:
        return {"name": "CO2", "device_class": SensorDeviceClass.CO2, "unit": "ppm", "state_class": SensorStateClass.MEASUREMENT}
    elif "pm25" in code or "pm2_5" in code:
        return {"name": "PM2.5", "device_class": SensorDeviceClass.PM25, "unit": "μg/m³", "state_class": SensorStateClass.MEASUREMENT}
    
    # Try to detect based on specification data
    if spec_data:
        if spec_data.get("type") == "Integer" or spec_data.get("type") == "Float":
            # Try to determine unit and type from value range and step
            value_min = spec_data.get("min", -1)
            value_max = spec_data.get("max", -1)
            
            # Generic percentage sensor if range is 0-100
            if value_min == 0 and value_max == 100:
                return {"name": code.replace("_", " ").title(), "device_class": None, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT}
    
    # Default: create a generic sensor with the code as name
    return {"name": code.replace("_", " ").title(), "device_class": None, "unit": None, "state_class": None}

class TuyaDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tuya data."""

    def __init__(self, hass, logger, tuya_api, device_id, scan_interval):
        """Initialize."""

        if isinstance(scan_interval, int):
            scan_interval = timedelta(seconds=scan_interval)

        super().__init__(
            hass,
            logger,
            name=f"tuya_{device_id}",
            update_interval=scan_interval,
        )
        self._tuya_api = tuya_api
        self._device_id = device_id

    async def _async_update_data(self):
        """Fetch data from Tuya API."""
        try:
            # Get device state from Tuya API
            response = await self.hass.async_add_executor_job(
                self._tuya_api.get, f"/v1.0/devices/{self._device_id}/status"
            )
            
            if not response.get("success", False):
                raise UpdateFailed(f"Failed to get status for device {self._device_id}")
                
            return response.get("result", [])
        except Exception as e:
            raise UpdateFailed(f"Error communicating with Tuya API: {e}")

class TuyaSensor(SensorEntity):
    """Representation of a Tuya Sensor."""
    
    def __init__(self, coordinator, device_name, code, name, device_class, unit, state_class):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._device_id = coordinator._device_id
        self._code = code
        self._name = f"{device_name} {name}"
        
        # Set entity properties
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"tuya_{self._device_id}_{code}"
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
        
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        # Extract value for this specific sensor
        for state in self.coordinator.data:
            if state.get("code") == self._code:
                if self._attr_device_class == SensorDeviceClass.TEMPERATURE:
                    return int(state.get("value")) / 10
                else:
                    return state.get("value")
        return None
        
    @property
    def available(self):
        """Return True if entity is available."""
        return self.coordinator.last_update_success
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "device_id": self._device_id,
            "code": self._code,
            "last_updated": self.coordinator.last_update_success
        }
        
    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
        
    async def async_update(self):
        """Update entity."""
        await self.coordinator.async_request_refresh()