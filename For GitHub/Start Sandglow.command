#!/bin/bash
# Double-click this file to start Sandglow (fake sand until a Kinect is connected).
cd "$(dirname "$0")"
echo "Starting Sandglow bridge..."
python3 sandglow_bridge.py "$@" &
BRIDGE=$!
sleep 1.5
open sandglow_live.html
echo ""
echo "Sandglow is running. Close this window (or press Control+C) to stop."
wait $BRIDGE
