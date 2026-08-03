"""
Ground Impact Physics & Dynamic Terrain Deformation Module.
Vectorized 2D NumPy execution for sub-millisecond crater formation, thermal heat dissipation, scorch marks, and shockwaves.
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
        Applies lightning strike impact physics using fast 2D vectorized NumPy operations:
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
        r_min, r_max = max(0, row - radius_grid * 2), min(self.grid_size, row + radius_grid * 2)
        c_min, c_max = max(0, col - radius_grid * 2), min(self.grid_size, col + radius_grid * 2)

        if r_max <= r_min or c_max <= c_min:
            return

        # Generate coordinate meshgrid for target slice
        r_coords = (np.arange(r_min, r_max, dtype=np.float32) / (self.grid_size - 1) - 0.5) * self.world_size
        c_coords = (np.arange(c_min, c_max, dtype=np.float32) / (self.grid_size - 1) - 0.5) * self.world_size
        C_grid, R_grid = np.meshgrid(c_coords, r_coords)

        # 2D Euclidean Distance array
        dist = np.sqrt((C_grid - world_x)**2 + (R_grid - world_z)**2)
        norm_dist = dist / radius

        # Parabolic Bowl Excavation Mask
        bowl_mask = norm_dist < 1.0
        depression = np.where(bowl_mask, (1.0 - norm_dist**2) * (depth / Config.TERRAIN_MAX_HEIGHT), 0.0)
        
        # Ejecta Rim Ridge Factor
        rim_mask = (norm_dist >= 1.0) & (norm_dist < 1.5)
        rim_factor = np.where(rim_mask, np.sin((norm_dist - 1.0) * np.pi * 2.0) * 0.12 * (depth / Config.TERRAIN_MAX_HEIGHT), 0.0)

        # Apply heightmap modifications in-place
        sub_hm = heightmap[r_min:r_max, c_min:c_max]
        sub_hm -= depression
        sub_hm += rim_factor
        np.clip(sub_hm, 0.0, 1.0, out=sub_hm)

        # Inject Heat & Scorch Marks
        influence_mask = norm_dist < 2.0
        heat_val = np.where(influence_mask, np.exp(-norm_dist * 1.8) * Config.MAX_HEAT, 0.0)
        scorch_val = np.where(influence_mask, np.exp(-norm_dist * 1.2) * 0.85, 0.0)

        sub_heat = self.heat_map[r_min:r_max, c_min:c_max]
        sub_scorch = self.scorch_map[r_min:r_max, c_min:c_max]

        np.clip(sub_heat + heat_val, 0.0, 1.0, out=sub_heat)
        np.clip(sub_scorch + scorch_val, 0.0, 1.0, out=sub_scorch)

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
