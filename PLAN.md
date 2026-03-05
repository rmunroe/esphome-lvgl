# Living Room LVGL Dashboard — Implementation Plan

**Status: Implemented** — The living room dashboard is complete. The final implementation evolved from the original plan into a more sophisticated card-based UI with tabview navigation, brightness sliders, arc controls, and full Sonos media transport.

## Context

The Guition ESP32-P4 JC1060P470 (7-inch, 1024×600, MIPI DSI) is configured for the Living Room (`esphome.yaml`: name=touch-screen-1, room=Living Room).

---

## Implemented UI

**Display: 1024×600 px**
- Header bar: ~40px (outdoor/indoor temps, clock, humidity, status LED — persistent in `top_layer`)
- Tabview: ~560px with 3 tabs (Lights, Climate, Media)

### Navigation

Tabview with top-positioned tabs (amber when active, gray when inactive). Three tabs: Lights, Climate, Media.

---

## Tab 1: LIGHTS (default tab)

**Layout:** Scene bar at top, then a two-column layout below.

### Scene Bar (4 non-checkable buttons, fire-and-forget)
| Label | Entity | Action |
|-------|--------|--------|
| All Off | `light.living_room` | `light.turn_off` |
| Energize | `scene.living_room_energize` | `scene.turn_on` |
| Read | `scene.living_room_read` | `scene.turn_on` |
| Relax | `scene.living_room_relax` | `scene.turn_on` |

### Light Controls (left column — 4 toggle buttons with brightness sliders)
| Label | Entity | Slider |
|-------|--------|--------|
| Track Lights | `light.living_room_track_lights` | brightness 0–255 |
| Floor Lamp | `light.hue_color_lamp_1_5` | brightness 0–255 |
| Table Lamp | `light.hue_color_lamp_1_4` | brightness 0–255 |
| Art Deco | `light.living_room_art_deco_lamp` | brightness 0–255 |

Each row: checkable toggle button (200px) + horizontal brightness slider (380px) + percentage label.

### Other Rooms (right column — warm-accent card)
| Label | Entity |
|-------|--------|
| Chandelier | `light.dining_room_chandelier` |
| Picture Lights | `light.dining_room_picture_lights` |
| Study | `light.study` |

---

## Tab 2: CLIMATE (Blinds + Fan + Environment)

**Layout:** 3-column card layout (Blinds | Fan | Environment)

### Blinds Card (blue accent)
- **Arc control** (0–100%) for `cover.living_room_blind` with position label
- **Quick buttons:** Open / Stop / Close

### Fan Card (teal accent)
- **Arc control** (0–100%) for `fan.living_room_fans` with speed label (Off/Low/Med/High)
- **Quick buttons:** Off / Low / Med / High (checkable, state from template binary sensors)

### Environment Card (blue accent)
- **Indoor Temperature** — icon + label + bar (`sensor.living_room_temperature`)
- **Humidity** — icon + label + bar (`sensor.living_room_sensor_humidity`)
- **Outdoor Temperature** — icon + label + bar (`weather.openweathermap`)

---

## Tab 3: MEDIA (Devices + Sonos)

**Layout:** 2-column card layout (Devices | Sonos)

### Device Toggles (purple-accent card)
| Label | Icon | Entity | Action |
|-------|------|--------|--------|
| TV | mdi:television | `media_player.living_room_tv` | `media_player.toggle` |
| Apple TV | mdi:apple | `remote.living_room_apple_tv` | `remote.toggle` |
| PS5 | mdi:sony-playstation | `switch.ps5_power` | `switch.toggle` |
| Sonos | mdi:speaker | `switch.sonos_living_room_plug` | `switch.toggle` |

Each row has a status LED + icon + label + toggle switch.

### Sonos Controls (purple-accent card)
- **Now Playing** — track title + artist from `media_player.living_room_sonos` attributes
- **Transport** — Previous / Play-Pause / Next / Stop buttons
- **Volume** — slider (0–100%) + percentage label + mute toggle

---

## Files Modified

| File | Change |
|------|--------|
| `assets/icons.yaml` | Full rewrite — 40px + 24px icon fonts with living room glyphs |
| `assets/fonts.yaml` | Added `value_font` (40px) and `value_font_medium` (28px) for sensor readings |
| `theme/button.yaml` | Full rewrite — card-based theme with accent cards, light/scene/action buttons, arc/slider styles, transport buttons, device rows, environment bars |
| `addon/backlight.yaml` | Presence entity: `binary_sensor.living_room_occupancy` |
| `device/sensors.yaml` | Full rewrite — all living room HA entity bindings |
| `device/lvgl.yaml` | Full rewrite — 3-tab card-based dashboard with header bar |

### Files unchanged
- `esphome.yaml` — already configured for Living Room
- `package.yaml` — include list unchanged
- `addon/time.yaml` — SNTP works universally
- `addon/network.yaml` — WiFi diagnostics are device-level
- `device/device.yaml` — hardware config unchanged
