"""
Average Destroy Time over time graph widget
Shows average destroy time over time for both algorithms
"""

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush


class DestroyTimeGraph(QWidget):
    """Graph showing average destroy time over time for both algorithms"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 200)
        self.setMaximumHeight(250)
        
        # Data points: (time_ms, avg_destroy_time_ms) for each algorithm
        self.old_data_points = []  # Conventional approach
        self.new_data_points = []   # SA+H approach
        self.max_points = 500  # Keep more points for longer timeline
        
        # Graph bounds
        self.min_time = 0.0      # ms
        self.max_time = 30000.0  # ms (30 seconds)
        self.min_destroy_time = 0.0    # ms
        self.max_destroy_time = 2000.0 # ms (2 seconds) - will auto-adjust
        
    def reset_graph(self):
        """Clear all graph data"""
        self.old_data_points = []
        self.new_data_points = []
        self.min_time = 0.0
        self.max_time = 30000.0
        self.min_destroy_time = 0.0
        self.max_destroy_time = 2000.0
        self.update()
    
    def add_data_point(self, old_destroy_time: float, new_destroy_time: float, elapsed_time_ms: float):
        """Add new data points for both algorithms
        
        Args:
            old_destroy_time: Average destroy time in ms for conventional approach
            new_destroy_time: Average destroy time in ms for SA+H approach
            elapsed_time_ms: Elapsed time since simulation start in milliseconds
        """
        self.old_data_points.append((elapsed_time_ms, old_destroy_time))
        self.new_data_points.append((elapsed_time_ms, new_destroy_time))
        
        # Auto-adjust time range to create sliding window
        if self.old_data_points or self.new_data_points:
            all_times = [t for t, _ in self.old_data_points + self.new_data_points]
            if all_times:
                current_max_time = max(all_times)
                # Create sliding window: show last 30 seconds of data
                window_size = 30000.0  # 30 seconds window
                self.min_time = max(0.0, current_max_time - window_size)
                self.max_time = max(30000.0, current_max_time)
        
        # Auto-adjust destroy time range based on data
        all_destroy_times = [d for _, d in self.old_data_points + self.new_data_points if d > 0]
        if all_destroy_times:
            max_destroy = max(all_destroy_times)
            self.max_destroy_time = max(2000.0, max_destroy * 1.2)  # Add 20% padding
        
        # Prune points that are outside the visible time window
        self.old_data_points = [(t, d) for t, d in self.old_data_points if t >= self.min_time]
        self.new_data_points = [(t, d) for t, d in self.new_data_points if t >= self.min_time]
        
        # Also limit by max_points to prevent memory issues
        if len(self.old_data_points) > self.max_points:
            self.old_data_points = self.old_data_points[-self.max_points:]
        if len(self.new_data_points) > self.max_points:
            self.new_data_points = self.new_data_points[-self.max_points:]
        
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Draw the merged comparison graph"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.fillRect(0, 0, width, height, QColor(20, 20, 20))
        
        # Graph area (with margins)
        margin_left = 60
        margin_right = 10
        margin_top = 30
        margin_bottom = 40
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
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(QColor(200, 200, 200)))
        
        # Y axis label (destroy time)
        painter.save()
        painter.translate(10, graph_y + graph_height / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, "Avg Destroy Time (ms)")
        painter.restore()
        
        # X axis label (time)
        painter.drawText(
            int(graph_x + graph_width / 2 - 30),
            int(height - 10),
            "Time (ms)"
        )
        
        # Draw Y axis ticks (destroy time - log scale for better visualization)
        # Use linear scale but auto-adjust based on max_destroy_time
        tick_count = 5
        for i in range(tick_count + 1):
            val = (self.max_destroy_time - self.min_destroy_time) * i / tick_count
            y = graph_y + graph_height - (i / tick_count) * graph_height
            painter.drawLine(graph_x - 5, int(y), graph_x, int(y))
            # Format nicely
            if val >= 1000:
                label = f"{val/1000:.1f}s"
            else:
                label = f"{int(val)}ms"
            painter.drawText(5, int(y + 5), label)
        
        # Draw X axis ticks (time)
        for i in range(6):
            val = self.min_time + (self.max_time - self.min_time) * i / 5
            x = graph_x + (i / 5) * graph_width
            painter.drawLine(int(x), graph_y + graph_height, int(x), graph_y + graph_height + 5)
            # Format time nicely
            if val >= 1000:
                label = f"{val/1000:.1f}s"
            else:
                label = f"{int(val)}ms"
            painter.drawText(int(x - 20), int(graph_y + graph_height + 20), label)
        
        # Draw curves
        # Conventional approach (orange)
        if len(self.old_data_points) > 1:
            self._draw_curve(painter, self.old_data_points, QColor(255, 165, 0), graph_x, graph_y, graph_width, graph_height)
        
        # SA+H approach (green)
        if len(self.new_data_points) > 1:
            self._draw_curve(painter, self.new_data_points, QColor(0, 255, 0), graph_x, graph_y, graph_width, graph_height)
        
        # Draw legend
        self._draw_legend(painter, width, margin_top)
        
        # Draw title
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(graph_x, 20, "Average Destroy Time Over Time")
    
    def _draw_curve(self, painter, data_points, color, graph_x, graph_y, graph_width, graph_height):
        """Draw a curve for one algorithm"""
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        points = []
        for time_ms, destroy_time in data_points:
            # Normalize to 0-1
            time_norm = (time_ms - self.min_time) / (self.max_time - self.min_time) if self.max_time > self.min_time else 0.5
            destroy_norm = (destroy_time - self.min_destroy_time) / (self.max_destroy_time - self.min_destroy_time) if self.max_destroy_time > self.min_destroy_time else 0.5
            
            # Clamp to valid range
            time_norm = max(0.0, min(1.0, time_norm))
            destroy_norm = max(0.0, min(1.0, destroy_norm))
            
            # Convert to screen coordinates
            x = graph_x + time_norm * graph_width
            y = graph_y + graph_height - destroy_norm * graph_height
            points.append((int(x), int(y)))
        
        # Draw line
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Draw points (smaller, less frequent)
        brush = QBrush(color)
        painter.setBrush(brush)
        for i in range(0, len(points), max(1, len(points) // 20)):  # Draw every 20th point
            x, y = points[i]
            painter.drawEllipse(x - 2, y - 2, 4, 4)
    
    def _draw_legend(self, painter, width, top):
        """Draw legend showing algorithm names"""
        font = QFont("Arial", 9)
        painter.setFont(font)
        
        legend_x = width - 200
        legend_y = top + 5
        
        # Conventional
        painter.setPen(QPen(QColor(255, 165, 0), 2))
        painter.drawLine(legend_x, legend_y, legend_x + 30, legend_y)
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(legend_x + 35, legend_y + 5, "CONVENTIONAL")
        
        # SA+H
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawLine(legend_x, legend_y + 20, legend_x + 30, legend_y + 20)
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(legend_x + 35, legend_y + 25, "SA+H")

