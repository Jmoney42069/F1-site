#!/usr/bin/env python3
"""Pretends to be the robot, so the hub can be tested without hardware.

python3 fake_device.py ws://localhost:8080/ws/device?token=dev
"""
import asyncio
import json
import random
import sys
import time

import websockets


async def main(url):
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "hello", "id": "fake-robot", "fw": "sim", "caps": ["led"]}))
        t0 = time.time()

        async def telemetry():
            while True:
                await ws.send(json.dumps({"type": "telemetry", "uptime_ms": int((time.time() - t0) * 1000),
                                          "rssi": random.randint(-65, -55), "free_heap": 250000}))
                await asyncio.sleep(1)

        asyncio.create_task(telemetry())
        async for raw in ws:
            msg = json.loads(raw)
            if msg["type"] == "ping":
                await ws.send(json.dumps({"type": "pong", "t": msg["t"]}))
            elif msg["type"] == "cmd":
                ok = msg["name"] in ("led",)
                print("cmd", msg["name"], msg["args"])
                await ws.send(json.dumps({"type": "ack", "cmd_id": msg["cmd_id"], "ok": ok,
                                          "error": None if ok else "unknown command"}))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8080/ws/device?token=dev"))
