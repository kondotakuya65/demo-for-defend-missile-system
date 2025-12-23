"""
3D Camera system for OpenGL rendering
"""

import numpy as np
from math import sin, cos, radians


class Camera:
    """3D camera with orbital rotation"""
    
    def __init__(self, config):
        self.config = config
        
        # Camera position (spherical coordinates)
        self.distance = config['camera']['initial_distance']
        self.elevation = radians(config['camera']['initial_elevation'])  # Vertical angle
        self.azimuth = radians(config['camera']['initial_azimuth'])  # Horizontal angle
        
        # Target point (center of scene)
        self.target = np.array([0.0, 0.0, 0.0])
        
        # Camera limits
        self.min_distance = config['camera']['min_distance']
        self.max_distance = config['camera']['max_distance']
        
        # Movement speeds
        self.rotation_speed = config['camera']['rotation_speed']
        self.zoom_speed = config['camera']['zoom_speed']
        
        # View matrix cache
        self._view_matrix = None
        self._needs_update = True
        
    def get_position(self):
        """Calculate camera position from spherical coordinates"""
        x = self.distance * cos(self.elevation) * sin(self.azimuth)
        y = self.distance * sin(self.elevation)
        z = self.distance * cos(self.elevation) * cos(self.azimuth)
        return np.array([x, y, z]) + self.target
        
    def get_view_matrix(self):
        """Get view matrix (look-at matrix)"""
        if self._needs_update or self._view_matrix is None:
            eye = self.get_position()
            up = np.array([0.0, 1.0, 0.0])  # World up vector
            
            # Calculate forward vector (from eye to target)
            forward = self.target - eye
            forward = forward / np.linalg.norm(forward)
            
            # Calculate right vector
            right = np.cross(forward, up)
            right = right / np.linalg.norm(right)
            
            # Recalculate up vector
            up = np.cross(right, forward)
            
            # Build view matrix (look-at)
            view = np.eye(4, dtype=np.float32)
            view[0, :3] = right
            view[1, :3] = up
            view[2, :3] = -forward
            view[0, 3] = -np.dot(right, eye)
            view[1, 3] = -np.dot(up, eye)
            view[2, 3] = np.dot(forward, eye)
            
            self._view_matrix = view
            self._needs_update = False
            
        return self._view_matrix
        
    def rotate(self, delta_azimuth, delta_elevation):
        """Rotate camera around target"""
        self.azimuth += delta_azimuth * self.rotation_speed
        self.elevation += delta_elevation * self.rotation_speed
        
        # Clamp elevation to prevent flipping
        self.elevation = max(radians(-89), min(radians(89), self.elevation))
        
        self._needs_update = True
        
    def zoom(self, delta):
        """Zoom camera in/out"""
        self.distance += delta * self.zoom_speed
        self.distance = max(self.min_distance, min(self.max_distance, self.distance))
        self._needs_update = True
        
    def reset(self):
        """Reset camera to initial position"""
        self.distance = self.config['camera']['initial_distance']
        self.elevation = radians(self.config['camera']['initial_elevation'])
        self.azimuth = radians(self.config['camera']['initial_azimuth'])
        self._needs_update = True

