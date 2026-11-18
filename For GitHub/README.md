# Sandglow

An interactive sand installation by **Niloofar Banaei** (HXID, CSULB), inspired by the UC Davis AR Sandbox.

Visitors shape real sand with their hands. A Kinect above the box measures the height of the sand, and a projector paints one of five worlds onto it, live:

| World | What happens |
|---|---|
| **Neon Topo** | Psychedelic neon contour lines that follow every hill and hole |
| **Galaxy** | A Milky Way with stars, shooting stars and planets you can grab and throw; nebulas glow on hills, black holes open in holes |
| **Hara Mangroves** | The Hara mangrove forest of Qeshm Island: dig to let the sea in, pile mud and mangroves grow back; egrets, herons and flamingos take off when your hand comes near |
| **Classic Map** | A topographic map like the original AR Sandbox, with blue peaks |
| **Lotus Marsh** | A misty marsh with reeds and duckweed; digging makes lotus flowers rise |

Every world has natural light, cast shadows and height contour lines, and its own sound scene made with [Satie](https://www.satie.world).

## Files

| File | What it is |
|---|---|
| `sandglow_live.html` | The whole piece: visuals, interaction, projector fitting, sound hookup |
| `sandglow_bridge.py` | Reads the Kinect, sends the sand height to the page, and serves it at http://localhost:9980/ |
| `satie/scene.satie` | The sound scene (readable text) |
| `satie/get_sounds.py` | Downloads the sounds and Satie's player for offline use |
| `Start Sandglow.command` | Double-click to run (macOS) |
| `Calibrate Sandglow.command` | Double-click once with flat sand |
| `Open in VS Code.command` | Opens the project in VS Code |

The sound files are not in this repository. Without them, everything works, just silently.

After cloning on a Mac, make the double-click files runnable once: `chmod +x *.command`

## Try it without a Kinect

Open `sandglow_live.html` in Chrome. Drag to pile sand; right-click or hold Shift to dig. Keys `1`–`5` switch worlds, `H` hides the panel, `D` resets the sand.

## Hardware

- Kinect for Xbox 360 (model 1414 or 1473) with its USB and power adapter
- Short-throw projector, ideally 3000+ lumens
- Sandbox about 100 × 75 cm with 15–20 cm sides, filled with about 10 cm of white play sand
- A frame that holds the Kinect about 1 m above the sand pointing straight down, and the projector above one long edge
- A Mac (or any computer with Python 3), HDMI cable, powered USB hub

## Kinect setup (macOS)

```bash
brew install libfreenect
pip3 install numpy freenect
```

Plug in the Kinect and run `freenect-glview` to check its depth image.

## Setting up at an exhibition

1. Mount the Kinect over the centre of the box and the projector so its image covers the box.
2. Rake the sand flat, keep hands away, and run **Calibrate Sandglow**. It finds the box in the camera image and measures the flat sand.
3. Run **Start Sandglow**, move the browser window to the projector, and press **Fullscreen**.
4. Press **Fit to box** and drag the 4 dots onto the 4 inside corners of the box, then press it again. The fit is remembered.
5. If a hill shows up mirrored, use **Flip ↔ / Flip ↕**, or set `flip_x`, `flip_y` or `rotate180` in `sandglow_config.json`.
6. Click once to turn sound on, pick a world, and press **H** to hide the panel.

For testing without a camera, `python3 sandglow_bridge.py --demo` plays pretend sand that moves by itself.

## Sound

Sound by [Satie](https://www.satie.world).
