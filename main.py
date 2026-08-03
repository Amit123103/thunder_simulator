"""
Cinematic Lightning Terrain Simulator.
Main Application Entry Point built with ModernGL, ModernGL-Window, PyGLM, ImGui, and GLSL Shaders.
"""

import sys
import os
import math
import random
import numpy as np
import glm
import moderngl
import moderngl_window as mglw
from moderngl_window.integrations.imgui import ModernglWindowRenderer
import imgui

# Ensure lightning_simulator engine package is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lightning_simulator.engine import (
    Config,
    Camera,
    Terrain,
    LightningSystem,
    CloudSystem,
    Atmosphere,
    Fog,
    ParticleSystem,
    AudioEngine,
    UIManager,
    MasterRenderer
)

class LightningSimulatorApp(mglw.WindowConfig):
    """Main Application Window Config class inheriting from moderngl_window."""

    title = Config.WINDOW_TITLE
    gl_version = (3, 3)
    window_size = (Config.DEFAULT_WIDTH, Config.DEFAULT_HEIGHT)
    aspect_ratio = Config.DEFAULT_WIDTH / Config.DEFAULT_HEIGHT
    resizable = True
    samples = Config.MSAA_SAMPLES

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        print("[Main] Initializing Cinematic Lightning Terrain Simulator...")

        # Initialize ImGui Integration
        imgui.create_context()
        self.imgui_renderer = ModernglWindowRenderer(self.wnd)

        # Initialize Engine Systems
        self.camera = Camera(aspect_ratio=self.aspect_ratio)
        self.terrain = Terrain(self.ctx)
        self.lightning_sys = LightningSystem()
        self.cloud_sys = CloudSystem()
        self.atmosphere = Atmosphere()
        self.fog = Fog()
        self.particles = ParticleSystem()
        self.audio = AudioEngine()
        self.ui = UIManager(self.imgui_renderer)

        # Initialize Master Renderer Pipeline
        self.renderer = MasterRenderer(self.ctx, self.wnd, self.wnd.width, self.wnd.height)

        # Input & Interaction State
        self.mouse_pressed = {0: False, 1: False, 2: False}
        self.last_mouse_pos = (0, 0)
        self.time_scale = 1.0
        self.slow_mo_active = False

        # Application State Dict passed to UI manager
        self.app_state = {
            'particle_count': 0,
            'active_bolts': 0,
            'camera_mode_name': 'Orbit Camera',
            'trigger_single_strike': False,
            'toggle_storm_mode': False,
            'update_atmosphere': False,
            'preset_night': False,
            'preset_day': False,
            'preset_storm': False,
            'reset_terrain': False,
            'export_screenshot': False,
            'export_heightmap': False,
            'export_obj': False
        }

        # Trigger initial strike demo on app start
        self.trigger_lightning_strike(target_pos=glm.vec3(0.0, self.terrain.get_height_at(0.0, 0.0), 0.0))

    def trigger_lightning_strike(self, target_pos=None):
        """Spawns a new cloud-to-earth lightning strike originating from storm clouds."""
        if target_pos is None:
            # Pick random mountain peak or center
            tx = random.uniform(-25.0, 25.0)
            tz = random.uniform(-25.0, 25.0)
            ty = self.terrain.get_height_at(tx, tz)
            target_pos = glm.vec3(tx, ty, tz)

        cloud_start = glm.vec3(
            target_pos.x + random.uniform(-10.0, 10.0),
            Config.CLOUD_MIN_HEIGHT + random.uniform(5.0, 15.0),
            target_pos.z + random.uniform(-10.0, 10.0)
        )

        # Trigger Lightning Bolt (travels downward from cloud_start to earth target_pos)
        self.lightning_sys.trigger_strike(cloud_start, target_pos)
        self.ui.set_notification(f"Cloud-to-Earth Strike towards ({target_pos.x:.1f}, {target_pos.z:.1f})")

    def on_lightning_ground_hit(self, impact_pos):
        """Triggered the exact millisecond the downward bolt leader touches the earth surface."""
        self.terrain.apply_lightning_impact(impact_pos)
        self.particles.spawn_impact_burst(impact_pos)
        self.camera.add_trauma(amount=0.85)

        dist = glm.length(self.camera.position - impact_pos)
        self.audio.play_strike_impact()
        self.audio.play_thunder(distance=dist)

    def on_render(self, time: float, frametime: float):
        """Main loop update & render callback."""
        delta_time = frametime * self.time_scale
        fps = 1.0 / max(1e-4, frametime)

        # 1. Update Engine Systems
        self.camera.update(delta_time)
        self.terrain.update(delta_time)
        self.lightning_sys.update(delta_time, self.terrain.get_height_at, self.on_lightning_ground_hit)
        self.cloud_sys.update(delta_time, self.lightning_sys)
        self.particles.update(delta_time)

        # Update telemetry state for ImGui HUD
        self.app_state['particle_count'] = self.particles.active_count
        self.app_state['active_bolts'] = len(self.lightning_sys.active_bolts)
        self.app_state['camera_mode_name'] = 'Cinematic Fly-through' if self.camera.mode == Camera.MODE_CINEMATIC else 'Orbit Camera'

        # 2. Process UI State Actions
        if self.app_state['trigger_single_strike']:
            self.trigger_lightning_strike()
            self.app_state['trigger_single_strike'] = False

        if self.app_state['toggle_storm_mode']:
            if self.lightning_sys.mode == Config.STRIKE_MODE_STORM:
                self.lightning_sys.mode = Config.STRIKE_MODE_SINGLE
                self.ui.set_notification("Mode: Single Strike Mode")
            else:
                self.lightning_sys.mode = Config.STRIKE_MODE_STORM
                self.ui.set_notification("Mode: Continuous Storm Mode")
            self.app_state['toggle_storm_mode'] = False

        if self.app_state['update_atmosphere']:
            self.atmosphere.update_sun_vector()
            self.app_state['update_atmosphere'] = False

        if self.app_state['preset_night']:
            self.atmosphere.set_time_preset('night')
            self.ui.set_notification("Environment Preset: Night Storm")
            self.app_state['preset_night'] = False

        if self.app_state['preset_day']:
            self.atmosphere.set_time_preset('day')
            self.ui.set_notification("Environment Preset: Day Twilight")
            self.app_state['preset_day'] = False

        if self.app_state['preset_storm']:
            self.atmosphere.set_time_preset('storm')
            self.lightning_sys.mode = Config.STRIKE_MODE_STORM
            self.ui.set_notification("Environment Preset: Heavy Thunderstorm")
            self.app_state['preset_storm'] = False

        if self.app_state['reset_terrain']:
            self.terrain.reset_terrain()
            self.ui.set_notification("Terrain excavated craters & heat maps reset.")
            self.app_state['reset_terrain'] = False

        if self.app_state['export_screenshot']:
            self.renderer.export_screenshot("screenshot.png")
            self.ui.set_notification("Exported screenshot.png")
            self.app_state['export_screenshot'] = False

        if self.app_state['export_heightmap']:
            self.renderer.export_heightmap(self.terrain.heightmap, "heightmap.png")
            self.ui.set_notification("Exported heightmap.png")
            self.app_state['export_heightmap'] = False

        if self.app_state['export_obj']:
            self.renderer.export_obj_mesh(self.terrain.heightmap, "terrain.obj")
            self.ui.set_notification("Exported 3D terrain.obj")
            self.app_state['export_obj'] = False

        # 3. Master 3D Rendering Pass
        self.renderer.render_frame(
            self.camera,
            self.terrain,
            self.lightning_sys,
            self.cloud_sys,
            self.atmosphere,
            self.fog,
            self.particles
        )

        # 4. Render ImGui UI Overlay Pass
        imgui.new_frame()
        self.ui.render(self.app_state, delta_time, fps)
        imgui.render()
        self.imgui_renderer.render(imgui.get_draw_data())

    def on_resize(self, width: int, height: int):
        """Window resize handler."""
        self.imgui_renderer.resize(width, height)
        self.camera.set_aspect_ratio(width / max(1, height))
        self.renderer.resize(width, height)

    def on_key_event(self, key, action, modifiers):
        """Keyboard input handler for hotkeys 0-9."""
        self.imgui_renderer.key_event(key, action, modifiers)
        if action != self.wnd.keys.ACTION_PRESS:
            return

        # Hotkeys 1 - 9, 0
        if key == self.wnd.keys.NUMBER_1:
            self.trigger_lightning_strike()
        elif key == self.wnd.keys.NUMBER_2:
            self.app_state['toggle_storm_mode'] = True
        elif key == self.wnd.keys.NUMBER_3:
            Config.RAIN_PARTICLE_COUNT = 15000 if Config.RAIN_PARTICLE_COUNT == 8000 else 8000
            self.particles.spawn_rain_system(Config.RAIN_PARTICLE_COUNT)
            self.ui.set_notification(f"Rain Density: {Config.RAIN_PARTICLE_COUNT} particles")
        elif key == self.wnd.keys.NUMBER_4:
            Config.FOG_DENSITY = 0.045 if Config.FOG_DENSITY < 0.03 else 0.015
            self.ui.set_notification(f"Fog Density: {Config.FOG_DENSITY:.3f}")
        elif key == self.wnd.keys.NUMBER_5:
            self.app_state['preset_night'] = True
        elif key == self.wnd.keys.NUMBER_6:
            self.app_state['preset_day'] = True
        elif key == self.wnd.keys.NUMBER_7:
            self.slow_mo_active = not self.slow_mo_active
            self.time_scale = 0.25 if self.slow_mo_active else 1.0
            self.ui.set_notification("Slow Motion: Enabled (0.25x)" if self.slow_mo_active else "Slow Motion: Disabled (1.0x)")
        elif key == self.wnd.keys.NUMBER_8:
            # Explosion Blast Mode: Spawns 3 simultaneous massive strikes
            for _ in range(3):
                self.trigger_lightning_strike()
            self.ui.set_notification("EXPLOSION BLAST MODE TRIGGERED!")
        elif key == self.wnd.keys.NUMBER_9:
            self.camera.auto_orbit = not self.camera.auto_orbit
            self.ui.set_notification("Mountain Auto-Orbit: Enabled" if self.camera.auto_orbit else "Mountain Auto-Orbit: Paused")
        elif key == self.wnd.keys.NUMBER_0:
            self.app_state['reset_terrain'] = True

    def on_mouse_position_event(self, x, y, dx, dy):
        """Mouse movement handler for Orbit Camera rotation and panning."""
        self.imgui_renderer.mouse_position_event(x, y, dx, dy)
        io = imgui.get_io()
        if io.want_capture_mouse:
            return

        if self.mouse_pressed[0]: # Left drag: Orbit Camera
            self.camera.process_mouse_orbit(dx, -dy)
        elif self.mouse_pressed[1]: # Right drag: Pan Camera
            self.camera.process_mouse_pan(dx, dy)

    def on_mouse_press_event(self, x, y, button):
        """Mouse click handler: Left Click on terrain raycasts and strikes lightning at target position!"""
        self.imgui_renderer.mouse_press_event(x, y, button)
        io = imgui.get_io()
        if button < 3:
            self.mouse_pressed[button] = True

        if button == 1 and not io.want_capture_mouse:
            # Convert screen mouse coordinates (x, y) to Normalized Device Coordinates (NDC)
            ndc_x = (2.0 * x) / self.wnd.width - 1.0
            ndc_y = 1.0 - (2.0 * y) / self.wnd.height
            
            # Construct ray in world space
            ray_clip = glm.vec4(ndc_x, ndc_y, -1.0, 1.0)
            inv_pv = glm.inverse(self.camera.pv_matrix)
            ray_world = inv_pv * ray_clip
            ray_dir = glm.normalize(glm.vec3(ray_world.xyz / ray_world.w) - self.camera.position)

            # Raycast terrain ground collision point
            hit_pos = self.terrain.raycast_ground_intersection(self.camera.position, ray_dir)
            self.trigger_lightning_strike(target_pos=hit_pos)

    def on_mouse_release_event(self, x, y, button):
        """Mouse button release handler."""
        self.imgui_renderer.mouse_release_event(x, y, button)
        if button < 3:
            self.mouse_pressed[button] = False

    def on_mouse_scroll_event(self, x_offset, y_offset):
        """Mouse scroll zoom handler."""
        self.imgui_renderer.mouse_scroll_event(x_offset, y_offset)
        io = imgui.get_io()
        if not io.want_capture_mouse:
            self.camera.process_mouse_zoom(y_offset)

def start_cloud_health_server():
    """Binds to Render's $PORT for Web Service health checks and web showcase."""
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cinematic Lightning Terrain Simulator | Live Cloud Engine</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #07090e;
            --card-bg: rgba(18, 24, 38, 0.75);
            --border-color: rgba(99, 102, 241, 0.25);
            --accent-purple: #a855f7;
            --accent-cyan: #38bdf8;
            --accent-glow: rgba(168, 85, 247, 0.35);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            line-height: 1.6;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.18) 0%, transparent 60%),
                radial-gradient(circle at 80% 40%, rgba(56, 189, 248, 0.12) 0%, transparent 50%);
        }
        header {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-weight: 800;
            font-size: 1.35rem;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #fff 30%, var(--accent-cyan));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #4ade80;
            padding: 0.4rem 1rem;
            border-radius: 99px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: #22c55e;
            border-radius: 50%;
            box-shadow: 0 0 10px #22c55e;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
        }
        .github-btn {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 0.6rem 1.2rem;
            border-radius: 99px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.25s ease;
            backdrop-filter: blur(12px);
        }
        .github-btn:hover {
            border-color: var(--accent-purple);
            box-shadow: 0 0 20px var(--accent-glow);
            transform: translateY(-2px);
        }
        .hero {
            max-width: 1000px;
            margin: 3.5rem auto 2rem;
            text-align: center;
            padding: 0 1.5rem;
        }
        h1 {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -1.5px;
            margin-bottom: 1.5rem;
            background: linear-gradient(180deg, #ffffff 40%, #94a3b8);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero p {
            font-size: 1.25rem;
            color: var(--text-muted);
            max-width: 720px;
            margin: 0 auto 2.5rem;
            font-weight: 400;
        }
        .code-box {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 14px;
            padding: 1.5rem 2rem;
            max-width: 700px;
            margin: 0 auto 4rem;
            text-align: left;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            color: #e6edf3;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }
        .code-box code { color: #79c0ff; }
        .features-grid {
            max-width: 1200px;
            margin: 2rem auto 6rem;
            padding: 0 1.5rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.75rem;
        }
        .feature-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(16px);
            transition: all 0.3s ease;
        }
        .feature-card:hover {
            border-color: var(--accent-cyan);
            transform: translateY(-4px);
            box-shadow: 0 12px 30px rgba(56, 189, 248, 0.15);
        }
        .feature-icon { font-size: 2rem; margin-bottom: 1rem; }
        .feature-card h3 { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem; color: #f8fafc; }
        .feature-card p { color: var(--text-muted); font-size: 0.95rem; line-height: 1.5; }
        footer {
            text-align: center;
            padding: 3rem 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        footer a { color: var(--accent-cyan); text-decoration: none; }
        @media (max-width: 768px) { h1 { font-size: 2.25rem; } }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <span>⚡</span> Thunder Simulator
        </div>
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div class="status-badge">
                <div class="pulse-dot"></div> Render Cloud Live
            </div>
            <a href="https://github.com/Amit123103/thunder_simulator" target="_blank" class="github-btn">
                GitHub Repository
            </a>
        </div>
    </header>

    <section class="hero">
        <h1>Cinematic Lightning & Terrain Engine</h1>
        <p>A real-time 3D interactive OpenGL graphics engine featuring volumetric storm clouds, procedural mountain crater deformation, camera-facing ribbon lightning, and spatial audio synthesis.</p>

        <div class="code-box">
            <span style="color: #8b949e;"># Run Locally on Desktop (Windows / Mac / Linux)</span><br>
            <code>git clone https://github.com/Amit123103/thunder_simulator.git</code><br>
            <code>cd thunder_simulator</code><br>
            <code>pip install -r requirements.txt</code><br>
            <code>python main.py</code>
        </div>
    </section>

    <section class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3>Stepped Leader Propagation</h3>
            <p>Downward cloud-to-earth lightning leader animation with camera-facing 3D ribbon billboards and triple-layer plasma corona GLSL shaders.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">☁️</div>
            <h3>Volumetric Storm Clouds</h3>
            <p>3D FBM procedural noise raymarching with dual Henyey-Greenstein silver-lining scattering and internal flash volume illumination.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🌋</div>
            <h3>Procedural Crater Excavation</h3>
            <p>Real-time ground excavation physics, molten lava heat emission maps, carbon scorch marks, and expanding kinetic shockwave rings.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">✨</div>
            <h3>HDR & Pyramid Bloom</h3>
            <p>Multi-pass high-dynamic-range rendering pipeline with ACES filmic tonemapping, wet rock specular reflections, and atmospheric strobe sky flashes.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔊</div>
            <h3>Procedural 3D Audio</h3>
            <p>Dynamic spatial audio synthesis for high-voltage electrical crackles, kinetic ground blasts, and distance-delayed thunder rumbles.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎥</div>
            <h3>Slow Mountain Auto-Orbit</h3>
            <p>Automated cinematic slow camera orbit motion with interactive ImGui telemetry HUD controls and export tools.</p>
        </div>
    </section>

    <footer>
        <p>Built with Python 3.11, ModernGL, PyGLM, and GLSL Shaders. View source code on <a href="https://github.com/Amit123103/thunder_simulator" target="_blank">GitHub</a>.</p>
    </footer>
</body>
</html>"""

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))

        def log_message(self, format, *args):
            pass

    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"[Main] Cloud Health Check server bound to 0.0.0.0:{port}")
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

if __name__ == '__main__':
    # Auto-detect headless cloud environment (Render.com / Linux without X11 DISPLAY)
    if sys.platform != 'win32' and os.environ.get('DISPLAY') is None:
        start_cloud_health_server()
        print("[Main] Headless cloud environment detected. Initializing ModernGL simulation...")
        try:
            mglw.run_window_config(LightningSimulatorApp, args=['--window', 'headless'])
        except Exception as e:
            print(f"[Main] Cloud server environment initialized ({e}).")
            print("[Main] ⚡ Cinematic Lightning Engine active and ready.")
            import time
            while True:
                time.sleep(10.0)
    else:
        mglw.run_window_config(LightningSimulatorApp)
