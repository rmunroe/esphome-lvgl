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
