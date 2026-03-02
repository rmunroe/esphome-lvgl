# Living Room LVGL Dashboard — Implementation Plan

## Context

The Guition ESP32-P4 JC1060P470 (7-inch, 1024×600, MIPI DSI) is already flashed with ESPHome and configured for the Living Room (`esphome.yaml`: name=touch-screen-1, room=Living Room). The existing YAML files contain an **office** dashboard that must be completely replaced with a **living room** dashboard covering lights, blinds, ceiling fan, and entertainment devices.

---

## Page Structure: 3 Pages + Bottom Nav Bar

**Display: 1024×600 px**
- Top bar: ~40px (temperature + clock, persistent in `top_layer`)
- Bottom nav bar: ~56px (3 tab icons, persistent in `top_layer`)
- Content area per page: ~504px tall × 1024px wide

### Bottom Navigation Bar (in `top_layer`)
3 icon buttons across the bottom, each 341px wide × 52px tall:
| Tab | Icon | Target Page |
|-----|------|-------------|
| Lights | mdi:lightbulb `\U000F0335` | `lights_page` |
| Blinds & Fan | mdi:blinds-open `\U000F1011` | `blinds_fan_page` |
| Entertainment | mdi:television `\U000F0502` | `entertainment_page` |

Active tab = orange text, inactive = gray. Each `on_click` calls `lvgl.page.show` + updates all nav button colors.

---

## Page 1: LIGHTS (default page)

**Layout:** `flex` / `column_wrap`, 4 columns × 3 rows of 200×130 buttons

### Row 1–2: Light Controls (6 checkable buttons)
| # | Label | Icon | Entity | Action | State Source |
|---|-------|------|--------|--------|-------------|
| 1 | All Lights | mdi:lightbulb-group `\U000F1253` | `light.living_room` | `light.toggle` | binary_sensor from `light.living_room` |
| 2 | Tracks | mdi:track-light `\U000F0914` | `light.living_room_track_lights` | `light.toggle` | binary_sensor from `light.living_room_track_lights` |
| 3 | Floor Lamp | mdi:floor-lamp `\U000F08DD` | `light.hue_color_lamp_1_5` | `light.toggle` | binary_sensor from entity |
| 4 | Table Lamp | mdi:desk-lamp `\U000F095F` | `light.hue_color_lamp_1_4` | `light.toggle` | binary_sensor from entity |
| 5 | TV Strip | mdi:led-strip `\U000F07D6` | `light.hue_play_gradient_lightstrip_1` | `light.toggle` | binary_sensor from entity |
| 6 | Art Deco | mdi:lamp `\U000F06B5` | `light.living_room_art_deco_lamp` | `light.toggle` | binary_sensor from entity |

### Row 3: Scene Buttons (4 non-checkable buttons, fire-and-forget)
| # | Label | Icon | Entity | Action |
|---|-------|------|--------|--------|
| 7 | Relax | mdi:sofa `\U000F04B9` | `scene.living_room_relax` | `scene.turn_on` |
| 8 | Watch TV | mdi:television-classic `\U000F07BC` | `scene.living_room_watch_tv` | `scene.turn_on` |
| 9 | Natural | mdi:white-balance-sunny `\U000F05A8` | `scene.living_room_all_day_scene` | `scene.turn_on` |
| 10 | All Off | mdi:power `\U000F0425` | `scene.time_for_bed` | `scene.turn_on` |

Scene buttons are **not checkable** (no state tracking for now — user will add Stateful Scenes later).

---

## Page 2: BLINDS & FAN

**Layout:** `flex` / `column_wrap`

### Blind Controls (5 checkable buttons) — position-based checked state
| # | Label | Icon | Position | State Logic |
|---|-------|------|----------|-------------|
| 1 | Open | mdi:blinds-open `\U000F1011` | 100 | `abs(position - 100) <= 3` |
| 2 | 3/4 | mdi:blinds-open `\U000F1011` | 75 | `abs(position - 75) <= 3` |
| 3 | Half | mdi:blinds-open `\U000F1011` | 50 | `abs(position - 50) <= 3` |
| 4 | 1/4 | mdi:blinds-open `\U000F1011` | 25 | `abs(position - 25) <= 3` |
| 5 | Closed | mdi:blinds-closed `\U000F00AC` | 0 | `abs(position - 0) <= 3` |

All call `cover.set_cover_position` on `cover.living_room_blind`.

### Fan Controls (4 checkable buttons) — speed-based checked state
| # | Label | Icon | Action | State Logic |
|---|-------|------|--------|-------------|
| 6 | Off | mdi:fan-off `\U000F081D` | `fan.turn_off` | fan state == "off" |
| 7 | Low | mdi:fan-speed-1 `\U000F1B04` | `fan.set_percentage: 33` | percentage ~33 |
| 8 | Medium | mdi:fan-speed-2 `\U000F1B05` | `fan.set_percentage: 66` | percentage ~66 |
| 9 | High | mdi:fan-speed-3 `\U000F1B06` | `fan.set_percentage: 100` | percentage ~100 |

All target `fan.living_room_fans`. Fan percentage tracked via `sensor` → template `binary_sensor`.

---

## Page 3: ENTERTAINMENT

**Layout:** `flex` / `column_wrap`

### Device Power Controls (4 checkable buttons)
| # | Label | Icon | Entity | Action | State Source |
|---|-------|------|--------|--------|-------------|
| 1 | TV | mdi:television `\U000F0502` | `media_player.living_room_tv` | `media_player.toggle` | binary_sensor from entity |
| 2 | Apple TV | mdi:apple `\U000F0035` | `remote.living_room_apple_tv` | `remote.toggle` | binary_sensor from entity |
| 3 | PS5 | mdi:sony-playstation `\U000F0414` | `switch.ps5_power` | `switch.toggle` | binary_sensor from entity |
| 4 | Sonos | mdi:speaker `\U000F04C3` | `switch.sonos_living_room_plug` | `switch.toggle` | binary_sensor from entity |

### Volume Controls (3 non-checkable buttons + 1 checkable mute)
| # | Label | Icon | Entity | Action |
|---|-------|------|--------|--------|
| 5 | Vol + | mdi:volume-plus `\U000F075D` | `media_player.living_room_sonos` | `media_player.volume_up` |
| 6 | Vol − | mdi:volume-minus `\U000F075E` | `media_player.living_room_sonos` | `media_player.volume_down` |
| 7 | Mute | mdi:volume-mute `\U000F075F` | `media_player.living_room_sonos` | `media_player.volume_mute` (toggle) |

Mute checked state tracked via `is_volume_muted` attribute on the Sonos entity.

---

## Files to Modify

### 1. `guition-esp32-p4-jc1060p470/assets/icons.yaml` — **Full rewrite**
Replace all office icons with ~25 living room icons + add `nav_icon_font` (28px) for bottom bar.

**Icon glyphs needed:**
```
\U000F0335  mdi:lightbulb           (all lights + nav)
\U000F1253  mdi:lightbulb-group     (all lights button)
\U000F0914  mdi:track-light         (track lights)
\U000F08DD  mdi:floor-lamp          (floor lamp)
\U000F095F  mdi:desk-lamp           (table lamp)
\U000F07D6  mdi:led-strip           (TV lightstrip)
\U000F06B5  mdi:lamp                (art deco)
\U000F04B9  mdi:sofa                (relax scene)
\U000F07BC  mdi:television-classic  (watch TV scene)
\U000F05A8  mdi:white-balance-sunny (natural light scene)
\U000F0425  mdi:power               (all off)
\U000F1011  mdi:blinds-open         (blind open + nav)
\U000F00AC  mdi:blinds-closed       (blind closed)
\U000F081D  mdi:fan-off             (fan off)
\U000F1B04  mdi:fan-speed-1         (fan low)
\U000F1B05  mdi:fan-speed-2         (fan medium)
\U000F1B06  mdi:fan-speed-3         (fan high)
\U000F0502  mdi:television          (TV + nav)
\U000F0035  mdi:apple               (Apple TV)
\U000F0414  mdi:sony-playstation    (PS5)
\U000F04C3  mdi:speaker             (Sonos)
\U000F075D  mdi:volume-plus         (vol up)
\U000F075E  mdi:volume-minus        (vol down)
\U000F075F  mdi:volume-mute         (mute)
```

### 2. `guition-esp32-p4-jc1060p470/assets/fonts.yaml` — **Minor addition**
Keep existing 3 fonts. Add `nav_icon_font` (28px MDI for bottom nav bar icons).

### 3. `guition-esp32-p4-jc1060p470/theme/button.yaml` — **Add nav styles**
Keep existing button theme. Add:
- `nav_button` style definition (bg: `0x1A1A1A`, text: gray, checked: orange)
- Nav button dimensions: ~341px wide × 52px tall

### 4. `guition-esp32-p4-jc1060p470/addon/backlight.yaml` — **One-line change**
Change `entity_id: binary_sensor.office_presence_group` → `entity_id: binary_sensor.living_room_occupancy`

### 5. `guition-esp32-p4-jc1060p470/device/sensors.yaml` — **Full rewrite**
**Regular sensors:**
- `sensor.living_room_temperature` → top bar indoor temp
- `weather.openweathermap` (attribute: temperature) → top bar outdoor temp
- `cover.living_room_blind` (attribute: current_position) → blind position tracking
- `fan.living_room_fans` (attribute: percentage) → fan speed tracking
- `media_player.living_room_sonos` (attribute: is_volume_muted) → mute state

**Binary sensors (HA entity → button checked state):**
- `light.living_room` → all_lights_button
- `light.living_room_track_lights` → tracks_button
- `light.hue_color_lamp_1_5` → floor_lamp_button
- `light.hue_color_lamp_1_4` → table_lamp_button
- `light.hue_play_gradient_lightstrip_1` → tv_strip_button
- `light.living_room_art_deco_lamp` → art_deco_button
- `media_player.living_room_tv` → tv_button
- `remote.living_room_apple_tv` → appletv_button
- `switch.ps5_power` → ps5_button
- `switch.sonos_living_room_plug` → sonos_button

**Template binary sensors (computed):**
- 5 blind position sensors (100/75/50/25/0 ±3%)
- 4 fan speed sensors (off / 33% / 66% / 100%)
- 1 Sonos mute sensor (from is_volume_muted attribute)

### 6. `guition-esp32-p4-jc1060p470/device/lvgl.yaml` — **Full rewrite**
**top_layer:**
- Temperature label (indoor/outdoor) — top left
- Clock label — top center
- Bottom nav bar with 3 tab buttons (Lights, Blinds & Fan, Entertainment)

**pages:**
- `lights_page` (default): 6 light buttons + 4 scene buttons
- `blinds_fan_page`: 5 blind buttons + 4 fan buttons
- `entertainment_page`: 4 power buttons + 3 volume buttons + mute

### Files unchanged:
- `esphome.yaml` — already configured
- `package.yaml` — include list stays the same
- `addon/time.yaml` — SNTP works universally
- `addon/network.yaml` — WiFi diagnostics are device-level
- `device/device.yaml` — hardware config unchanged

---

## Implementation Order

1. `assets/icons.yaml` — icons first (everything else references them)
2. `assets/fonts.yaml` — add nav icon font
3. `theme/button.yaml` — add nav button style
4. `addon/backlight.yaml` — quick presence entity swap
5. `device/sensors.yaml` — all HA bindings (referenced by lvgl.yaml)
6. `device/lvgl.yaml` — full UI (largest file, depends on all above)

---

## Verification

1. **Compile:** `esphome compile guition-esp32-p4-jc1060p470/esphome.yaml` — must succeed without errors
2. **Flash:** `esphome run guition-esp32-p4-jc1060p470/esphome.yaml` (OTA or USB)
3. **Visual check:** 3 pages render correctly, bottom nav switches between them
4. **Functional check:** Toggle lights, set blind positions, change fan speeds, control entertainment devices — verify all buttons trigger HA services and checked states sync back correctly
5. **Top bar:** Temperature and clock display correctly
6. **Screensaver:** Occupancy sensor triggers backlight on/off
