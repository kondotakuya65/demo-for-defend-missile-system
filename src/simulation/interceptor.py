"""
Interceptor class for defense missiles
"""

import numpy as np
from typing import Optional
from src.simulation.missile import Missile


class Interceptor:
    """Defense interceptor missile"""
    
    def __init__(self, launch_pos: np.ndarray, target_missile: Missile,
                 speed: float, config: dict, algorithm_color: np.ndarray):
        """
        Initialize interceptor
        
        Args:
            launch_pos: Launch position [x, y, z]
            target_missile: Target missile to intercept
            speed: Speed units per second
            config: Configuration dictionary
            algorithm_color: Color based on algorithm (old/new)
        """
        self.config = config
        self.position = np.array(launch_pos, dtype=np.float32)
        self.target_missile = target_missile
        self.speed = speed
        
        # Calculate intercept trajectory
        self.velocity = self._calculate_intercept_velocity()
        
        # State
        self.active = True
        self.destroyed = False
        self.intercepted = False
        
        # Visual properties
        self.length = config['models']['interceptor']['length']
        self.radius = config['models']['interceptor']['radius']
        self.color = algorithm_color
        
        # Trail for visualization
        self.trail: list = []
        self.max_trail_length = config['effects']['trail_particle_count']
        
    def _calculate_intercept_velocity(self) -> np.ndarray:
        """Calculate velocity vector to intercept target missile"""
        if not self.target_missile or not self.target_missile.active:
            # If target is invalid, just move forward
            return np.array([0.0, 0.0, -self.speed], dtype=np.float32)
        
        # Simple intercept calculation: predict where target will be
        # and aim for that point
        target_pos = self.target_missile.position
        target_vel = self.target_missile.velocity
        
        # Vector from interceptor to target
        to_target = target_pos - self.position
        distance = np.linalg.norm(to_target)
        
        if distance < 0.1:
            # Already very close
            return np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        # Simple prediction: assume we can reach target in time T
        # where T = distance / (interceptor_speed - target_speed_component)
        target_speed = np.linalg.norm(target_vel)
        if target_speed > 0:
            # Calculate relative speed
            to_target_norm = to_target / distance
            target_speed_toward = np.dot(target_vel, to_target_norm)
            relative_speed = self.speed - target_speed_toward
            
            if relative_speed > 0.1:
                # Predict intercept point
                time_to_intercept = distance / relative_speed
                predicted_pos = target_pos + target_vel * time_to_intercept
                direction = predicted_pos - self.position
                direction_norm = direction / np.linalg.norm(direction)
                return direction_norm * self.speed
        
        # Fallback: aim directly at current target position
        direction = to_target / distance
        return direction * self.speed
        
    def update(self, delta_time: float):
        """Update interceptor position and check for interception"""
        if not self.active or self.destroyed or self.intercepted:
            return
            
        if not self.target_missile or not self.target_missile.active:
            # Target destroyed or invalid
            self.active = False
            return
        
        # Recalculate intercept trajectory (adaptive)
        self.velocity = self._calculate_intercept_velocity()
        
        # Update position
        self.position += self.velocity * delta_time
        
        # Add to trail
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
        
        # Check for interception
        distance_to_target = np.linalg.norm(
            self.position - self.target_missile.position
        )
        
        success_threshold = self.config['simulation']['success_threshold']
        if distance_to_target < success_threshold:
            # Interception successful!
            self.intercepted = True
            self.interception_position = self.position.copy()  # Store explosion position
            # Mark missile as intercepted before destroying it
            try:
                self.target_missile.intercepted = True
            except AttributeError:
                # In case older missile instances don't have this attribute
                pass
            self.target_missile.destroy()
            self.active = False
            
    def get_direction(self) -> np.ndarray:
        """Get normalized direction vector"""
        if np.linalg.norm(self.velocity) > 0:
            return self.velocity / np.linalg.norm(self.velocity)
        return np.array([0.0, 0.0, -1.0], dtype=np.float32)
        
    def get_model_matrix(self) -> np.ndarray:
        """Get model transformation matrix for rendering"""
        # Similar to Missile class
        model = np.eye(4, dtype=np.float32)
        
        # Translation
        model[0, 3] = self.position[0]
        model[1, 3] = self.position[1]
        model[2, 3] = self.position[2]
        
        # Rotation to face velocity direction
        direction = self.get_direction()
        forward = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        
        dot = np.clip(np.dot(forward, direction), -1.0, 1.0)
        angle = np.arccos(dot)
        
        if angle > 0.001:
            axis = np.cross(forward, direction)
            axis_norm = np.linalg.norm(axis)
            if axis_norm > 0.001:
                axis = axis / axis_norm
                cos_a = np.cos(angle)
                sin_a = np.sin(angle)
                one_minus_cos = 1 - cos_a
                
                rot = np.array([
                    [cos_a + axis[0]*axis[0]*one_minus_cos,
                     axis[0]*axis[1]*one_minus_cos - axis[2]*sin_a,
                     axis[0]*axis[2]*one_minus_cos + axis[1]*sin_a, 0],
                    [axis[1]*axis[0]*one_minus_cos + axis[2]*sin_a,
                     cos_a + axis[1]*axis[1]*one_minus_cos,
                     axis[1]*axis[2]*one_minus_cos - axis[0]*sin_a, 0],
                    [axis[2]*axis[0]*one_minus_cos - axis[1]*sin_a,
                     axis[2]*axis[1]*one_minus_cos + axis[0]*sin_a,
                     cos_a + axis[2]*axis[2]*one_minus_cos, 0],
                    [0, 0, 0, 1]
                ], dtype=np.float32)
                
                model = model @ rot
        
        return model
        
    def destroy(self):
        """Mark interceptor as destroyed"""
        self.destroyed = True
        self.active = False

