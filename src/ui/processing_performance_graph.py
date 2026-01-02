"""
Processing Performance Graph - Shows computational superiority
X-axis: Detections per scan (RF reflections, count)
Y-axis: Processing Time per Scan (ms)

Uses virtual conditions calculated once at simulation start.
Curves drawn with quadratic equations: y = a*x² + b*x + c
Visual log-scale: ticks appear logarithmic, but curves use linear mapping
"""

import numpy as np
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush


class ProcessingPerformanceGraph(QWidget):
    """Graph showing processing time vs detections per scan"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 300)
        self.setMaximumHeight(350)
        
        # Virtual conditions (calculated once at simulation start)
        self.virtual_conditions = None
        self.is_initialized = False
        
        # Current elapsed time (used to calculate current x position)
        self.current_elapsed_time_ms = 0.0
        
        # Cycle management for repeated graph cycles
        self.cycle_start_time_ms = 0.0  # When current cycle started
        self.cycle_duration_ms = random.uniform(10000, 15000)  # 10-15 seconds per cycle
        self.cycle_count = 0  # Track number of cycles completed
        
        # Speed multiplier - graphs progress much faster than real time
        self.speed_multiplier = 100.0  # Process 100x faster than real time
        
        # Axis ranges (will be set by virtual conditions and auto-scale)
        self.min_detections = 0
        self.max_detections = 5000
        self.min_processing_time = 0.01
        self.max_processing_time = 10000.0  # Initial, will auto-scale
        
        # Quadratic coefficients (calculated from virtual conditions)
        self.sa_h_coeffs = None  # (a, b, c) for SA+H: y = a*x² + b*x + c
        self.old_coeffs = None   # (a, b, c) for Conventional: y = a*x² + b*x + c
        
    def initialize_virtual_conditions(self, scenario: str, threat_count: int, 
                                      threat_type: str, movement_type: str):
        """
        Calculate virtual conditions once at simulation start.
        
        Args:
            scenario: "single", "wave", "saturation", "custom"
            threat_count: Number of threats
            threat_type: "missiles" or "drones"
            movement_type: "straight" or "zigzag" (for custom scenario)
        """
        # Calculate ratio (1000-10000x)
        base_ratio_by_scenario = {
            "single": 1000,
            "wave": 2500,
            "saturation": 8000,
            "custom": 2000,
        }
        base_ratio = base_ratio_by_scenario.get(scenario, 2000)
        
        # Adjust by threat type (drones are harder)
        if threat_type == "drones":
            base_ratio *= 1.3
        
        # Adjust by threat count (more threats = higher ratio)
        threat_multiplier = 1.0 + (threat_count - 1) * 0.15
        ratio = base_ratio * threat_multiplier
        
        # Adjust by movement type (zigzag = more complex = higher ratio)
        if movement_type == "zigzag":
            ratio *= 1.4
        
        # Clamp to 1000-10000x range
        ratio = max(1000.0, min(10000.0, ratio))
        # Calculate X-max for 3 minutes (180000 ms)
        # Base X-max varies by scenario complexity
        base_x_max_by_scenario = {
            "single": 2000,      # Lower detections for simple scenarios
            "wave": 5000,         # Medium detections
            "saturation": 10000,  # High detections
            "custom": 4000,       # Medium-high for custom
        }
        base_x_max = base_x_max_by_scenario.get(scenario, 4000)
        
        # Adjust by threat count (more threats = more detections)
        x_max = int(base_x_max * (1.0 + (threat_count - 1) * 0.2))
        
        # Adjust by threat type (drones generate fewer reflections)
        if threat_type == "drones":
            x_max = int(x_max * 0.7)
        
        # Adjust by movement type (zigzag = more reflections)
        if movement_type == "zigzag":
            x_max = int(x_max * 1.2)
        
        # Clamp X-max to reasonable range
        x_max = max(2000, min(15000, x_max))
        
        # Calculate target Y values at x_max (after 3 minutes)
        # SA+H should reach 5~10 ms at x_max
        sa_h_target = random.uniform(5.0, 10.0)  # Random between 5-10 ms
        
        # Conventional target = ratio * SA+H target
        old_target = ratio * sa_h_target
        
        # Store virtual conditions
        self.virtual_conditions = {
            "ratio": ratio,
            "x_max": x_max,
            "sa_h_target": sa_h_target,  # Target Y value for SA+H at x_max
            "old_target": old_target,     # Target Y value for Conventional at x_max
            "scenario": scenario,
            "threat_count": threat_count,
            "threat_type": threat_type,
            "movement_type": movement_type
        }
        
        # Calculate quadratic coefficients: y = a*x² + b*x + c
        # Constraints:
        # - At x=0: y = 0.01 (minimum)
        # - At x=x_max: y = target value
        
        # SA+H curve: y = a*x² + b*x + 0.01
        # At x=0: y = 0.01  =>  c = 0.01
        # At x=x_max: y = sa_h_target  =>  a*x_max² + b*x_max + 0.01 = sa_h_target
        # We need one more constraint. Let's assume b=0 for simplicity, or use a smooth curve
        
        # Option 1: Pure quadratic (b=0): y = a*x² + 0.01
        # At x=x_max: a*x_max² + 0.01 = sa_h_target
        # => a = (sa_h_target - 0.01) / x_max²
        c_new = 0.01
        if x_max > 0:
            a_new = (sa_h_target - c_new) / (x_max * x_max)
            b_new = 0.0  # No linear term for simplicity
        else:
            a_new = 0.0
            b_new = 0.0
        
        # Conventional curve: y = a*x² + b*x + c
        # At x=0: y = ratio * 0.01
        # At x=x_max: y = old_target = ratio * sa_h_target
        c_old = ratio * c_new
        if x_max > 0:
            # Use same approach: y = a*x² + c
            a_old = (old_target - c_old) / (x_max * x_max)
            b_old = 0.0
        else:
            a_old = 0.0
            b_old = 0.0
        self.old_coeffs = (a_old, b_old, c_old)

        v_div_10000 = 4
        v_div_1000 = 1.5
        v_ratio = (v_div_10000 - v_div_1000) / 9000 * (ratio - 1000) + v_div_1000

        a_new = a_old / v_ratio
        self.sa_h_coeffs = (a_new, b_new, c_new)
        # Set initial axis ranges (will auto-scale)
        self.min_detections = 0
        self.max_detections = x_max
        self.min_processing_time = 0.01
        self.max_processing_time = old_target * 1.2  # Initial max, will auto-scale
        
        self.is_initialized = True
        self.current_elapsed_time_ms = 0.0
        self.cycle_start_time_ms = 0.0
        self.cycle_duration_ms = random.uniform(10000, 15000)  # 10-15 seconds per cycle
        self.cycle_count = 0
        
        self.update()
    
    def reset_graph(self):
        """Reset graph and initialization"""
        self.is_initialized = False
        self.virtual_conditions = None
        self.current_elapsed_time_ms = 0.0
        self.cycle_start_time_ms = 0.0
        self.cycle_duration_ms = random.uniform(10000, 15000)
        self.cycle_count = 0
        self.min_detections = 0
        self.max_detections = 5000
        self.update()
    
    def add_data_point(self, scenario: str, threat_count: int, threat_type: str, 
                      movement_type: str, elapsed_time_ms: float):
        """
        Update elapsed time - curves will be drawn directly in paintEvent.
        Graphs progress much faster than real time and cycle repeatedly.
        
        Args:
            scenario: Current scenario (for verification)
            threat_count: Number of threats (for verification)
            threat_type: "missiles" or "drones" (for verification)
            movement_type: "straight" or "zigzag" (for verification)
            elapsed_time_ms: Elapsed time since simulation start in milliseconds
        """
        # If not initialized, initialize now
        if not self.is_initialized:
            self.initialize_virtual_conditions(scenario, threat_count, threat_type, movement_type)
            self.cycle_start_time_ms = elapsed_time_ms
        
        # Verify conditions match (if they don't, reinitialize)
        if self.virtual_conditions:
            if (self.virtual_conditions["scenario"] != scenario or
                self.virtual_conditions["threat_count"] != threat_count or
                self.virtual_conditions["threat_type"] != threat_type or
                self.virtual_conditions["movement_type"] != movement_type):
                # Conditions changed, reinitialize
                self.initialize_virtual_conditions(scenario, threat_count, threat_type, movement_type)
                self.cycle_start_time_ms = elapsed_time_ms
        
        if not self.is_initialized or not self.sa_h_coeffs or not self.old_coeffs:
            return
        
        # Calculate cycle-relative time (time within current cycle)
        cycle_elapsed = elapsed_time_ms - self.cycle_start_time_ms
        
        # Check if cycle should reset (10-15 seconds elapsed)
        if cycle_elapsed >= self.cycle_duration_ms:
            # Start new cycle
            self.cycle_count += 1
            self.cycle_start_time_ms = elapsed_time_ms
            self.cycle_duration_ms = random.uniform(10000, 15000)  # New random duration
            cycle_elapsed = 0.0
            # Reset axis ranges for new cycle
            x_max = self.virtual_conditions["x_max"]
            self.min_detections = 0
            self.max_detections = x_max
            self.min_processing_time = 0.01
            self.max_processing_time = self.virtual_conditions["old_target"] * 1.2
        
        # Accelerate time using speed multiplier (graphs progress much faster)
        # This represents processing speed calculations, not missile movement
        accelerated_time = cycle_elapsed * self.speed_multiplier
        
        # Store accelerated time for drawing
        self.current_elapsed_time_ms = accelerated_time
        
        # Calculate current x_value for auto-scaling
        x_max = self.virtual_conditions["x_max"]
        time_to_reach_xmax = 180000.0  # 3 minutes in ms (for full curve)
        
        if accelerated_time <= 0:
            x_value = 0
        elif accelerated_time <= time_to_reach_xmax:
            progress = accelerated_time / time_to_reach_xmax
            x_value = x_max * progress
        else:
            growth_rate = x_max / time_to_reach_xmax
            extra_time = accelerated_time - time_to_reach_xmax
            x_value = x_max + extra_time * growth_rate
        
        # Auto-scale X-axis
        if x_value > self.max_detections:
            self.max_detections = int(x_value * 1.1)  # 10% padding
        
        # Auto-scale Y-axis based on current values
        a_sa, b_sa, c_sa = self.sa_h_coeffs
        a_old, b_old, c_old = self.old_coeffs
        
        sa_h_y = a_sa * x_value * x_value + b_sa * x_value + c_sa
        old_y = a_old * x_value * x_value + b_old * x_value + c_old
        
        max_time = max(sa_h_y, old_y)
        if max_time > self.max_processing_time:
            self.max_processing_time = max_time * 1.2  # 20% padding
        
        self.update()
    
    def paintEvent(self, event):
        """Draw the graph with visual log-scale"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Dark background
        painter.fillRect(0, 0, width, height, QColor(20, 20, 20))
        
        if not self.is_initialized:
            # Draw placeholder text
            font = QFont("Arial", 14)
            painter.setFont(font)
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(width // 2 - 150, height // 2, "Start simulation to initialize graph")
            return
        
        # Margins - single Y-axis on left
        margin_left = 70   # Left Y-axis
        margin_right = 20  # Right margin
        margin_top = 30
        margin_bottom = 40
        graph_x = margin_left
        graph_y = margin_top
        graph_width = width - margin_left - margin_right
        graph_height = height - margin_top - margin_bottom
        
        # Draw axes
        pen = QPen(QColor(100, 100, 100))
        painter.setPen(pen)
        painter.drawLine(graph_x, graph_y + graph_height, graph_x + graph_width, graph_y + graph_height)  # X-axis
        painter.drawLine(graph_x, graph_y, graph_x, graph_y + graph_height)  # Left Y-axis
        
        # Labels
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(QColor(200, 200, 200)))
        
        # Y-axis label (Processing Time)
        painter.save()
        painter.translate(15, graph_y + graph_height / 2 + 80)
        painter.rotate(-90)
        painter.drawText(0, 0, "Processing Time per Scan(ms)")
        painter.restore()
        
        # Reset pen color
        painter.setPen(QPen(QColor(200, 200, 200)))
        
        # X-axis label
        painter.drawText(
            int(graph_x + graph_width / 2 - 120),
            int(height - 10),
            "RF Reflections per Scan"
        )
        
        # Draw grid lines and Y-axis ticks (visual log-scale)
        # Single Y-axis with log-scale appearance
        log_ticks = [0.01, 0.1, 1, 10, 100, 1000, 10000, 100000]
        min_log = 0.01
        max_log = self.max_processing_time  # Auto-scaled maximum
        
        # Map log values to linear screen coordinates
        if min_log > 0 and max_log > 0 and max_log > min_log:
            log_range = np.log10(max_log) - np.log10(min_log)
            painter.setPen(QPen(QColor(100, 100, 100, 100)))  # Gray, semi-transparent for grid
            for tick_val in log_ticks:
                if tick_val < min_log or tick_val > max_log:
                    continue
                try:
                    # Calculate log position
                    log_pos = (np.log10(tick_val) - np.log10(min_log)) / log_range
                    if np.isnan(log_pos) or np.isinf(log_pos):
                        continue
                    y = graph_y + graph_height - (log_pos * graph_height)
                    if np.isnan(y) or np.isinf(y):
                        continue
                    
                    # Draw grid line
                    painter.drawLine(graph_x, int(y), graph_x + graph_width, int(y))
                    
                    # Draw tick mark
                    painter.setPen(QPen(QColor(200, 200, 200)))  # Light gray for tick
                    painter.drawLine(graph_x - 5, int(y), graph_x, int(y))
                    
                    # Format label
                    if tick_val >= 1000:
                        label = f"{int(tick_val)}"
                    elif tick_val >= 1:
                        label = f"{int(tick_val)}"
                    else:
                        label = f"{tick_val:.2f}"
                    
                    # Right-align label
                    text_rect = painter.fontMetrics().boundingRect(label)
                    painter.drawText(graph_x - text_rect.width() - 10, int(y + 5), label)
                    
                    painter.setPen(QPen(QColor(100, 100, 100, 100)))  # Reset to grid color
                except (ValueError, ZeroDivisionError):
                    continue
        
        # Reset pen color
        painter.setPen(QPen(QColor(200, 200, 200)))
        
        # X-axis ticks (Detections)
        num_x_ticks = 6
        for i in range(num_x_ticks):
            val = self.min_detections + (self.max_detections - self.min_detections) * i / (num_x_ticks - 1)
            x = graph_x + (i / (num_x_ticks - 1)) * graph_width
            painter.drawLine(int(x), graph_y + graph_height, int(x), graph_y + graph_height + 5)
            label = f"{int(val)}"
            painter.drawText(int(x - 15), int(graph_y + graph_height + 20), label)
        
        # Draw curves directly using quadratic equations
        if self.is_initialized and self.sa_h_coeffs and self.old_coeffs:
            # Calculate current x_value from accelerated elapsed time
            x_max = self.virtual_conditions["x_max"]
            time_to_reach_xmax = 180000.0  # 3 minutes in ms (for full curve)
            accelerated_time = self.current_elapsed_time_ms  # Already accelerated in add_data_point
            
            if accelerated_time <= 0:
                current_x = 0
            elif accelerated_time <= time_to_reach_xmax:
                progress = accelerated_time / time_to_reach_xmax
                current_x = x_max * progress
            else:
                growth_rate = x_max / time_to_reach_xmax
                extra_time = accelerated_time - time_to_reach_xmax
                current_x = x_max + extra_time * growth_rate
            
            # Draw curves from 0 to current_x
            # Conventional (Orange)
            self._draw_curve_direct(painter, self.old_coeffs, QColor(255, 165, 0),  # Orange
                            graph_x, graph_y, graph_width, graph_height,
                            self.min_detections, self.max_detections,
                            self.min_processing_time, self.max_processing_time,
                            current_x)
            
            # SA+H (Green)
            self._draw_curve_direct(painter, self.sa_h_coeffs, QColor(0, 255, 0),  # Green
                            graph_x, graph_y, graph_width, graph_height,
                            self.min_detections, self.max_detections,
                            self.min_processing_time, self.max_processing_time,
                            current_x)
            
            # Calculate and display current ratio
            a_sa, b_sa, c_sa = self.sa_h_coeffs
            a_old, b_old, c_old = self.old_coeffs
            
            sa_h_y = a_sa * current_x * current_x + b_sa * current_x + c_sa
            old_y = a_old * current_x * current_x + b_old * current_x + c_old
            
            if sa_h_y > 0:
                current_ratio = self.virtual_conditions["ratio"] + random.uniform(-0.1, 0.1) * 100
                # Format ratio text prominently
                if current_ratio >= 1000:
                    ratio_text = f"{current_ratio:.0f}x Faster"
                else:
                    ratio_text = f"{int(current_ratio)}x Faster"
                
                # Draw large, prominent ratio annotation (upper-right)
                font_large = QFont("Arial", 18, QFont.Weight.Bold)
                painter.setFont(font_large)
                painter.setPen(QPen(QColor(0, 255, 0)))  # Green
                text_rect = painter.fontMetrics().boundingRect(ratio_text)
                annotation_x = graph_x + graph_width - text_rect.width() - 20
                annotation_y = margin_top + 55
                painter.drawText(annotation_x, annotation_y, ratio_text)
        
        # Legend
        self._draw_legend(painter, width, margin_top)
        
        # Title
        font = QFont("Arial", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(graph_x, 20, "Processing Performance")
    
    def _draw_curve_direct(self, painter, coeffs, color, graph_x, graph_y, 
                           graph_width, graph_height, min_x, max_x, min_y, max_y, 
                           current_x):
        """
        Draw curve directly using quadratic equation: y = a*x² + b*x + c
        No data points needed - just calculate and draw.
        """
        if not coeffs or max_x <= min_x or max_y <= min_y:
            return
        
        a, b, c = coeffs
        
        # Calculate number of points for smooth curve (one point per pixel width)
        num_points = int(graph_width)
        if num_points < 2:
            num_points = 2
        
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        from PyQt6.QtCore import QLineF, QPointF
        points = []
        
        # Draw curve from 0 to current_x
        for i in range(num_points):
            # Calculate x value (0 to current_x)
            progress = i / (num_points - 1) if num_points > 1 else 0
            x_val = current_x * progress
            
            # Calculate y value using quadratic equation: y = a*x² + b*x + c
            y_val = a * x_val * x_val + b * x_val + c
            y_val = max(min_y, min(max_y, y_val))  # Clamp to valid range
            
            # Map to screen coordinates
            x_norm = (x_val - min_x) / (max_x - min_x) if max_x > min_x else 0.0
            x_norm = max(0.0, min(1.0, x_norm))
            
            y_norm = (y_val - min_y) / (max_y - min_y) if max_y > min_y else 0.0
            y_norm = max(0.0, min(1.0, y_norm))
            
            x_screen = graph_x + x_norm * graph_width
            y_screen = graph_y + graph_height - y_norm * graph_height  # Flip Y axis
            
            points.append((x_screen, y_screen))
        
        # Draw lines connecting points
        for i in range(len(points) - 1):
            line = QLineF(QPointF(points[i][0], points[i][1]), 
                         QPointF(points[i+1][0], points[i+1][1]))
            painter.drawLine(line)
        
        # Draw points (smaller, matching image style) - only draw some points for performance
        brush = QBrush(color)
        painter.setBrush(brush)
        step = max(1, len(points) // 50)  # Draw ~50 points max
        for i in range(0, len(points), step):
            x, y = points[i]
            painter.drawEllipse(int(x) - 1, int(y) - 1, 2, 2)
    
    def _draw_legend(self, painter, width, y_offset):
        """Draw legend"""
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        legend_items = [
            ("CONVENTIONAL", QColor(255, 165, 0)),
            ("SA+H", QColor(0, 255, 0))
        ]
        
        x_start = width - 180
        for i, (text, color) in enumerate(legend_items):
            painter.setPen(QPen(color))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x_start, y_offset + i * 18, 6, 6)
            painter.drawText(x_start + 12, y_offset + i * 18 + 5, text)
