"""
Performance Metrics Panel
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush


class MetricsPanel(QWidget):
    """Performance metrics display panel"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """Initialize metrics panel UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # CPU Usage Group
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout()
        
        # Old Algorithm CPU
        old_cpu_layout = QHBoxLayout()
        old_cpu_layout.addWidget(QLabel("Old:"))
        self.old_cpu_bar = QProgressBar()
        self.old_cpu_bar.setMinimum(0)
        self.old_cpu_bar.setMaximum(100)
        self.old_cpu_bar.setValue(0)
        self.old_cpu_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ff8800;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #ff8800;
            }
        """)
        old_cpu_layout.addWidget(self.old_cpu_bar)
        self.old_cpu_label = QLabel("0%")
        self.old_cpu_label.setMinimumWidth(40)
        old_cpu_layout.addWidget(self.old_cpu_label)
        cpu_layout.addLayout(old_cpu_layout)
        
        # New Algorithm CPU
        new_cpu_layout = QHBoxLayout()
        new_cpu_layout.addWidget(QLabel("New:"))
        self.new_cpu_bar = QProgressBar()
        self.new_cpu_bar.setMinimum(0)
        self.new_cpu_bar.setMaximum(100)
        self.new_cpu_bar.setValue(0)
        self.new_cpu_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00ff00;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
            }
        """)
        new_cpu_layout.addWidget(self.new_cpu_bar)
        self.new_cpu_label = QLabel("0%")
        self.new_cpu_label.setMinimumWidth(40)
        new_cpu_layout.addWidget(self.new_cpu_label)
        cpu_layout.addLayout(new_cpu_layout)
        
        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)
        
        # Response Time Group (Enhanced)
        response_group = QGroupBox("Response Time")
        response_layout = QVBoxLayout()
        
        # Total response time
        self.old_response_label = QLabel("Old: --")
        self.old_response_label.setStyleSheet("color: #ff8800; font-weight: bold;")
        response_layout.addWidget(self.old_response_label)
        
        self.new_response_label = QLabel("New: --")
        self.new_response_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        response_layout.addWidget(self.new_response_label)
        
        # Phase-specific response times
        response_layout.addWidget(QLabel("Per Phase:"))
        
        self.old_phase_times_label = QLabel("Tracing: -- | Warning: -- | Destroy: --")
        self.old_phase_times_label.setStyleSheet("color: #ff8800; font-size: 9px;")
        response_layout.addWidget(self.old_phase_times_label)
        
        self.new_phase_times_label = QLabel("Tracing: -- | Warning: -- | Destroy: --")
        self.new_phase_times_label.setStyleSheet("color: #00ff00; font-size: 9px;")
        response_layout.addWidget(self.new_phase_times_label)
        
        response_group.setLayout(response_layout)
        layout.addWidget(response_group)
        
        # Success Rate Group (Enhanced with progress bars)
        success_group = QGroupBox("Success Rate")
        success_layout = QVBoxLayout()
        
        # Old Algorithm Success Rate
        old_success_layout = QHBoxLayout()
        old_success_layout.addWidget(QLabel("Old:"))
        self.old_success_bar = QProgressBar()
        self.old_success_bar.setMinimum(0)
        self.old_success_bar.setMaximum(100)
        self.old_success_bar.setValue(0)
        self.old_success_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ff8800;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #ff8800;
            }
        """)
        old_success_layout.addWidget(self.old_success_bar)
        self.old_success_label = QLabel("--")
        self.old_success_label.setMinimumWidth(40)
        self.old_success_label.setStyleSheet("color: #ff8800;")
        old_success_layout.addWidget(self.old_success_label)
        success_layout.addLayout(old_success_layout)
        
        # New Algorithm Success Rate
        new_success_layout = QHBoxLayout()
        new_success_layout.addWidget(QLabel("New:"))
        self.new_success_bar = QProgressBar()
        self.new_success_bar.setMinimum(0)
        self.new_success_bar.setMaximum(100)
        self.new_success_bar.setValue(0)
        self.new_success_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #00ff00;
                border-radius: 3px;
                text-align: center;
                background-color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
            }
        """)
        new_success_layout.addWidget(self.new_success_bar)
        self.new_success_label = QLabel("--")
        self.new_success_label.setMinimumWidth(40)
        self.new_success_label.setStyleSheet("color: #00ff00;")
        new_success_layout.addWidget(self.new_success_label)
        success_layout.addLayout(new_success_layout)
        
        success_group.setLayout(success_layout)
        layout.addWidget(success_group)
        
        # Interceptors Used Group
        interceptor_group = QGroupBox("Interceptors Used")
        interceptor_layout = QVBoxLayout()
        
        self.old_interceptor_label = QLabel("Old: 0")
        self.old_interceptor_label.setStyleSheet("color: #ff8800;")
        interceptor_layout.addWidget(self.old_interceptor_label)
        
        self.new_interceptor_label = QLabel("New: 0")
        self.new_interceptor_label.setStyleSheet("color: #00ff00;")
        interceptor_layout.addWidget(self.new_interceptor_label)
        
        interceptor_group.setLayout(interceptor_layout)
        layout.addWidget(interceptor_group)
        
        layout.addStretch()
        
        # Apply styling
        self.apply_styling()
        
    def apply_styling(self):
        """Apply styling to metrics panel"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                font-size: 11px;
            }
        """)
        
    def update_cpu_usage(self, old_cpu, new_cpu):
        """Update CPU usage displays"""
        self.old_cpu_bar.setValue(int(old_cpu))
        self.old_cpu_label.setText(f"{int(old_cpu)}%")
        self.new_cpu_bar.setValue(int(new_cpu))
        self.new_cpu_label.setText(f"{int(new_cpu)}%")
        
    def update_response_time(self, old_time, new_time, old_phase_times=None, new_phase_times=None):
        """Update response time displays"""
        self.old_response_label.setText(f"Old: {old_time:.1f}ms")
        self.new_response_label.setText(f"New: {new_time:.1f}ms")
        
        # Update phase-specific times
        if old_phase_times:
            tracing = old_phase_times.get('Tracing', 0.0)
            warning = old_phase_times.get('Warning', 0.0)
            destroy = old_phase_times.get('Destroy', 0.0)
            self.old_phase_times_label.setText(
                f"Tracing: {tracing:.1f}ms | Warning: {warning:.1f}ms | Destroy: {destroy:.1f}ms"
            )
        else:
            self.old_phase_times_label.setText("Tracing: -- | Warning: -- | Destroy: --")
        
        if new_phase_times:
            tracing = new_phase_times.get('Tracing', 0.0)
            warning = new_phase_times.get('Warning', 0.0)
            destroy = new_phase_times.get('Destroy', 0.0)
            self.new_phase_times_label.setText(
                f"Tracing: {tracing:.1f}ms | Warning: {warning:.1f}ms | Destroy: {destroy:.1f}ms"
            )
        else:
            self.new_phase_times_label.setText("Tracing: -- | Warning: -- | Destroy: --")
        
    def update_success_rate(self, old_rate, new_rate):
        """Update success rate displays"""
        self.old_success_bar.setValue(int(old_rate))
        self.old_success_label.setText(f"{old_rate:.1f}%")
        self.new_success_bar.setValue(int(new_rate))
        self.new_success_label.setText(f"{new_rate:.1f}%")
        
    def update_interceptors(self, old_count, new_count):
        """Update interceptor count displays"""
        self.old_interceptor_label.setText(f"Old: {old_count}")
        self.new_interceptor_label.setText(f"New: {new_count}")

