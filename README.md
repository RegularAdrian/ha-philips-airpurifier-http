# Philips Air Purifier HTTP for Home Assistant

This is a small custom integration fork aimed at Philips air purifiers that work through `http` in `homebridge-philips-air`.

It was created because the common Home Assistant `philips_airpurifier_coap` custom component is CoAP-only and YAML-only. If your Homebridge config uses `"protocol": "http"`, that CoAP integration is unlikely to add or communicate with the purifier.

## Install

Copy `custom_components/philips_airpurifier_http` into your Home Assistant `custom_components` folder, then restart Home Assistant.

You should then be able to add it from:

`Settings -> Devices & services -> Add integration -> Philips Air Purifier HTTP`

For your purifier, use:

- Host: `REDACTED`
- Name: `Air Purifier`
- Polling interval: `120`
- Enable sleep speed: yes
- Enable allergy mode: yes
- Enable light controls: yes

## What works in this first fork

- Direct encrypted HTTP communication, based on the same protocol used by the Homebridge plugin.
- UI config flow.
- Fan on/off.
- Preset modes for AC2889-style devices: normal auto, allergy/allergen, bacteria/virus, manual speeds, turbo, and sleep.
- Separate dropdown controls for auto mode and manual fan speed, because Home Assistant's default fan tile may only show on/off.
- Timer control for the purifier's built-in shutoff timer.
- More explicit air-quality sensors, including a readable Air Quality sensor, PM2.5, indoor allergen index, display preference, and timer remaining.
- Local `icon.png` and `logo.png` assets for custom-integration displays.
- Sensors for PM2.5, humidity, temperature, indoor allergen index, air quality index, water level, error code, and filter life values when the purifier reports them.
- Optional light entity for display/air-quality light brightness.

## Notes

This is a pragmatic first version. If it connects successfully, the next improvements should be:

- Add humidifier controls for combo purifier/humidifier models.
- Add button/switch entities for child lock and display backlight.
- Add model-specific device classes if your model exposes unusual status keys.
- Package it as a GitHub/HACS repository.
