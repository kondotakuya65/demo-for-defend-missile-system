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
    
    def __init__(self, config=None):
        super().__init__()
        self.setMinimumSize(800, 300)
        self.setMaximumHeight(350)
        
        # Load config with defaults
        self.config = config.get("graph", {}) if config else {}
        self.x_axis_auto_scale = self.config.get("x_axis_auto_scale", False)
        self.x_axis_fixed_max = self.config.get("x_axis_fixed_max", None)
        self.y_axis_auto_scale = self.config.get("y_axis_auto_scale", True)
        self.speed_multiplier = self.config.get("speed_multiplier", 100.0)
        self.cycle_duration_min_ms = self.config.get("cycle_duration_min_ms", 10000)
        self.cycle_duration_max_ms = self.config.get("cycle_duration_max_ms", 15000)
        self.time_to_reach_xmax_ms = self.config.get("time_to_reach_xmax_ms", 180000)
        self.y_axis_padding_factor = self.config.get("y_axis_padding_factor", 1.2)
        self.target_steps_per_cycle = self.config.get("target_steps_per_cycle", 300)
        
        # Load scenario-based ratios and multipliers
        self.base_ratio_by_scenario = self.config.get("base_ratio_by_scenario", {
            "single": 1000,
            "wave": 2500,
            "saturation": 8000,
            "custom": 2000
        })
        self.base_x_max_by_scenario = self.config.get("base_x_max_by_scenario", {
            "single": 2000,
            "wave": 5000,
            "saturation": 10000,
            "custom": 4000
        })
        ratio_mult = self.config.get("ratio_multipliers", {})
        self.drone_ratio_multiplier = ratio_mult.get("drone_multiplier", 1.3)
        self.threat_count_ratio_factor = ratio_mult.get("threat_count_factor", 0.15)
        self.zigzag_ratio_multiplier = ratio_mult.get("zigzag_multiplier", 1.4)
        self.min_ratio = ratio_mult.get("min_ratio", 1000.0)
        self.max_ratio = ratio_mult.get("max_ratio", 10000.0)
        
        x_max_mult = self.config.get("x_max_multipliers", {})
        self.threat_count_xmax_factor = x_max_mult.get("threat_count_factor", 0.2)
        self.drone_xmax_multiplier = x_max_mult.get("drone_multiplier", 0.7)
        self.zigzag_xmax_multiplier = x_max_mult.get("zigzag_multiplier", 1.2)
        self.min_x_max = x_max_mult.get("min_x_max", 2000)
        self.max_x_max = x_max_mult.get("max_x_max", 15000)
        
        # Virtual conditions (calculated once at simulation start)
        self.virtual_conditions = None
        self.is_initialized = False
        
        # Step-based cycle management
        self.cycle_start_time_ms = 0.0  # When current cycle started
        self.cycle_duration_ms = random.uniform(self.cycle_duration_min_ms, self.cycle_duration_max_ms)
        self.cycle_count = 0  # Track number of cycles completed
        
        # Step-based progression
        self.total_steps_per_cycle = 0  # Total steps to reach x_max in one cycle
        self.current_step = 0  # Current step index (0 to total_steps_per_cycle)
        self.time_per_step_ms = 0.0  # Real time per step (ms)
        self.last_step_time_ms = 0.0  # Last time we advanced a step
        self.current_x_value = 0.0  # Current x value calculated from step
        
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
        # Calculate ratio (1000-10000x) using config values
        base_ratio = self.base_ratio_by_scenario.get(scenario, 2000)
        
        # Adjust by threat type (drones are harder)
        if threat_type == "drones":
            base_ratio *= self.drone_ratio_multiplier
        
        # Adjust by threat count (more threats = higher ratio)
        threat_multiplier = 1.0 + (threat_count - 1) * self.threat_count_ratio_factor
        ratio = base_ratio * threat_multiplier
        
        # Adjust by movement type (zigzag = more complex = higher ratio)
        if movement_type == "zigzag":
            ratio *= self.zigzag_ratio_multiplier
        
        # Clamp to configured range
        ratio = max(self.min_ratio, min(self.max_ratio, ratio))
        
        # Calculate X-max for 3 minutes (180000 ms)
        # Base X-max varies by scenario complexity (from config)
        base_x_max = self.base_x_max_by_scenario.get(scenario, 4000)
        
        # Adjust by threat count (more threats = more detections)
        x_max = int(base_x_max * (1.0 + (threat_count - 1) * self.threat_count_xmax_factor))
        
        # Adjust by threat type (drones generate fewer reflections)
        if threat_type == "drones":
            x_max = int(x_max * self.drone_xmax_multiplier)
        
        # Adjust by movement type (zigzag = more reflections)
        if movement_type == "zigzag":
            x_max = int(x_max * self.zigzag_xmax_multiplier)
        
        # Clamp X-max to configured range
        x_max = max(self.min_x_max, min(self.max_x_max, x_max))
        
        # Override x_max with config value if provided
        if self.x_axis_fixed_max is not None:
            x_max = self.x_axis_fixed_max
        
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
        # Set initial axis ranges
        self.min_detections = 0
        self.max_detections = x_max  # Fixed x-axis max
        self.min_processing_time = 0.01
        self.max_processing_time = old_target * self.y_axis_padding_factor  # Initial max, will auto-scale if enabled
        
        self.is_initialized = True
        self.cycle_start_time_ms = 0.0
        self.cycle_duration_ms = random.uniform(self.cycle_duration_min_ms, self.cycle_duration_max_ms)
        self.cycle_count = 0
        
        # Calculate step-based parameters for this cycle
        self._calculate_cycle_steps(x_max, self.cycle_duration_ms)
        
        self.update()
    
    def reset_graph(self):
        """Reset graph and initialization"""
        self.is_initialized = False
        self.virtual_conditions = None
        self.cycle_start_time_ms = 0.0
        self.cycle_duration_ms = random.uniform(self.cycle_duration_min_ms, self.cycle_duration_max_ms)
        self.cycle_count = 0
        self.current_step = 0
        self.total_steps_per_cycle = 0
        self.time_per_step_ms = 0.0
        self.last_step_time_ms = 0.0
        self.current_x_value = 0.0
        self.min_detections = 0
        self.max_detections = 5000
        self.update()
    
    def _calculate_cycle_steps(self, x_max: float, cycle_duration_ms: float):
        """
        Calculate step-based parameters for a cycle.
        
        Args:
            x_max: Maximum x value for this cycle
            cycle_duration_ms: Total duration of the cycle in milliseconds
        """
        # Determine total steps: use configurable target for smooth animation
        # Higher number of steps = smoother animation
        # Calculate how many steps we need based on cycle duration
        # Use time_to_reach_xmax_ms as the reference time scale
        if cycle_duration_ms > 0 and self.time_to_reach_xmax_ms > 0:
            # Scale steps based on cycle duration relative to time_to_reach_xmax
            duration_ratio = cycle_duration_ms / self.time_to_reach_xmax_ms
            self.total_steps_per_cycle = max(10, int(self.target_steps_per_cycle * duration_ratio))
        else:
            self.total_steps_per_cycle = self.target_steps_per_cycle
        
        # Calculate time per step (real time, not accelerated)
        if self.total_steps_per_cycle > 0:
            self.time_per_step_ms = cycle_duration_ms / self.total_steps_per_cycle
        else:
            self.time_per_step_ms = cycle_duration_ms
        
        # Reset step tracking
        self.current_step = 0
        self.last_step_time_ms = 0.0
    
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
            self.current_x_value = 0.0
        
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
        
        # Check if cycle should reset
        if cycle_elapsed >= self.cycle_duration_ms:
            # Start new cycle
            self.cycle_count += 1
            self.cycle_start_time_ms = elapsed_time_ms
            self.cycle_duration_ms = random.uniform(self.cycle_duration_min_ms, self.cycle_duration_max_ms)
            # Reset axis ranges for new cycle (x-axis stays fixed)
            x_max = self.virtual_conditions["x_max"]
            self.min_detections = 0
            self.max_detections = x_max  # Fixed x-axis
            self.min_processing_time = 0.01
            self.max_processing_time = self.virtual_conditions["old_target"] * self.y_axis_padding_factor
            # Recalculate steps for new cycle
            self._calculate_cycle_steps(x_max, self.cycle_duration_ms)
            self.current_x_value = 0.0
            cycle_elapsed = 0.0
        
        # Step-based progression with smooth interpolation
        x_max = self.virtual_conditions["x_max"]
        if self.total_steps_per_cycle > 0 and self.time_per_step_ms > 0:
            # Calculate fractional step progress for smooth growth
            fractional_steps = cycle_elapsed / self.time_per_step_ms
            # Clamp to total steps to prevent overflow
            fractional_steps = min(fractional_steps, self.total_steps_per_cycle)
            
            # Use fractional progress for smooth continuous growth
            progress = fractional_steps / self.total_steps_per_cycle
            x_value = x_max * progress
            
            # Store current step (integer) for reference, but use fractional for smoothness
            self.current_step = int(fractional_steps)
        else:
            self.current_step = 0
            x_value = 0
        
        # Ensure x_value never exceeds x_max (safety check)
        x_value = min(x_value, x_max, self.max_detections)
        
        # X-axis: Fixed (no auto-scaling) or auto-scale based on config
        if self.x_axis_auto_scale and x_value > self.max_detections:
            self.max_detections = int(x_value * 1.1)  # 10% padding
        # Otherwise, x-axis stays fixed at x_max
        
        # Y-axis: Auto-scale based on config
        if self.y_axis_auto_scale:
            a_sa, b_sa, c_sa = self.sa_h_coeffs
            a_old, b_old, c_old = self.old_coeffs
            
            sa_h_y = a_sa * x_value * x_value + b_sa * x_value + c_sa
            old_y = a_old * x_value * x_value + b_old * x_value + c_old
            
            max_time = max(sa_h_y, old_y)
            if max_time > self.max_processing_time:
                self.max_processing_time = max_time * self.y_axis_padding_factor
        
        # Store current x_value for drawing (for compatibility with paintEvent)
        self.current_x_value = x_value
        
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
            # Use step-based current_x_value (calculated in add_data_point)
            # This ensures we never exceed x_max
            current_x = getattr(self, 'current_x_value', 0)
            x_max = self.virtual_conditions["x_max"]
            
            # Safety: ensure current_x never exceeds x_max or max_detections
            current_x = min(current_x, x_max, self.max_detections)
            
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
        if not coeffs or max_x <= min_x or max_y <= min_y or graph_width <= 0:
            return
        
        # Safety: clamp current_x to never exceed max_x
        current_x = min(current_x, max_x)
        
        a, b, c = coeffs
        
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        from PyQt6.QtCore import QLineF, QPointF
        points = []
        
        # Calculate fixed x-axis increment per pixel at start
        # This ensures consistent step size regardless of current_x
        x_axis_range = max_x - min_x
        x_increment_per_pixel = x_axis_range / graph_width if graph_width > 0 else 0
        
        # Draw curve from 0 to current_x using fixed increment
        # Iterate through pixel positions and calculate corresponding x values
        for pixel_pos in range(int(graph_width) + 1):
            # Calculate x value for this pixel position
            x_val = min_x + pixel_pos * x_increment_per_pixel
            
            # Stop drawing if we've exceeded current_x
            if x_val > current_x:
                break
            
            # Ensure x_val doesn't exceed current_x or max_x (safety check)
            x_val = min(x_val, current_x, max_x)
            
            # Calculate y value using quadratic equation: y = a*x² + b*x + c
            y_val = a * x_val * x_val + b * x_val + c
            y_val = max(min_y, min(max_y, y_val))  # Clamp to valid range
            
            # Map to screen coordinates
            x_norm = (x_val - min_x) / x_axis_range if x_axis_range > 0 else 0.0
            x_norm = max(0.0, min(1.0, x_norm))  # Clamp to [0, 1]
            
            y_norm = (y_val - min_y) / (max_y - min_y) if max_y > min_y else 0.0
            y_norm = max(0.0, min(1.0, y_norm))  # Clamp to [0, 1]
            
            x_screen = graph_x + x_norm * graph_width
            y_screen = graph_y + graph_height - y_norm * graph_height  # Flip Y axis
            
            # Ensure screen coordinates are within bounds
            x_screen = max(graph_x, min(graph_x + graph_width, x_screen))
            y_screen = max(graph_y, min(graph_y + graph_height, y_screen))
            
            points.append((x_screen, y_screen))
        
        # Draw lines connecting points (only if we have at least 2 points)
        if len(points) < 2:
            return
        
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            
            # Clamp line endpoints to graph bounds
            x1 = max(graph_x, min(graph_x + graph_width, x1))
            x2 = max(graph_x, min(graph_x + graph_width, x2))
            y1 = max(graph_y, min(graph_y + graph_height, y1))
            y2 = max(graph_y, min(graph_y + graph_height, y2))
            
            line = QLineF(QPointF(x1, y1), QPointF(x2, y2))
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
