"""
Procedural Terrain Engine.
Handles heightmap generation, dynamic mesh updating, normal calculation, terrain picking raycasts, and ground PBR shaders.
"""

import math
import numpy as np
import glm
import moderngl
from .config import Config
from .utilities import (
    generate_fbm_noise2d,
    domain_warp_2d,
    generate_normal_map,
    generate_ambient_occlusion_map,
    create_terrain_mesh_data
)
from .physics import ImpactPhysics

class Terrain:
    """Procedural Terrain engine with dynamic crater deformation, heat glow textures, and GPU buffers."""

    def __init__(self, ctx, grid_size=Config.TERRAIN_GRID_SIZE, world_size=Config.TERRAIN_WORLD_SIZE):
        self.ctx = ctx
        self.grid_size = grid_size
        self.world_size = world_size
        self.max_height = Config.TERRAIN_MAX_HEIGHT

        self.physics = ImpactPhysics(grid_size, world_size)

        # Generate base procedural heightmap array
        self.generate_procedural_heightmap()
        
        # Build initial vertex mesh and GPU buffers
        self.build_mesh_gpu_buffers()
        
        # Create GPU Textures
        self.update_gpu_textures()

    def generate_procedural_heightmap(self):
        """Synthesizes high-detail terrain elevation array using FBM and Domain Warping."""
        base_noise = generate_fbm_noise2d(
            self.grid_size, self.grid_size,
            scale=1.2,
            octaves=Config.OCTAVES,
            persistence=Config.PERSISTENCE,
            lacunarity=Config.LACUNARITY,
            seed=123
        )
        warped_noise = domain_warp_2d(base_noise, strength=1.4)
        
        # Apply valley leveling formula for contrast
        self.heightmap = np.power(warped_noise, 1.3).astype(np.float32)

    def build_mesh_gpu_buffers(self):
        """Constructs vertex array object and index buffer for modernGL rendering."""
        vertices, indices = create_terrain_mesh_data(self.heightmap, self.world_size, self.max_height)
        self.num_indices = len(indices)

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo = self.ctx.buffer(indices.tobytes())

    def update_gpu_textures(self):
        """Computes normal maps, AO maps, heat maps, and uploads to ModernGL textures."""
        normal_rgb = generate_normal_map(self.heightmap, strength=4.5)
        ao_gray = generate_ambient_occlusion_map(self.heightmap)

        # Create/Update ModernGL Textures
        if not hasattr(self, 'tex_normal'):
            self.tex_normal = self.ctx.texture((self.grid_size, self.grid_size), 3, normal_rgb.tobytes())
            self.tex_ao = self.ctx.texture((self.grid_size, self.grid_size), 1, ao_gray.tobytes())
            
            # Heat Map Texture (R32F float format for continuous temperature values)
            self.tex_heat = self.ctx.texture((self.grid_size, self.grid_size), 1, self.physics.heat_map.tobytes(), dtype='f4')
            self.tex_scorch = self.ctx.texture((self.grid_size, self.grid_size), 1, self.physics.scorch_map.tobytes(), dtype='f4')
        else:
            self.tex_normal.write(normal_rgb.tobytes())
            self.tex_ao.write(ao_gray.tobytes())
            self.tex_heat.write(self.physics.heat_map.tobytes())
            self.tex_scorch.write(self.physics.scorch_map.tobytes())

    def apply_lightning_impact(self, impact_world_pos):
        """Triggers ground crater excavation, heat injection, and updates GPU mesh & textures."""
        self.physics.process_impact(impact_world_pos, self.heightmap)

        # Re-upload updated vertex positions & normals to GPU buffer
        vertices, _ = create_terrain_mesh_data(self.heightmap, self.world_size, self.max_height)
        self.vbo.write(vertices.tobytes())

        # Refresh normal, heat, and scorch textures
        self.update_gpu_textures()

    def update(self, delta_time):
        """Updates physics heat cooling lifecycle and refreshes heat map GPU texture."""
        self.physics.update(delta_time)
        self.tex_heat.write(self.physics.heat_map.tobytes())

    def get_height_at(self, world_x, world_z):
        """Calculates interpolated terrain height Y at any (world_x, world_z) position."""
        half_size = self.world_size * 0.5
        norm_x = (world_x + half_size) / self.world_size
        norm_z = (world_z + half_size) / self.world_size

        col = max(0, min(self.grid_size - 2, int(norm_x * (self.grid_size - 1))))
        row = max(0, min(self.grid_size - 2, int(norm_z * (self.grid_size - 1))))

        # Bilinear interpolation
        h00 = self.heightmap[row, col]
        h10 = self.heightmap[row, col + 1]
        h01 = self.heightmap[row + 1, col]
        h11 = self.heightmap[row + 1, col + 1]

        fx = (norm_x * (self.grid_size - 1)) - col
        fz = (norm_z * (self.grid_size - 1)) - row

        interpolated_h = (h00 * (1 - fx) * (1 - fz) +
                          h10 * fx * (1 - fz) +
                          h01 * (1 - fx) * fz +
                          h11 * fx * fz)
        
        return interpolated_h * self.max_height

    def raycast_ground_intersection(self, ray_origin, ray_dir):
        """
        Raycasts screen ray against terrain surface to pick exact ground strike point.
        """
        step_size = 0.5
        max_dist = 250.0
        curr_dist = 0.0

        while curr_dist < max_dist:
            pos = ray_origin + ray_dir * curr_dist
            terrain_y = self.get_height_at(pos.x, pos.z)
            
            if pos.y <= terrain_y:
                return glm.vec3(pos.x, terrain_y, pos.z)

            curr_dist += step_size

        return glm.vec3(0.0, self.get_height_at(0.0, 0.0), 0.0)

    def reset_terrain(self):
        """Resets heightmap to original un-damaged state and clears heat/scorch."""
        self.physics.reset()
        self.generate_procedural_heightmap()
        
        vertices, _ = create_terrain_mesh_data(self.heightmap, self.world_size, self.max_height)
        self.vbo.write(vertices.tobytes())
        self.update_gpu_textures()
