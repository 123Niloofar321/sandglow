#!/usr/bin/env python3
"""
Sandglow bridge: serves the Sandglow page and sends the real sand's height from a Kinect.
Runs on any Mac (Intel or Apple Silicon).

  python3 sandglow_bridge.py              # Kinect if connected and calibrated, otherwise mouse only
  python3 sandglow_bridge.py --calibrate  # with the sand raked flat: measure it once
  python3 sandglow_bridge.py --demo       # pretend sand that moves by itself (testing only)

Then open http://localhost:9980/ . Settings (crop, flips) are in sandglow_config.json.
Kinect for Xbox 360 setup (once):  brew install libfreenect   and   pip3 install numpy freenect
"""
import argparse
import asyncio
import base64
import hashlib
import json
import math
import sys
import os
import time
from urllib.parse import unquote

W, H = 160, 100            # Sandglow's grid
PORT = 9980
FPS = 30
GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

clients = set()
ROOT = os.path.dirname(os.path.abspath(__file__))
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json",
         ".satie": "text/plain; charset=utf-8", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
         ".m4a": "audio/mp4", ".flac": "audio/flac", ".webm": "audio/webm", ".map": "application/json", ".css": "text/css"}


async def serve_file(request, writer):
    try:
        path = request.split(b" ", 2)[1].decode("latin-1").split("?", 1)[0]
        path = unquote(path).lstrip("/") or "sandglow_live.html"
        full = os.path.realpath(os.path.join(ROOT, path))
        if not full.startswith(ROOT + os.sep) or not os.path.isfile(full):
            writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot found")
        else:
            with open(full, "rb") as f:
                body = f.read()
            ctype = TYPES.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
            writer.write(("HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
                          "Cache-Control: no-cache\r\nConnection: close\r\n\r\n" % (ctype, len(body))).encode() + body)
        await writer.drain()
    except Exception:
        pass
    try:
        writer.close()
    except Exception:
        pass


# ---------------------------------------------------------------- websocket (standard library only)
async def handle(reader, writer):
    try:
        request = await reader.readuntil(b"\r\n\r\n")
    except Exception:
        writer.close()
        return
    key = None
    for line in request.split(b"\r\n"):
        if line.lower().startswith(b"sec-websocket-key:"):
            key = line.split(b":", 1)[1].strip()
    if not key:  # plain browser visit: serve files from the Sandglow folder
        await serve_file(request, writer)
        return
    accept = base64.b64encode(hashlib.sha1(key + GUID).digest())
    writer.write(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                 b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n")
    await writer.drain()
    clients.add(writer)
    print("Sandglow connected  (%d open)" % len(clients))
    try:
        while True:                       # we ignore what the page sends; just notice when it leaves
            data = await reader.read(1024)
            if not data or (data[0] & 0x0F) == 0x8:
                break
    except Exception:
        pass
    clients.discard(writer)
    try:
        writer.close()
    except Exception:
        pass
    print("Sandglow disconnected (%d open)" % len(clients))


def frame(payload: bytes) -> bytes:
    n = len(payload)
    if n < 126:
        head = bytes([0x82, n])
    elif n < 65536:
        head = bytes([0x82, 126]) + n.to_bytes(2, "big")
    else:
        head = bytes([0x82, 127]) + n.to_bytes(8, "big")
    return head + payload


async def broadcast(source):
    while True:
        t0 = time.time()
        if clients:
            msg = frame(source())
            for w in list(clients):
                try:
                    w.write(msg)
                    await w.drain()
                except Exception:
                    clients.discard(w)
        await asyncio.sleep(max(0, 1 / FPS - (time.time() - t0)))


# ---------------------------------------------------------------- fake sand (no camera)
def fake_source():
    """Gentle dunes plus a 'hand' that slowly digs a path, so you can test everything."""
    def get():
        t = time.time()
        hx = W / 2 + math.cos(t * .35) * W * .3
        hy = H / 2 + math.sin(t * .5) * H * .3
        out = bytearray(W * H)
        i = 0
        for y in range(H):
            for x in range(W):
                v = .45 + .12 * math.sin(x * .07 + t * .2) * math.cos(y * .09 - t * .15) \
                    + .1 * math.sin((x + y) * .05 + t * .1)
                d2 = (x - hx) ** 2 + (y - hy) ** 2
                v -= .28 * math.exp(-d2 / 60)       # the "hand" digging
                out[i] = max(0, min(255, int(v * 255)))
                i += 1
        return bytes(out)
    return get


# ---------------------------------------------------------------- Kinect for Xbox 360 (libfreenect)
CONFIG = os.path.join(ROOT, "sandglow_config.json")
DEFAULTS = {"near_mm": 0, "far_mm": 0, "crop": [0, 0, 640, 480], "flip_x": False, "flip_y": False, "rotate180": False}


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG) as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)


def open_kinect():
    """Return a function giving one depth frame in millimetres (480x640 numpy), or None if no Kinect."""
    try:
        import numpy as np
        import freenect
    except Exception as e:
        print("Kinect library not installed (%s)." % e)
        return None
    def grab():
        d, _ = freenect.sync_get_depth(format=freenect.DEPTH_MM)
        return d.astype(np.float32)
    try:
        if grab() is None:
            return None
    except Exception as e:
        print("No Kinect found (%s)." % e)
        return None
    return grab


def calibrate(grab, cfg):
    """With the sand raked FLAT: find the box in the camera image and measure how far the sand is."""
    import numpy as np
    d = np.median(np.stack([grab() for _ in range(30)]), axis=0)
    valid = (d > 300) & (d < 4000)
    if valid.sum() < 5000:
        sys.exit("Calibration failed: the Kinect does not see the sand. Check it points straight down at the box.")
    # the flat sand is the biggest area at one distance; the box walls and floor around it are at other distances
    hist, edges = np.histogram(d[valid], bins=200)
    k = int(np.argmax(hist))
    flat = (edges[k] + edges[k + 1]) / 2
    sand = valid & (np.abs(d - flat) < 35)
    rows = np.where(sand.mean(axis=1) > .5)[0]
    cols = np.where(sand.mean(axis=0) > .5)[0]
    if len(rows) > 40 and len(cols) > 40:
        cfg["crop"] = [int(cols[0]) + 4, int(rows[0]) + 4, int(cols[-1]) - 3, int(rows[-1]) - 3]
    x0, y0, x1, y1 = cfg["crop"]
    far = float(np.median(d[y0:y1, x0:x1][valid[y0:y1, x0:x1]]))
    cfg["far_mm"] = round(far + 100)         # 10 cm below flat sand = the deepest hole
    cfg["near_mm"] = round(far - 120)        # 12 cm above flat sand = the tallest hill
    save_config(cfg)
    print("Calibrated: flat sand is %.0f mm from the Kinect; the box is camera area x %d-%d, y %d-%d."
          % (far, x0, x1, y0, y1))
    print("Saved to %s" % CONFIG)


def kinect_source(grab, cfg, hand):
    import numpy as np
    prev = np.full((H, W), .45, dtype=np.float32)
    x0, y0, x1, y1 = cfg["crop"]
    near, far = cfg["near_mm"], cfg["far_mm"]

    def get():
        nonlocal prev
        d = grab()[y0:y1, x0:x1]
        invalid = (d <= 0) | (d > 6000)
        hgt = (far - d) / float(far - near)            # closer to the camera = higher sand
        invalid = invalid | (hgt > hand) | (hgt < -.3) # far taller than sand = a hand or arm: ignore those pixels
        ys = np.linspace(0, d.shape[0], H + 1).astype(int)
        xs = np.linspace(0, d.shape[1], W + 1).astype(int)
        def block(a):
            return np.add.reduceat(np.add.reduceat(a, ys[:-1], axis=0), xs[:-1], axis=1)
        good = (~invalid).astype(np.float32)
        small = block(np.where(invalid, 0, hgt)) / np.maximum(block(good), 1)
        bad = block(good) < block(np.ones_like(good)) * .35   # mostly hidden by a hand: keep the last value
        small = np.where(bad, prev, small)
        prev = prev * .5 + small * .5                  # calm the camera noise
        out = np.clip(prev, 0, 1)
        if cfg.get("flip_x"):
            out = out[:, ::-1]
        if cfg.get("flip_y"):
            out = out[::-1, :]
        if cfg.get("rotate180"):
            out = out[::-1, ::-1]
        return (out * 255).astype(np.uint8).tobytes()
    return get


async def main():
    ap = argparse.ArgumentParser(description="Sandglow bridge")
    ap.add_argument("--demo", action="store_true", help="play pretend sand that moves by itself (for testing only)")
    ap.add_argument("--calibrate", action="store_true", help="measure the FLAT sand once and save it, then exit")
    ap.add_argument("--hand", type=float, default=1.3, help="anything taller than this (1 = tallest hill) is treated as a hand")
    a = ap.parse_args()
    cfg = load_config()

    source, label = None, "no camera: use the mouse"
    if a.demo:
        source, label = fake_source(), "demo sand"
    else:
        grab = open_kinect()
        if a.calibrate:
            if not grab:
                sys.exit("Connect the Kinect first.")
            calibrate(grab, cfg)
            return
        if grab:
            if not cfg["far_mm"]:
                print("Kinect found but not calibrated yet: rake the sand flat and run 'Calibrate Sandglow'.")
            else:
                source, label = kinect_source(grab, cfg, a.hand), "Kinect"
    server = await asyncio.start_server(handle, "127.0.0.1", PORT)
    print("Sandglow running on http://localhost:%d/  (%s)" % (PORT, label))
    print("Ctrl+C to stop.")
    async with server:
        if source:
            await asyncio.gather(server.serve_forever(), broadcast(source))
        else:
            await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")

