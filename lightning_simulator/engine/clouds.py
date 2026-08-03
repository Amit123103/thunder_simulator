"""
Procedural Volumetric Clouds System.
Handles 3D storm cloud raymarching parameters, density movement, wind drift, and internal lightning flash illumination.
"""

import math
import numpy as np
import glm
from .config import Config

class CloudSystem:
    """Manages storm cloud volume bounds, dynamic wind animation, and internal lightning illumination state."""

    def __init__(self):
        self.min_height = Config.CLOUD_MIN_HEIGHT
        self.max_height = Config.CLOUD_MAX_HEIGHT
        self.density = Config.CLOUD_DENSITY
        self.coverage = Config.CLOUD_COVERAGE
        self.wind_offset = glm.vec3(0.0)
        self.wind_speed = glm.vec3(Config.WIND_VECTOR)

        # Internal lightning flash illumination parameters
        self.internal_light_pos = glm.vec3(0.0, 50.0, 0.0)
        self.internal_light_intensity = 0.0

    def update(self, delta_time, lightning_system=None):
        """Updates wind drift animation and lightning flash illumination state inside clouds."""
        self.wind_offset += self.wind_speed * delta_time * 0.5

        if lightning_system and len(lightning_system.active_bolts) > 0:
            primary_bolt = lightning_system.active_bolts[0]
            self.internal_light_pos = primary_bolt.start_pos
            self.internal_light_intensity = primary_bolt.current_intensity * 2.5
        else:
            self.internal_light_intensity = max(0.0, self.internal_light_intensity - delta_time * 4.0)

    def bind_shader_uniforms(self, shader_program, camera_pos, sun_dir):
        """Passes volumetric cloud raymarching uniforms to GLSL shader."""
        if 'u_CloudMinHeight' in shader_program:
            shader_program['u_CloudMinHeight'].value = self.min_height
        if 'u_CloudMaxHeight' in shader_program:
            shader_program['u_CloudMaxHeight'].value = self.max_height
        if 'u_CloudDensity' in shader_program:
            shader_program['u_CloudDensity'].value = self.density
        if 'u_CloudCoverage' in shader_program:
            shader_program['u_CloudCoverage'].value = self.coverage
        if 'u_WindOffset' in shader_program:
            shader_program['u_WindOffset'].value = tuple(self.wind_offset)
        if 'u_InternalLightPos' in shader_program:
            shader_program['u_InternalLightPos'].value = tuple(self.internal_light_pos)
        if 'u_InternalLightIntensity' in shader_program:
            shader_program['u_InternalLightIntensity'].value = self.internal_light_intensity
