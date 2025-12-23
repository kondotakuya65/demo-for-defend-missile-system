"""
Simple test objects for debugging rendering
"""

import numpy as np
from OpenGL.GL import (
    glGenVertexArrays, glGenBuffers, glBindVertexArray, glBindBuffer,
    GL_ARRAY_BUFFER, glBufferData, GL_STATIC_DRAW,
    glEnableVertexAttribArray, glVertexAttribPointer, GL_FLOAT,
    glDrawArrays, GL_TRIANGLES
)


def create_test_cube(size=2.0):
    """Create a simple cube for testing"""
    # 8 vertices of a cube
    s = size / 2.0
    vertices = np.array([
        # Front face
        [-s, -s,  s], [ s, -s,  s], [ s,  s,  s],  # Triangle 1
        [-s, -s,  s], [ s,  s,  s], [-s,  s,  s],  # Triangle 2
        # Back face
        [-s, -s, -s], [ s,  s, -s], [ s, -s, -s],  # Triangle 1
        [-s, -s, -s], [-s,  s, -s], [ s,  s, -s],  # Triangle 2
        # Top face
        [-s,  s, -s], [-s,  s,  s], [ s,  s,  s],  # Triangle 1
        [-s,  s, -s], [ s,  s,  s], [ s,  s, -s],  # Triangle 2
        # Bottom face
        [-s, -s, -s], [ s, -s,  s], [-s, -s,  s],  # Triangle 1
        [-s, -s, -s], [ s, -s, -s], [ s, -s,  s],  # Triangle 2
        # Right face
        [ s, -s, -s], [ s,  s,  s], [ s, -s,  s],  # Triangle 1
        [ s, -s, -s], [ s,  s, -s], [ s,  s,  s],  # Triangle 2
        # Left face
        [-s, -s, -s], [-s, -s,  s], [-s,  s,  s],  # Triangle 1
        [-s, -s, -s], [-s,  s,  s], [-s,  s, -s],  # Triangle 2
    ], dtype=np.float32)
    
    # Normals for each face
    normals = np.array([
        # Front face (z+)
        [0, 0, 1], [0, 0, 1], [0, 0, 1],
        [0, 0, 1], [0, 0, 1], [0, 0, 1],
        # Back face (z-)
        [0, 0, -1], [0, 0, -1], [0, 0, -1],
        [0, 0, -1], [0, 0, -1], [0, 0, -1],
        # Top face (y+)
        [0, 1, 0], [0, 1, 0], [0, 1, 0],
        [0, 1, 0], [0, 1, 0], [0, 1, 0],
        # Bottom face (y-)
        [0, -1, 0], [0, -1, 0], [0, -1, 0],
        [0, -1, 0], [0, -1, 0], [0, -1, 0],
        # Right face (x+)
        [1, 0, 0], [1, 0, 0], [1, 0, 0],
        [1, 0, 0], [1, 0, 0], [1, 0, 0],
        # Left face (x-)
        [-1, 0, 0], [-1, 0, 0], [-1, 0, 0],
        [-1, 0, 0], [-1, 0, 0], [-1, 0, 0],
    ], dtype=np.float32)
    
    # Combine vertices and normals
    vertex_count = len(vertices)
    data = np.zeros((vertex_count, 6), dtype=np.float32)
    data[:, :3] = vertices
    data[:, 3:6] = normals
    
    # Create VAO and VBO
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
    
    # Position attribute (location 0)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, None)
    
    # Normal attribute (location 1)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, np.array([3 * 4], dtype=np.uintp))
    
    glBindVertexArray(0)
    
    return vao, vertex_count


def create_simple_triangle():
    """Create a simple triangle for testing"""
    vertices = np.array([
        [0.0, 2.0, 0.0],   # Top
        [-2.0, -2.0, 0.0], # Bottom left
        [2.0, -2.0, 0.0],  # Bottom right
    ], dtype=np.float32)
    
    normals = np.array([
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)
    
    vertex_count = len(vertices)
    data = np.zeros((vertex_count, 6), dtype=np.float32)
    data[:, :3] = vertices
    data[:, 3:6] = normals
    
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
    
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, None)
    
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, np.array([3 * 4], dtype=np.uintp))
    
    glBindVertexArray(0)
    
    return vao, vertex_count


def render_test_cube(vao, vertex_count):
    """Render the test cube"""
    from OpenGL.GL import glGetError, GL_NO_ERROR
    error = glGetError()
    if error != GL_NO_ERROR:
        print(f"OpenGL Error before bind VAO: {error}")
    
    glBindVertexArray(vao)
    
    error = glGetError()
    if error != GL_NO_ERROR:
        print(f"OpenGL Error after bind VAO: {error}")
    
    glDrawArrays(GL_TRIANGLES, 0, vertex_count)
    
    error = glGetError()
    if error != GL_NO_ERROR:
        print(f"OpenGL Error after draw: {error}")
    
    glBindVertexArray(0)

