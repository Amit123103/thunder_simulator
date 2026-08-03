# Cinematic Lightning & Terrain Simulator (Python + ModernGL)

A movie-quality interactive 3D lightning and terrain simulation desktop application written in Python using ModernGL, GLSL Shaders, PyGLM, and ImGui.

---

## Technical Overview & Features

### ⚡ Procedural 3D Lightning Engine
- **Fractal Subdivision & Recursive Branching**: Generates realistic 3D branching lightning bolts with primary trunks, sub-branches, and micro-arcs.
- **Voltage Flicker & UV Scrolling**: Dynamic electric plasma glow with exponential decay and voltage flicker curves.
- **Light Emission Point Sources**: Binds point light sources along active bolts to illuminate terrain surfaces and cloud volumes in real time.
- **Multiple Strike Modes**: Single Strike, Continuous Storm Mode, and Explosion Blast Mode.

### 🏔️ Procedural Terrain & Dynamic Impact Physics
- **Multi-Octave FBM & Domain Warping**: Synthesizes high-detail mountain ranges, valleys, and rocky cliffs.
- **Dynamic Crater Formation**: Real-time terrain heightmap excavation creating parabolic impact bowls and outer ejecta rims upon lightning hit.
- **Thermal Heat & Scorch Maps**: Real-time glowing molten lava core temperature map that cools dynamically over time according to physical heat decay equations.
- **Raycasted Terrain Picker**: Click anywhere on the 3D terrain surface with the mouse to launch a lightning strike precisely at that spot.

### ☁️ Volumetric Storm Clouds
- **3D Raymarching & Wind Animation**: Raymarched volumetric cloud volume with procedural noise sampling, wind vectors, and Henyey-Greenstein forward scattering.
- **Internal Lightning Illumination**: Active lightning strikes illuminate the internal volume of storm clouds from within.

### 🌌 Atmospheric Scattering & Fog
- **Rayleigh & Mie Scattering Sky Dome**: Physically based atmospheric sky model supporting Sun/Moon positions (Day Twilight, Night Storm, Heavy Thunderstorm).
- **Volumetric Exponential Height Fog**: Distance and height fog integration.

### 💥 GPU Accelerated Particle System
- **Instanced Billboard Rendering**: Simulated physics for thousands of simultaneous particles:
  - **Electric Sparks**: Emissive velocity drag trails.
  - **Smoke Plumes**: Soft alpha-blended expanding smoke clouds.
  - **Kinetic Rock Debris**: Falling physical rock fragments.
  - **Volumetric Rain**: Falling rain sheets.

### 🎥 Post-Processing & HDR Pipeline
- **Floating Point HDR Framebuffer (RGBA16F)**.
- **Multi-Pass Pyramid Bloom**: Threshold extraction and Kawase downsample/upsample blur filters for emissive bolt glow.
- **ACES Film Tonemapping & Gamma Correction**.
- **Chromatic Aberration, Lens Vignette, and Procedural Film Grain**.

### 🔊 Procedural Spatial Audio Engine
- **Pure Python Sound Synthesis**: Generates low-frequency thunder rumbles, high-voltage crackles, rolling reverb echoes, and ground impact explosion thuds using NumPy waveforms without external audio asset file dependencies.

### 🖥️ Professional ImGui GUI & Exporters
- Real-time parameter tweaking dock (Lightning intensity, bolt width, fog density, cloud coverage, bloom threshold, exposure).
- One-click exporter tools:
  - **PNG Screenshots**: Captures rendered HDR frame.
  - **PNG Heightmaps**: 16-bit terrain elevation map.
  - **Wavefront 3D OBJ Models**: Exports deformed terrain mesh to standard `.obj` files.

---

## ⌨️ Keyboard Shortcuts & Controls

| Key | Action |
|:---|:---|
| **Mouse Left Click** | Raycast terrain ground point & trigger Lightning Strike at target position |
| **Mouse Left Drag** | Orbit Camera around target |
| **Mouse Right Drag** | Pan Camera target position |
| **Mouse Scroll** | Zoom Camera In / Out |
| **1** | Trigger Single Lightning Strike |
| **2** | Toggle Continuous Storm Mode |
| **3** | Toggle Volumetric Rain Density |
| **4** | Toggle Atmospheric Fog Density |
| **5** | Night Storm Environment Preset |
| **6** | Day Twilight Environment Preset |
| **7** | Toggle Slow Motion (0.25x time scale) |
| **8** | Explosion Blast Mode (3 simultaneous strikes) |
| **9** | Toggle Cinematic Fly-Through Camera Mode |
| **0** | Reset Terrain Craters & Thermal Heat Maps |

---

## 📁 Project Architecture

```
thunder/
├── main.py                          # ModernGL-Window Application Entry Point
├── requirements.txt                 # Python Dependencies
├── README.md                        # Documentation
└── lightning_simulator/
    ├── __init__.py
    ├── main.py
    ├── assets/
    │   └── shaders/
    │       ├── terrain.vert / frag  # Terrain PBR, Heat Map Glow & Scorch Marks
    │       ├── lightning.vert / frag# 3D Lightning Billboard & Plasma Core
    │       ├── clouds.vert / frag   # Volumetric Cloud Raymarching & Internal Flash
    │       ├── sky.vert / frag      # Rayleigh/Mie Atmospheric Scattering
    │       ├── particles.vert / frag# Instanced Particle System (Sparks/Smoke/Rain)
    │       ├── post.vert / frag     # ACES Tonemapping, Bloom Composite & Vignette
    │       └── bloom.vert / frag    # Threshold Extraction & Kawase Blur
    └── engine/
        ├── config.py                # Engine Settings & Hotkey Map
        ├── utilities.py             # FBM Noise, Normal/AO Generators & Mesh Creators
        ├── camera.py                # Orbit, FPS, Cinematic Camera & Camera Shake
        ├── terrain.py               # Procedural Terrain & Raycasting
        ├── lightning.py             # 3D Branching Bolt Fractal Subdivisions
        ├── clouds.py                # Volumetric Cloud State & Wind Drift
        ├── atmosphere.py            # Sky Scattering & Sun Position
        ├── fog.py                   # Height Fog Parameters
        ├── particles.py             # GPU Instanced Particle Physics
        ├── physics.py               # Crater Excavation & Heat Cooling Map
        ├── bloom.py                 # Multi-pass Bloom Pyramid FBO Pipeline
        ├── audio.py                 # Procedural Spatial Sound Synthesizer
        ├── ui.py                    # ImGui Dock & Telemetry HUD
        └── renderer.py              # Master ModernGL Multi-Pass Renderer
```

---

## 🚀 Installation & Execution

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Graphics Card supporting OpenGL 3.3 Core Profile or higher

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
python main.py
```
