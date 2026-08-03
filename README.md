# ⚡ Cinematic Lightning & Terrain Simulator

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![ModernGL](https://img.shields.io/badge/ModernGL-5.12-brightgreen.svg)](https://moderngl.readthedocs.io/)
[![OpenGL](https://img.shields.io/badge/OpenGL-3.3%20Core-orange.svg)](https://www.opengl.org/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Render Cloud](https://img.shields.io/badge/Render-Live%203D%20WebGL-success.svg)](https://thunder-simulator.onrender.com)

A state-of-the-art interactive **3D Lightning & Procedural Terrain Simulation Engine** written in Python using ModernGL, GLSL Shaders, PyGLM, NumPy, and ImGui.

---

## 🧮 Mathematical Concepts & Physics Formulation

### 1. Procedural 3D Lightning Fractal Subdivision
Lightning channels are synthesized using recursive **3D Midpoint Displacement Fractal Subdivision** with perpendicular Gaussian perturbation vectors:

$$P_{\text{mid}} = \frac{P_A + P_B}{2} + \vec{n} \cdot \sigma \cdot \delta_{\text{jitter}}$$

where the perpendicular displacement direction vector $\vec{n}$ is generated via orthogonal cross-product projection:

$$\vec{n} = \frac{\vec{v}_{\text{segment}} \times \vec{r}_{\text{random}}}{\|\vec{v}_{\text{segment}} \times \vec{r}_{\text{random}}\|}$$

- **Stepped Leader Propagation**: Downward cloud-to-earth leader channel travels at $v \approx 2 \times 10^5 \text{ m/s}$ over $t \approx 110\text{ ms}$.
- **Return Stroke Brightness Spike**: Upon ground contact, brightness spikes according to exponential return stroke decay:

$$B(t) = B_{\text{base}} + B_{\text{peak}} \cdot \exp\left(-\frac{t - t_{\text{contact}}}{\tau_{\text{decay}}}\right)$$

---

### 2. Ridged Multifractal Terrain Heightmaps
Terrain topology is synthesized via 5-octave **Ridged Multifractal Noise** with Domain Warping for sharp craggy mountain peaks:

$$h(x, z) = \sum_{k=0}^{O-1} a^k \cdot \left| \text{Noise}\left(f^k x, f^k z\right) \right|$$

where amplitude decay $a = 0.48$ and frequency multiplier $f = 2.1$.

**Domain Warping** applies turbulent displacement to coordinate vectors prior to height evaluation:

$$\vec{p}' = \vec{p} + \gamma \cdot \text{Noise}(\vec{p})$$

---

### 3. Thermal Heat Dissipation & Scorch Physics
Lightning impact points generate high-temperature molten lava cores ($T_0 \approx 3000\text{ K}$) that decay according to Newton's law of cooling heat diffusion:

$$T(x, z, t) = T_0 \cdot \exp\left(-\frac{(x - x_0)^2 + (z - z_0)^2}{2 \sigma_{\text{crater}}^2}\right) \cdot \exp(-\alpha \cdot t)$$

---

### 4. Expanding Kinetic Shockwave Rings
Ground impact pressure waves create radial kinetic shockwave rings expanding across mountain rock surfaces:

$$I_{\text{shock}}(r, t) = I_0 \cdot \exp\left(-\frac{(r - v_{\text{shock}} \cdot t)^2}{2 \sigma_{\text{ring}}^2}\right) \cdot \exp(-\gamma_{\text{decay}} \cdot t)$$

---

### 5. Henyey-Greenstein Volumetric Cloud Scattering
Volumetric cloud raymarching evaluates atmospheric forward/backward scattering using the dual **Henyey-Greenstein Phase Function**:

$$P_{\text{HG}}(\theta, g) = \frac{1 - g^2}{4\pi \left(1 + g^2 - 2g \cos\theta\right)^{3/2}}$$

---

## 🏗️ Architecture & How It Was Built

```
thunder/
├── main.py                          # Application Entry Point & Auto-Cloud Detection
├── requirements.txt                 # Python Dependencies
├── runtime.txt / .python-version    # Python 3.11.9 Build Lock
├── README.md                        # Documentation
└── lightning_simulator/
    ├── __init__.py
    ├── main.py
    ├── assets/
    │   └── shaders/
    │       ├── terrain.vert / frag  # PBR Terrain, Heat Maps & Shockwave Rings
    │       ├── lightning.vert / frag# Triple-Layer Plasma Corona Shader
    │       ├── clouds.vert / frag   # Volumetric Raymarching & Flash Illumination
    │       ├── sky.vert / frag      # Rayleigh & Mie Atmospheric Scattering
    │       ├── particles.vert / frag# Instanced Particle System (Sparks/Smoke/Rain)
    │       ├── post.vert / frag     # ACES Tonemapping & Vignette Composite
    │       └── bloom.vert / frag    # Multi-Pass Kawase Bloom Pyramid
    └── engine/
        ├── config.py                # Global Engine Parameters
        ├── camera.py                # Orbit, Fly-through & Camera Shake
        ├── terrain.py               # Procedural Mesh & Raycast Picker
        ├── lightning.py             # 3D Branching Fractal Bolt Generation
        ├── clouds.py                # Cloud Volume State & Wind Drift
        ├── atmosphere.py            # Sun Vector & Sky Model
        ├── fog.py                   # Exponential Height Fog
        ├── particles.py             # 2D Vectorized Particle Loop (120+ FPS)
        ├── physics.py               # Vectorized Crater Excavation & Heat Map
        ├── bloom.py                 # Multi-pass Bloom Pyramid FBO Pipeline
        ├── audio.py                 # NumPy Waveform Spatial Sound Synthesizer
        ├── ui.py                    # ImGui Telemetry HUD Panel
        └── renderer.py              # Master ModernGL Multi-Pass Renderer
```

### Key Engineering Principles:
1. **Persistent Pre-allocated VBOs**: Dynamic GPU buffers (`reserve=...`) eliminate per-frame ModernGL memory allocations, maintaining **120+ FPS**.
2. **2D Vectorized NumPy Physics**: Crater excavation and heat map calculations execute in $<0.1\text{ ms}$ using vectorized 2D `np.meshgrid` operations.
3. **Triple-Layer Plasma Corona Shader**: GLSL shader renders a white-hot core ($RGB = 1.0, 1.0, 1.0$), electric violet inner plasma ($RGB = 0.6, 0.4, 1.0$), and cyan outer halo.
4. **Universal Cloud Deployment (`main.py`)**: Automatically detects cloud environments (Render.com without X11 `DISPLAY`) and binds a background HTTP server serving a live 3D WebGL simulator with full desktop ImGui UI replication.

---

## 🎮 How You Can Use This

### 🖥️ Local Desktop Execution (Windows / Mac / Linux)

#### 1. Clone Repository
```bash
git clone https://github.com/Amit123103/thunder_simulator.git
cd thunder_simulator
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Launch Simulator
```bash
python main.py
```

---

### 🌐 Live Web Browser Version
Visit the live deployed WebGL simulator directly in your browser:
👉 **[https://thunder-simulator.onrender.com](https://thunder-simulator.onrender.com)**

---

## ⌨️ Keyboard Shortcuts & Mouse Controls

| Input | Action |
|:---|:---|
| **Mouse Left Click** | Raycast terrain ground point & trigger Lightning Strike at target |
| **Mouse Left Drag** | Orbit Camera 360° around mountain target |
| **Mouse Right Drag** | Pan Camera target position |
| **Mouse Scroll** | Zoom Camera In / Out |
| **Key 1** | Trigger Single Cloud-to-Earth Lightning Strike |
| **Key 2** | Toggle Continuous Storm Mode |
| **Key 3** | Toggle Volumetric Rain Particle Streaks |
| **Key 4** | Toggle Atmospheric Height Fog Density |
| **Key 5** | Apply Night Storm Environment Preset |
| **Key 6** | Apply Day Twilight Environment Preset |
| **Key 7** | Toggle Slow Motion (0.25x time scale) |
| **Key 8** | Trigger Explosion Blast Mode (3 simultaneous strikes) |
| **Key 9** | Toggle Cinematic Slow Mountain Orbit Camera Mode |
| **Key 0** | Reset Terrain Craters & Thermal Scorch Maps |

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
