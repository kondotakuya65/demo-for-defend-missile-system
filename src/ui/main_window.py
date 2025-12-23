"""
Main application window for Missile Defense Simulation
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QLabel, QPushButton, QSlider, QComboBox,
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from src.ui.control_panel import ControlPanel
from src.ui.metrics_panel import MetricsPanel
from src.ui.radar_widget import RadarWidget


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Defensive Missile System Simulation")
        
        # Center window on screen
        screen = self.screen().availableGeometry()
        window_width = self.config['visualization']['window_width']
        window_height = self.config['visualization']['window_height']
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        if y<0:
            y = 0
        self.setGeometry(x, y, window_width, window_height)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(3)  # Reduced spacing to maximize viewer area
        main_layout.setContentsMargins(3, 3, 3, 3)  # Reduced margins
        
        # Control Panel (Top) - with minimal space
        self.control_panel = ControlPanel(self.config)
        main_layout.addWidget(self.control_panel, stretch=0)  # No stretch - fixed size
        
        # Visualization Area (Middle) - Side by side
        viz_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Old Algorithm Visualization
        old_viz_container = QWidget()
        old_viz_layout = QVBoxLayout(old_viz_container)
        old_viz_layout.setContentsMargins(0, 0, 0, 0)
        
        old_label = QLabel("OLD ALGORITHM")
        old_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        old_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        old_label.setStyleSheet("background-color: #2b2b2b; color: #ff8800; padding: 2px;")
        old_label.setFixedHeight(int(old_label.fontMetrics().height() * 1.1))  # 1.1x text height
        old_viz_layout.addWidget(old_label)
        
        self.old_radar_widget = RadarWidget(self.config, "old")
        old_viz_layout.addWidget(self.old_radar_widget, stretch=1)  # Maximize radar widget
        
        # Phase indicators for old algorithm (compact)
        old_phases = self.create_phase_indicators("old")
        old_viz_layout.addLayout(old_phases)
        
        viz_splitter.addWidget(old_viz_container)
        
        # New Algorithm Visualization
        new_viz_container = QWidget()
        new_viz_layout = QVBoxLayout(new_viz_container)
        new_viz_layout.setContentsMargins(0, 0, 0, 0)
        
        new_label = QLabel("NEW ALGORITHM")
        new_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        new_label.setStyleSheet("background-color: #2b2b2b; color: #00ff00; padding: 2px;")
        new_label.setFixedHeight(int(new_label.fontMetrics().height() * 1.1))  # 1.1x text height
        new_viz_layout.addWidget(new_label)
        
        self.new_radar_widget = RadarWidget(self.config, "new")
        new_viz_layout.addWidget(self.new_radar_widget, stretch=1)  # Maximize radar widget
        
        # Phase indicators for new algorithm (compact)
        new_phases = self.create_phase_indicators("new")
        new_viz_layout.addLayout(new_phases)
        
        viz_splitter.addWidget(new_viz_container)
        
        # Set equal sizes for both visualization areas
        half_width = self.config['visualization']['window_width'] // 2
        viz_splitter.setSizes([half_width, half_width])
        
        # Set stretch factors to maximize radar viewer size
        viz_splitter.setStretchFactor(0, 1)
        viz_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(viz_splitter, stretch=1)  # Maximize stretch for radar viewers
        
        # Metrics Panel (Bottom) - with minimal space
        self.metrics_panel = MetricsPanel(self.config)
        main_layout.addWidget(self.metrics_panel, stretch=0)  # No stretch - fixed size
        
        # Connect control panel signals to simulation engines (after both widgets are created)
        def start_old_sim():
            # Generate new seed for synchronized spawning
            import random
            seed = random.randint(0, 1000000)
            print(f"Starting old simulation with {self.current_threat_count} threats (seed: {seed})...")
            self.old_radar_widget.simulation.start(self.current_threat_count, seed)
        def start_new_sim():
            # Use same seed as old simulation for synchronization
            seed = getattr(self.old_radar_widget.simulation, 'spawn_seed', None)
            if seed is None:
                import random
                seed = random.randint(0, 1000000)
            print(f"Starting new simulation with {self.current_threat_count} threats (seed: {seed})...")
            self.new_radar_widget.simulation.start(self.current_threat_count, seed)
            
        # Connect control panel signals
        self.control_panel.start_simulation.connect(start_old_sim)
        self.control_panel.start_simulation.connect(start_new_sim)
        self.control_panel.pause_simulation.connect(self.old_radar_widget.simulation.pause)
        self.control_panel.pause_simulation.connect(self.new_radar_widget.simulation.pause)
        self.control_panel.reset_simulation.connect(self.old_radar_widget.simulation.reset)
        self.control_panel.reset_simulation.connect(self.new_radar_widget.simulation.reset)
        
        # Connect threat count slider
        self.control_panel.threat_count_changed.connect(self.on_threat_count_changed)
        
        # Connect speed controls
        self.control_panel.speed_changed.connect(self.on_speed_changed)
        
        # Connect scenario selector
        self.control_panel.scenario_changed.connect(self.on_scenario_changed)
        
        # Connect export button
        self.control_panel.export_metrics.connect(self.on_export_metrics)
        
        # Timer to update phase indicators and metrics
        from PyQt6.QtCore import QTimer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(50)  # Update every 50ms for smooth progress bars
        
        # Apply styling
        self.apply_styling()
        
        # Store current scenario settings
        self.current_threat_count = self.config['simulation']['default_threat_count']
        self.current_speed = 1.0
        self.current_scenario = "custom"
    
    def on_threat_count_changed(self, count: int):
        """Handle threat count change"""
        self.current_threat_count = count
        # Update will apply on next start
    
    def on_speed_changed(self, speed: float):
        """Handle speed change"""
        self.current_speed = speed
        self.old_radar_widget.simulation.simulation_speed = speed
        self.new_radar_widget.simulation.simulation_speed = speed
    
    def on_scenario_changed(self, scenario: str):
        """Handle scenario change"""
        self.current_scenario = scenario
        scenario_configs = {
            "single": {"count": 1, "spawn_interval": 999.0},  # No continuous spawn
            "wave": {"count": 5, "spawn_interval": 2.0},
            "saturation": {"count": 15, "spawn_interval": 1.0},
            "custom": {"count": self.current_threat_count, "spawn_interval": 3.0}
        }
        
        config = scenario_configs.get(scenario, scenario_configs["custom"])
        self.current_threat_count = config["count"]
        
        # Update spawn intervals for continuous spawning
        self.old_radar_widget.simulation.spawn_interval = config["spawn_interval"]
        self.new_radar_widget.simulation.spawn_interval = config["spawn_interval"]
        
        # Update scenario type for movement patterns
        self.old_radar_widget.simulation.current_scenario = scenario
        self.new_radar_widget.simulation.current_scenario = scenario
    
    def on_export_metrics(self):
        """Handle metrics export"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.metrics_exporter import MetricsExporter
        
        # Get current metrics
        old_stats = self.old_radar_widget.simulation.get_statistics()
        new_stats = self.new_radar_widget.simulation.get_statistics()
        
        metrics = {
            'old': old_stats,
            'new': new_stats
        }
        
        # Ask user for export format
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Metrics")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Choose export format:"))
        
        json_btn = QPushButton("Export as JSON")
        csv_btn = QPushButton("Export as CSV")
        both_btn = QPushButton("Export Both")
        cancel_btn = QPushButton("Cancel")
        
        def export_json():
            filepath, _ = QFileDialog.getSaveFileName(
                dialog, "Save JSON File", "", "JSON Files (*.json)"
            )
            if filepath:
                MetricsExporter.export_json(metrics, filepath)
                QMessageBox.information(dialog, "Success", f"Metrics exported to:\n{filepath}")
                dialog.accept()
        
        def export_csv():
            filepath, _ = QFileDialog.getSaveFileName(
                dialog, "Save CSV File", "", "CSV Files (*.csv)"
            )
            if filepath:
                MetricsExporter.export_csv(metrics, filepath)
                QMessageBox.information(dialog, "Success", f"Metrics exported to:\n{filepath}")
                dialog.accept()
        
        def export_both():
            json_path, _ = QFileDialog.getSaveFileName(
                dialog, "Save JSON File", "", "JSON Files (*.json)"
            )
            if json_path:
                csv_path = json_path.replace('.json', '.csv')
                MetricsExporter.export_json(metrics, json_path)
                MetricsExporter.export_csv(metrics, csv_path)
                QMessageBox.information(dialog, "Success", 
                    f"Metrics exported to:\n{json_path}\n{csv_path}")
                dialog.accept()
        
        json_btn.clicked.connect(export_json)
        csv_btn.clicked.connect(export_csv)
        both_btn.clicked.connect(export_both)
        cancel_btn.clicked.connect(dialog.reject)
        
        layout.addWidget(json_btn)
        layout.addWidget(csv_btn)
        layout.addWidget(both_btn)
        layout.addWidget(cancel_btn)
        
        dialog.exec()
    
    def update_ui(self):
        """Update phase indicators and metrics panel"""
        # Update old algorithm phases
        old_stats = self.old_radar_widget.simulation.get_statistics()
        old_phase_stats = old_stats.get('phase_stats', {})
        
        if hasattr(self, 'old_tracing_progress'):
            self.old_tracing_progress.setValue(int(old_phase_stats.get('Tracing', {}).get('progress', 0)))
        if hasattr(self, 'old_warning_progress'):
            self.old_warning_progress.setValue(int(old_phase_stats.get('Warning', {}).get('progress', 0)))
        if hasattr(self, 'old_destroy_progress'):
            self.old_destroy_progress.setValue(int(old_phase_stats.get('Destroy', {}).get('progress', 0)))
        
        # Update new algorithm phases
        new_stats = self.new_radar_widget.simulation.get_statistics()
        new_phase_stats = new_stats.get('phase_stats', {})
        
        if hasattr(self, 'new_tracing_progress'):
            self.new_tracing_progress.setValue(int(new_phase_stats.get('Tracing', {}).get('progress', 0)))
        if hasattr(self, 'new_warning_progress'):
            self.new_warning_progress.setValue(int(new_phase_stats.get('Warning', {}).get('progress', 0)))
        if hasattr(self, 'new_destroy_progress'):
            self.new_destroy_progress.setValue(int(new_phase_stats.get('Destroy', {}).get('progress', 0)))
        
        # Update metrics panel
        self.metrics_panel.update_cpu_usage(
            old_stats.get('cpu_usage', 0),
            new_stats.get('cpu_usage', 0)
        )
        self.metrics_panel.update_success_rate(
            old_stats.get('success_rate', 0),
            new_stats.get('success_rate', 0)
        )
        self.metrics_panel.update_interceptors(
            old_stats.get('interceptors_launched', 0),
            new_stats.get('interceptors_launched', 0)
        )
        self.metrics_panel.update_response_time(
            old_stats.get('total_response_time', 0),
            new_stats.get('total_response_time', 0),
            old_stats.get('response_times', {}),
            new_stats.get('response_times', {})
        )
        
    def create_phase_indicators(self, algorithm_type):
        """Create phase indicator layout - compact version"""
        phase_layout = QHBoxLayout()
        phase_layout.setSpacing(3)
        phase_layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        
        phases = [
            ("Tracing", "#ffff00"),
            ("Warning", "#ff8800"),
            ("Destroy", "#ff0000")
        ]
        
        for phase_name, color in phases:
            phase_group = QGroupBox(phase_name)
            phase_group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    font-size: 9px;
                    border: 1px solid {color};
                    border-radius: 3px;
                    margin-top: 3px;
                    padding-top: 5px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 5px;
                    padding: 0 3px;
                    color: {color};
                    font-size: 9px;
                }}
            """)
            
            phase_layout_inner = QVBoxLayout()
            phase_layout_inner.setContentsMargins(3, 3, 3, 3)
            phase_layout_inner.setSpacing(2)
            
            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(100)
            progress.setValue(0)
            progress.setFixedHeight(12)  # Compact height
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {color};
                    border-radius: 2px;
                    text-align: center;
                    background-color: #1a1a1a;
                    font-size: 8px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            
            phase_layout_inner.addWidget(progress)
            phase_group.setLayout(phase_layout_inner)
            phase_layout.addWidget(phase_group)
            
            # Store reference for later updates
            if algorithm_type == "old":
                setattr(self, f"old_{phase_name.lower()}_progress", progress)
            else:
                setattr(self, f"new_{phase_name.lower()}_progress", progress)
        
        return phase_layout
        
    def apply_styling(self):
        """Apply application-wide styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
        """)
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up OpenGL resources if needed
        event.accept()

