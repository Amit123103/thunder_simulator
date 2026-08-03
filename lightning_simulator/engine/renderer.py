"""
Master Renderer Pipeline Module.
Orchestrates HDR multi-pass rendering, GLSL shader compilation, FBO bindings, Bloom pyramid filter, and asset exporter.
"""

import os
import math
import numpy as np
import glm
import moderngl
from PIL import Image

from .config import Config
from .utilities import create_screen_quad_data
from .bloom import BloomPipeline

class MasterRenderer:
    """Master Render Pipeline using ModernGL OpenGL 4.3 Core profile."""

    def __init__(self, ctx, wnd=None, width=1600, height=900):
        self.ctx = ctx
        self.wnd = wnd
        self.width = width
        self.height = height

        # Enable Depth testing and Alpha Blending
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Load Shaders
        self.load_shaders()
        
        # Build Quad VBO
        self.setup_quad_geometry()

        # Setup FBOs
        self.setup_framebuffers()

        # Initialize Bloom Pipeline
        self.bloom_pipeline = BloomPipeline(ctx, width, height)

    def shader_path(self, filename):
        """Resolves absolute path to shader source file."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'assets', 'shaders', filename)

    def load_shaders(self):
        """Compiles GLSL shader programs."""
        def read_file(path):
            with open(path, 'r') as f:
                return f.read()

        # 1. Terrain Shader
        self.prog_terrain = self.ctx.program(
            vertex_shader=read_file(self.shader_path('terrain.vert')),
            fragment_shader=read_file(self.shader_path('terrain.frag'))
        )

        # 2. Lightning Shader
        self.prog_lightning = self.ctx.program(
            vertex_shader=read_file(self.shader_path('lightning.vert')),
            fragment_shader=read_file(self.shader_path('lightning.frag'))
        )

        # 3. Volumetric Clouds Shader
        self.prog_clouds = self.ctx.program(
            vertex_shader=read_file(self.shader_path('clouds.vert')),
            fragment_shader=read_file(self.shader_path('clouds.frag'))
        )

        # 4. Sky Atmospheric Scattering Shader
        self.prog_sky = self.ctx.program(
            vertex_shader=read_file(self.shader_path('sky.vert')),
            fragment_shader=read_file(self.shader_path('sky.frag'))
        )

        # 5. Instanced Particles Shader
        self.prog_particles = self.ctx.program(
            vertex_shader=read_file(self.shader_path('particles.vert')),
            fragment_shader=read_file(self.shader_path('particles.frag'))
        )

        # 6. Post-Processing HDR Shader
        self.prog_post = self.ctx.program(
            vertex_shader=read_file(self.shader_path('post.vert')),
            fragment_shader=read_file(self.shader_path('post.frag'))
        )

        # 7. Bloom Shader
        self.prog_bloom = self.ctx.program(
            vertex_shader=read_file(self.shader_path('bloom.vert')),
            fragment_shader=read_file(self.shader_path('bloom.frag'))
        )

    def setup_quad_geometry(self):
        """Creates Screen Quad VAO for full-screen pass shaders and pre-allocated dynamic VBOs."""
        quad_data = create_screen_quad_data()
        self.quad_vbo = self.ctx.buffer(quad_data.tobytes())
        
        self.vao_quad_post = self.ctx.vertex_array(self.prog_post, [(self.quad_vbo, '2f 2f', 'a_Position', 'a_TexCoord')])
        self.vao_quad_sky = self.ctx.vertex_array(self.prog_sky, [(self.quad_vbo, '2f 2f', 'a_Position', 'a_TexCoord')])
        self.vao_quad_clouds = self.ctx.vertex_array(self.prog_clouds, [(self.quad_vbo, '2f 2f', 'a_Position', 'a_TexCoord')])
        self.vao_quad_bloom = self.ctx.vertex_array(self.prog_bloom, [(self.quad_vbo, '2f 2f', 'a_Position', 'a_TexCoord')])

        # Pre-allocate dynamic GPU VBOs for 120+ FPS high performance (zero allocation churn)
        max_p_bytes = Config.MAX_PARTICLES * 10 * 4
        self.vbo_particles_dyn = self.ctx.buffer(reserve=max_p_bytes)
        self.vao_particles = self.ctx.vertex_array(
            self.prog_particles,
            [(self.vbo_particles_dyn, '3f 1f 1f 4f 1f/i', 'a_InstancePos', 'a_InstanceSize', 'a_InstanceType', 'a_InstanceColor', 'a_InstanceLifeRatio')]
        )

        max_bolt_bytes = 8000 * 6 * 4
        self.vbo_bolt_dyn = self.ctx.buffer(reserve=max_bolt_bytes)
        self.vao_bolt = self.ctx.vertex_array(
            self.prog_lightning,
            [(self.vbo_bolt_dyn, '3f 1f 2f', 'a_Position', 'a_Level', 'a_TexCoord')]
        )

    def setup_framebuffers(self):
        """Creates HDR floating point (RGBA16F) color attachment buffer and depth stencil attachment."""
        self.tex_hdr_color = self.ctx.texture((self.width, self.height), 4, dtype='f2')
        self.tex_hdr_depth = self.ctx.depth_texture((self.width, self.height))
        self.fbo_hdr = self.ctx.framebuffer(color_attachments=[self.tex_hdr_color], depth_attachment=self.tex_hdr_depth)

    def resize(self, width, height):
        """Resizes viewport FBOs on window resize event."""
        self.width = width
        self.height = height
        self.tex_hdr_color.release()
        self.tex_hdr_depth.release()
        self.fbo_hdr.release()
        self.setup_framebuffers()
        self.bloom_pipeline.resize(width, height)

    def render_frame(self, camera, terrain, lightning_sys, cloud_sys, atmosphere, fog, particles):
        """Executes full cinematic render pipeline passes."""
        pv = camera.pv_matrix
        inv_pv = glm.inverse(pv)

        # --------------------------------------------------------
        # PASS 1: Render 3D Scene into HDR Framebuffer
        # --------------------------------------------------------
        self.fbo_hdr.use()
        self.fbo_hdr.clear(0.02, 0.04, 0.08, 1.0)

        # 1. Sky Dome Atmospheric Scattering Pass
        self.prog_sky['u_InverseViewProj'].write(inv_pv.to_bytes())
        self.prog_sky['u_CamPos'].value = tuple(camera.position)
        atmosphere.bind_shader_uniforms(self.prog_sky)
        self.prog_sky['u_FlashIntensity'].value = lightning_sys.flash_intensity
        self.vao_quad_sky.render()

        # 2. Volumetric Clouds Raymarching Pass
        self.prog_clouds['u_InverseViewProj'].write(inv_pv.to_bytes())
        self.prog_clouds['u_CamPos'].value = tuple(camera.position)
        cloud_sys.bind_shader_uniforms(self.prog_clouds, camera.position, atmosphere.sun_dir)
        self.vao_quad_clouds.render()

        # 3. Terrain PBR Surface Pass
        terrain.tex_normal.use(location=0)
        terrain.tex_ao.use(location=1)
        terrain.tex_heat.use(location=2)
        terrain.tex_scorch.use(location=3)

        self.prog_terrain['u_NormalMap'].value = 0
        self.prog_terrain['u_AOMap'].value = 1
        self.prog_terrain['u_HeatMap'].value = 2
        self.prog_terrain['u_ScorchMap'].value = 3

        self.prog_terrain['u_PV'].write(pv.to_bytes())
        self.prog_terrain['u_Model'].write(glm.mat4(1.0).to_bytes())
        self.prog_terrain['u_CamPos'].value = tuple(camera.position)
        atmosphere.bind_shader_uniforms(self.prog_terrain)
        fog.bind_shader_uniforms(self.prog_terrain)

        # Binds active lightning light sources
        lights = lightning_sys.get_light_sources()
        num_lights = min(8, len(lights))
        if 'u_NumLightningLights' in self.prog_terrain:
            self.prog_terrain['u_NumLightningLights'].value = num_lights
        for idx in range(num_lights):
            pos, intensity = lights[idx]
            p_key = f'u_LightningLightPos[{idx}]'
            i_key = f'u_LightningLightIntensity[{idx}]'
            if p_key in self.prog_terrain:
                self.prog_terrain[p_key].value = tuple(pos)
            if i_key in self.prog_terrain:
                self.prog_terrain[i_key].value = intensity

        # Bind active shockwave uniforms to terrain shader
        active_waves = terrain.physics.active_shockwaves
        num_waves = min(4, len(active_waves))
        if 'u_NumShockwaves' in self.prog_terrain:
            self.prog_terrain['u_NumShockwaves'].value = num_waves
        for idx in range(num_waves):
            wave = active_waves[idx]
            pos_key = f'u_ShockwavePos[{idx}]'
            rad_key = f'u_ShockwaveRadius[{idx}]'
            str_key = f'u_ShockwaveStrength[{idx}]'
            if pos_key in self.prog_terrain:
                self.prog_terrain[pos_key].value = tuple(wave['pos'])
            if rad_key in self.prog_terrain:
                self.prog_terrain[rad_key].value = wave['radius']
            if str_key in self.prog_terrain:
                self.prog_terrain[str_key].value = wave['strength']

        # Render terrain mesh grid
        vao_terrain = self.ctx.vertex_array(
            self.prog_terrain,
            [(terrain.vbo, '3f 3f 3f 2f', 'a_Position', 'a_Normal', 'a_Tangent', 'a_TexCoord')],
            index_buffer=terrain.ibo
        )
        vao_terrain.render(moderngl.TRIANGLES)

        # 4. 3D Lightning Bolts Billboard Mesh Pass
        self.ctx.enable(moderngl.DEPTH_TEST)
        for bolt in lightning_sys.active_bolts:
            mesh_data = bolt.build_mesh_data(camera.position)
            if len(mesh_data) > 0:
                raw_bytes = mesh_data.tobytes()
                self.vbo_bolt_dyn.write(raw_bytes)
                self.prog_lightning['u_PV'].write(pv.to_bytes())
                self.prog_lightning['u_Intensity'].value = bolt.current_intensity
                
                # Render bolt geometry with additive blend
                self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE
                self.vao_bolt.render(moderngl.TRIANGLES, vertices=len(mesh_data) // 6)
                self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # 5. Instanced GPU Particles Pass
        self.ctx.enable(moderngl.DEPTH_TEST)
        particle_bytes = particles.get_render_buffer_data()
        if len(particle_bytes) > 0:
            raw_p_bytes = particle_bytes.tobytes()
            self.vbo_particles_dyn.write(raw_p_bytes)
            self.prog_particles['u_PV'].write(pv.to_bytes())
            self.prog_particles['u_CamPos'].value = tuple(camera.position)
            
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE
            self.vao_particles.render(moderngl.TRIANGLES, vertices=6, instances=len(particle_bytes))
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # --------------------------------------------------------
        # PASS 2: Multi-Pass Pyramid Bloom Extraction & Filter
        # --------------------------------------------------------
        # Extract Threshold
        self.bloom_pipeline.fbo_pass1.use()
        self.tex_hdr_color.use(location=0)
        self.prog_bloom['u_Texture'].value = 0
        self.prog_bloom['u_Pass'].value = 0
        self.prog_bloom['u_Threshold'].value = Config.BLOOM_THRESHOLD
        self.vao_quad_bloom.render()

        # Kawase Blur Pass
        self.bloom_pipeline.fbo_pass2.use()
        self.bloom_pipeline.tex_pass1.use(location=0)
        self.prog_bloom['u_Pass'].value = 1
        self.prog_bloom['u_TexelSize'].value = (1.0 / self.bloom_pipeline.width, 1.0 / self.bloom_pipeline.height)
        self.vao_quad_bloom.render()

        # --------------------------------------------------------
        # PASS 3: Composite Post-Processing to Screen Viewport
        # --------------------------------------------------------
        self.ctx.disable(moderngl.DEPTH_TEST)
        if self.wnd is not None and hasattr(self.wnd, 'use'):
            self.wnd.use()
            self.wnd.clear(0.0, 0.0, 0.0, 1.0)
        elif hasattr(self.ctx, 'fbo') and self.ctx.fbo is not None:
            self.ctx.fbo.use()
            self.ctx.fbo.clear(0.0, 0.0, 0.0, 1.0)
        elif hasattr(self.ctx, 'screen') and self.ctx.screen is not None:
            self.ctx.screen.use()
            self.ctx.screen.clear(0.0, 0.0, 0.0, 1.0)

        self.tex_hdr_color.use(location=0)
        self.bloom_pipeline.tex_pass2.use(location=1)

        self.prog_post['u_SceneTexture'].value = 0
        self.prog_post['u_BloomTexture'].value = 1
        self.prog_post['u_Exposure'].value = Config.EXPOSURE
        self.prog_post['u_BloomIntensity'].value = Config.BLOOM_INTENSITY
        self.prog_post['u_ChromaticAberration'].value = Config.CHROMATIC_ABERRATION
        self.prog_post['u_VignetteStrength'].value = Config.VIGNETTE_STRENGTH

        self.vao_quad_post.render()

    def export_screenshot(self, filepath="screenshot.png"):
        """Captures active screen frame and writes to PNG image file."""
        target_fbo = self.ctx.fbo if (hasattr(self.ctx, 'fbo') and self.ctx.fbo is not None) else self.ctx.screen
        image_bytes = target_fbo.read(components=3)
        image = Image.frombytes('RGB', (self.width, self.height), image_bytes)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(filepath)
        print(f"[Renderer] Screenshot saved to: {filepath}")

    def export_heightmap(self, heightmap, filepath="heightmap.png"):
        """Exports terrain heightmap array to 16-bit PNG image file."""
        norm_h = (heightmap * 65535.0).astype(np.uint16)
        img = Image.fromarray(norm_h)
        img.save(filepath)
        print(f"[Renderer] Heightmap saved to: {filepath}")

    def export_obj_mesh(self, heightmap, filepath="terrain.obj"):
        """Exports 3D terrain mesh to standard Wavefront OBJ file."""
        h, w = heightmap.shape
        world_size = Config.TERRAIN_WORLD_SIZE
        max_height = Config.TERRAIN_MAX_HEIGHT

        with open(filepath, 'w') as f:
            f.write("# Terrain Wavefront OBJ Mesh\n")
            for r in range(h):
                z = (r / (h - 1) - 0.5) * world_size
                for c in range(w):
                    x = (c / (w - 1) - 0.5) * world_size
                    y = heightmap[r, c] * max_height
                    f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")

            for r in range(h - 1):
                for c in range(w - 1):
                    v1 = r * w + c + 1
                    v2 = v1 + 1
                    v3 = (r + 1) * w + c + 1
                    v4 = v3 + 1
                    f.write(f"f {v1} {v3} {v2}\n")
                    f.write(f"f {v2} {v3} {v4}\n")

        print(f"[Renderer] Terrain 3D OBJ mesh exported to: {filepath}")
