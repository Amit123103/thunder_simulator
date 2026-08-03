"""
3D Mountain Waterfall Engine.
Generates 3D cascading cliff stream geometry, mountain river basin mesh, animated foam shaders, and waterfall mist spray particles.
"""

import math
import random
import numpy as np
import glm
import moderngl
from .config import Config

class Waterfall:
    """Manages mountain waterfall cascading mesh, valley river pool, and mist spray particles."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.time = 0.0

        # Build 3D mesh data for waterfall cliff cascade and river basin pool
        self.build_waterfall_mesh()

    def build_waterfall_mesh(self):
        """Constructs indexed vertex buffer data for cascading cliff stream and river pool."""
        vertices = []
        indices = []

        # ----------------------------------------------------
        # 1. Cascading Cliff Waterfall Stream Mesh (Top to Bottom)
        # ----------------------------------------------------
        steps = 30
        width = 5.0
        start_x, start_y, start_z = -15.0, 24.0, -10.0
        end_x, end_y, end_z     = -15.0, 3.0, 10.0

        for i in range(steps + 1):
            t = i / steps
            
            # Curved parabolic cliff cascade path
            curr_x = start_x + (end_x - start_x) * t
            curr_y = start_y + (end_y - start_y) * (t**1.4)
            curr_z = start_z + (end_z - start_z) * t

            # Tangent & Normal vectors for cliff slope
            next_t = min(1.0, t + 0.05)
            next_y = start_y + (end_y - start_y) * (next_t**1.4)
            next_z = start_z + (end_z - start_z) * next_t
            
            slope_dir = glm.normalize(glm.vec3(0.0, next_y - curr_y, next_z - curr_z))
            side_dir  = glm.vec3(1.0, 0.0, 0.0)
            normal    = glm.normalize(glm.cross(side_dir, slope_dir))

            # Left & Right vertex positions
            p_left  = glm.vec3(curr_x - width * 0.5, curr_y, curr_z)
            p_right = glm.vec3(curr_x + width * 0.5, curr_y, curr_z)

            u = 0.0
            v = t * 6.0  # UV tiling for scrolling water texture

            vertices.extend([p_left.x, p_left.y, p_left.z, normal.x, normal.y, normal.z, 0.0, v])
            vertices.extend([p_right.x, p_right.y, p_right.z, normal.x, normal.y, normal.z, 1.0, v])

        for i in range(steps):
            v0 = i * 2
            v1 = v0 + 1
            v2 = (i + 1) * 2
            v3 = v2 + 1
            indices.extend([v0, v2, v1])
            indices.extend([v1, v2, v3])

        # ----------------------------------------------------
        # 2. Valley River Pool / Basin Lake (Flat water surface at base)
        # ----------------------------------------------------
        base_vertex_start = (steps + 1) * 2
        pool_r = 18.0
        pool_center_x, pool_center_y, pool_center_z = -15.0, 3.0, 15.0

        grid = 16
        for r in range(grid + 1):
            pz = pool_center_z + (r / grid - 0.5) * pool_r
            for c in range(grid + 1):
                px = pool_center_x + (c / grid - 0.5) * pool_r
                py = pool_center_y

                u = c / grid * 3.0
                v = r / grid * 3.0
                vertices.extend([px, py, pz, 0.0, 1.0, 0.0, u, v])

        for r in range(grid):
            for c in range(grid):
                v0 = base_vertex_start + r * (grid + 1) + c
                v1 = v0 + 1
                v2 = base_vertex_start + (r + 1) * (grid + 1) + c
                v3 = v2 + 1
                indices.extend([v0, v2, v1])
                indices.extend([v1, v2, v3])

        # Create ModernGL GPU Buffers
        self.vertices_data = np.array(vertices, dtype=np.float32)
        self.indices_data = np.array(indices, dtype=np.uint32)

        self.vbo = self.ctx.buffer(self.vertices_data.tobytes())
        self.ibo = self.ctx.buffer(self.indices_data.tobytes())
        self.num_indices = len(indices)

    def update(self, delta_time, particles=None):
        """Updates water animation time and emits waterfall mist spray particles at base pool."""
        self.time += delta_time

        # Emit waterfall plunge mist particles at waterfall base
        if particles and random.random() < 0.65:
            base_pos = glm.vec3(-15.0 + random.uniform(-2.5, 2.5), 3.2, 10.0 + random.uniform(-1.0, 2.0))
            
            # Spawn soft mist smoke particles rising from plunge pool
            free_indices = np.where(particles.particles[:, 7] <= 0.0)[0]
            if len(free_indices) > 0:
                idx = free_indices[0]
                particles.particles[idx] = [
                    base_pos.x, base_pos.y, base_pos.z,
                    random.uniform(-1.5, 1.5), random.uniform(2.0, 5.0), random.uniform(-1.5, 1.5), # Velocity
                    random.uniform(1.0, 2.8), 2.5, 2.5, 1.0,                                       # Size, Life, MaxLife, Type (SMOKE)
                    0.8, 0.9, 1.0, 0.35                                                            # Color RGBA (Mist white-blue)
                ]

    def render(self, prog_water, camera, atmosphere, fog, lightning_sys):
        """Renders 3D waterfall stream and river basin with animated foam and lightning reflections."""
        pv = camera.pv_matrix

        prog_water['u_PV'].write(pv.to_bytes())
        prog_water['u_Model'].write(glm.mat4(1.0).to_bytes())
        prog_water['u_CamPos'].value = tuple(camera.position)
        prog_water['u_Time'].value = self.time
        atmosphere.bind_shader_uniforms(prog_water)
        fog.bind_shader_uniforms(prog_water)

        # Binds active lightning light sources for water reflections
        lights = lightning_sys.get_light_sources()
        num_lights = min(8, len(lights))
        if 'u_NumLightningLights' in prog_water:
            prog_water['u_NumLightningLights'].value = num_lights
        for idx in range(num_lights):
            pos, intensity = lights[idx]
            p_key = f'u_LightningLightPos[{idx}]'
            i_key = f'u_LightningLightIntensity[{idx}]'
            if p_key in prog_water:
                prog_water[p_key].value = tuple(pos)
            if i_key in prog_water:
                prog_water[i_key].value = intensity

        vao_water = self.ctx.vertex_array(
            prog_water,
            [(self.vbo, '3f 3f 2f', 'a_Position', 'a_Normal', 'a_TexCoord')],
            index_buffer=self.ibo
        )

        # Render with alpha blending enabled
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        vao_water.render(moderngl.TRIANGLES)
