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

---

## Feature: LVGL Screenshot Server

**Status: In Progress** — HTTP endpoint works and returns JPEG images, but screenshot content has a vertical shift on MIPI DSI displays.

### Overview

Custom ESPHome component (`components/lvgl_screenshot/`) that serves a live JPEG screenshot at `http://<device-ip>:8080/screenshot`. Designed specifically for ESP32-P4 MIPI DSI displays where the standard `display_capture` component crashes (MIPI DSI doesn't inherit from `DisplayBuffer`).

### What Works

- Component compiles, installs, and boots without OTA rollback
- HTTP server starts on port 8080 and responds to GET `/screenshot`
- Returns a valid JPEG image of the display content
- PSRAM allocation for all large buffers (snapshot ~1.2MB, RGB888 ~1.8MB, JPEG ~1.1MB)
- Semaphore-based thread safety (httpd task signals main loop for LVGL access)

### Current Issue: Vertical Shift

The screenshot image is shifted vertically — the header bar at the top of the screen is cut off, and content from the bottom of the screen is repeated/wrapped. The real display looks correct.

**Root cause:** On ESP32-P4 MIPI DSI, the DPI panel driver manages its own DMA framebuffers. LVGL's draw buffers (`buf1`/`buf2`/`buf_act`) ARE those DMA framebuffers (zero-copy setup), but reading them directly produces shifted content due to how DMA scanning interacts with LVGL's double-buffered rendering.

**Attempts that did NOT fix it:**
1. Reading from `buf_act` instead of `buf1` — same result (likely same pointer)
2. Reading from `buf1` after `lv_refr_now(disp)` — same shift
3. Both approaches produce identical shifted output

### Fix Plan: Use LVGL Snapshot API

**Approach:** Replace direct draw buffer reading with LVGL's `lv_snapshot_take_to_buf()` API, which creates a temporary display driver and re-renders the LVGL object tree to a fresh user-provided buffer. This completely bypasses the hardware display's DMA framebuffer management.

**Implementation steps:**

1. **`__init__.py`** (done): Add `cg.add_build_flag("-DLV_USE_SNAPSHOT=1")` to enable the LVGL snapshot feature at compile time. LVGL 8.4's `lv_conf_internal.h` uses `#ifndef LV_USE_SNAPSHOT` so a `-D` flag takes precedence.

2. **`lvgl_screenshot.h`** (done): Add `lv_color_t *snap_buf_{nullptr}` member for the snapshot render target.

3. **`lvgl_screenshot.cpp` setup()** (done): Allocate `snap_buf_` in PSRAM (`width * height * sizeof(lv_color_t)` = ~1.2MB for 1024x600).

4. **`lvgl_screenshot.cpp` do_capture_()`** (TODO): Rewrite to use `lv_snapshot_take_to_buf()`:
   ```cpp
   lv_img_dsc_t dsc;
   uint32_t snap_bytes = width * height * sizeof(lv_color_t);
   lv_res_t res = lv_snapshot_take_to_buf(
       lv_scr_act(), LV_IMG_CF_TRUE_COLOR,
       &dsc, this->snap_buf_, snap_bytes);
   // Then read from dsc.data for RGB565→RGB888 conversion
   ```

**Why this should work:**
- `lv_snapshot_take_to_buf()` creates a temporary LVGL display driver with its own draw buffer (our `snap_buf_`)
- It re-renders the active screen's widget tree into that buffer using LVGL's software renderer
- No hardware DMA involvement — purely software rendering
- Output is guaranteed to be a complete, pixel-perfect, correctly-oriented frame
- The temporary display is unregistered after rendering

**Potential issues:**
- If `LV_USE_SNAPSHOT` build flag conflicts with ESPHome's generated `lv_conf.h`, may need an alternative approach (custom flush callback interception)
- Snapshot re-renders the entire screen, which may take 50-100ms for 1024x600 — acceptable for on-demand screenshots
- `lv_snapshot_take_to_buf()` uses `lv_mem_alloc()` internally for a small descriptor struct — should fit in LVGL's memory pool

### Files

| File | Status | Description |
|------|--------|-------------|
| `components/lvgl_screenshot/__init__.py` | Modified | Added `LV_USE_SNAPSHOT=1` build flag |
| `components/lvgl_screenshot/lvgl_screenshot.h` | Modified | Added `snap_buf_` member |
| `components/lvgl_screenshot/lvgl_screenshot.cpp` | Partially modified | `setup()` allocates snap_buf; `do_capture_()` still reads draw buffer directly — needs rewrite to use snapshot API |
| `components/lvgl_screenshot/stb_image_write.h` | Unchanged | v1.16 JPEG encoder |
| `guition-esp32-p4-jc1060p470/device/device.yaml` | Modified | Contains `external_components` + `lvgl_screenshot:` config |

### Issues Resolved Along the Way

| Issue | Cause | Fix |
|-------|-------|-----|
| `beginResponse_P` compile error | ESP-IDF/Arduino branches swapped | Swapped `#ifdef USE_ESP_IDF` branches |
| ESPHome git cache stale | No `ref:` or `refresh:` on git source | Added `ref: main`, `refresh: 1s` |
| OTA rollback on boot | `display_capture` used `static_cast<DisplayBuffer*>` on MIPI DSI | Replaced with `lvgl_screenshot` (reads LVGL buffer) |
| `green_h` struct error | `LV_COLOR_16_SWAP` layout difference | Added `#if LV_COLOR_16_SWAP` conditional |
| Component never instantiates | YAML key in separate `!include` file | Moved both `external_components` and `lvgl_screenshot:` into `device.yaml` |
| LWIP socket starvation | httpd default `max_open_sockets=7` | Set to 2 |
| stb OOM from internal SRAM | stb malloc uses default allocator | Override `STBIW_MALLOC/REALLOC/FREE` to PSRAM |
