"""
2D Radar/Sonar Widget for missile defense visualization
"""

import numpy as np
import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from src.simulation.simulation_engine import SimulationEngine


class RadarWidget(QWidget):
    """2D Radar/Sonar widget for top-down view of missile defense"""
    
    def __init__(self, config, algorithm_type):
        super().__init__()
        self.config = config
        self.algorithm_type = algorithm_type  # "old" or "new"
        self.setMinimumSize(400, 400)
        
        # Simulation engine
        self.simulation = SimulationEngine(config, algorithm_type)
        
        # Radar display settings
        self.radar_range = config['visualization'].get('radar_range', 100.0)
        self.show_grid = config['visualization'].get('show_grid', True)
        self.show_trails = config['visualization'].get('show_trails', True)
        
        # Animation timer for continuous rendering
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        # Radar sweep angle (for visual effect)
        self.sweep_angle = 0.0
        self.sweep_speed = 2.0  # degrees per frame
        
        # Background color (dark green/black like radar)
        self.bg_color = QColor(0, 20, 0)
        self.grid_color = QColor(0, 100, 0)
        
        # Explosion effects tracking
        self.explosions = []  # List of (position, time, max_age)
        self.missed_missile_effects = []  # List of missed missile effects at center
        
    def paintEvent(self, event):
        """Paint the radar display"""
        # Update simulation state first
        self.simulation.update()
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 20
        
        # Fill background
        painter.fillRect(0, 0, width, height, self.bg_color)
        
        # Draw radar circles and grid
        if self.show_grid:
            self._draw_radar_grid(painter, center_x, center_y, radius)
        
        # Draw radar sweep (rotating line)
        self._draw_radar_sweep(painter, center_x, center_y, radius)
        
        # Draw defense system at center
        self._draw_defense_system(painter, center_x, center_y)
        
        # Draw missiles
        missiles = self.simulation.get_missiles()
        for missile in missiles:
            self._draw_missile(painter, missile, center_x, center_y, radius)
        
        # Draw interceptors
        interceptors = self.simulation.get_interceptors()
        for interceptor in interceptors:
            self._draw_interceptor(painter, interceptor, center_x, center_y, radius)
            
            # Check for new explosions
            if interceptor.intercepted and interceptor.interception_position is not None:
                # Add explosion effect
                self.explosions.append({
                    'pos': interceptor.interception_position.copy(),
                    'time': time.time(),
                    'max_age': 1.0  # 1 second explosion duration
                })
                interceptor.interception_position = None  # Clear to avoid duplicates
        
        # Draw explosion effects (enhanced with multiple rings)
        current_time = time.time()
        self.explosions = [exp for exp in self.explosions if current_time - exp['time'] < exp['max_age']]
        for exp in self.explosions:
            age = current_time - exp['time']
            progress = age / exp['max_age']
            
            # Convert 3D position to 2D
            pos_3d = exp['pos']
            screen_x = center_x + (pos_3d[0] / self.radar_range) * radius
            screen_y = center_y + (pos_3d[2] / self.radar_range) * radius
            
            # Draw multiple expanding rings for better visual effect
            for ring in range(3):
                ring_progress = (progress + ring * 0.2) % 1.0
                size = 8 + ring_progress * 35  # Grow from 8 to 43 pixels
                alpha = int(200 * (1.0 - ring_progress))  # Fade out
                
                # Color gradient: yellow -> orange -> red
                if ring_progress < 0.33:
                    color = QColor(255, 255, 0, alpha)  # Yellow
                elif ring_progress < 0.66:
                    color = QColor(255, 165, 0, alpha)  # Orange
                else:
                    color = QColor(255, 100, 0, alpha)  # Red-orange
                
                brush = QBrush(QColor(color.red(), color.green(), color.blue(), alpha // 2))
                painter.setBrush(brush)
                pen = QPen(color)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(screen_x, screen_y), size, size)
            
            # Draw bright center flash
            center_alpha = int(255 * (1.0 - progress))
            brush = QBrush(QColor(255, 255, 255, center_alpha))
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(screen_x, screen_y), 4, 4)
        
        # Check for new missed missiles and add visual effects (only for old algorithm)
        if self.algorithm_type == "old":
            if hasattr(self.simulation, 'missed_missiles') and self.simulation.missed_missiles:
                for missed in self.simulation.missed_missiles[:]:
                    # Add missed missile effect at center
                    self.missed_missile_effects.append({
                        'time': time.time(),
                        'max_age': 3.0  # Show for 3 seconds
                    })
                # Clear the list after processing
                self.simulation.missed_missiles.clear()
        
        # Draw missed missile effects at center
        self.missed_missile_effects = [eff for eff in self.missed_missile_effects 
                                       if current_time - eff['time'] < eff['max_age']]
        for missed_eff in self.missed_missile_effects:
            age = current_time - missed_eff['time']
            progress = age / missed_eff['max_age']
            
            # Draw explosion at center
            screen_x = center_x
            screen_y = center_y
            
            # Draw multiple expanding rings (red for missed)
            for ring in range(3):
                ring_progress = (progress + ring * 0.2) % 1.0
                size = 10 + ring_progress * 40
                alpha = int(200 * (1.0 - ring_progress))
                
                # Red color for missed missile
                color = QColor(255, 0, 0, alpha)
                brush = QBrush(QColor(color.red(), color.green(), color.blue(), alpha // 2))
                painter.setBrush(brush)
                pen = QPen(color)
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(screen_x, screen_y), size, size)
            
            # Draw "MISSILE MISSED" text
            if progress < 0.7:  # Show text for first 70% of effect
                font = QFont("Arial", 16, QFont.Weight.Bold)
                painter.setFont(font)
                text_alpha = int(255 * (1.0 - progress / 0.7))
                pen = QPen(QColor(255, 0, 0, text_alpha))
                painter.setPen(pen)
                # Show "DRONE MISSED" or "MISSILE MISSED" based on threat type
                threat_type = getattr(self.simulation, 'threat_type', 'missiles')
                if threat_type == "drones":
                    text = "DRONE MISSED"
                else:
                    text = "MISSILE MISSED"
                text_rect = painter.fontMetrics().boundingRect(text)
                painter.drawText(
                    int(center_x - text_rect.width() / 2),
                    int(center_y - 30),
                    text
                )
        
        # Draw interception time clocks and counters
        self._draw_interception_info(painter, width, height)
        
        # Draw legend/title
        self._draw_legend(painter, width, height)
        
        # Update sweep angle only if simulation is running
        if self.simulation.is_running and not self.simulation.is_paused:
            self.sweep_angle += self.sweep_speed
            if self.sweep_angle >= 360:
                self.sweep_angle -= 360
    
    def _draw_radar_grid(self, painter, center_x, center_y, radius):
        """Draw radar grid (concentric circles and lines)"""
        pen = QPen(self.grid_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Draw concentric circles
        for i in range(1, 6):
            r = radius * (i / 5)
            painter.drawEllipse(QPointF(center_x, center_y), r, r)
        
        # Draw radial lines (every 30 degrees)
        for angle in range(0, 360, 30):
            rad = np.radians(angle)
            x = center_x + radius * np.cos(rad)
            y = center_y + radius * np.sin(rad)
            painter.drawLine(int(center_x), int(center_y), int(x), int(y))
    
    def _draw_radar_sweep(self, painter, center_x, center_y, radius):
        """Draw rotating radar sweep line with trailing fade"""
        # Draw trailing sweep effect (multiple lines with decreasing opacity)
        for i in range(5):
            angle_offset = self.sweep_angle - (i * 5)  # Trail behind main sweep
            rad = np.radians(angle_offset)
            
            # Calculate end point
            x = center_x + radius * np.cos(rad)
            y = center_y + radius * np.sin(rad)
            
            # Fade effect: newer lines are brighter
            alpha = int(150 * (1.0 - i * 0.15))
            pen = QPen(QColor(0, 255, 0, alpha))
            pen.setWidth(max(1, int(2 - i * 0.3)))
            painter.setPen(pen)
            painter.drawLine(int(center_x), int(center_y), int(x), int(y))
        
        # Draw bright leading edge
        rad = np.radians(self.sweep_angle)
        x = center_x + radius * np.cos(rad)
        y = center_y + radius * np.sin(rad)
        pen = QPen(QColor(0, 255, 0, 200))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(int(center_x), int(center_y), int(x), int(y))
    
    def _draw_defense_system(self, painter, center_x, center_y):
        """Draw defense system at center with pulsing effect"""
        current_time = time.time()
        pulse = 1.0 + 0.1 * np.sin(current_time * 2.0)  # Subtle pulse animation
        
        # Draw outer pulsing ring
        brush = QBrush(QColor(0, 100, 255, 40))
        painter.setBrush(brush)
        pen = QPen(QColor(0, 150, 255, 150))
        pen.setWidth(2)
        painter.setPen(pen)
        size = int(8 * pulse)
        painter.drawEllipse(QPointF(center_x, center_y), size, size)
        
        # Draw middle ring
        brush = QBrush(QColor(0, 120, 255, 60))
        painter.setBrush(brush)
        pen = QPen(QColor(0, 150, 255))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(center_x, center_y), 6, 6)
        
        # Draw center dot
        brush = QBrush(QColor(0, 200, 255))
        painter.setBrush(brush)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(center_x, center_y), 4, 4)
        
        # Draw crosshair for better visibility
        pen = QPen(QColor(0, 150, 255, 100))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(int(center_x - 10), int(center_y), int(center_x + 10), int(center_y))
        painter.drawLine(int(center_x), int(center_y - 10), int(center_x), int(center_y + 10))
    
    def _draw_missile(self, painter, missile, center_x, center_y, radius):
        """Draw a missile on the radar with phase-based coloring"""
        # Convert 3D position to 2D (top-down view: x, z -> x, y on screen)
        pos_3d = missile.position
        screen_x = center_x + (pos_3d[0] / self.radar_range) * radius
        screen_y = center_y + (pos_3d[2] / self.radar_range) * radius  # Use Z for Y on screen
        
        # Check if missile is within radar range
        distance = np.sqrt(pos_3d[0]**2 + pos_3d[2]**2)
        if distance > self.radar_range:
            return
        
        # Get phase-based colors
        phase = getattr(missile, 'phase', 'Tracing')
        phase_colors = {
            'Tracing': {
                'main': QColor(255, 255, 0),      # Yellow
                'trail': QColor(255, 255, 0, 100),  # Semi-transparent yellow
                'glow': QColor(255, 255, 100),
                'direction': QColor(255, 255, 150)
            },
            'Warning': {
                'main': QColor(255, 165, 0),      # Orange
                'trail': QColor(255, 165, 0, 100),  # Semi-transparent orange
                'glow': QColor(255, 200, 100),
                'direction': QColor(255, 200, 150)
            },
            'Destroy': {
                'main': QColor(255, 0, 0),        # Red
                'trail': QColor(255, 0, 0, 100),    # Semi-transparent red
                'glow': QColor(255, 100, 100),
                'direction': QColor(255, 150, 150)
            }
        }
        colors = phase_colors.get(phase, phase_colors['Tracing'])
        
        # Get threat type (missiles or drones)
        threat_type = getattr(missile, 'threat_type', 'missiles')
        
        # Visual differences: drones are smaller
        if threat_type == "drones":
            size_multiplier = 0.6  # Drones are 60% the size of missiles
            dot_size = 4  # Smaller dot for drones
        else:
            size_multiplier = 1.0  # Missiles are full size
            dot_size = 6  # Larger dot for missiles
        
        # Draw missile trail if enabled
        if self.show_trails and hasattr(missile, 'trail') and len(missile.trail) > 1:
            pen = QPen(colors['trail'])
            pen.setWidth(1)
            painter.setPen(pen)
            for i in range(len(missile.trail) - 1):
                p1 = missile.trail[i]
                p2 = missile.trail[i + 1]
                x1 = center_x + (p1[0] / self.radar_range) * radius
                y1 = center_y + (p1[2] / self.radar_range) * radius
                x2 = center_x + (p2[0] / self.radar_range) * radius
                y2 = center_y + (p2[2] / self.radar_range) * radius
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw phase indicator ring (outer glow) - size varies by threat type
        ring_size = int(6 * size_multiplier)
        brush = QBrush(QColor(colors['glow'].red(), colors['glow'].green(), colors['glow'].blue(), 80))
        painter.setBrush(brush)
        pen = QPen(colors['glow'])
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(screen_x, screen_y), ring_size, ring_size)  # Outer ring
        
        # Draw missile/drone dot with phase color - size varies by threat type
        brush = QBrush(colors['main'])
        painter.setBrush(brush)
        pen = QPen(colors['glow'])
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(screen_x, screen_y), dot_size, dot_size)
        
        # Draw direction indicator (small line showing velocity direction)
        if np.linalg.norm(missile.velocity) > 0:
            vel = missile.velocity
            vel_2d = np.array([vel[0], vel[2]])  # Use X and Z components
            vel_2d = vel_2d / np.linalg.norm(vel_2d) * (8 * size_multiplier)  # Scale by threat type
            pen = QPen(colors['direction'])
            pen.setWidth(max(1, int(2 * size_multiplier)))  # Thinner line for drones
            painter.setPen(pen)
            painter.drawLine(
                int(screen_x), int(screen_y),
                int(screen_x + vel_2d[0]), int(screen_y + vel_2d[1])
            )
    
    def _draw_interceptor(self, painter, interceptor, center_x, center_y, radius):
        """Draw an interceptor on the radar"""
        # Convert 3D position to 2D (top-down view)
        pos_3d = interceptor.position
        screen_x = center_x + (pos_3d[0] / self.radar_range) * radius
        screen_y = center_y + (pos_3d[2] / self.radar_range) * radius
        
        # Check if interceptor is within radar range
        distance = np.sqrt(pos_3d[0]**2 + pos_3d[2]**2)
        if distance > self.radar_range:
            return
        
        # Draw interceptor trail if enabled (with fade effect)
        if self.show_trails and hasattr(interceptor, 'trail') and len(interceptor.trail) > 1:
            # Use algorithm-specific color
            base_color = QColor(255, 165, 0) if self.algorithm_type == "old" else QColor(0, 255, 0)
            trail_points = interceptor.trail[-20:]  # Limit trail length for performance
            for i in range(len(trail_points) - 1):
                # Fade trail based on age (newer = brighter)
                alpha = int(100 * (i + 1) / len(trail_points))
                color = QColor(base_color.red(), base_color.green(), base_color.blue(), alpha)
                pen = QPen(color)
                pen.setWidth(1)
                painter.setPen(pen)
                p1 = trail_points[i]
                p2 = trail_points[i + 1]
                x1 = center_x + (p1[0] / self.radar_range) * radius
                y1 = center_y + (p1[2] / self.radar_range) * radius
                x2 = center_x + (p2[0] / self.radar_range) * radius
                y2 = center_y + (p2[2] / self.radar_range) * radius
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        # Draw interceptor dot with glow effect
        interceptor_color = QColor(255, 165, 0) if self.algorithm_type == "old" else QColor(0, 255, 0)
        
        # Outer glow
        brush = QBrush(QColor(interceptor_color.red(), interceptor_color.green(), interceptor_color.blue(), 60))
        painter.setBrush(brush)
        pen = QPen(QColor(interceptor_color.red(), interceptor_color.green(), interceptor_color.blue(), 100))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(screen_x, screen_y), 5, 5)
        
        # Inner dot
        brush = QBrush(interceptor_color)
        painter.setBrush(brush)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(screen_x, screen_y), 3, 3)
        
        # Draw direction indicator
        if np.linalg.norm(interceptor.velocity) > 0:
            vel = interceptor.velocity
            vel_2d = np.array([vel[0], vel[2]])
            vel_2d = vel_2d / np.linalg.norm(vel_2d) * 6
            pen = QPen(interceptor_color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(
                int(screen_x), int(screen_y),
                int(screen_x + vel_2d[0]), int(screen_y + vel_2d[1])
            )
    
    def _draw_explosion(self, painter, explosion, center_x, center_y, radius, current_time):
        """Draw explosion effect"""
        age = current_time - explosion['time']
        max_age = explosion['max_age']
        progress = age / max_age  # 0.0 to 1.0
        
        if progress >= 1.0:
            return
        
        # Convert 3D position to 2D
        pos_3d = explosion['pos']
        screen_x = center_x + (pos_3d[0] / self.radar_range) * radius
        screen_y = center_y + (pos_3d[2] / self.radar_range) * radius
        
        # Explosion size grows then fades
        if progress < 0.3:
            # Growing phase
            size = progress / 0.3 * 15  # Grow to 15 pixels
            alpha = 255
        else:
            # Fading phase
            size = 15 * (1.0 - (progress - 0.3) / 0.7)
            alpha = int(255 * (1.0 - progress))
        
        # Draw multiple circles for explosion effect
        for i in range(3):
            circle_size = size * (1.0 + i * 0.3)
            circle_alpha = int(alpha * (1.0 - i * 0.3))
            
            # Outer glow (yellow/orange)
            brush = QBrush(QColor(255, 200, 0, circle_alpha // 2))
            painter.setBrush(brush)
            pen = QPen(QColor(255, 150, 0, circle_alpha))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawEllipse(QPointF(screen_x, screen_y), circle_size, circle_size)
            
            # Inner core (white/yellow)
            if i == 0:
                brush = QBrush(QColor(255, 255, 255, circle_alpha))
                painter.setBrush(brush)
                pen = QPen(QColor(255, 255, 0, circle_alpha))
                pen.setWidth(1)
                painter.setPen(pen)
                painter.drawEllipse(QPointF(screen_x, screen_y), circle_size * 0.5, circle_size * 0.5)
    
    def _draw_interception_info(self, painter, width, height):
        """Draw interception time clocks and missile counters"""
        stats = self.simulation.get_statistics()
        
        # Set font for digital clock style
        font = QFont("Courier", 16, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Draw average interception time (digital clock style)
        avg_time = stats.get('avg_interception_time', 0.0)
        if avg_time > 0:
            time_str = f"{avg_time:.1f}ms"
            color = QColor(255, 165, 0) if self.algorithm_type == "old" else QColor(0, 255, 0)
            painter.setPen(QPen(color))
            painter.drawText(10, 30, f"Avg Intercept: {time_str}")
        
        # Draw current interception times for active missiles (top 3)
        current_times = stats.get('current_interception_times', {})
        if current_times:
            sorted_times = sorted(current_times.items(), key=lambda x: x[1], reverse=True)[:3]
            y_offset = 55
            for i, (missile_id, intercept_time) in enumerate(sorted_times):
                time_str = f"{intercept_time:.1f}ms"
                color = QColor(255, 200, 100) if self.algorithm_type == "old" else QColor(100, 255, 100)
                painter.setPen(QPen(color))
                painter.drawText(10, y_offset + i * 20, f"M{i+1}: {time_str}")
        
        # Draw missile interception counter (based on engaged threats)
        missiles_intercepted = stats.get('missiles_intercepted', 0)
        missiles_engaged = stats.get('missiles_engaged', 0)
        missiles_missed = stats.get('missiles_missed', 0)
        
        font_counter = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font_counter)
        counter_color = QColor(255, 165, 0) if self.algorithm_type == "old" else QColor(0, 255, 0)
        painter.setPen(QPen(counter_color))
        counter_text = f"Intercepted: {missiles_intercepted} / {missiles_engaged} (Missed: {missiles_missed})"
        painter.drawText(10, height - 30, counter_text)
        
        # Draw success rate
        success_rate = stats.get('success_rate', 0.0)
        success_color = QColor(255, 100, 100) if success_rate < 90 else QColor(100, 255, 100)
        painter.setPen(QPen(success_color))
        painter.drawText(10, height - 10, f"Success: {success_rate:.1f}%")

    def _draw_legend(self, painter, width, height):
        """Draw legend and title"""
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        # Title (commented out as it's shown in main window)
        # title = "CONVENTIONAL APPROACH" if self.algorithm_type == "old" else "SA+H APPROACH"
        # pen = QPen(QColor(0, 255, 0))
        # painter.setPen(pen)
        # painter.drawText(10, 20, title)
        
        # Legend with phase colors
        y_offset = height - 100
        
        # Phase indicators
        phase_legend = [
            ("Tracing", QColor(255, 255, 0)),      # Yellow
            ("Warning", QColor(255, 165, 0)),     # Orange
            ("Destroy", QColor(255, 0, 0))         # Red
        ]
        
        for i, (phase_name, color) in enumerate(phase_legend):
            # Draw colored dot
            brush = QBrush(color)
            painter.setBrush(brush)
            pen = QPen(color)
            painter.setPen(pen)
            painter.drawEllipse(QPointF(10, y_offset + i * 15), 3, 3)
            
            # Draw text
            pen = QPen(QColor(0, 255, 0))
            painter.setPen(pen)
            painter.drawText(18, y_offset + i * 15 + 4, f"{phase_name} Phase")
        
        # Other elements
        y_offset += 50
        pen = QPen(QColor(0, 255, 0))
        painter.setPen(pen)
        # painter.drawText(10, y_offset, "Orange: Old Interceptors" if self.algorithm_type == "old" else "Green: New Interceptors")
        # painter.drawText(10, y_offset + 15, "Blue: Defense System")
    
    def get_simulation(self):
        """Get simulation engine instance"""
        return self.simulation

