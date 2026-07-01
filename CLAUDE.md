# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Python app that drives a Waveshare 7.3" 6-color e-Paper display (connected to a Raspberry Pi) with calendar events, weather, and sports schedules pulled from Home Assistant. It runs hourly via cron or on-demand via a webhook server.

## Commands

### Setup (Raspberry Pi)
```bash
chmod +x install.sh && ./install.sh   # installs system deps, venv, Waveshare library
./setup-cron.sh                        # installs hourly cron job
./setup-webhook.sh                     # installs webhook service
```

### Windows development (mock mode)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install requests PyYAML python-dateutil pytz pillow
```

### Run
```bash
python3 src/main.py              # single update cycle (hardware or PNG in mock mode)
python3 src/webhook_server.py   # HTTP webhook server for HA triggers
python3 src/show_pic.py         # display a custom image on the e-paper
```

### Tests (visual — output PNGs for manual inspection)
```bash
python3 tests/test_full_palette.py     # generates palette_preview.png + palette_dithered.png
python3 tests/test_text_sharpness.py   # tests font rendering
```

There is no automated test runner or linter configured.

## Architecture

```
Home Assistant API → ha_client.py → [calendar_data.py / weather_data.py] → Renderer → epaper_driver.py → Display
```

**`src/main.py`** — entry point. Loads config, checks HA reachability, fetches data in parallel (weather, forecast, all calendars, optional footer sensor, optional AI weather summary), selects a renderer, renders a PIL image, and sends it to the display. Retries every 5 minutes up to 12 times if HA is unreachable.

**`src/ha_client.py`** — Home Assistant REST API client with retry logic and parallel requests.

**`src/calendar_data.py`** / **`src/weather_data.py`** — parse HA API responses into `CalendarEvent` and `WeatherInfo` dataclasses.

**`src/renderer/`** — one renderer per view, all inheriting from `base_renderer.py` (shared PIL helpers and font loading):
- `two_week_renderer.py` — 2×7 grid (default view)
- `month_renderer.py` — traditional month grid
- `week_renderer.py` — single week with detail
- `agenda_renderer.py` — chronological list; shows AI weather summary if configured
- `four_day_renderer.py` — compact 4-day view

**`src/display/epaper_driver.py`** — Waveshare 7.3" HAT (E) driver. The display supports 6 native inks (black, white, red, yellow, green, blue). Colors outside those 6 are approximated via Floyd-Steinberg dithering. Set `mock_mode: true` in config to save a PNG instead of writing to hardware.

**`src/utils/color_manager.py`** — maps 50+ color names to dithered pixel patterns. Light colors (e.g. yellow) automatically get black contrast borders. Colors are assigned to calendars via `config.yaml`.

**`src/utils/state_manager.py`** — persists `state.json` (last updated time, current view).

**`src/webhook_server.py`** — lightweight HTTP server; Home Assistant automations POST to it to trigger an immediate refresh.

## Configuration

Copy `config/config.example.yaml` → `config/config.yaml` (gitignored). Key sections:

- `home_assistant` — URL and long-lived token
- `calendars` — list of `entity_id` + `display_name` + `color` (any of the 50+ color names)
- `weather.entity_id` — HA weather entity
- `view_selector.entity_id` — `input_select` helper that controls which renderer is active; `override_view` bypasses it locally
- `display.mock_mode: true` — outputs PNG instead of writing to hardware

The active view is stored in `state.json` and read each cycle so HA can change views without restarting the process.

## Cross-repo context

Changes that affect HA integration points (sensors, automations, Lovelace cards) may also need corresponding edits in the companion **`HA-config`** repo (Home Assistant configuration). Note this explicitly when relevant.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on KennyNeal/HA-Calendar. External PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary — needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one CONTEXT.md + docs/adr/ at the repo root. A related external repo (HA-config) holds Home Assistant configuration that may require cross-repo context for some changes. See `docs/agents/domain.md`.
