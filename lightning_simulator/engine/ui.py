"""
ImGui Interface Dock & Telemetry HUD.
Provides interactive sliders, mode switches, scene presets, camera controls, and OBJ/PNG export triggers.
"""

import imgui
from .config import Config

class UIManager:
    """Manages real-time ImGui HUD windows, parameter docks, and telemetry telemetry."""

    def __init__(self, imgui_renderer=None):
        self.imgui_renderer = imgui_renderer
        self.show_hud = True
        self.show_demo = False

        # Status & Notifications
        self.notification_msg = "Ready. Click terrain or press [1] to strike lightning."
        self.notification_timer = 5.0

    def render(self, app_state, delta_time, fps):
        """Renders ImGui GUI widgets."""
        if not self.show_hud:
            return

        if self.notification_timer > 0.0:
            self.notification_timer -= delta_time

        # Style customization for modern cinematic dark theme
        imgui.style_colors_dark()
        style = imgui.get_style()
        style.window_rounding = 8.0
        style.frame_rounding = 4.0
        style.grab_rounding = 4.0
        style.item_spacing = (8.0, 6.0)

        # ----------------------------------------------------
        # Main Telemetry & Control Panel Dock
        # ----------------------------------------------------
        imgui.set_next_window_position(15, 15, imgui.ONCE)
        imgui.set_next_window_size(380, 720, imgui.ONCE)

        imgui.begin("Cinematic Lightning Simulator", True)

        imgui.text_colored("REALTIME GPU TELEMETRY", 0.3, 0.85, 1.0, 1.0)
        imgui.text(f"Performance: {fps:.1f} FPS | Frame Time: {1000.0 / max(1.0, fps):.2f} ms")
        imgui.text(f"Active Particles: {app_state['particle_count']}")
        imgui.text(f"Active Lightning Bolts: {app_state['active_bolts']}")
        imgui.text(f"Camera Mode: {app_state['camera_mode_name']}")
        imgui.separator()

        # Notification Banner
        if self.notification_timer > 0.0:
            imgui.text_colored(f">> {self.notification_msg}", 1.0, 0.9, 0.2, 1.0)
            imgui.separator()

        # Tabbed Control Docks
        if imgui.begin_tab_bar("SimulatorTabs"):
            
            # --- TAB 1: LIGHTNING SIMULATION ---
            if imgui.begin_tab_item("Lightning")[0]:
                imgui.spacing()
                imgui.text_colored("Strike Trigger Mode", 0.4, 0.8, 1.0, 1.0)
                
                if imgui.button("Single Strike [1]"):
                    app_state['trigger_single_strike'] = True
                imgui.same_line()
                if imgui.button("Storm Mode [2]"):
                    app_state['toggle_storm_mode'] = True
                
                imgui.spacing()
                imgui.text("Bolt Parameters")
                
                _, Config.LIGHTNING_GLOW_INTENSITY = imgui.slider_float(
                    "Glow Intensity", Config.LIGHTNING_GLOW_INTENSITY, 1.0, 25.0
                )
                _, Config.LIGHTNING_BOLT_WIDTH = imgui.slider_float(
                    "Bolt Width", Config.LIGHTNING_BOLT_WIDTH, 0.1, 1.5
                )
                _, Config.LIGHTNING_BRANCH_PROBABILITY = imgui.slider_float(
                    "Branch Count", Config.LIGHTNING_BRANCH_PROBABILITY, 0.1, 0.8
                )
                _, Config.LIGHTNING_ROUGHNESS = imgui.slider_float(
                    "Fractal Jitter", Config.LIGHTNING_ROUGHNESS, 0.1, 0.8
                )
                imgui.end_tab_item()

            # --- TAB 2: ATMOSPHERE & WEATHER ---
            if imgui.begin_tab_item("Atmosphere")[0]:
                imgui.spacing()
                imgui.text_colored("Sun & Sky Scattering", 0.4, 0.8, 1.0, 1.0)
                
                changed, Config.SUN_ELEVATION = imgui.slider_float("Sun Elevation", Config.SUN_ELEVATION, -20.0, 80.0)
                if changed:
                    app_state['update_atmosphere'] = True

                changed, Config.SUN_AZIMUTH = imgui.slider_float("Sun Azimuth", Config.SUN_AZIMUTH, 0.0, 360.0)
                if changed:
                    app_state['update_atmosphere'] = True

                imgui.spacing()
                imgui.text("Volumetric Weather")
                _, Config.FOG_DENSITY = imgui.slider_float("Fog Density", Config.FOG_DENSITY, 0.0, 0.08)
                _, Config.CLOUD_DENSITY = imgui.slider_float("Cloud Density", Config.CLOUD_DENSITY, 0.1, 1.5)
                _, Config.CLOUD_COVERAGE = imgui.slider_float("Cloud Coverage", Config.CLOUD_COVERAGE, 0.1, 1.0)

                imgui.spacing()
                imgui.text("Presets")
                if imgui.button("Night Mode [5]"):
                    app_state['preset_night'] = True
                imgui.same_line()
                if imgui.button("Day Mode [6]"):
                    app_state['preset_day'] = True
                imgui.same_line()
                if imgui.button("Storm [2]"):
                    app_state['preset_storm'] = True

                imgui.end_tab_item()

            # --- TAB 3: TERRAIN & CRATER PHYSICS ---
            if imgui.begin_tab_item("Terrain")[0]:
                imgui.spacing()
                imgui.text_colored("Impact Physics", 0.4, 0.8, 1.0, 1.0)
                
                _, Config.CRATER_RADIUS_BASE = imgui.slider_float("Crater Radius", Config.CRATER_RADIUS_BASE, 1.0, 10.0)
                _, Config.CRATER_DEPTH_BASE = imgui.slider_float("Crater Depth", Config.CRATER_DEPTH_BASE, 0.5, 6.0)
                _, Config.IMPACT_HEAT_DURATION = imgui.slider_float("Molten Cooling Time", Config.IMPACT_HEAT_DURATION, 1.0, 20.0)

                imgui.spacing()
                if imgui.button("Reset Terrain [0]"):
                    app_state['reset_terrain'] = True
                
                imgui.end_tab_item()

            # --- TAB 4: POST-PROCESSING & HDR ---
            if imgui.begin_tab_item("Post Process")[0]:
                imgui.spacing()
                imgui.text_colored("HDR & Tonemapping", 0.4, 0.8, 1.0, 1.0)

                _, Config.EXPOSURE = imgui.slider_float("Exposure", Config.EXPOSURE, 0.2, 3.5)
                _, Config.BLOOM_THRESHOLD = imgui.slider_float("Bloom Threshold", Config.BLOOM_THRESHOLD, 0.5, 3.0)
                _, Config.BLOOM_INTENSITY = imgui.slider_float("Bloom Glow", Config.BLOOM_INTENSITY, 0.1, 5.0)
                _, Config.CHROMATIC_ABERRATION = imgui.slider_float("Chromatic Aberr.", Config.CHROMATIC_ABERRATION, 0.0, 0.02)
                _, Config.VIGNETTE_STRENGTH = imgui.slider_float("Vignette", Config.VIGNETTE_STRENGTH, 0.0, 1.0)
                
                imgui.end_tab_item()

            # --- TAB 5: EXPORT & TOOLS ---
            if imgui.begin_tab_item("Export")[0]:
                imgui.spacing()
                imgui.text_colored("Screenshot & Asset Exporters", 0.4, 0.8, 1.0, 1.0)

                if imgui.button("Export Screenshot PNG"):
                    app_state['export_screenshot'] = True
                
                if imgui.button("Export Heightmap PNG"):
                    app_state['export_heightmap'] = True

                if imgui.button("Export Terrain OBJ Mesh"):
                    app_state['export_obj'] = True

                imgui.end_tab_item()

            imgui.end_tab_bar()

        imgui.end()

    def set_notification(self, msg):
        """Displays temporary notification message on UI dock."""
        self.notification_msg = msg
        self.notification_timer = 4.5
