"""
Volumetric Distance & Height Fog Module.
"""

import glm
from .config import Config

class Fog:
    """Manages volumetric exponential height fog parameters and color tints."""

    def __init__(self):
        self.density = Config.FOG_DENSITY
        self.height_falloff = Config.FOG_HEIGHT_FALLOFF
        self.color = Config.FOG_COLOR

    def bind_shader_uniforms(self, shader_program):
        """Passes fog uniforms to GLSL terrain, sky, and particle shaders."""
        if 'u_FogDensity' in shader_program:
            shader_program['u_FogDensity'].value = self.density
        if 'u_FogHeightFalloff' in shader_program:
            shader_program['u_FogHeightFalloff'].value = self.height_falloff
        if 'u_FogColor' in shader_program:
            shader_program['u_FogColor'].value = self.color
