#!/usr/bin/env python3
"""
Downloads Sandglow's Satie sounds and Satie's player into the Sandglow/satie folder,
so the installation plays sound offline at the exhibition.

    python3 satie/get_sounds.py "<samples.json link from Satie>"

The link is valid for one hour; ask Claude for a fresh one if it has expired.
Uses macOS's built-in curl.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from urllib.parse import urljoin, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))          # .../Sandglow/satie
RUNTIME_BASE = "https://www.satie.world/runtime/"


def curl(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(["curl", "-fsSL", "--retry", "3", url, "-o", dest], check=True)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 satie/get_sounds.py '<samples.json link>'")
    link = sys.argv[1]
    merge = "--merge" in sys.argv[2:]

    # 1. samples.json, saved exactly as Satie returned it (a second set is kept beside it when merging)
    samples_path = os.path.join(HERE, "samples_%s.json" % hashlib.sha1(link.split("?")[0].encode()).hexdigest()[:8] if merge else "samples.json")
    print("Downloading samples.json ...")
    curl(link, samples_path)
    with open(samples_path) as f:
        samples = json.load(f)

    # 2. every sound file, plus a local map that points at the downloaded copies
    local = {}
    if merge:
        try:
            with open(os.path.join(HERE, "samples.local.json")) as f:
                local = json.load(f)
        except Exception:
            pass
    total = len(samples)
    for i, (clip, entry) in enumerate(samples.items(), 1):
        url = entry["url"] if isinstance(entry, dict) else entry
        ext = os.path.splitext(urlparse(url).path)[1] or ".mp3"
        name = hashlib.sha1(urlparse(url).path.encode()).hexdigest()[:16] + ext
        dest = os.path.join(HERE, "audio", name)
        if not os.path.exists(dest) or os.path.getsize(dest) == 0:
            print("  [%d/%d] %s" % (i, total, clip))
            curl(url, dest)
        local[clip] = dict(entry, url="satie/audio/" + name) if isinstance(entry, dict) else {"url": "satie/audio/" + name}
    with open(os.path.join(HERE, "samples.local.json"), "w") as f:
        json.dump(local, f, indent=1)

    # 3. Satie's player (the main file and every chunk it imports)
    print("Downloading Satie's player ...")
    seen, queue = set(), ["satie-runtime.js"]
    while queue:
        rel = queue.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        dest = os.path.join(HERE, "runtime", rel)
        curl(urljoin(RUNTIME_BASE, rel), dest)
        with open(dest, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        for m in re.finditer(r"""(?:from|import)\s*\(?\s*["'](\.\.?/[^"']+)["']""", text):
            full = urljoin(urljoin(RUNTIME_BASE, rel), m.group(1))
            if full.startswith(RUNTIME_BASE):
                queue.append(full[len(RUNTIME_BASE):])
    print("Done: %d sounds and %d player files saved in %s" % (len(local), len(seen), HERE))


if __name__ == "__main__":
    main()
