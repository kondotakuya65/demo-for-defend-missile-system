"""
Missile class for incoming threats
"""

import numpy as np
from typing import List, Tuple


class Missile:
    """Incoming missile threat"""
    
    def __init__(self, start_pos: np.ndarray, target_pos: np.ndarray, 
                 speed: float, config: dict, movement_pattern: str = "straight"):
        """
        Initialize missile
        
        Args:
            start_pos: Starting position [x, y, z]
            target_pos: Target position [x, y, z]
            speed: Speed units per second
            config: Configuration dictionary
            movement_pattern: Movement pattern - "straight", "curved", "zigzag", "spiral"
        """
        self.config = config
        self.position = np.array(start_pos, dtype=np.float32)
        self.target = np.array(target_pos, dtype=np.float32)
        self.speed = speed
        self.movement_pattern = movement_pattern
        
        # Calculate initial direction
        direction = self.target - self.position
        distance = np.linalg.norm(direction)
        if distance > 0:
            self.base_velocity = (direction / distance) * self.speed
            self.velocity = self.base_velocity.copy()
        else:
            self.base_velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        # Pattern-specific parameters
        self.pattern_time = 0.0
        if movement_pattern == "zigzag":
            self.zigzag_amplitude = 5.0
            self.zigzag_frequency = 2.0
        elif movement_pattern == "spiral":
            self.spiral_radius = 3.0
            self.spiral_frequency = 1.5
        elif movement_pattern == "curved":
            self.curve_amplitude = 8.0
            self.curve_frequency = 1.0
        
        # State
        self.active = True
        self.destroyed = False
        self.intercepted = False  # Set to True when destroyed by an interceptor
        
        # Phase tracking
        self.phase = "Tracing"  # Tracing, Warning, Destroy
        self.phase_start_time = None  # Will be set when phase changes
        self.detected = False
        
        # Visual properties
        self.length = config['models']['missile']['length']
        self.radius = config['models']['missile']['radius']
        self.color = np.array(config['models']['missile']['color'], dtype=np.float32)
        
        # Trail for visualization
        self.trail: List[np.ndarray] = []
        self.max_trail_length = config['effects']['trail_particle_count']
        
    def update(self, delta_time: float):
        """Update missile position"""
        if not self.active or self.destroyed:
            return
        
        # Update pattern time
        self.pattern_time += delta_time
        
        # Apply movement pattern
        if self.movement_pattern == "straight":
            # Straight line - no change
            self.velocity = self.base_velocity.copy()
        elif self.movement_pattern == "curved":
            # Curved path - sinusoidal deviation
            direction_to_target = self.target - self.position
            distance_to_target = np.linalg.norm(direction_to_target)
            if distance_to_target > 0.1:
                base_dir = direction_to_target / distance_to_target
                # Perpendicular vector for curve
                perp = np.cross(base_dir, np.array([0, 1, 0]))
                if np.linalg.norm(perp) < 0.1:
                    perp = np.cross(base_dir, np.array([1, 0, 0]))
                perp = perp / np.linalg.norm(perp)
                # Add sinusoidal deviation
                curve_offset = np.sin(self.pattern_time * self.curve_frequency) * self.curve_amplitude * perp
                curved_dir = base_dir + curve_offset * 0.1
                curved_dir = curved_dir / np.linalg.norm(curved_dir)
                self.velocity = curved_dir * self.speed
            else:
                self.velocity = self.base_velocity.copy()
        elif self.movement_pattern == "zigzag":
            # Zigzag pattern - alternating side-to-side
            direction_to_target = self.target - self.position
            distance_to_target = np.linalg.norm(direction_to_target)
            if distance_to_target > 0.1:
                base_dir = direction_to_target / distance_to_target
                # Perpendicular vector for zigzag
                perp = np.cross(base_dir, np.array([0, 1, 0]))
                if np.linalg.norm(perp) < 0.1:
                    perp = np.cross(base_dir, np.array([1, 0, 0]))
                perp = perp / np.linalg.norm(perp)
                # Alternating side movement
                zigzag_offset = np.sign(np.sin(self.pattern_time * self.zigzag_frequency)) * self.zigzag_amplitude * perp
                zigzag_dir = base_dir + zigzag_offset * 0.15
                zigzag_dir = zigzag_dir / np.linalg.norm(zigzag_dir)
                self.velocity = zigzag_dir * self.speed
            else:
                self.velocity = self.base_velocity.copy()
        elif self.movement_pattern == "spiral":
            # Spiral pattern - rotating around base direction
            direction_to_target = self.target - self.position
            distance_to_target = np.linalg.norm(direction_to_target)
            if distance_to_target > 0.1:
                base_dir = direction_to_target / distance_to_target
                # Perpendicular vectors for spiral
                perp1 = np.cross(base_dir, np.array([0, 1, 0]))
                if np.linalg.norm(perp1) < 0.1:
                    perp1 = np.cross(base_dir, np.array([1, 0, 0]))
                perp1 = perp1 / np.linalg.norm(perp1)
                perp2 = np.cross(base_dir, perp1)
                perp2 = perp2 / np.linalg.norm(perp2)
                # Spiral rotation
                angle = self.pattern_time * self.spiral_frequency
                spiral_offset = (np.cos(angle) * perp1 + np.sin(angle) * perp2) * self.spiral_radius
                spiral_dir = base_dir + spiral_offset * 0.1
                spiral_dir = spiral_dir / np.linalg.norm(spiral_dir)
                self.velocity = spiral_dir * self.speed
            else:
                self.velocity = self.base_velocity.copy()
        else:
            self.velocity = self.base_velocity.copy()
            
        # Update position
        self.position += self.velocity * delta_time
        
        # Add to trail
        self.trail.append(self.position.copy())
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)
        
        # Check if reached target or out of bounds
        distance_to_target = np.linalg.norm(self.position - self.target)
        if distance_to_target < 1.0:  # Close enough to target
            self.active = False
            self.destroyed = True
            
        # Check bounds (simple check - can be improved)
        if np.linalg.norm(self.position) > 1000.0:
            self.active = False
            
    def get_direction(self) -> np.ndarray:
        """Get normalized direction vector"""
        if np.linalg.norm(self.velocity) > 0:
            return self.velocity / np.linalg.norm(self.velocity)
        return np.array([0.0, 0.0, -1.0], dtype=np.float32)
        
    def get_model_matrix(self) -> np.ndarray:
        """Get model transformation matrix for rendering"""
        # Create model matrix with rotation to face velocity direction
        model = np.eye(4, dtype=np.float32)
        
        # Translation
        model[0, 3] = self.position[0]
        model[1, 3] = self.position[1]
        model[2, 3] = self.position[2]
        
        # Rotation to face velocity direction
        direction = self.get_direction()
        
        # Calculate rotation matrix to align with direction
        # Default forward is -Z, so we need to rotate to match direction
        forward = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        
        # Calculate rotation axis and angle
        dot = np.clip(np.dot(forward, direction), -1.0, 1.0)
        angle = np.arccos(dot)
        
        if angle > 0.001:  # Avoid division by zero
            axis = np.cross(forward, direction)
            axis_norm = np.linalg.norm(axis)
            if axis_norm > 0.001:
                axis = axis / axis_norm
                # Create rotation matrix using Rodrigues' formula
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
                
                # Apply rotation to model matrix
                model = model @ rot
        
        return model
        
    def destroy(self):
        """Mark missile as destroyed"""
        self.destroyed = True
        self.active = False

