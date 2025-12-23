"""
OpenGL renderer for 3D scene
"""

import os
import numpy as np
from math import radians
from OpenGL.GL import (
    glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    glEnable, GL_DEPTH_TEST, glViewport, GL_LINES, GL_TRIANGLES,
    glGenBuffers, glBindBuffer, GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER,
    glBufferData, GL_STATIC_DRAW, glGenVertexArrays, glBindVertexArray,
    glEnableVertexAttribArray, glVertexAttribPointer,
    glDrawArrays, glLineWidth, GL_FLOAT, GL_UNSIGNED_INT
)

from src.visualization.opengl.camera import Camera
from src.visualization.opengl.shader import Shader
from src.visualization.opengl.models import (
    create_missile_model, create_interceptor_model, create_defense_system_model
)
from src.visualization.opengl.test_objects import create_test_cube, render_test_cube, create_simple_triangle


class Renderer:
    """3D scene renderer"""
    
    def __init__(self, config):
        self.config = config
        self.camera = Camera(config)
        self.shader = None
        self.projection_matrix = None
        
        # VAOs and VBOs for rendering
        self.ground_vao = None
        self.ground_vbo = None
        self.axes_vao = None
        self.axes_vbo = None
        
        # Test cube for debugging
        self.test_cube_vao = None
        self.test_cube_vertex_count = 0
        # Simple triangle for testing
        self.test_triangle_vao = None
        self.test_triangle_vertex_count = 0
        
    def initialize(self):
        """Initialize OpenGL state"""
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        
        # Check OpenGL version and load appropriate shaders
        from OpenGL.GL import glGetString, GL_VERSION, glGetError, GL_NO_ERROR
        gl_version = glGetString(GL_VERSION)
        
        # Check for OpenGL errors
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error during initialization: {error}")
        
        if gl_version:
            gl_version_str = gl_version.decode('utf-8')
            print(f"OpenGL Version: {gl_version_str}")
            # Check if we're using OpenGL ES
            is_es = 'ES' in gl_version_str
        else:
            is_es = False
            print("Warning: Could not get OpenGL version")
            
        # Load shaders (use absolute path)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        shader_dir = os.path.join(project_root, "resources", "shaders")
        
        if is_es:
            # Use ES-compatible shaders
            vertex_shader = os.path.join(shader_dir, "vertex_es.glsl")
            fragment_shader = os.path.join(shader_dir, "fragment_es.glsl")
            print("Using OpenGL ES shaders")
        else:
            # Use desktop OpenGL shaders
            vertex_shader = os.path.join(shader_dir, "vertex.glsl")
            fragment_shader = os.path.join(shader_dir, "fragment.glsl")
            print("Using desktop OpenGL shaders")
            
        print(f"Loading shaders: {vertex_shader}, {fragment_shader}")
        self.shader = Shader(vertex_shader, fragment_shader)
        print("Shaders loaded successfully")
        
        # Create ground plane geometry
        self._create_ground_plane()
        
        # Create coordinate axes geometry
        self._create_coordinate_axes()
        
        # Create test cube for debugging
        print("Creating test cube...")
        self.test_cube_vao, self.test_cube_vertex_count = create_test_cube(size=5.0)
        print(f"Test cube created: VAO={self.test_cube_vao}, Vertices={self.test_cube_vertex_count}")
        
        # Create simple triangle for testing
        print("Creating test triangle...")
        self.test_triangle_vao, self.test_triangle_vertex_count = create_simple_triangle()
        print(f"Test triangle created: VAO={self.test_triangle_vao}, Vertices={self.test_triangle_vertex_count}")
        
        # Check for errors after creating geometry
        from OpenGL.GL import glGetError, GL_NO_ERROR
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error after creating test geometry: {error}")
        
        # Create 3D models
        self.missile_model = create_missile_model(
            self.config['models']['missile']['length'],
            self.config['models']['missile']['radius']
        )
        self.interceptor_model = create_interceptor_model(
            self.config['models']['interceptor']['length'],
            self.config['models']['interceptor']['radius']
        )
        self.defense_system_model = create_defense_system_model(
            self.config['models']['defense_system']['base_radius'],
            self.config['models']['defense_system']['base_height'],
            self.config['models']['defense_system']['dish_radius'],
            self.config['models']['defense_system']['dish_height']
        )
        
    def set_viewport(self, width, height):
        """Update projection matrix based on viewport size"""
        # Note: glViewport should be called in resizeGL, not here
        # This method only updates the projection matrix
        
        # Calculate projection matrix (perspective)
        fov = radians(self.config['visualization']['fov'])
        aspect = width / height if height > 0 else 1.0
        near = self.config['visualization']['near_plane']
        far = self.config['visualization']['far_plane']
        
        # Perspective projection matrix (OpenGL style)
        # Using the same approach as gluPerspective
        f = 1.0 / np.tan(fov / 2.0)
        self.projection_matrix = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)
        
    def begin_frame(self):
        """Begin rendering frame"""
        # Clear buffers
        bg_color = self.config['visualization']['background_color']
        from OpenGL.GL import glClearColor, glGetError, GL_NO_ERROR
        glClearColor(bg_color[0], bg_color[1], bg_color[2], bg_color[3])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Check for errors after clear
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error after clear: {error}")
        
        # Use shader (must be called before setting uniforms)
        if self.shader:
            self.shader.use()
            
            # Set up matrices
            if self.projection_matrix is not None:
                view_matrix = self.camera.get_view_matrix()
                
                # Debug: Print matrices (first frame only)
                if not hasattr(self, '_matrix_debug_printed'):
                    print(f"View matrix:\n{view_matrix}")
                    print(f"Projection matrix:\n{self.projection_matrix}")
                    self._matrix_debug_printed = True
                
                self.shader.set_uniform_matrix4("view", view_matrix)
                self.shader.set_uniform_matrix4("projection", self.projection_matrix)
                
                # Set up lighting
                light_dir = np.array([0.5, -1.0, 0.5], dtype=np.float32)
                light_dir = light_dir / np.linalg.norm(light_dir)
                self.shader.set_uniform_vec3("lightDir", light_dir)
                self.shader.set_uniform_vec3("lightColor", np.array([1.0, 1.0, 1.0]))
                
                # Set view position (camera position)
                view_pos = self.camera.get_position()
                self.shader.set_uniform_vec3("viewPos", view_pos)
                
                # Default to lighting enabled
                self.shader.set_uniform_bool("useLighting", True)
                
                # Check for errors after setting uniforms
                error = glGetError()
                if error != GL_NO_ERROR:
                    print(f"OpenGL Error after setting uniforms: {error}")
        
    def _create_ground_plane(self, size=50.0, grid_size=5.0):
        """Create ground plane geometry using VBO"""
        vertices = []
        
        # Generate grid lines
        for i in range(-int(size), int(size) + 1, int(grid_size)):
            # Lines along X axis
            vertices.extend([i, 0.0, -size, 0.0, 1.0, 0.0])  # position + normal
            vertices.extend([i, 0.0, size, 0.0, 1.0, 0.0])
            # Lines along Z axis
            vertices.extend([-size, 0.0, i, 0.0, 1.0, 0.0])
            vertices.extend([size, 0.0, i, 0.0, 1.0, 0.0])
        
        vertices = np.array(vertices, dtype=np.float32)
        
        # Create VAO and VBO
        self.ground_vao = glGenVertexArrays(1)
        self.ground_vbo = glGenBuffers(1)
        
        glBindVertexArray(self.ground_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.ground_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        # Position attribute (location 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, None)  # 6 floats per vertex (3 pos + 3 normal)
        
        # Normal attribute (location 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, np.array([3 * 4], dtype=np.uintp))
        
        glBindVertexArray(0)
        self.ground_vertex_count = len(vertices) // 6
        
    def _create_coordinate_axes(self, length=10.0):
        """Create coordinate axes geometry using VBO"""
        # X axis (red), Y axis (green), Z axis (blue)
        vertices = np.array([
            # X axis
            0.0, 0.0, 0.0, 1.0, 0.0, 0.0,  # position + color (red)
            length, 0.0, 0.0, 1.0, 0.0, 0.0,
            # Y axis
            0.0, 0.0, 0.0, 0.0, 1.0, 0.0,  # position + color (green)
            0.0, length, 0.0, 0.0, 1.0, 0.0,
            # Z axis
            0.0, 0.0, 0.0, 0.0, 0.0, 1.0,  # position + color (blue)
            0.0, 0.0, length, 0.0, 0.0, 1.0,
        ], dtype=np.float32)
        
        # Create VAO and VBO
        self.axes_vao = glGenVertexArrays(1)
        self.axes_vbo = glGenBuffers(1)
        
        glBindVertexArray(self.axes_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.axes_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        # Position attribute (location 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, False, 6 * 4, None)
        
        # Color as normal (location 1) - we'll use color instead of normal for axes
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 6 * 4, np.array([3 * 4], dtype=np.uintp))
        
        glBindVertexArray(0)
        self.axes_vertex_count = len(vertices) // 6
        
    def render_ground_plane(self, size=50.0, grid_size=5.0):
        """Render ground plane with grid"""
        if self.ground_vao is None:
            return
            
        # Set model matrix to identity
        model_matrix = np.eye(4, dtype=np.float32)
        self.shader.set_uniform_matrix4("model", model_matrix)
        
        # Set color (gray) and disable lighting for lines
        self.shader.set_uniform_vec3("color", np.array([0.3, 0.3, 0.3]))
        self.shader.set_uniform_bool("useLighting", False)
        
        glLineWidth(1.0)
        glBindVertexArray(self.ground_vao)
        glDrawArrays(GL_LINES, 0, self.ground_vertex_count)
        glBindVertexArray(0)
        
        # Re-enable lighting for other objects
        self.shader.set_uniform_bool("useLighting", True)
        
    def render_coordinate_axes(self, length=10.0):
        """Render coordinate axes"""
        if self.axes_vao is None:
            return
            
        # Set model matrix to identity
        model_matrix = np.eye(4, dtype=np.float32)
        self.shader.set_uniform_matrix4("model", model_matrix)
        
        # Disable lighting for axes (they use color directly)
        self.shader.set_uniform_bool("useLighting", False)
        
        glLineWidth(2.0)
        glBindVertexArray(self.axes_vao)
        glDrawArrays(GL_LINES, 0, self.axes_vertex_count)
        glBindVertexArray(0)
        
        # Re-enable lighting
        self.shader.set_uniform_bool("useLighting", True)
        
    def render_missile(self, missile):
        """Render a missile"""
        if not missile or not missile.active or not self.shader or not self.missile_model:
            return
            
        # Make sure shader is active
        self.shader.use()
        
        # Re-setup view/projection in case they were lost
        if self.projection_matrix is not None:
            view_matrix = self.camera.get_view_matrix()
            self.shader.set_uniform_matrix4("view", view_matrix)
            self.shader.set_uniform_matrix4("projection", self.projection_matrix)
            
        # Set model matrix
        model_matrix = missile.get_model_matrix()
        self.shader.set_uniform_matrix4("model", model_matrix)
        
        # Set color
        self.shader.set_uniform_vec3("color", missile.color)
        self.shader.set_uniform_bool("useLighting", True)
        
        # Render model
        self.missile_model.render()
        
    def render_interceptor(self, interceptor):
        """Render an interceptor"""
        if not interceptor or not interceptor.active or not self.shader or not self.interceptor_model:
            return
            
        # Make sure shader is active
        self.shader.use()
        
        # Re-setup view/projection in case they were lost
        if self.projection_matrix is not None:
            view_matrix = self.camera.get_view_matrix()
            self.shader.set_uniform_matrix4("view", view_matrix)
            self.shader.set_uniform_matrix4("projection", self.projection_matrix)
            
        # Set model matrix
        model_matrix = interceptor.get_model_matrix()
        self.shader.set_uniform_matrix4("model", model_matrix)
        
        # Set color
        self.shader.set_uniform_vec3("color", interceptor.color)
        self.shader.set_uniform_bool("useLighting", True)
        
        # Render model
        self.interceptor_model.render()
        
    def render_test_cube(self):
        """Render a test cube at origin for debugging"""
        if not self.shader:
            print("ERROR: Shader not initialized!")
            return
        if not self.test_cube_vao:
            print("ERROR: Test cube VAO not created!")
            return
        if self.projection_matrix is None:
            print("ERROR: Projection matrix not set!")
            return
            
        # Make sure shader is active
        self.shader.use()
        
        # Re-setup view/projection
        view_matrix = self.camera.get_view_matrix()
        self.shader.set_uniform_matrix4("view", view_matrix)
        self.shader.set_uniform_matrix4("projection", self.projection_matrix)
        
        # Set up lighting
        light_dir = np.array([0.5, -1.0, 0.5], dtype=np.float32)
        light_dir = light_dir / np.linalg.norm(light_dir)
        self.shader.set_uniform_vec3("lightDir", light_dir)
        self.shader.set_uniform_vec3("lightColor", np.array([1.0, 1.0, 1.0]))
        view_pos = self.camera.get_position()
        self.shader.set_uniform_vec3("viewPos", view_pos)
        
        # Model matrix (identity - at origin)
        model_matrix = np.eye(4, dtype=np.float32)
        self.shader.set_uniform_matrix4("model", model_matrix)
        
        # Bright red color - try without lighting first
        self.shader.set_uniform_vec3("color", np.array([1.0, 0.0, 0.0]))
        self.shader.set_uniform_bool("useLighting", False)  # Disable lighting for test
        
        # Check for OpenGL errors before rendering
        from OpenGL.GL import glGetError, GL_NO_ERROR
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL Error before rendering cube: {error}")
        
        # Render test cube (simple rendering for debugging)
        render_test_cube(self.test_cube_vao, self.test_cube_vertex_count)
        
    def render_defense_system(self, position: np.ndarray, color: np.ndarray):
        """Render defense system at position"""
        if not self.shader:
            return
            
        # Make sure shader is active
        self.shader.use()
        
        # Create model matrix
        model_matrix = np.eye(4, dtype=np.float32)
        model_matrix[0, 3] = position[0]
        model_matrix[1, 3] = position[1]
        model_matrix[2, 3] = position[2]
        
        self.shader.set_uniform_matrix4("model", model_matrix)
        self.shader.set_uniform_vec3("color", color)
        self.shader.set_uniform_bool("useLighting", True)
        
        # Render model
        if self.defense_system_model:
            self.defense_system_model.render()
        
    def render_trail(self, trail_points: list, color: np.ndarray, fade: bool = True):
        """Render trail line"""
        if len(trail_points) < 2:
            return
            
        # Create line vertices
        vertices = []
        for i, point in enumerate(trail_points):
            vertices.extend([point[0], point[1], point[2], 0.0, 1.0, 0.0])  # pos + normal
            
        vertices = np.array(vertices, dtype=np.float32)
        
        # Use a simple line rendering approach
        # For now, we'll skip trail rendering in this step (can be added later)
        # This would require creating a temporary VBO or using a different approach

