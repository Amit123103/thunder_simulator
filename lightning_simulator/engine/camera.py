"""
Camera System Module.
Supports Orbit, Free FPS, Slow Mountain Auto-Orbit, and Automated Cinematic Fly-Through modes, complete with impulse camera shake.
"""

import math
import random
import glm

class Camera:
    MODE_ORBIT = 0
    MODE_FPS = 1
    MODE_CINEMATIC = 2

    def __init__(self, aspect_ratio=16/9, fov=60.0, z_near=0.1, z_far=500.0):
        self.aspect_ratio = aspect_ratio
        self.fov = fov
        self.z_near = z_near
        self.z_far = z_far
        self.mode = Camera.MODE_ORBIT

        # Slow Mountain Auto-Orbit Motion
        self.auto_orbit = True
        self.auto_orbit_speed = 3.5  # Degrees per second slow cinematic rotation

        # Orbit Parameters
        self.target = glm.vec3(0.0, 5.0, 0.0)
        self.distance = 75.0
        self.yaw = -45.0    # Degrees
        self.pitch = 22.0   # Degrees

        # Free / FPS Parameters
        self.position = glm.vec3(0.0, 20.0, 60.0)
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)

        # Smooth Interpolation Targets
        self._target_yaw = self.yaw
        self._target_pitch = self.pitch
        self._target_distance = self.distance
        self._target_pos = glm.vec3(self.position)

        # Camera Shake Parameters
        self.shake_trauma = 0.0       # Range 0.0 to 1.0
        self.shake_decay = 1.8         # Decay rate per second
        self.shake_max_offset = 1.5    # Max translation shake (units)
        self.shake_max_roll = 4.0      # Max rotation shake (degrees)
        self.shake_offset = glm.vec3(0.0)
        self.shake_roll = 0.0

        # Cinematic Path Controls
        self.cinematic_time = 0.0
        self.cinematic_speed = 0.15

        self.update_matrices()

    def update(self, delta_time):
        """Update camera position, slow mountain auto-orbit, smooth lerp interpolation, and camera shake."""
        # Slow Mountain Auto-Orbit Continuous Pan
        if self.auto_orbit and self.mode == Camera.MODE_ORBIT:
            self._target_yaw += delta_time * self.auto_orbit_speed

        # Damped lerp for smooth orbit movement
        lerp_factor = min(1.0, delta_time * 12.0)
        self.yaw += (self._target_yaw - self.yaw) * lerp_factor
        self.pitch += (self._target_pitch - self.pitch) * lerp_factor
        self.distance += (self._target_distance - self.distance) * lerp_factor

        # Process Camera Shake Trauma Decay
        if self.shake_trauma > 0.0:
            shake_amount = self.shake_trauma * self.shake_trauma  # Non-linear quadratic shake response
            self.shake_offset = glm.vec3(
                (random.uniform(-1.0, 1.0)) * self.shake_max_offset * shake_amount,
                (random.uniform(-1.0, 1.0)) * self.shake_max_offset * shake_amount,
                (random.uniform(-1.0, 1.0)) * self.shake_max_offset * shake_amount
            )
            self.shake_roll = (random.uniform(-1.0, 1.0)) * self.shake_max_roll * shake_amount
            self.shake_trauma = max(0.0, self.shake_trauma - self.shake_decay * delta_time)
        else:
            self.shake_offset = glm.vec3(0.0)
            self.shake_roll = 0.0

        # Cinematic Mode Interpolation
        if self.mode == Camera.MODE_CINEMATIC:
            self.cinematic_time += delta_time * self.cinematic_speed
            radius = 65.0 + math.sin(self.cinematic_time * 0.5) * 15.0
            height = 20.0 + math.cos(self.cinematic_time * 0.7) * 10.0
            angle = self.cinematic_time

            cam_x = math.sin(angle) * radius
            cam_z = math.cos(angle) * radius
            self.position = glm.vec3(cam_x, height, cam_z)
            self.target = glm.vec3(0.0, 6.0, 0.0)
        
        elif self.mode == Camera.MODE_ORBIT:
            rad_yaw = math.radians(self.yaw)
            rad_pitch = math.radians(self.pitch)

            cam_x = self.target.x + self.distance * math.cos(rad_pitch) * math.sin(rad_yaw)
            cam_y = self.target.y + self.distance * math.sin(rad_pitch)
            cam_z = self.target.z + self.distance * math.cos(rad_pitch) * math.cos(rad_yaw)
            
            self.position = glm.vec3(cam_x, cam_y, cam_z)

        self.update_matrices()

    def add_trauma(self, amount=0.75):
        """Triggers dynamic camera shake (e.g. upon lightning strike)."""
        self.shake_trauma = min(1.0, self.shake_trauma + amount)

    def process_mouse_orbit(self, dx, dy):
        """Rotates camera around target point."""
        sensitivity = 0.25
        self._target_yaw += dx * sensitivity
        self._target_pitch += dy * sensitivity
        self._target_pitch = max(-89.0, min(89.0, self._target_pitch))

    def process_mouse_zoom(self, dy):
        """Zooms camera in/out."""
        zoom_speed = 4.0
        self._target_distance = max(5.0, min(200.0, self._target_distance - dy * zoom_speed))

    def process_mouse_pan(self, dx, dy):
        """Pans camera target position."""
        pan_speed = 0.05 * (self.distance / 50.0)
        right = self.right
        up = self.up
        self.target -= right * (dx * pan_speed) - up * (dy * pan_speed)

    def set_aspect_ratio(self, aspect_ratio):
        self.aspect_ratio = aspect_ratio
        self.update_matrices()

    def update_matrices(self):
        """Recalculates View and Projection matrices."""
        final_pos = self.position + self.shake_offset
        self.projection_matrix = glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.z_near, self.z_far)

        if self.mode == Camera.MODE_ORBIT or self.mode == Camera.MODE_CINEMATIC:
            view = glm.lookAt(final_pos, self.target, self.up)
        else:
            view = glm.lookAt(final_pos, final_pos + self.front, self.up)

        # Apply roll shake rotation if active
        if self.shake_roll != 0.0:
            view = glm.rotate(view, glm.radians(self.shake_roll), glm.vec3(0, 0, 1))

        self.view_matrix = view
        self.pv_matrix = self.projection_matrix * self.view_matrix

    def reset(self):
        """Reset camera view to initial state."""
        self.target = glm.vec3(0.0, 5.0, 0.0)
        self.distance = 75.0
        self._target_distance = 75.0
        self.yaw = -45.0
        self._target_yaw = -45.0
        self.pitch = 22.0
        self._target_pitch = 22.0
        self.mode = Camera.MODE_ORBIT
        self.auto_orbit = True
        self.shake_trauma = 0.0
