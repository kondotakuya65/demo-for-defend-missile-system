"""
Performance comparison graph widget
Shows latency vs measurements per scan
"""

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush


class PerformanceGraph(QWidget):
    """Graph showing latency vs measurements per scan"""
    
    def __init__(self, algorithm_type: str):
        super().__init__()
        self.algorithm_type = algorithm_type  # "old" or "new"
        self.setMinimumSize(200, 150)
        self.setMaximumHeight(200)
        
        # Data points: (measurements, latency_ms)
        self.data_points = []
        self.max_points = 200  # Keep last 200 points for longer timeline
        
        # Graph bounds (will auto-adjust based on data)
        self.min_measurements = 50
        self.max_measurements = 5000  # Initial max, will auto-expand
        self.min_latency = 1.0  # ms (log scale)
        self.max_latency = 1000.0  # ms (log scale)
        
    def add_data_point(self, measurements: float, latency_ms: float):
        """Add a new data point"""
        self.data_points.append((measurements, latency_ms))
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Draw the graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, QColor(20, 20, 20))
        
        # Graph area (with margins)
        margin_left = 50
        margin_right = 10
        margin_top = 20
        margin_bottom = 30
        graph_x = margin_left
        graph_y = margin_top
        graph_width = width - margin_left - margin_right
        graph_height = height - margin_top - margin_bottom
        
        # Draw axes
        pen = QPen(QColor(100, 100, 100))
        painter.setPen(pen)
        # X axis (bottom)
        painter.drawLine(graph_x, graph_y + graph_height, graph_x + graph_width, graph_y + graph_height)
        # Y axis (left)
        painter.drawLine(graph_x, graph_y, graph_x, graph_y + graph_height)
        
        # Draw axis labels
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(200, 200, 200)))
        
        # Y axis label (latency - log scale)
        painter.save()
        painter.translate(10, graph_y + graph_height / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, "Latency (ms)")
        painter.restore()
        
        # X axis label (measurements)
        painter.drawText(
            int(graph_x + graph_width / 2 - 60),
            int(height - 10),
            "Measurements/Scan"
        )
        
        # Draw Y axis ticks (log scale)
        log_min = np.log10(self.min_latency)
        log_max = np.log10(self.max_latency)
        for i in range(4):
            log_val = log_min + (log_max - log_min) * i / 3
            val = 10 ** log_val
            y = graph_y + graph_height - (i / 3) * graph_height
            painter.drawLine(graph_x - 5, int(y), graph_x, int(y))
            painter.drawText(5, int(y + 5), f"{val:.0f}")
        
        # Calculate actual range from data for X axis ticks
        if self.data_points:
            actual_min = min(m for m, _ in self.data_points)
            actual_max = max(m for m, _ in self.data_points)
            range_padding = (actual_max - actual_min) * 0.1 if actual_max > actual_min else 100
            display_min = max(self.min_measurements, actual_min - range_padding)
            display_max = max(self.max_measurements, actual_max + range_padding)
        else:
            display_min = self.min_measurements
            display_max = self.max_measurements
        
        # Draw X axis ticks
        for i in range(5):
            val = display_min + (display_max - display_min) * i / 4
            x = graph_x + (i / 4) * graph_width
            painter.drawLine(int(x), graph_y + graph_height, int(x), graph_y + graph_height + 5)
            # Format large numbers nicely
            if val >= 1000:
                label = f"{val/1000:.1f}K"
            else:
                label = f"{int(val)}"
            painter.drawText(int(x - 25), int(graph_y + graph_height + 18), label)
        
        # Draw data points and line
        if len(self.data_points) > 1:
            color = QColor(255, 165, 0) if self.algorithm_type == "old" else QColor(0, 255, 0)
            pen = QPen(color, 2)
            painter.setPen(pen)
            
            # Use the same auto-adjusted range for data points
            # (display_min and display_max are calculated above for X axis ticks)
            
            points = []
            for measurements, latency_ms in self.data_points:
                # Convert to log scale for Y
                log_latency = np.log10(max(self.min_latency, min(self.max_latency, latency_ms)))
                log_min = np.log10(self.min_latency)
                log_max = np.log10(self.max_latency)
                
                # Normalize to 0-1 using auto-adjusted range (same as X axis)
                measurement_range = display_max - display_min
                if measurement_range > 0:
                    x_norm = (measurements - display_min) / measurement_range
                else:
                    x_norm = 0.5
                x_norm = max(0.0, min(1.0, x_norm))  # Clamp to 0-1
                y_norm = (log_latency - log_min) / (log_max - log_min)
                
                # Convert to screen coordinates
                x = graph_x + x_norm * graph_width
                y = graph_y + graph_height - y_norm * graph_height
                points.append((int(x), int(y)))
            
            # Draw line
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            
            # Draw points
            brush = QBrush(color)
            painter.setBrush(brush)
            for x, y in points:
                painter.drawEllipse(x - 2, y - 2, 4, 4)
        
        # Draw title
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        title = "CONVENTIONAL" if self.algorithm_type == "old" else "SA+H"
        title_color = QColor(255, 165, 0) if self.algorithm_type == "old" else QColor(0, 255, 0)
        painter.setPen(QPen(title_color))
        painter.drawText(5, 15, title)

