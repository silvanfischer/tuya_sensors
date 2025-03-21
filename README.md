# Home Assistant TuyaCloud Sensor Integration

This Home Assistant integration allows you to connect and read sensor data from Tuya Cloud using the `tuya-connector-python` library. It supports both **UI-based configuration (config flow)** and **manual setup via `configuration.yaml`**.

## Features
- Read sensor data from Tuya Cloud.
- Support for multiple device IDs.
- Configurable scan interval.
- Setup via **Home Assistant UI** or **configuration.yaml**.
- Works with sensors that are **not yet supported** through the official Tuya Integration on Home Assistant.

---

## Installation
### Manual Installation
1. Download the integration files and place them in your Home Assistant `custom_components/tuya_sensors` directory.
2. Restart Home Assistant.

### HACS (Recommended)
1. Add this repository as a custom repository in HACS.
2. Install the integration via HACS.
3. Restart Home Assistant.

---

## Configuration
### **Option 1: UI Setup (Recommended)**
1. Navigate to **Settings → Devices & Services → Add Integration**.
2. Search for **Tuya Sensors**.
3. Enter your Tuya API credentials:
   - **API Key**
   - **API Secret**
   - **Region** (e.g., `us`, `eu`, `cn`)
   - **Device IDs** (comma-separated list)
   - **Scan Interval** (optional, in seconds)
4. Click **Submit**.

### **Option 2: Configuration via `configuration.yaml`**
Alternatively, you can configure the integration manually:

```yaml
# Example configuration.yaml entry
  tuya_sensors:
    api_key: "your_api_key"
    api_secret: "your_api_secret"
    device_ids:
      - "device_id_1"
      - "device_id_2"
    region: "us"
    scan_interval: 60  # Optional, in seconds
```

After modifying `configuration.yaml`, restart Home Assistant.

---

## Updating Options
- If configured via **UI**, you can update options by going to:
  **Settings → Devices & Services → Tuya Sensors → Configure**.
- If using **configuration.yaml**, edit the file and restart Home Assistant.

---

## Troubleshooting
### Sensors are not updating
- Ensure your Tuya API credentials are correct.
- Check logs in **Developer Tools → Logs** for errors.
- Increase `scan_interval` if updates are too frequent.

### Integration is not loading
- Make sure the files are in `custom_components/tuya_sensors/`.
- Restart Home Assistant after installing the integration.
- Check logs for error messages related to `tuya_sensors`.

---

## Contributing
Contributions and feature requests are welcome! Feel free to open an issue or submit a pull request.

---

## License
This project is licensed under the MIT License.
