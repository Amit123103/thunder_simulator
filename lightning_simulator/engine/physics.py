"""
Ground Impact Physics & Dynamic Terrain Deformation Module.
Handles crater formation, heat dissipation map, scorch marks, shockwaves, and kinetic particle ejection.
"""

import math
import numpy as np
import glm
from .config import Config

class ImpactPhysics:
    """Manages ground impact physics state, crater deformation, and heat map grid."""

    def __init__(self, grid_size=256, world_size=120.0):
        self.grid_size = grid_size
        self.world_size = world_size
        self.dx = world_size / (grid_size - 1)

        # 2D Grids for real-time terrain thermal & scorch effects
        self.heat_map = np.zeros((grid_size, grid_size), dtype=np.float32)
        self.scorch_map = np.zeros((grid_size, grid_size), dtype=np.float32)
        self.active_shockwaves = []  # List of active expanding shockwaves {pos, radius, strength}

    def process_impact(self, impact_world_pos, heightmap, radius=Config.CRATER_RADIUS_BASE, depth=Config.CRATER_DEPTH_BASE):
        """
        Applies lightning strike impact physics:
        1. Deforms heightmap array creating parabolic crater + outer rim ridge.
        2. Injects extreme thermal energy into heat map (molten glowing ground).
        3. Leaves permanent carbon scorch mark ring.
        4. Spawns outward propagating shockwave event.
        """
        world_x, world_y, world_z = impact_world_pos.x, impact_world_pos.y, impact_world_pos.z

        # Convert world position to grid indices
        col = int((world_x / self.world_size + 0.5) * (self.grid_size - 1))
        row = int((world_z / self.world_size + 0.5) * (self.grid_size - 1))

        radius_grid = int(radius / self.dx)
        r_min = max(0, row - radius_grid * 2)
        r_max = min(self.grid_size, row + radius_grid * 2)
        c_min = max(0, col - radius_grid * 2)
        c_max = min(self.grid_size, col + radius_grid * 2)

        for r in range(r_min, r_max):
            z_pos = (r / (self.grid_size - 1) - 0.5) * self.world_size
            for c in range(c_min, c_max):
                x_pos = (c / (self.grid_size - 1) - 0.5) * self.world_size

                dist = math.sqrt((x_pos - world_x)**2 + (z_pos - world_z)**2)
                if dist < radius * 2.0:
                    norm_dist = dist / radius

                    # Parabolic Crater Excavation Formula + Ejecta Rim Ridge
                    if norm_dist < 1.0:
                        # Crater bowl depression
                        depression = (1.0 - norm_dist**2) * (depth / Config.TERRAIN_MAX_HEIGHT)
                        heightmap[r, c] = max(0.0, heightmap[r, c] - depression)
                    elif norm_dist < 1.5:
                        # Ejecta rim ridge height boost
                        rim_factor = math.sin((norm_dist - 1.0) * math.pi * 2.0) * 0.12 * (depth / Config.TERRAIN_MAX_HEIGHT)
                        heightmap[r, c] = max(0.0, heightmap[r, c] + rim_factor)

                    # Inject Heat & Scorch Marks
                    heat_val = math.exp(-norm_dist * 1.8) * Config.MAX_HEAT
                    self.heat_map[r, c] = min(1.0, self.heat_map[r, c] + heat_val)
                    
                    scorch_val = math.exp(-norm_dist * 1.2) * 0.85
                    self.scorch_map[r, c] = min(1.0, self.scorch_map[r, c] + scorch_val)

        # Trigger Shockwave
        self.active_shockwaves.append({
            'pos': glm.vec3(world_x, world_y, world_z),
            'radius': 0.1,
            'max_radius': radius * 6.0,
            'strength': 1.0
        })

    def update(self, delta_time):
        """Cools heat map over time and expands shockwave rings."""
        # Exponential heat cooling decay
        cooling_rate = delta_time / Config.IMPACT_HEAT_DURATION
        self.heat_map = np.maximum(0.0, self.heat_map - cooling_rate)

        # Update Shockwaves
        updated_waves = []
        for wave in self.active_shockwaves:
            wave['radius'] += Config.SHOCKWAVE_SPEED * delta_time
            wave['strength'] = max(0.0, 1.0 - (wave['radius'] / wave['max_radius']))
            if wave['radius'] < wave['max_radius']:
                updated_waves.append(wave)
        self.active_shockwaves = updated_waves

    def reset(self):
        """Clears thermal heat maps and scorch marks."""
        self.heat_map.fill(0.0)
        self.scorch_map.fill(0.0)
        self.active_shockwaves.clear()
