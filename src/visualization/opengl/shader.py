"""
Shader loading and management
"""

import os
from OpenGL.GL import (
    glCreateShader, glShaderSource, glCompileShader,
    glGetShaderiv, GL_COMPILE_STATUS, GL_INFO_LOG_LENGTH,
    glGetShaderInfoLog, glDeleteShader, glCreateProgram,
    glAttachShader, glLinkProgram, glGetProgramiv,
    GL_LINK_STATUS, glGetProgramInfoLog, glUseProgram,
    glGetUniformLocation, GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
)


class Shader:
    """OpenGL shader program"""
    
    def __init__(self, vertex_path, fragment_path):
        self.program_id = None
        self.vertex_path = vertex_path
        self.fragment_path = fragment_path
        self.load()
        
    def load(self):
        """Load and compile shaders"""
        # Read shader source files
        vertex_code = self._read_file(self.vertex_path)
        fragment_code = self._read_file(self.fragment_path)
        
        # Compile shaders
        vertex_shader = self._compile_shader(GL_VERTEX_SHADER, vertex_code)
        fragment_shader = self._compile_shader(GL_FRAGMENT_SHADER, fragment_code)
        
        # Create shader program
        self.program_id = glCreateProgram()
        glAttachShader(self.program_id, vertex_shader)
        glAttachShader(self.program_id, fragment_shader)
        glLinkProgram(self.program_id)
        
        # Check for linking errors
        if not glGetProgramiv(self.program_id, GL_LINK_STATUS):
            error = glGetProgramInfoLog(self.program_id).decode()
            glDeleteShader(vertex_shader)
            glDeleteShader(fragment_shader)
            raise RuntimeError(f"Shader linking failed: {error}")
        
        # Clean up shaders (no longer needed after linking)
        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)
        
    def _read_file(self, filepath):
        """Read shader source file"""
        # Convert to absolute path if relative
        if not os.path.isabs(filepath):
            # Assume relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            filepath = os.path.join(project_root, filepath)
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Shader file not found: {filepath}")
        with open(filepath, 'r') as f:
            return f.read()
            
    def _compile_shader(self, shader_type, source):
        """Compile a shader"""
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        
        # Check for compilation errors
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader).decode()
            glDeleteShader(shader)
            raise RuntimeError(f"Shader compilation failed: {error}")
            
        return shader
        
    def use(self):
        """Activate this shader program"""
        glUseProgram(self.program_id)
        
    def get_uniform_location(self, name):
        """Get uniform variable location"""
        return glGetUniformLocation(self.program_id, name)
        
    def set_uniform_matrix4(self, name, matrix):
        """Set 4x4 matrix uniform"""
        from OpenGL.GL import glUniformMatrix4fv
        location = self.get_uniform_location(name)
        if location != -1:
            glUniformMatrix4fv(location, 1, False, matrix)
            
    def set_uniform_vec3(self, name, vec):
        """Set vec3 uniform"""
        from OpenGL.GL import glUniform3f
        location = self.get_uniform_location(name)
        if location != -1:
            glUniform3f(location, vec[0], vec[1], vec[2])
            
    def set_uniform_float(self, name, value):
        """Set float uniform"""
        from OpenGL.GL import glUniform1f
        location = self.get_uniform_location(name)
        if location != -1:
            glUniform1f(location, value)
            
    def set_uniform_bool(self, name, value):
        """Set bool uniform"""
        from OpenGL.GL import glUniform1i
        location = self.get_uniform_location(name)
        if location != -1:
            glUniform1i(location, 1 if value else 0)

