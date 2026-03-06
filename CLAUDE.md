# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESPHome LVGL configuration repository for ESP32 touch LCD displays used in home automation. All configuration is declarative YAML — there is no traditional source code, build system, or test suite. The configs are compiled and flashed via the ESPHome dashboard/CLI.

## Supported Devices

| Device | Chip | Display | Directory |
|--------|------|---------|-----------|
| Guition JC1060P470 | ESP32-P4 | 7" MIPI DSI | `guition-esp32-p4-jc1060p470/` |
| Guition JC4880P443 | ESP32-P4 | 4.8" MIPI DSI | `guition-esp32-p4-jc4880p443/` |
| Guition JC8012P4A1 | ESP32-P4 | MIPI DSI | `guition-esp32-p4-jc8012p4a1/` |
| Guition 4848S040 | ESP32-S3 | 4" ST7701S RGB | `guition-esp32-s3-4848s040/` |

Archived: `archived/waveshare-esp32-s3-touch-lcd-7/`

## Architecture

### Two-file entry point

- **`esphome.yaml`** — User-facing template. Sets `substitutions` (name, friendly_name, room), WiFi credentials via `!secret`, and pulls packages from GitHub.
- **`package.yaml`** — Includes all modular config files via `!include`.

### Per-device directory layout

```
<device>/
├── esphome.yaml          # Entry point (substitutions + WiFi + remote package ref)
├── package.yaml          # Package manifest (!include for each module)
├── device/
│   ├── device.yaml       # Hardware: ESP32 variant, display, touchscreen, I2C, PSRAM, backlight output
│   ├── sensors.yaml      # HA entity bindings: sensor values + binary_sensor → LVGL widget state sync
│   └── lvgl.yaml         # UI layout: pages, buttons, labels using flex layout
├── addon/
│   ├── backlight.yaml    # Screensaver/presence-based backlight control
│   ├── network.yaml      # WiFi signal, uptime, IP sensors
│   └── time.yaml         # SNTP time sync + clock label update
├── assets/
│   ├── fonts.yaml        # Google Fonts (Roboto) at various sizes
│   └── icons.yaml        # MDI icon font glyphs + substitution mappings
├── theme/
│   └── button.yaml       # Button styling: colors, sizes, checked state via substitutions
└── spares/               # (P4 devices only) Optional configs: ethernet, sdcard, speaker, voice
```

### Key hardware differences

- **ESP32-P4 devices** use MIPI DSI displays, `esp32_hosted` for a secondary ESP32-C6 (WiFi/BLE), hex-mode PSRAM at 200MHz, and external components from `p1ngb4ck/esphome@dev`.
- **ESP32-S3 devices** use ST7701S RGB displays over SPI, have built-in WiFi, and use octal-mode PSRAM at 80MHz.

### UI pattern (LVGL)

The UI uses LVGL flex layout with `column_wrap`. Each control is a `checkable` button with:
- An icon label (MDI font) at `top_left`
- A text label at `bottom_left`
- `on_press`/`on_click` triggers `homeassistant.service` calls
- Button checked state is synced from HA via `binary_sensor` → `lvgl.widget.update`

Sensors use `platform: homeassistant` to pull entity state. The `on_value` callback updates LVGL labels using `format`/`args` with C-style printf formatting (wrapped in `!lambda` for logic).

### Theming via substitutions

`theme/button.yaml` defines substitutions (`$button_on_color`, `$button_height`, `$button_width`, etc.) and `assets/icons.yaml` maps icon names (`$printer`, `$aircon`, etc.) to MDI Unicode codepoints. These substitutions are referenced throughout `lvgl.yaml`.

## Working with this repo

- **No build/test/lint commands** — validation happens at ESPHome compile time.
- **To compile**: `esphome compile <device>/esphome.yaml` (requires ESPHome installed).
- **To flash**: `esphome run <device>/esphome.yaml` (USB) or OTA from the ESPHome dashboard.
- YAML is the only file type. Changes are validated by compiling against the ESPHome framework.
- WiFi credentials and other secrets use `!secret` tags and are stored in the ESPHome dashboard secrets, not in this repo.

## Conventions

- The remote package URL in `esphome.yaml` points to `github://jtenniswood/esphome-lvgl/` — when editing, the local files under each device directory are what get published.
- Icons must be declared in both the `font.glyphs` array and the `substitutions` map in `icons.yaml`.
- Button IDs in `lvgl.yaml` must have matching binary_sensor entries in `sensors.yaml` to sync checked state.
- The `spares/` directory contains optional/experimental configs not included in `package.yaml` by default.
- Stateful Scenes integration (external HA add-on) is used for scene state tracking — scene buttons toggle `switch.*_stateful_scene` entities.

## Custom Components

### `components/lvgl_screenshot/`

An ESPHome external component that serves a live JPEG screenshot of the LVGL display via HTTP. Designed for ESP32-P4 MIPI DSI displays where the standard `display_capture` component doesn't work (MIPI DSI displays don't inherit from `DisplayBuffer`).

**Files:**
- `__init__.py` — ESPHome component registration; config schema with `port` option; enables `LV_USE_SNAPSHOT=1` build flag
- `lvgl_screenshot.h` — Class definition (`LvglScreenshot : public Component`) with semaphore-based HTTP↔main-loop sync
- `lvgl_screenshot.cpp` — Full implementation: PSRAM buffer allocation, esp_http_server on configurable port, RGB565→RGB888 conversion, JPEG encoding via stb_image_write
- `stb_image_write.h` — v1.16 public domain JPEG/PNG encoder library

**Architecture:**
- Runs a standalone `esp_http_server` (ESP-IDF httpd) on port 8080 (configurable), independent from ESPHome's `web_server` component
- HTTP handler runs on httpd task, signals main loop via FreeRTOS semaphores, main loop does LVGL capture (LVGL is not thread-safe), signals back when done
- All large buffers (snapshot, RGB888 intermediate, JPEG output, stb temp buffers) allocated in PSRAM via `heap_caps_malloc(MALLOC_CAP_SPIRAM)`
- `max_open_sockets = 2` to avoid LWIP socket starvation (ESPHome doesn't account for this server's sockets)

**YAML config** (placed in `device/device.yaml` alongside `external_components` — must NOT be in a separate `!include` file):
```yaml
external_components:
  - source:
      type: git
      url: https://github.com/rmunroe/esphome-lvgl
      ref: main
    refresh: 1s
    components: [lvgl_screenshot]

lvgl_screenshot:
  port: 8080
```

**Key lessons learned:**
- The `lvgl_screenshot:` YAML key and its `external_components` source MUST be in the same file (e.g., `device.yaml`). ESPHome's remote package system does NOT properly merge external component YAML keys from separate `!include` files.
- ESPHome compiles ALL `.cpp` files in external component directories regardless of whether `to_code()` runs — a component can appear to compile but never instantiate if the YAML key isn't recognized.
- For ESP-IDF builds, use `beginResponse` not `beginResponse_P` (the latter is Arduino-only).
- `LV_COLOR_16_SWAP` affects the `lv_color_t` struct layout — use `#if LV_COLOR_16_SWAP` to handle split vs unified green channel.

**Current status:** Fully working. Screenshots are pixel-perfect with header bar compositing. Uses LVGL's `lv_snapshot_take_to_buf()` API to re-render the screen to a fresh PSRAM buffer (bypassing DMA framebuffers), then composites `lv_layer_top()` (header bar) via alpha blending, converts RGB565→RGB888, and encodes to JPEG via stb_image_write.

**Screenshot URL:** `http://10.3.0.243:8080/screenshot` (Touch Screen 1 / Living Room)

## Build Automation

### `scripts/esphome_build.py`

Triggers ESPHome compile+flash from the command line via the HA WebSocket API → ESPHome dashboard ingress.

**Usage:**
```bash
python3 scripts/esphome_build.py [device-name]          # compile + flash OTA
python3 scripts/esphome_build.py [device-name] --compile-only  # compile only
```
Default device: `touch-screen-1`

**How it works:**
1. Connects to HA WebSocket API (`wss://hass.robmunroe.com/api/websocket`)
2. Authenticates with long-lived access token
3. Gets ESPHome addon info via `supervisor/api` WS command (addon slug: `5c53de3b_esphome`)
4. Creates an ingress session via `supervisor/api` WS command
5. Connects to ESPHome dashboard's `/run` WebSocket endpoint through HA ingress proxy
6. Sends `{"type": "spawn", "configuration": "<device>.yaml", "port": "OTA"}` to start the build
7. Streams build output in real-time

**Key details:**
- HA URL: `https://hass.robmunroe.com`
- HA long-lived access token is embedded in the script (expires 2088)
- ESPHome addon slug: `5c53de3b_esphome` (ESPHome Device Builder)
- Ingress URL: `/api/hassio_ingress/B8-6qoGVVsSNqIm7cy0qaPThHToClGeaicyq7rclWWw/`
- The `X-HA-Ingress: YES` header is required for ESPHome dashboard auth bypass when accessed via ingress
- SSL certificate verification is disabled (HA uses custom/self-signed cert)
- The HA Supervisor REST API (`/api/hassio/*`) returns 401 with long-lived tokens in HA 2026.3+; the WebSocket API (`supervisor/api` command type) works correctly
- ESPHome dashboard compile/run endpoints use WebSocket (not HTTP POST), with message type `"spawn"`
- Typical build time: ~15s compile + ~6s OTA upload

**Dependencies:** `pip3 install websockets aiohttp`
