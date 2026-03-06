#!/usr/bin/env python3
"""Trigger an ESPHome compile+install via the HA WebSocket API.

Usage:
    python3 scripts/esphome_build.py [device-name]
    python3 scripts/esphome_build.py [device-name] --compile-only

Default device: touch-screen-1

Connects to the HA WebSocket API, obtains an ingress session for the
ESPHome addon, then connects to the ESPHome dashboard's /run WebSocket
endpoint to compile and flash OTA.
"""

import asyncio
import json
import ssl
import sys
import os

# Force unbuffered output so background runs show progress
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)

try:
    import websockets
except ImportError:
    print("Installing websockets...", flush=True)
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

try:
    import aiohttp
except ImportError:
    print("Installing aiohttp...", flush=True)
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp", "-q"])
    import aiohttp

# SSL context that doesn't verify certs (common for HA with self-signed/custom certs)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Configuration
HA_URL = os.environ.get("HA_URL", "https://hass.robmunroe.com")
HA_TOKEN = os.environ.get("HA_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIxM2QxYzcxZTllY2E0ZmRkOTZjNWVjNjBkNDg1MDk4NiIsImlhdCI6MTc3MjgyNzA3OSwiZXhwIjoyMDg4MTg3MDc5fQ.dO7wB5_qPpDXefo2FwKrrMhQnO3mv7dZzl7hmb2rOpU")
ESPHOME_ADDON_SLUG = "5c53de3b_esphome"
DEFAULT_DEVICE = "touch-screen-1"
DEVICE_IP = os.environ.get("DEVICE_IP", "10.3.0.243")
SCREENSHOT_PORT = 8080

HA_WS_URL = HA_URL.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"


def log(msg):
    print(msg, flush=True)


async def ha_ws_connect():
    """Connect to HA WS API and get ESPHome ingress info."""
    ws = await websockets.connect(HA_WS_URL, ssl=ssl_context)

    msg = json.loads(await ws.recv())  # auth_required
    await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
    msg = json.loads(await ws.recv())  # auth_ok
    if msg["type"] != "auth_ok":
        raise RuntimeError(f"Auth failed: {msg}")
    log(f"✓ Authenticated with HA {msg.get('ha_version', 'unknown')}")

    # Get addon info
    await ws.send(json.dumps({
        "id": 1, "type": "supervisor/api",
        "endpoint": f"/addons/{ESPHOME_ADDON_SLUG}/info",
        "method": "get",
    }))
    msg = json.loads(await ws.recv())
    data = msg.get("result", {}).get("data", msg.get("result", {}))
    ingress_url = data.get("ingress_url", "").rstrip("/")
    log(f"✓ ESPHome {data.get('name', '?')} v{data.get('version', '?')}")

    # Get ingress session
    await ws.send(json.dumps({
        "id": 2, "type": "supervisor/api",
        "endpoint": "/ingress/session",
        "method": "post",
    }))
    msg = json.loads(await ws.recv())
    session = msg.get("result", {}).get("data", msg.get("result", {})).get("session", "")
    log(f"✓ Got ingress session")

    await ws.close()
    return ingress_url, session


async def trigger_build(base_url, session_cookie, device_name, action="run"):
    """Connect to ESPHome dashboard WS and trigger compile+install."""
    config_file = f"{device_name}.yaml"
    ws_base = base_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_base}/{action}"

    log(f"\n→ Connecting to ESPHome /{action} for {config_file}...")

    headers = {
        "Cookie": f"ingress_session={session_cookie}",
        "X-HA-Ingress": "YES",  # ESPHome dashboard checks this for auth bypass on HA addon
    }

    try:
        async with websockets.connect(
            ws_url, ssl=ssl_context,
            additional_headers=headers,
            open_timeout=10,
            ping_interval=30,
            ping_timeout=120,
        ) as ws:
            log(f"✓ Connected to ESPHome dashboard")

            # Send spawn command with configuration and port
            spawn_msg = json.dumps({
                "type": "spawn",
                "configuration": config_file,
                "port": "OTA",
            })
            log(f"→ Sending: {spawn_msg}")
            await ws.send(spawn_msg)

            # Stream build output
            line_count = 0
            last_lines = []
            success = False

            try:
                async for raw_msg in ws:
                    try:
                        event = json.loads(raw_msg)
                        event_type = event.get("event", "")

                        if event_type == "line":
                            line = event.get("data", "")
                            line_count += 1
                            last_lines.append(line)
                            if len(last_lines) > 10:
                                last_lines.pop(0)
                            # Show all output
                            log(f"  {line}")

                        elif event_type == "exit":
                            code = event.get("code", -1)
                            if code == 0:
                                log(f"\n✓ {action.title()} completed! ({line_count} lines)")
                                success = True
                            else:
                                log(f"\n✗ {action.title()} failed (exit {code}, {line_count} lines)")
                                if last_lines:
                                    log("Last output:")
                                    for l in last_lines[-5:]:
                                        log(f"  {l}")
                            break
                        else:
                            log(f"  [{event_type}] {raw_msg[:200]}")

                    except json.JSONDecodeError:
                        log(f"  {raw_msg[:300]}")

            except websockets.exceptions.ConnectionClosed as e:
                log(f"Connection closed: {e} (after {line_count} lines)")

            return success

    except Exception as e:
        log(f"✗ Failed: {type(e).__name__}: {e}")
        return False


async def main():
    device_name = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else DEFAULT_DEVICE
    action = "compile" if "--compile-only" in sys.argv else "run"

    log(f"ESPHome Build — {action} {device_name}")
    log(f"HA: {HA_URL}\n")

    # Get ingress access
    ingress_url, session = await ha_ws_connect()
    base_url = f"{HA_URL}{ingress_url}"

    # Trigger build
    success = await trigger_build(base_url, session, device_name, action)

    if success and action == "run":
        log(f"\n🎉 Device '{device_name}' is running the latest firmware.")
        log(f"   Screenshot: http://{DEVICE_IP}:{SCREENSHOT_PORT}/screenshot")
    elif success:
        log(f"\n✓ Compilation successful.")
    else:
        log(f"\n❌ Build failed.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
