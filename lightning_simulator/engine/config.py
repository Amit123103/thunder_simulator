"""
Engine Configuration and Global Parameters for Lightning Terrain Simulator.
"""

import math

class Config:
    # Window & Graphics Settings
    WINDOW_TITLE = "Cinematic Lightning Terrain Simulator (ModernGL)"
    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 900
    VSYNC = False
    TARGET_FPS = 120
    MSAA_SAMPLES = 4

    # Terrain Settings
    TERRAIN_GRID_SIZE = 256  # 256x256 vertex grid
    TERRAIN_WORLD_SIZE = 120.0  # Physical world width/depth
    TERRAIN_MAX_HEIGHT = 28.0
    TERRAIN_ROUGHNESS = 1.2
    OCTAVES = 6
    PERSISTENCE = 0.5
    LACUNARITY = 2.0
    PARALLAX_SCALE = 0.04
    PARALLAX_LAYERS = 32

    # Physics & Impact Crater Settings
    CRATER_RADIUS_BASE = 4.5
    CRATER_DEPTH_BASE = 2.2
    IMPACT_HEAT_DURATION = 8.0  # seconds until molten ground fully cools
    SHOCKWAVE_SPEED = 45.0
    MAX_HEAT = 1.0

    # Lightning Generation
    LIGHTNING_MAX_BRANCHES = 128
    LIGHTNING_SUBDIVISIONS = 6
    LIGHTNING_ROUGHNESS = 0.38
    LIGHTNING_BRANCH_PROBABILITY = 0.35
    LIGHTNING_BRANCH_DECAY = 0.65
    LIGHTNING_BOLT_WIDTH = 0.45
    LIGHTNING_GLOW_INTENSITY = 9.5
    LIGHTNING_STRIKE_DURATION = 0.38  # seconds
    LIGHTNING_STORM_INTERVAL = 1.6   # seconds between automatic strikes in storm mode

    # Volumetric Clouds
    CLOUD_MIN_HEIGHT = 45.0
    CLOUD_MAX_HEIGHT = 70.0
    CLOUD_DENSITY = 0.85
    CLOUD_COVERAGE = 0.65
    CLOUD_STEPS = 64
    CLOUD_LIGHT_STEPS = 6
    WIND_VECTOR = (3.5, 0.0, 2.0)

    # Atmosphere & Sky
    SUN_AZIMUTH = 45.0
    SUN_ELEVATION = 12.0  # Twilight storm look
    RAYLEIGH_COEFF = (0.0058, 0.0135, 0.0331)
    MIE_COEFF = 0.004
    MIE_G = 0.76
    FOG_DENSITY = 0.015
    FOG_HEIGHT_FALLOFF = 0.08
    FOG_COLOR = (0.08, 0.12, 0.18)

    # GPU Particles
    MAX_PARTICLES = 30000
    SPARK_COUNT_PER_IMPACT = 800
    SMOKE_COUNT_PER_IMPACT = 300
    DEBRIS_COUNT_PER_IMPACT = 250
    RAIN_PARTICLE_COUNT = 8000

    # Post-Processing & HDR
    EXPOSURE = 1.35
    BLOOM_THRESHOLD = 1.1
    BLOOM_INTENSITY = 2.2
    BLOOM_RADIUS = 0.85
    CHROMATIC_ABERRATION = 0.0035
    VIGNETTE_STRENGTH = 0.45
    FILM_GRAIN = 0.03
    DEPTH_OF_FIELD_ENABLED = True
    DOF_FOCUS_DISTANCE = 35.0
    DOF_BOLEH_RANGE = 25.0

    # Modes & Presets
    STRIKE_MODE_SINGLE = 1
    STRIKE_MODE_STORM = 2
    STRIKE_MODE_CONTINUOUS = 3

    # Key Bindings
    KEY_MAP = {
        '1': 'Single Strike',
        '2': 'Storm Mode Toggle',
        '3': 'Rain Density Toggle',
        '4': 'Fog Density Toggle',
        '5': 'Night Mode',
        '6': 'Day Mode',
        '7': 'Slow Motion Toggle',
        '8': 'Explosion Mode',
        '9': 'Toggle Auto-Orbit',
        '0': 'Reset Terrain',
    }
