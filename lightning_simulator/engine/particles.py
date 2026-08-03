"""
GPU Accelerated Particle System with Vectorized CPU Buffer Extraction.
Manages instanced billboard rendering for Sparks, Smoke Plumes, Rock Debris, and Rain sheets.
"""

import math
import random
import numpy as np
import glm
from .config import Config

class ParticleType:
    SPARK = 0
    SMOKE = 1
    DEBRIS = 2
    RAIN = 3

class ParticleSystem:
    """Manages particle buffers, dynamic spawning on lightning impact, and fast vectorized particle simulation."""

    def __init__(self, max_particles=Config.MAX_PARTICLES):
        self.max_particles = max_particles

        # Particle attribute arrays for fast vectorized NumPy simulation
        # Layout: PosX, PosY, PosZ, VelX, VelY, VelZ, Size, Life, MaxLife, Type, ColorR, ColorG, ColorB, ColorA
        self.particles = np.zeros((max_particles, 14), dtype=np.float32)
        self.active_count = 0

        # Initialize background rain particles
        self.spawn_rain_system(Config.RAIN_PARTICLE_COUNT)

    def spawn_rain_system(self, count):
        """Creates continuous volumetric rain sheets around the camera/scene."""
        for i in range(min(count, self.max_particles)):
            self.particles[i] = [
                random.uniform(-60.0, 60.0), random.uniform(0.0, 80.0), random.uniform(-60.0, 60.0), # Pos
                random.uniform(-1.0, 1.0), random.uniform(-25.0, -40.0), random.uniform(-1.0, 1.0),  # Vel
                0.15, 999.0, 999.0, ParticleType.RAIN,                                               # Size, Life, MaxLife, Type
                0.7, 0.85, 1.0, 0.4                                                                   # Color RGBA
            ]
        self.active_count = count

    def spawn_impact_burst(self, impact_pos):
        """Spawns hundreds of electric sparks, heavy rising smoke, and kinetic rock debris upon lightning ground hit."""
        free_indices = np.where(self.particles[:, 7] <= 0.0)[0]
        if len(free_indices) == 0:
            return

        idx_ptr = 0
        px, py, pz = impact_pos.x, impact_pos.y, impact_pos.z

        # 1. Electric Sparks
        num_sparks = min(Config.SPARK_COUNT_PER_IMPACT, len(free_indices) - idx_ptr)
        for i in range(num_sparks):
            idx = free_indices[idx_ptr]
            idx_ptr += 1
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0.1, math.pi * 0.45)
            speed = random.uniform(15.0, 45.0)

            vx = math.sin(phi) * math.cos(theta) * speed
            vy = math.cos(phi) * speed
            vz = math.sin(phi) * math.sin(theta) * speed
            life = random.uniform(0.4, 1.2)

            self.particles[idx] = [
                px, py + 0.2, pz, vx, vy, vz,
                random.uniform(0.2, 0.5), life, life, ParticleType.SPARK,
                1.0, 0.85, 0.3, 1.0
            ]

        # 2. Smoke Plumes
        num_smoke = min(Config.SMOKE_COUNT_PER_IMPACT, len(free_indices) - idx_ptr)
        for i in range(num_smoke):
            idx = free_indices[idx_ptr]
            idx_ptr += 1
            vx = random.uniform(-3.5, 3.5)
            vy = random.uniform(4.0, 12.0)
            vz = random.uniform(-3.5, 3.5)
            life = random.uniform(2.5, 6.0)

            self.particles[idx] = [
                px + random.uniform(-1.0, 1.0), py, pz + random.uniform(-1.0, 1.0),
                vx, vy, vz,
                random.uniform(1.2, 3.5), life, life, ParticleType.SMOKE,
                0.2, 0.22, 0.25, 0.65
            ]

        # 3. Kinetic Rock Debris
        num_debris = min(Config.DEBRIS_COUNT_PER_IMPACT, len(free_indices) - idx_ptr)
        for i in range(num_debris):
            idx = free_indices[idx_ptr]
            idx_ptr += 1
            vx = random.uniform(-15.0, 15.0)
            vy = random.uniform(10.0, 30.0)
            vz = random.uniform(-15.0, 15.0)
            life = random.uniform(1.5, 3.5)

            self.particles[idx] = [
                px, py + 0.3, pz,
                vx, vy, vz,
                random.uniform(0.3, 0.8), life, life, ParticleType.DEBRIS,
                0.4, 0.35, 0.3, 1.0
            ]

    def update(self, delta_time, gravity=-18.0):
        """Vectorized particle motion, drag physics, gravity, and lifetime updates."""
        mask = self.particles[:, 7] > 0.0
        
        # Position integration
        self.particles[mask, 0:3] += self.particles[mask, 3:6] * delta_time

        # Gravity application (sparks & debris)
        grav_mask = mask & ((self.particles[:, 9] == ParticleType.SPARK) | (self.particles[:, 9] == ParticleType.DEBRIS))
        self.particles[grav_mask, 4] += gravity * delta_time

        # Air drag on smoke & sparks
        drag_mask = mask & ((self.particles[:, 9] == ParticleType.SPARK) | (self.particles[:, 9] == ParticleType.SMOKE))
        self.particles[drag_mask, 3:6] *= (1.0 - delta_time * 1.5)

        # Smoke size expansion over time
        smoke_mask = mask & (self.particles[:, 9] == ParticleType.SMOKE)
        self.particles[smoke_mask, 6] += delta_time * 1.8

        # Lifetime decay
        non_rain_mask = mask & (self.particles[:, 9] != ParticleType.RAIN)
        self.particles[non_rain_mask, 7] -= delta_time

        # Rain loop repositioning (Zero-allocation wrap-around)
        rain_mask = mask & (self.particles[:, 9] == ParticleType.RAIN)
        below_ground = rain_mask & (self.particles[:, 1] < 0.0)
        n_below = np.count_nonzero(below_ground)
        if n_below > 0:
            self.particles[below_ground, 1] += 75.0

        self.active_count = int(np.count_nonzero(self.particles[:, 7] > 0.0))

    def get_render_buffer_data(self):
        """Fast vectorized particle buffer extraction for 120+ FPS GPU instanced rendering."""
        active_mask = self.particles[:, 7] > 0.0
        n_active = np.count_nonzero(active_mask)
        if n_active == 0:
            return np.zeros((0, 10), dtype=np.float32)

        active_data = self.particles[active_mask]
        
        # Format: Pos (3F), Size (1F), Type (1F), Color (4F), LifeRatio (1F)
        buf = np.empty((n_active, 10), dtype=np.float32)
        buf[:, 0:3] = active_data[:, 0:3]                     # Position
        buf[:, 3]   = active_data[:, 6]                       # Size
        buf[:, 4]   = active_data[:, 9]                       # Type
        buf[:, 5:9] = active_data[:, 10:14]                   # Color RGBA
        buf[:, 9]   = active_data[:, 7] / np.maximum(0.01, active_data[:, 8]) # LifeRatio

        return buf
