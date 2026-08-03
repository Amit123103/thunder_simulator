"""
Atmosphere & Sky Dome System.
Physically-based Rayleigh & Mie atmospheric scattering sky model with dynamic sun elevation & twilight storm rendering.
"""

import math
import glm
from .config import Config

class Atmosphere:
    """Manages sky dome light scattering vectors, Sun/Moon illumination, and atmospheric coefficients."""

    def __init__(self):
        self.sun_azimuth = Config.SUN_AZIMUTH
        self.sun_elevation = Config.SUN_ELEVATION
        self.rayleigh = Config.RAYLEIGH_COEFF
        self.mie = Config.MIE_COEFF
        self.mie_g = Config.MIE_G
        
        self.update_sun_vector()

    def update_sun_vector(self):
        """Calculates 3D Sun direction unit vector from azimuth & elevation angles."""
        az_rad = math.radians(self.sun_azimuth)
        el_rad = math.radians(self.sun_elevation)

        y = math.sin(el_rad)
        x = math.cos(el_rad) * math.sin(az_rad)
        z = math.cos(el_rad) * math.cos(az_rad)

        self.sun_dir = glm.normalize(glm.vec3(x, y, z))

    def set_time_preset(self, mode='storm'):
        """Applies environment presets: 'night', 'day', 'storm'."""
        if mode == 'night':
            self.sun_elevation = -15.0
            self.sun_azimuth = 210.0
        elif mode == 'day':
            self.sun_elevation = 55.0
            self.sun_azimuth = 135.0
        elif mode == 'storm':
            self.sun_elevation = 12.0
            self.sun_azimuth = 45.0
        self.update_sun_vector()

    def bind_shader_uniforms(self, shader_program):
        """Binds sun direction and scattering parameters to GLSL shaders."""
        if 'u_SunDir' in shader_program:
            shader_program['u_SunDir'].value = tuple(self.sun_dir)
        if 'u_Rayleigh' in shader_program:
            shader_program['u_Rayleigh'].value = self.rayleigh
        if 'u_Mie' in shader_program:
            shader_program['u_Mie'].value = self.mie
        if 'u_MieG' in shader_program:
            shader_program['u_MieG'].value = self.mie_g
