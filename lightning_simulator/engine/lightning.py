"""
3D Procedural Lightning Engine with Stepped Leader Propagation & Multi-Bolt Simultaneous Ground Strikes.
"""

import math
import random
import numpy as np
import glm
from .config import Config

class LightningBolt:
    """Represents a single active lightning strike event with stepped leader cloud-to-earth propagation."""

    def __init__(self, start_pos, target_pos, max_subdivisions=5, roughness=0.35, branch_prob=0.30):
        self.start_pos = glm.vec3(start_pos)
        self.target_pos = glm.vec3(target_pos)
        self.max_subdivisions = max_subdivisions
        self.roughness = roughness
        self.branch_prob = branch_prob

        self.age = 0.0
        self.growth_duration = 0.11  # 110ms downward leader travel time from cloud to earth
        self.growth_ratio = 0.0
        self.has_struck_ground = False

        self.lifetime = Config.LIGHTNING_STRIKE_DURATION
        self.intensity = Config.LIGHTNING_GLOW_INTENSITY
        self.flicker_phase = random.uniform(0.0, 100.0)

        # Store generated segments: list of dicts {start, end, width, level}
        self.segments = []
        self.light_sources = []
        
        self.generate_bolt_geometry()

    def generate_bolt_geometry(self):
        """Recursively subdivides bolt path from cloud to earth, spawning secondary branches."""
        self.segments.clear()
        self.light_sources.clear()

        # Build primary main trunk bolt
        trunk_segments = self._subdivide_line(
            self.start_pos, self.target_pos,
            level=0,
            max_level=self.max_subdivisions,
            width=Config.LIGHTNING_BOLT_WIDTH
        )
        self.segments.extend(trunk_segments)

        # Sample light source locations along main bolt trunk
        num_lights = min(8, len(trunk_segments))
        step = max(1, len(trunk_segments) // num_lights)
        for i in range(0, len(trunk_segments), step):
            mid_point = (trunk_segments[i]['start'] + trunk_segments[i]['end']) * 0.5
            self.light_sources.append(mid_point)

    def _subdivide_line(self, p1, p2, level, max_level, width):
        segments = []
        dir_vec = p2 - p1
        length = glm.length(dir_vec)

        if level >= max_level or length < 1.2:
            return [{'start': p1, 'end': p2, 'width': width, 'level': level}]

        mid = (p1 + p2) * 0.5
        
        # Calculate perpendicular displacement offset
        offset_magnitude = length * self.roughness * (0.55 ** level)
        random_dir = glm.normalize(glm.vec3(
            random.uniform(-1.0, 1.0),
            random.uniform(-0.3, 0.3),
            random.uniform(-1.0, 1.0)
        ))
        mid += random_dir * offset_magnitude

        # Left & right subdivisions along main path
        left_segs = self._subdivide_line(p1, mid, level + 1, max_level, width)
        right_segs = self._subdivide_line(mid, p2, level + 1, max_level, width * 0.92)
        segments.extend(left_segs)
        segments.extend(right_segs)

        # Branching logic for micro-arcs
        if level < max_level - 1 and random.random() < self.branch_prob:
            branch_dir = glm.normalize(dir_vec + random_dir * 1.8)
            branch_length = length * random.uniform(0.25, 0.5)
            branch_end = mid + branch_dir * branch_length
            
            branch_segs = self._subdivide_line(
                mid, branch_end,
                level + 1, max_level - 1,
                width * 0.45  # Secondary branches are narrower than main trunk
            )
            segments.extend(branch_segs)

        return segments

    def update(self, delta_time):
        """Updates downward cloud-to-earth growth, bolt lifespan, brightness flicker, and decay curve."""
        self.age += delta_time
        
        # Calculate downward propagation ratio from cloud to ground
        self.growth_ratio = min(1.0, self.age / self.growth_duration)

        # Flag the moment the leader touches the ground mountain surface
        just_struck = False
        if self.growth_ratio >= 1.0 and not self.has_struck_ground:
            self.has_struck_ground = True
            just_struck = True

        progress = self.age / self.lifetime
        
        # Rapid random voltage flicker effect
        flicker = 0.75 + 0.25 * math.sin(self.age * 75.0 + self.flicker_phase)
        
        # Return stroke brightness spike when hitting earth
        return_stroke_multiplier = 2.5 if (self.has_struck_ground and self.age < self.growth_duration + 0.10) else 1.0

        # Exponential fade out
        fade = math.exp(-progress * 4.5)
        self.current_intensity = self.intensity * flicker * fade * return_stroke_multiplier

        return (self.age < self.lifetime, just_struck)

    def build_mesh_data(self, camera_pos):
        """
        Converts 3D line segments into continuous, camera-facing ribbon billboard quads.
        Calculates segment side vectors perpendicular to BOTH line direction AND camera view vector.
        """
        vertex_data = []

        # Calculate current lowest Y coordinate reached by downward traveling leader
        height_delta = self.start_pos.y - self.target_pos.y
        current_reach_y = self.start_pos.y - height_delta * self.growth_ratio

        for seg in self.segments:
            p1 = glm.vec3(seg['start'])
            p2 = glm.vec3(seg['end'])
            w = seg['width'] * 0.5
            lvl = float(seg['level'])

            # Skip segments below current downward reach
            if p1.y < current_reach_y and p2.y < current_reach_y:
                continue

            # Clip segment endpoint if bolt is currently traveling through it
            if p2.y < current_reach_y:
                ratio = (current_reach_y - p1.y) / (p2.y - p1.y + 1e-6)
                p2 = p1 + (p2 - p1) * ratio

            seg_dir = p2 - p1
            length = glm.length(seg_dir)
            if length < 1e-4:
                continue
            
            seg_dir = seg_dir / length

            # Compute camera-facing perpendicular side vector
            mid = (p1 + p2) * 0.5
            view_dir = glm.normalize(camera_pos - mid)
            side_dir = glm.cross(seg_dir, view_dir)
            
            side_len = glm.length(side_dir)
            if side_len > 1e-4:
                side_dir = side_dir / side_len
            else:
                side_dir = glm.vec3(1.0, 0.0, 0.0)

            # Compute 4 quad corners in 3D world space facing the camera
            v0 = p1 - side_dir * w
            v1 = p2 - side_dir * w
            v2 = p2 + side_dir * w
            v3 = p1 + side_dir * w

            # Quad Triangle 1: (v0, v1, v2)
            # Vertex format: Position (3F), Level (1F), UV (2F)
            vertex_data.extend([v0.x, v0.y, v0.z, lvl, 0.0, 0.0])
            vertex_data.extend([v1.x, v1.y, v1.z, lvl, 1.0, 0.0])
            vertex_data.extend([v2.x, v2.y, v2.z, lvl, 1.0, 1.0])

            # Quad Triangle 2: (v0, v2, v3)
            vertex_data.extend([v0.x, v0.y, v0.z, lvl, 0.0, 0.0])
            vertex_data.extend([v2.x, v2.y, v2.z, lvl, 1.0, 1.0])
            vertex_data.extend([v3.x, v3.y, v3.z, lvl, 0.0, 1.0])

        return np.array(vertex_data, dtype=np.float32)


class LightningSystem:
    """Manages active lightning bolts, strike triggers, and automatic storm simulation modes."""

    def __init__(self):
        self.active_bolts = []
        self.mode = Config.STRIKE_MODE_STORM  # Automatic Storm mode on by default!
        self.storm_timer = 0.0
        self.flash_intensity = 0.0  # Overall atmospheric cloud/terrain flash brightness

    def trigger_strike(self, start_pos, target_pos, allow_fork=True):
        """Spawns a new primary lightning strike event originating from clouds."""
        bolt = LightningBolt(start_pos, target_pos)
        self.active_bolts.append(bolt)
        self.flash_intensity = 0.5  # Initial cloud illumination

        # Simultaneous Multi-Strike Fork: 40% probability to spawn second simultaneous bolt
        if allow_fork and random.random() < 0.40:
            offset_x = random.uniform(-18.0, 18.0)
            offset_z = random.uniform(-18.0, 18.0)
            start_pos2 = glm.vec3(start_pos.x + offset_x * 0.4, start_pos.y, start_pos.z + offset_z * 0.4)
            target_pos2 = glm.vec3(target_pos.x + offset_x, target_pos.y, target_pos.z + offset_z)
            
            bolt2 = LightningBolt(start_pos2, target_pos2)
            self.active_bolts.append(bolt2)

        return bolt

    def update(self, delta_time, terrain_height_func, on_ground_impact_cb=None):
        """Updates active bolts, cloud-to-earth propagation, and triggers automatic strikes in storm mode."""
        self.flash_intensity = max(0.0, self.flash_intensity - delta_time * 3.5)

        # Storm Mode Automatic Spawning
        if self.mode == Config.STRIKE_MODE_STORM or self.mode == Config.STRIKE_MODE_CONTINUOUS:
            self.storm_timer += delta_time
            interval = 0.15 if self.mode == Config.STRIKE_MODE_CONTINUOUS else Config.LIGHTNING_STORM_INTERVAL
            
            if self.storm_timer >= interval:
                self.storm_timer = 0.0
                cloud_x = random.uniform(-35.0, 35.0)
                cloud_z = random.uniform(-35.0, 35.0)
                cloud_start = glm.vec3(cloud_x, Config.CLOUD_MIN_HEIGHT + random.uniform(5.0, 15.0), cloud_z)

                target_y = terrain_height_func(cloud_x, cloud_z)
                target_pos = glm.vec3(cloud_x, target_y, cloud_z)

                self.trigger_strike(cloud_start, target_pos)

        # Update active bolts & trigger ground impact callback on strike
        surviving_bolts = []
        for bolt in self.active_bolts:
            is_alive, just_struck = bolt.update(delta_time)
            if just_struck:
                self.flash_intensity = 1.4  # Return stroke flash peak on ground contact
                if on_ground_impact_cb:
                    on_ground_impact_cb(bolt.target_pos)
            if is_alive:
                surviving_bolts.append(bolt)

        self.active_bolts = surviving_bolts

    def get_light_sources(self):
        """Returns point light locations along active lightning bolts reached by downward leader."""
        lights = []
        for bolt in self.active_bolts:
            height_delta = bolt.start_pos.y - bolt.target_pos.y
            current_reach_y = bolt.start_pos.y - height_delta * bolt.growth_ratio
            
            for src in bolt.light_sources:
                if src.y >= current_reach_y:
                    lights.append((src, bolt.current_intensity))
        return lights
