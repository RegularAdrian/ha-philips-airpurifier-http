# Philips Air Purifier HTTP for Home Assistant

This is a small custom integration fork aimed at Philips air purifiers that work through `http` in `homebridge-philips-air`.

## Install

Copy `custom_components/philips_airpurifier_http` into your Home Assistant `custom_components` folder, then restart Home Assistant.

You should then be able to add it from:

`Settings -> Devices & services -> Add integration -> Philips Air Purifier HTTP`

For your purifier, use:

- Host: 'IP Address Here'
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
- Sensors for PM2.5, humidity, temperature, indoor allergen index, air quality index, water level, error code, and filter life values when the purifier reports them.
- Optional light entity for display/air-quality light brightness.
