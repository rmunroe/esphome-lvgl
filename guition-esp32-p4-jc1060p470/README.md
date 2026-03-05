# Guition ESP32-P4 JC1060P470 (7")

7-inch touch LCD panel with ESP32-P4, running ESPHome and LVGL for home automation and sensor displays.

![Guition ESP32-P4 JC1060P470](../images/guition-esp32-p4-jc1060p470.jpg)

## Living Room Dashboard

This device is configured as a **Living Room** control panel with 3 tabs and a persistent header bar.

### Header Bar (always visible)

- Outdoor / indoor temperature (from `weather.openweathermap` and `sensor.living_room_temperature`)
- Clock (SNTP)
- Humidity (`sensor.living_room_sensor_humidity`) + connection status LED

### Tab 1: Lights

- **Scene bar** — quick-fire scene buttons: All Off, Energize, Read, Relax
- **Light controls** — 4 toggle buttons with brightness sliders:
  - Track Lights (`light.living_room_track_lights`)
  - Floor Lamp (`light.hue_color_lamp_1_5`)
  - Table Lamp (`light.hue_color_lamp_1_4`)
  - Art Deco (`light.living_room_art_deco_lamp`)
- **Other Rooms** — toggles for Chandelier, Picture Lights, Study

### Tab 2: Climate

- **Blinds** — arc control + Open/Stop/Close buttons for `cover.living_room_blind`
- **Ceiling Fan** — arc control + Off/Low/Med/High buttons for `fan.living_room_fans`
- **Environment** — indoor temp, humidity, and outdoor temp bars

### Tab 3: Media

- **Device toggles** — switch rows with LED indicators for TV, Apple TV, PS5, Sonos plug
- **Sonos controls** — now playing (title + artist), transport buttons (prev/play-pause/next/stop), volume slider + mute

## Configuration

- **Template**: [esphome.yaml](esphome.yaml) — use the **contents of this file as your ESPHome config** in the dashboard or CLI (create or edit your device config so it matches this file).

## Where to Buy

- **Panel**: [AliExpress](https://s.click.aliexpress.com/e/_c335W0r5) (~£40)

## Stand

- **Desk mount** (3D printable): [MakerWorld](https://makerworld.com/en/models/2387421-guition-esp32p4-jc1060p470-7inch-screen-desk-mount#profileId-2614995)

## Folder Structure

```
guition-esp32-p4-jc1060p470/
├── addon/          # Time, network, backlight
├── assets/         # Fonts and icons
├── device/         # device.yaml, sensors.yaml, lvgl.yaml
├── theme/          # Button and UI styling
└── esphome.yaml    # ESPHome config template
```

## Home Assistant Entities Required

### Lights
| Entity | Used For |
|--------|----------|
| `light.living_room_track_lights` | Track lights toggle + brightness |
| `light.hue_color_lamp_1_5` | Floor lamp toggle + brightness |
| `light.hue_color_lamp_1_4` | Table lamp toggle + brightness |
| `light.living_room_art_deco_lamp` | Art deco lamp toggle + brightness |
| `light.living_room` | All Off (turn off all) |
| `light.dining_room_chandelier` | Other Rooms: Chandelier |
| `light.dining_room_picture_lights` | Other Rooms: Picture Lights |
| `light.study` | Other Rooms: Study |

### Scenes
| Entity | Used For |
|--------|----------|
| `scene.living_room_energize` | Energize scene |
| `scene.living_room_read` | Read scene |
| `scene.living_room_relax` | Relax scene |

### Climate
| Entity | Used For |
|--------|----------|
| `cover.living_room_blind` | Blind position (arc + buttons) |
| `fan.living_room_fans` | Ceiling fan speed (arc + buttons) |
| `sensor.living_room_temperature` | Indoor temperature |
| `sensor.living_room_sensor_humidity` | Humidity |
| `weather.openweathermap` | Outdoor temperature |

### Media
| Entity | Used For |
|--------|----------|
| `media_player.living_room_tv` | TV power toggle |
| `remote.living_room_apple_tv` | Apple TV toggle |
| `switch.ps5_power` | PS5 power toggle |
| `switch.sonos_living_room_plug` | Sonos plug toggle |
| `media_player.living_room_sonos` | Sonos playback, volume, mute |

### Other
| Entity | Used For |
|--------|----------|
| `binary_sensor.living_room_occupancy` | Screensaver / backlight trigger |

Customize for your setup by editing the YAML files under `device/`, `addon/`, and `theme/`. See the [main README](../README.md) for full quick start and ESPHome setup.
