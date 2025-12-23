"""
3D model generation for missiles, interceptors, and defense systems
"""

import numpy as np
from OpenGL.GL import (
    glGenVertexArrays, glGenBuffers, glBindVertexArray, glBindBuffer,
    GL_ARRAY_BUFFER, glBufferData, GL_STATIC_DRAW,
    glEnableVertexAttribArray, glVertexAttribPointer, GL_FLOAT,
    glDrawArrays, GL_TRIANGLES
)


class Model3D:
    """3D model with VAO/VBO"""
    
    def __init__(self, vertices: np.ndarray, normals: np.ndarray):
        """
        Initialize 3D model
        
        Args:
            vertices: Vertex positions (N, 3)
            normals: Vertex normals (N, 3)
        """
        self.vertex_count = len(vertices)
        
        # Combine vertices and normals
        data = np.zeros((self.vertex_count, 6), dtype=np.float32)
        data[:, :3] = vertices
        data[:, 3:6] = normals
        
        # Create VAO and VBO
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        
        # Position attribute (location 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, None)
        
        # Normal attribute (location 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, np.array([3 * 4], dtype=np.uintp))
        
        glBindVertexArray(0)
        
    def render(self):
        """Render the model"""
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        glBindVertexArray(0)


def create_missile_model(length: float, radius: float) -> Model3D:
    """Create 3D missile model (cylinder + cone)"""
    segments = 16
    vertices = []
    normals = []
    
    # Cylinder body
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments
        
        x1 = radius * np.cos(angle1)
        z1 = radius * np.sin(angle1)
        x2 = radius * np.cos(angle2)
        z2 = radius * np.sin(angle2)
        
        # Two triangles per segment
        # Triangle 1
        vertices.extend([
            [x1, -length/2, z1],
            [x2, -length/2, z2],
            [x1, length/2, z1]
        ])
        norm = np.array([x1, 0, z1])
        norm = norm / np.linalg.norm(norm)
        normals.extend([norm, norm, norm])
        
        # Triangle 2
        vertices.extend([
            [x1, length/2, z1],
            [x2, -length/2, z2],
            [x2, length/2, z2]
        ])
        norm = np.array([x2, 0, z2])
        norm = norm / np.linalg.norm(norm)
        normals.extend([norm, norm, norm])
    
    # Cone tip
    tip_y = length / 2
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments
        
        x1 = radius * np.cos(angle1)
        z1 = radius * np.sin(angle1)
        x2 = radius * np.cos(angle2)
        z2 = radius * np.sin(angle2)
        
        # Triangle from base to tip
        vertices.extend([
            [x1, tip_y, z1],
            [x2, tip_y, z2],
            [0, tip_y + length * 0.3, 0]  # Tip point
        ])
        
        # Calculate normal for cone face
        v1 = np.array([x1, tip_y, z1]) - np.array([0, tip_y + length * 0.3, 0])
        v2 = np.array([x2, tip_y, z2]) - np.array([0, tip_y + length * 0.3, 0])
        norm = np.cross(v1, v2)
        norm = norm / np.linalg.norm(norm)
        normals.extend([norm, norm, norm])
    
    vertices = np.array(vertices, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    
    return Model3D(vertices, normals)


def create_interceptor_model(length: float, radius: float) -> Model3D:
    """Create 3D interceptor model (smaller missile)"""
    # Similar to missile but smaller
    return create_missile_model(length, radius)


def create_defense_system_model(base_radius: float, base_height: float,
                                dish_radius: float, dish_height: float) -> Model3D:
    """Create 3D defense system model (cylinder base + radar dish)"""
    segments = 16
    vertices = []
    normals = []
    
    # Cylindrical base
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments
        
        x1 = base_radius * np.cos(angle1)
        z1 = base_radius * np.sin(angle1)
        x2 = base_radius * np.cos(angle2)
        z2 = base_radius * np.sin(angle2)
        
        # Two triangles per segment
        vertices.extend([
            [x1, 0, z1],
            [x2, 0, z2],
            [x1, base_height, z1]
        ])
        norm = np.array([x1, 0, z1])
        norm = norm / np.linalg.norm(norm)
        normals.extend([norm, norm, norm])
        
        vertices.extend([
            [x1, base_height, z1],
            [x2, 0, z2],
            [x2, base_height, z2]
        ])
        norm = np.array([x2, 0, z2])
        norm = norm / np.linalg.norm(norm)
        normals.extend([norm, norm, norm])
    
    # Radar dish (cone shape)
    dish_y = base_height
    for i in range(segments):
        angle1 = 2 * np.pi * i / segments
        angle2 = 2 * np.pi * (i + 1) / segments
        
        x1 = dish_radius * np.cos(angle1)
        z1 = dish_radius * np.sin(angle1)
        x2 = dish_radius * np.cos(angle2)
        z2 = dish_radius * np.sin(angle2)
        
        # Triangle from base to top
        vertices.extend([
            [x1, dish_y, z1],
            [x2, dish_y, z2],
            [0, dish_y + dish_height, 0]
        ])
        
        v1 = np.array([x1, dish_y, z1]) - np.array([0, dish_y + dish_height, 0])
        v2 = np.array([x2, dish_y, z2]) - np.array([0, dish_y + dish_height, 0])
        norm = np.cross(v1, v2)
        norm = norm / np.linalg.norm(norm)
        normals.extend([norm, norm, norm])
    
    vertices = np.array(vertices, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32)
    
    return Model3D(vertices, normals)

