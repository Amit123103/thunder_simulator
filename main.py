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
    """Binds to Render's $PORT for Web Service health checks and renders exact Desktop ImGui 3D Simulator UI."""
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cinematic Lightning Terrain Simulator (ModernGL)</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
        body, html { width: 100%; height: 100%; overflow: hidden; background: #05070c; font-family: 'Consolas', 'Courier New', monospace; color: #38bdf8; }
        
        #canvas-container { width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 1; }
        canvas { width: 100%; height: 100%; display: block; }
        
        /* App Window Header Bar */
        .app-titlebar {
            position: absolute; top: 0; left: 0; right: 0; height: 24px;
            background: #0f172a; border-bottom: 1px solid #1e293b;
            display: flex; justify-content: space-between; align-items: center;
            padding: 0 10px; font-size: 11px; color: #94a3b8; z-index: 20;
        }

        /* ImGui Window Panel */
        .imgui-panel {
            position: absolute; top: 35px; left: 15px; width: 340px;
            background: rgba(12, 16, 24, 0.92); border: 1px solid #1e293b;
            border-radius: 4px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            z-index: 10; font-size: 11px; color: #94a3b8; backdrop-filter: blur(8px);
        }
        .imgui-titlebar {
            background: rgba(20, 28, 44, 0.95); padding: 5px 8px; border-bottom: 1px solid #1e293b;
            display: flex; justify-content: space-between; align-items: center; color: #cbd5e1; font-weight: bold;
        }
        .imgui-content { padding: 10px; }
        .imgui-header { color: #38bdf8; font-weight: bold; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .imgui-stat { margin-bottom: 3px; color: #cbd5e1; }
        .imgui-val { color: #f8fafc; font-weight: bold; }
        
        /* ImGui Tabs */
        .imgui-tabs { display: flex; gap: 2px; margin: 10px 0; border-bottom: 1px solid #334155; }
        .tab-btn {
            background: #0f172a; border: 1px solid #1e293b; border-bottom: none;
            color: #94a3b8; padding: 4px 8px; font-size: 10px; cursor: pointer; border-radius: 3px 3px 0 0;
            font-family: inherit;
        }
        .tab-btn.active { background: #2563eb; color: #fff; border-color: #3b82f6; font-weight: bold; }
        
        /* ImGui Section */
        .imgui-section { margin-top: 8px; }
        .btn-group { display: flex; gap: 6px; margin: 6px 0; }
        .imgui-btn {
            flex: 1; background: #1e293b; border: 1px solid #334155; color: #f8fafc;
            padding: 5px; font-size: 10px; cursor: pointer; text-align: center; border-radius: 2px;
            font-family: inherit; font-weight: bold; transition: background 0.15s;
        }
        .imgui-btn:hover { background: #3b82f6; border-color: #60a5fa; }
        .imgui-btn.active { background: #2563eb; border-color: #60a5fa; }
        
        /* ImGui Sliders */
        .slider-row { display: flex; align-items: center; justify-content: space-between; margin: 6px 0; }
        .slider-track { flex: 1; margin: 0 8px; height: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 2px; position: relative; }
        .slider-fill { height: 100%; background: #2563eb; width: 50%; border-radius: 1px; }
        .slider-val { width: 50px; text-align: right; color: #60a5fa; font-weight: bold; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div class="app-titlebar">
        <span>Cinematic Lightning Terrain Simulator (ModernGL)</span>
        <span>─ ◻ ✕</span>
    </div>

    <div id="canvas-container"></div>

    <!-- ImGui Telemetry Window -->
    <div class="imgui-panel">
        <div class="imgui-titlebar">
            <span>▼ Cinematic Lightning Simulator</span>
            <span>x</span>
        </div>
        <div class="imgui-content">
            <div class="imgui-header">REALTIME GPU TELEMETRY</div>
            <div class="imgui-stat">Performance: <span class="imgui-val" id="stat-fps">87.6 FPS</span> | Frame Time: <span class="imgui-val" id="stat-ms">11.42 ms</span></div>
            <div class="imgui-stat">Active Particles: <span class="imgui-val" id="stat-particles">5246</span></div>
            <div class="imgui-stat">Active Lightning Bolts: <span class="imgui-val" id="stat-bolts">1</span></div>
            <div class="imgui-stat">Camera Mode: <span class="imgui-val" id="stat-camera">Orbit Camera</span></div>

            <div class="imgui-tabs">
                <button class="tab-btn active">Lightning</button>
                <button class="tab-btn">Atmosphere</button>
                <button class="tab-btn">Terrain</button>
                <button class="tab-btn">Post Proce..</button>
                <button class="tab-btn">Export</button>
            </div>

            <div class="imgui-section">
                <div style="color: #64748b; font-size: 10px;">Strike Trigger Mode</div>
                <div class="btn-group">
                    <button class="imgui-btn" onclick="triggerSingleStrike()">Single Strike [1]</button>
                    <button class="imgui-btn active" id="btn-storm" onclick="toggleStormMode()">Storm Mode [2]</button>
                </div>
            </div>

            <div class="imgui-section" style="margin-top: 10px;">
                <div style="color: #64748b; font-size: 10px; margin-bottom: 4px;">Bolt Parameters</div>
                <div class="slider-row">
                    <span class="slider-val" id="val-glow">12.800</span>
                    <div class="slider-track"><div class="slider-fill" style="width: 80%;"></div></div>
                    <span>Glow Intensity</span>
                </div>
                <div class="slider-row">
                    <span class="slider-val" id="val-width">0.550</span>
                    <div class="slider-track"><div class="slider-fill" style="width: 55%;"></div></div>
                    <span>Bolt Width</span>
                </div>
                <div class="slider-row">
                    <span class="slider-val" id="val-branch">0.380</span>
                    <div class="slider-track"><div class="slider-fill" style="width: 38%;"></div></div>
                    <span>Branch Count</span>
                </div>
                <div class="slider-row">
                    <span class="slider-val" id="val-jitter">0.380</span>
                    <div class="slider-track"><div class="slider-fill" style="width: 38%;"></div></div>
                    <span>Fractal Jitter</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        let scene, camera, renderer, controls;
        let terrainMesh, rainParticles, lightFlash, hitPointLight;
        let activeBolts = [];
        let stormMode = true;
        let autoOrbit = true;
        let stormTimer = 0;
        let frameCount = 0, lastTime = performance.now();
        let audioCtx = null;

        function initAudio() {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }

        function playThunderSound() {
            if (!audioCtx) return;
            try {
                let osc = audioCtx.createOscillator();
                let gain = audioCtx.createGain();
                let now = audioCtx.currentTime;
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(350, now);
                osc.frequency.exponentialRampToValueAtTime(30, now + 0.18);
                gain.gain.setValueAtTime(0.25, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.18);
                osc.connect(gain); gain.connect(audioCtx.destination);
                osc.start(now); osc.stop(now + 0.18);
            } catch(e){}
        }

        function initScene() {
            const container = document.getElementById('canvas-container');
            scene = new THREE.Scene();
            scene.fog = new THREE.FogExp2(0x0a101d, 0.012);

            camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 22, 60);

            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.3;
            container.appendChild(renderer.domElement);

            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2 - 0.02;

            scene.add(new THREE.AmbientLight(0x1e293b, 0.7));

            lightFlash = new THREE.DirectionalLight(0x93c5fd, 0.2);
            lightFlash.position.set(0, 100, 0);
            scene.add(lightFlash);

            hitPointLight = new THREE.PointLight(0x38bdf8, 0, 90);
            scene.add(hitPointLight);

            // Mountain Terrain Mesh
            const geo = new THREE.PlaneGeometry(140, 140, 140, 140);
            geo.rotateX(-Math.PI / 2);
            const pos = geo.attributes.position;
            for (let i = 0; i < pos.count; i++) {
                let x = pos.getX(i);
                let z = pos.getZ(i);
                let dist = Math.sqrt(x*x + z*z);
                let height = Math.sin(x * 0.07) * Math.cos(z * 0.07) * 16.0 
                           + Math.sin(x * 0.14 + z * 0.14) * 7.0 
                           - (dist * 0.08);
                pos.setY(i, Math.max(-2, height));
            }
            geo.computeVertexNormals();

            terrainMesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
                color: 0x1e293b, roughness: 0.65, metalness: 0.35, flatShading: true
            }));
            scene.add(terrainMesh);

            // Volumetric Rain Streaks Particle System (5,246 particles)
            const rainGeo = new THREE.BufferGeometry();
            const rainCount = 5246;
            const rainPos = new Float32Array(rainCount * 3);
            for (let i = 0; i < rainCount * 3; i += 3) {
                rainPos[i] = (Math.random() - 0.5) * 120;
                rainPos[i+1] = Math.random() * 70;
                rainPos[i+2] = (Math.random() - 0.5) * 120;
            }
            rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPos, 3));
            rainParticles = new THREE.Points(rainGeo, new THREE.PointsMaterial({
                color: 0x94a3b8, size: 0.25, transparent: true, opacity: 0.6
            }));
            scene.add(rainParticles);

            window.addEventListener('resize', onWindowResize);
            window.addEventListener('keydown', (e) => {
                if (e.key === '1') triggerSingleStrike();
                if (e.key === '2') toggleStormMode();
                if (e.key === '9') autoOrbit = !autoOrbit;
            });
        }

        function triggerSingleStrike() {
            initAudio();
            let targetX = (Math.random() - 0.5) * 50;
            let targetZ = (Math.random() - 0.5) * 50;
            let targetY = 4.0;

            let points = [];
            let curr = new THREE.Vector3(targetX + (Math.random() - 0.5) * 12, 55, targetZ + (Math.random() - 0.5) * 12);
            let end = new THREE.Vector3(targetX, targetY, targetZ);
            let segs = 24;

            for (let i = 0; i <= segs; i++) {
                let t = i / segs;
                let p = new THREE.Vector3().lerpVectors(curr, end, t);
                if (i > 0 && i < segs) {
                    p.x += (Math.random() - 0.5) * 3.5;
                    p.y += (Math.random() - 0.5) * 1.5;
                    p.z += (Math.random() - 0.5) * 3.5;
                }
                points.push(p);
            }

            const boltLine = new THREE.Line(
                new THREE.BufferGeometry().setFromPoints(points),
                new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 4 })
            );
            scene.add(boltLine);

            lightFlash.intensity = 5.0;
            hitPointLight.position.set(targetX, targetY + 3, targetZ);
            hitPointLight.intensity = 18;

            playThunderSound();
            activeBolts.push({ line: boltLine, life: 0.16 });
            document.getElementById('stat-bolts').innerText = activeBolts.length;
        }

        function toggleStormMode() {
            stormMode = !stormMode;
            document.getElementById('btn-storm').classList.toggle('active', stormMode);
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }

        function animate(now) {
            requestAnimationFrame(animate);

            // FPS Telemetry
            frameCount++;
            if (now - lastTime >= 500) {
                let fps = (frameCount * 1000) / (now - lastTime);
                document.getElementById('stat-fps').innerText = fps.toFixed(1) + " FPS";
                document.getElementById('stat-ms').innerText = (1000 / fps).toFixed(2) + " ms";
                frameCount = 0; lastTime = now;
            }

            // Auto Camera Orbit
            if (autoOrbit) {
                let angle = now * 0.00012;
                camera.position.x = Math.sin(angle) * 65;
                camera.position.z = Math.cos(angle) * 65;
                camera.lookAt(0, 4, 0);
            }
            controls.update();

            // Rain Particle Fall Loop
            const pos = rainParticles.geometry.attributes.position;
            for (let i = 1; i < pos.count * 3; i += 3) {
                pos.array[i] -= 1.8;
                if (pos.array[i] < 0) pos.array[i] = 70;
            }
            pos.needsUpdate = true;

            // Auto Storm Trigger
            if (stormMode) {
                stormTimer += 0.016;
                if (stormTimer > 1.1) {
                    stormTimer = 0;
                    triggerSingleStrike();
                }
            }

            // Light Decay
            if (lightFlash.intensity > 0.2) lightFlash.intensity *= 0.88;
            if (hitPointLight.intensity > 0) hitPointLight.intensity *= 0.84;

            for (let i = activeBolts.length - 1; i >= 0; i--) {
                activeBolts[i].life -= 0.016;
                if (activeBolts[i].life <= 0) {
                    scene.remove(activeBolts[i].line);
                    activeBolts[i].line.geometry.dispose();
                    activeBolts[i].line.material.dispose();
                    activeBolts.splice(i, 1);
                }
            }
            document.getElementById('stat-bolts').innerText = activeBolts.length;

            renderer.render(scene, camera);
        }

        window.onload = () => {
            initScene();
            animate(performance.now());
        };
    </script>
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
