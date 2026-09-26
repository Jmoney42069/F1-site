"""Home hub: devices connect over WebSocket, the hub sends commands and tracks latency.

Run locally:   DEVICE_TOKEN=dev uvicorn app:app --host 0.0.0.0 --port 8080
Device URL:    ws://<server-ip>:8080/ws/device?token=<DEVICE_TOKEN>

Protocol (JSON text frames)
  device -> hub  {"type":"hello","id":"dweilrobo","fw":"0.1.0","caps":["led"]}
                 {"type":"telemetry","uptime_ms":..,"rssi":..,"free_heap":..}
                 {"type":"pong","t":<echo>}
                 {"type":"ack","cmd_id":n,"ok":true,"error":null}
  hub -> device  {"type":"ping","t":<hub monotonic ms>}
                 {"type":"cmd","cmd_id":n,"name":"led","args":{...}}
The device must treat >1 s without any hub message as "link lost" and go to a safe state.
"""
import asyncio
import itertools
import os
import time
from dataclasses import dataclass, field

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

TOKEN = os.environ.get("DEVICE_TOKEN", "dev")
PING_INTERVAL_S = 0.5
ACK_TIMEOUT_S = 2.0

app = FastAPI(title="home hub")
_cmd_ids = itertools.count(1)


def now_ms() -> float:
    return time.monotonic() * 1000


@dataclass
class Device:
    id: str
    ws: WebSocket
    fw: str = "?"
    caps: list = field(default_factory=list)
    connected_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    rtt_ms: float | None = None
    rtt_hist: list = field(default_factory=list)
    telemetry: dict = field(default_factory=dict)
    pending: dict = field(default_factory=dict)  # cmd_id -> Future

    def public(self):
        h = sorted(self.rtt_hist)
        return {
            "id": self.id, "fw": self.fw, "caps": self.caps,
            "online_s": round(time.time() - self.connected_at),
            "last_seen_ms_ago": round((time.time() - self.last_seen) * 1000),
            "rtt_ms": None if self.rtt_ms is None else round(self.rtt_ms, 1),
            "rtt_p50_ms": round(h[len(h) // 2], 1) if h else None,
            "rtt_p95_ms": round(h[int(len(h) * 0.95) - 1], 1) if len(h) >= 20 else None,
            "telemetry": self.telemetry,
        }


devices: dict[str, Device] = {}


async def pinger(dev: Device):
    while True:
        await asyncio.sleep(PING_INTERVAL_S)
        await dev.ws.send_json({"type": "ping", "t": now_ms()})


@app.websocket("/ws/device")
async def device_ws(ws: WebSocket, token: str = ""):
    if token != TOKEN:
        await ws.close(code=4401)
        return
    await ws.accept()
    hello = await asyncio.wait_for(ws.receive_json(), timeout=5)
    if hello.get("type") != "hello" or not hello.get("id"):
        await ws.close(code=4400)
        return
    dev = Device(id=str(hello["id"]), ws=ws, fw=hello.get("fw", "?"), caps=hello.get("caps", []))
    old = devices.get(dev.id)
    if old:
        await old.ws.close(code=4409)
    devices[dev.id] = dev
    task = asyncio.create_task(pinger(dev))
    try:
        while True:
            msg = await ws.receive_json()
            dev.last_seen = time.time()
            kind = msg.get("type")
            if kind == "pong" and isinstance(msg.get("t"), (int, float)):
                dev.rtt_ms = now_ms() - msg["t"]
                dev.rtt_hist = (dev.rtt_hist + [dev.rtt_ms])[-200:]
            elif kind == "telemetry":
                dev.telemetry = {k: v for k, v in msg.items() if k != "type"}
            elif kind == "ack":
                fut = dev.pending.pop(msg.get("cmd_id"), None)
                if fut and not fut.done():
                    fut.set_result(msg)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        task.cancel()
        if devices.get(dev.id) is dev:
            del devices[dev.id]
        for fut in dev.pending.values():
            if not fut.done():
                fut.set_exception(ConnectionError("device disconnected"))


class Command(BaseModel):
    name: str
    args: dict = {}


@app.get("/api/devices")
def list_devices():
    return [d.public() for d in devices.values()]


@app.post("/api/devices/{device_id}/cmd")
async def send_cmd(device_id: str, cmd: Command):
    dev = devices.get(device_id)
    if not dev:
        raise HTTPException(404, "device not connected")
    cmd_id = next(_cmd_ids)
    fut = asyncio.get_running_loop().create_future()
    dev.pending[cmd_id] = fut
    t0 = now_ms()
    await dev.ws.send_json({"type": "cmd", "cmd_id": cmd_id, "name": cmd.name, "args": cmd.args})
    try:
        ack = await asyncio.wait_for(fut, ACK_TIMEOUT_S)
    except asyncio.TimeoutError:
        dev.pending.pop(cmd_id, None)
        raise HTTPException(504, "device did not acknowledge in time")
    except ConnectionError as e:
        raise HTTPException(503, str(e))
    return {"ok": bool(ack.get("ok")), "error": ack.get("error"), "roundtrip_ms": round(now_ms() - t0, 1)}


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
