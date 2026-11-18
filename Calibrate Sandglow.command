#!/bin/bash
# Rake the sand FLAT, make sure no hands are over the box, then double-click this.
cd "$(dirname "$0")"
python3 sandglow_bridge.py --calibrate
echo ""
echo "Done. Close this window and start Sandglow."
