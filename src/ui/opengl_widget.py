"""
OpenGL Widget for 3D visualization
"""

import numpy as np
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QSurfaceFormat

from src.visualization.opengl.renderer import Renderer
from src.simulation.simulation_engine import SimulationEngine


class OpenGLWidget(QOpenGLWidget):
    """OpenGL widget for 3D rendering"""
    
    def __init__(self, config, algorithm_type):
        # Set OpenGL format to request desktop OpenGL 3.3+
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        fmt.setSamples(4)  # 4x MSAA
        QSurfaceFormat.setDefaultFormat(fmt)
        
        super().__init__()
        self.config = config
        self.algorithm_type = algorithm_type  # "old" or "new"
        self.setMinimumSize(400, 300)
        
        # Renderer
        self.renderer = None
        
        # Simulation engine
        self.simulation = SimulationEngine(config, algorithm_type)
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.mouse_pressed = False
        
        # Animation timer for continuous rendering
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
    def initializeGL(self):
        """Initialize OpenGL"""
        print(f"[{self.algorithm_type}] Initializing OpenGL context...")
        
        # Initialize renderer
        self.renderer = Renderer(self.config)
        self.renderer.initialize()
        
        # Don't set viewport here - wait for resizeGL to be called
        # The widget might not have its final size yet
        
    def resizeGL(self, width, height):
        """Handle OpenGL resize"""
        # This is called after initializeGL and whenever the widget is resized
        # Set viewport here (like the working sample projects do)
        from OpenGL.GL import glViewport
        glViewport(0, 0, width, height)
        
        if self.renderer:
            self.renderer.set_viewport(width, height)
        
    def paintGL(self):
        """Render OpenGL scene"""
        if not self.renderer:
            return
            
        # Update simulation
        self.simulation.update()
        
        # Begin frame
        self.renderer.begin_frame()
        
        # Render test cube (for debugging - can remove later)
        # self.renderer.render_test_cube()  # Commented out - objects are working!
        
        # Render ground plane
        if self.config['visualization']['show_grid']:
            self.renderer.render_ground_plane()
        
        # Always render defense system (for testing visibility)
        defense_color = np.array(
            self.config['models']['defense_system']['color'],
            dtype=np.float32
        )
        self.renderer.render_defense_system(
            self.simulation.defense_system_pos,
            defense_color
        )
        
        # Render missiles
        missiles = self.simulation.get_missiles()
        for missile in missiles:
            self.renderer.render_missile(missile)
            
        # Render interceptors
        interceptors = self.simulation.get_interceptors()
        for interceptor in interceptors:
            self.renderer.render_interceptor(interceptor)
        
    def get_camera(self):
        """Get camera instance"""
        return self.renderer.camera if self.renderer else None
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = True
            self.last_mouse_pos = event.position()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = False
            self.last_mouse_pos = None
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for camera rotation"""
        if self.mouse_pressed and self.last_mouse_pos and self.renderer:
            # Calculate mouse delta
            dx = event.position().x() - self.last_mouse_pos.x()
            dy = event.position().y() - self.last_mouse_pos.y()
            
            # Rotate camera
            camera = self.renderer.camera
            camera.rotate(dx * 0.01, -dy * 0.01)  # Negative dy for natural rotation
            
            self.last_mouse_pos = event.position()
            self.update()
            
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zoom"""
        if self.renderer:
            delta = event.angleDelta().y() / 120.0  # Normalize wheel delta
            camera = self.renderer.camera
            camera.zoom(-delta)  # Negative for zoom in on scroll up
            self.update()

