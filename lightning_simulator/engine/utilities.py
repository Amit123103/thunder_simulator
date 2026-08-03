"""
Utilities Module for Lightning Terrain Simulator.
Contains procedural noise algorithms, texture synthesis, matrix helpers, mesh generators, and shader utilities.
"""

import math
import numpy as np
import glm
from PIL import Image

def generate_fbm_noise2d(width, height, scale=1.0, octaves=6, persistence=0.5, lacunarity=2.0, seed=42):
    """
    Vectorized Fractional Brownian Motion (FBM) 2D noise generator using NumPy sinusoids & permutation tables.
    Provides fast, high-detail terrain elevation maps without external C-extension locks.
    """
    np.random.seed(seed)
    grid_x = np.linspace(0, scale * 5.0, width, endpoint=False)
    grid_y = np.linspace(0, scale * 5.0, height, endpoint=False)
    X, Y = np.meshgrid(grid_x, grid_y)

    total_noise = np.zeros((height, width), dtype=np.float32)
    amplitude = 1.0
    frequency = 1.0
    max_value = 0.0

    # Gradient table
    angles = np.random.uniform(0, 2 * np.pi, size=(16, 16))
    gx = np.cos(angles)
    gy = np.sin(angles)

    for o in range(octaves):
        # Domain rotation per octave to eliminate cardinal alignment artifacts
        angle = o * 0.5
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        RX = (X * cos_a - Y * sin_a) * frequency
        RY = (X * sin_a + Y * cos_a) * frequency

        # Sinusoidal turbulence blending with harmonic frequencies
        n = (np.sin(RX) * np.cos(RY) + 
             0.5 * np.sin(RX * 2.1 + 1.2) * np.cos(RY * 1.7 + 0.8) +
             0.25 * np.sin(RX * 4.3 + 2.5) * np.sin(RY * 3.9 + 1.9))
        
        # Ridged mountain enhancement on higher octaves
        if o > 1:
            n = 1.0 - np.abs(n)
            n = n * n

        total_noise += n * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= lacunarity

    # Normalize to [0, 1]
    total_noise = (total_noise - total_noise.min()) / (total_noise.max() - total_noise.min() + 1e-6)
    return total_noise.astype(np.float32)

def domain_warp_2d(heightmap, strength=1.5):
    """
    Applies domain warping (turbulent flow vector field) to heighten organic cliff and ridge features.
    """
    h, w = heightmap.shape
    gy, gx = np.gradient(heightmap)
    
    # Create shifted grid coordinates
    y_coords, x_coords = np.indices((h, w), dtype=np.float32)
    warped_x = np.clip(x_coords + gx * strength * 10.0, 0, w - 1).astype(np.int32)
    warped_y = np.clip(y_coords + gy * strength * 10.0, 0, h - 1).astype(np.int32)

    return heightmap[warped_y, warped_x]

def generate_normal_map(heightmap, strength=3.0):
    """
    Computes Tangent-Space Normal Map (RGB) from a 2D Heightmap array.
    """
    h, w = heightmap.shape
    gy, gx = np.gradient(heightmap)
    
    # Scale gradients by strength factor
    dzdx = -gx * strength
    dzdy = -gy * strength
    dzdz = np.ones_like(heightmap)

    # Normalize vectors
    norm = np.sqrt(dzdx**2 + dzdy**2 + dzdz**2)
    nx = dzdx / norm
    ny = dzdy / norm
    nz = dzdz / norm

    # Map [-1, 1] to [0, 1] for RGB texture conversion
    rgb = np.stack([(nx * 0.5 + 0.5), (ny * 0.5 + 0.5), (nz * 0.5 + 0.5)], axis=-1)
    return (rgb * 255.0).astype(np.uint8)

def generate_ambient_occlusion_map(heightmap, samples=8, radius=3.0):
    """
    Generates screen/terrain space Ambient Occlusion map from elevation curvature.
    """
    h, w = heightmap.shape
    ao = np.ones((h, w), dtype=np.float32)
    
    gy, gx = np.gradient(heightmap)
    laplacian = np.abs(np.gradient(gx)[0] + np.gradient(gy)[1])
    
    ao = 1.0 - np.clip(laplacian * 4.0, 0.0, 0.85)
    return (ao * 255.0).astype(np.uint8)

def create_screen_quad_data():
    """
    Full screen quad VBO data for post-processing passes.
    Pos (2F), UV (2F)
    """
    quad_data = np.array([
        # Position  # UV
        -1.0,  1.0,  0.0, 1.0,
        -1.0, -1.0,  0.0, 0.0,
         1.0, -1.0,  1.0, 0.0,

        -1.0,  1.0,  0.0, 1.0,
         1.0, -1.0,  1.0, 0.0,
         1.0,  1.0,  1.0, 1.0,
    ], dtype=np.float32)
    return quad_data

def create_terrain_mesh_data(heightmap, world_size=120.0, max_height=28.0):
    """
    Generates indexed vertex buffer data for a high-detailed heightmap mesh.
    Vertex layout: Position (3F), Normal (3F), Tangent (3F), UV (2F)
    """
    h, w = heightmap.shape
    dx = world_size / (w - 1)
    dz = world_size / (h - 1)

    # Compute normals and tangents
    gy, gx = np.gradient(heightmap * max_height)
    
    vertices = []
    for r in range(h):
        z = (r / (h - 1) - 0.5) * world_size
        for c in range(w):
            x = (c / (w - 1) - 0.5) * world_size
            y = heightmap[r, c] * max_height

            # Normal vector calculation
            nx = -gx[r, c]
            ny = 1.0
            nz = -gy[r, c]
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            nx, ny, nz = nx/length, ny/length, nz/length

            # Tangent vector calculation (along U axis)
            tx, ty, tz = 1.0, gx[r, c], 0.0
            t_len = math.sqrt(tx*tx + ty*ty + tz*tz)
            tx, ty, tz = tx/t_len, ty/t_len, tz/t_len

            # UV coordinates
            u = c / (w - 1) * 8.0  # Tiling UV
            v = r / (h - 1) * 8.0

            vertices.extend([x, y, z, nx, ny, nz, tx, ty, tz, u, v])

    vertices = np.array(vertices, dtype=np.float32)

    # Index buffer creation (triangle strip or triangle indices)
    indices = []
    for r in range(h - 1):
        for c in range(w - 1):
            top_left = r * w + c
            top_right = top_left + 1
            bottom_left = (r + 1) * w + c
            bottom_right = bottom_left + 1

            indices.extend([top_left, bottom_left, top_right])
            indices.extend([top_right, bottom_left, bottom_right])

    indices = np.array(indices, dtype=np.uint32)
    return vertices, indices

def create_noise_texture_3d(size=32):
    """
    Creates a 3D texture raw byte array containing volumetric noise for cloud raymarching.
    """
    np.random.seed(1337)
    noise_3d = np.random.uniform(0, 255, (size, size, size, 4)).astype(np.uint8)
    return noise_3d.tobytes()

def smoothstep(edge0, edge1, x):
    """Smoothstep interpolation function."""
    x = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)
