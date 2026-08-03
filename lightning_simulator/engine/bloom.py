"""
Multi-Pass Gaussian & Kawase Pyramid Bloom Manager.
Applies downsample extraction and upsample blending for high-quality emissive lightning glow halos.
"""

from .config import Config

class BloomPipeline:
    """Manages threshold extraction and multi-pass downscaling/upscaling for bloom post-processing."""

    def __init__(self, ctx, width, height):
        self.ctx = ctx
        self.width = width
        self.height = height
        
        self.threshold = Config.BLOOM_THRESHOLD
        self.intensity = Config.BLOOM_INTENSITY
        self.radius = Config.BLOOM_RADIUS

        self.setup_framebuffers()

    def setup_framebuffers(self):
        """Creates half-resolution and quarter-resolution FBOs for pyramid blur."""
        w1, h1 = max(1, self.width // 2), max(1, self.height // 2)
        w2, h2 = max(1, self.width // 4), max(1, self.height // 4)

        self.tex_pass1 = self.ctx.texture((w1, h1), 4, dtype='f2')
        self.fbo_pass1 = self.ctx.framebuffer(color_attachments=[self.tex_pass1])

        self.tex_pass2 = self.ctx.texture((w2, h2), 4, dtype='f2')
        self.fbo_pass2 = self.ctx.framebuffer(color_attachments=[self.tex_pass2])

    def resize(self, width, height):
        """Reallocates bloom FBOs upon window resize."""
        self.width = width
        self.height = height
        self.tex_pass1.release()
        self.fbo_pass1.release()
        self.tex_pass2.release()
        self.fbo_pass2.release()
        self.setup_framebuffers()
