"""
Control Panel for simulation controls
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QLabel, QSlider, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ControlPanel(QWidget):
    """Control panel widget with simulation controls"""
    
    # Signals
    start_simulation = pyqtSignal()
    pause_simulation = pyqtSignal()
    reset_simulation = pyqtSignal()
    threat_count_changed = pyqtSignal(int)
    threat_type_changed = pyqtSignal(str)  # "missiles" or "drones"
    movement_type_changed = pyqtSignal(str)  # "straight" or "zigzag" (for custom scenario)
    speed_changed = pyqtSignal(float)
    scenario_changed = pyqtSignal(str)
    export_metrics = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.is_running = False
        self.init_ui()
        
    def init_ui(self):
        """Initialize control panel UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Simulation Controls Group
        sim_group = QGroupBox("Simulation Controls")
        sim_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.setMinimumWidth(80)
        self.start_button.clicked.connect(self.on_start_clicked)
        sim_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumWidth(80)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        sim_layout.addWidget(self.pause_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setMinimumWidth(80)
        self.reset_button.clicked.connect(self.on_reset_clicked)
        sim_layout.addWidget(self.reset_button)
        
        sim_group.setLayout(sim_layout)
        layout.addWidget(sim_group)
        
        # Threat Configuration Group
        threat_group = QGroupBox("Threat Configuration")
        threat_layout = QVBoxLayout()
        
        threat_count_layout = QHBoxLayout()
        threat_count_layout.addWidget(QLabel("Threat Count:"))
        
        self.threat_count_slider = QSlider(Qt.Orientation.Horizontal)
        self.threat_count_slider.setMinimum(1)
        self.threat_count_slider.setMaximum(20)
        self.threat_count_slider.setValue(self.config['simulation']['default_threat_count'])
        self.threat_count_slider.valueChanged.connect(self.on_threat_count_changed)
        threat_count_layout.addWidget(self.threat_count_slider)
        
        self.threat_count_label = QLabel(str(self.config['simulation']['default_threat_count']))
        self.threat_count_label.setMinimumWidth(30)
        self.threat_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threat_count_layout.addWidget(self.threat_count_label)
        
        threat_layout.addLayout(threat_count_layout)
        threat_group.setLayout(threat_layout)
        layout.addWidget(threat_group)
        
        # Threat Type Group (separate frame)
        threat_type_group = QGroupBox("Threat Type")
        threat_type_layout = QHBoxLayout()
        
        threat_type_layout.addWidget(QLabel("Type:"))
        
        self.threat_type_combo = QComboBox()
        self.threat_type_combo.addItems(["Missiles", "Drones"])
        self.threat_type_combo.currentTextChanged.connect(self.on_threat_type_changed)
        threat_type_layout.addWidget(self.threat_type_combo)
        
        threat_type_group.setLayout(threat_type_layout)
        layout.addWidget(threat_type_group)
        
        # Simulation Speed Group
        speed_group = QGroupBox("Simulation Speed")
        speed_layout = QHBoxLayout()
        
        speed_buttons = [
            ("0.5x", 0.5),
            ("1x", 1.0),
            ("2x", 2.0)
        ]
        
        self.speed_buttons = []
        for label, value in speed_buttons:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if value == 1.0:
                btn.setChecked(True)
            # Use a proper lambda closure
            def make_speed_handler(v):
                return lambda checked: self.on_speed_changed(v) if checked else None
            btn.clicked.connect(make_speed_handler(value))
            speed_layout.addWidget(btn)
            self.speed_buttons.append((btn, value))
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Preset Scenarios Group
        scenario_group = QGroupBox("Preset Scenarios")
        scenario_layout = QHBoxLayout()
        
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems([
            "Single Threat",
            "Wave Attack (5 threats)",
            "Saturation Attack (15 threats)",
            "Custom"
        ])
        self.scenario_combo.currentTextChanged.connect(self.on_scenario_changed)
        scenario_layout.addWidget(self.scenario_combo)
        
        scenario_group.setLayout(scenario_layout)
        layout.addWidget(scenario_group)
        
        # Movement Type Group (only enabled for Custom scenario)
        movement_type_group = QGroupBox("Movement Type")
        movement_type_layout = QHBoxLayout()
        
        movement_type_layout.addWidget(QLabel("Type:"))
        
        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItems(["Straight Line", "Zigzag"])
        self.movement_type_combo.currentTextChanged.connect(self.on_movement_type_changed)
        self.movement_type_combo.setEnabled(False)  # Disabled by default (only for Custom)
        movement_type_layout.addWidget(self.movement_type_combo)
        
        movement_type_group.setLayout(movement_type_layout)
        layout.addWidget(movement_type_group)
        
        # Export Button
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export Metrics")
        self.export_button.clicked.connect(self.on_export_clicked)
        export_layout.addWidget(self.export_button)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        # Apply styling
        self.apply_styling()
        
    def apply_styling(self):
        """Apply styling to control panel"""
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
            QPushButton {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 15px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:pressed {
                background-color: #222;
            }
            QPushButton:checked {
                background-color: #0066cc;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0066cc;
                border: 1px solid #555;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QComboBox {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                min-width: 150px;
            }
        """)
        
    def on_start_clicked(self):
        """Handle start button click"""
        if not self.is_running:
            self.is_running = True
            self.start_button.setText("Running...")
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            print("Start button clicked - emitting start_simulation signal")
            self.start_simulation.emit()
        else:
            self.on_pause_clicked()
            
    def on_pause_clicked(self):
        """Handle pause button click"""
        self.is_running = False
        self.start_button.setText("Start")
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_simulation.emit()
        
    def on_reset_clicked(self):
        """Handle reset button click"""
        self.is_running = False
        self.start_button.setText("Start")
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.reset_simulation.emit()
        
    def on_threat_count_changed(self, value):
        """Handle threat count slider change"""
        self.threat_count_label.setText(str(value))
        self.threat_count_changed.emit(value)
        
    def on_speed_changed(self, value):
        """Handle speed button change"""
        # Uncheck other buttons
        for btn, btn_value in self.speed_buttons:
            if btn_value != value:
                btn.setChecked(False)
        self.speed_changed.emit(value)
        
    def on_scenario_changed(self, text):
        """Handle scenario selection change"""
        scenario_map = {
            "Single Threat": "single",
            "Wave Attack (5 threats)": "wave",
            "Saturation Attack (15 threats)": "saturation",
            "Custom": "custom"
        }
        scenario = scenario_map.get(text, "custom")
        
        # Enable/disable movement type dropdown based on scenario
        is_custom = (scenario == "custom")
        self.movement_type_combo.setEnabled(is_custom)
        
        self.scenario_changed.emit(scenario)
        
        # If custom scenario is selected, emit current movement type
        if is_custom:
            self.on_movement_type_changed(self.movement_type_combo.currentText())
    
    def on_movement_type_changed(self, text):
        """Handle movement type selection change (only for Custom scenario)"""
        if not self.movement_type_combo.isEnabled():
            return  # Ignore if disabled
        
        movement_type_map = {
            "Straight Line": "straight",
            "Zigzag": "zigzag"
        }
        self.movement_type_changed.emit(movement_type_map.get(text, "straight"))
        
    def on_threat_type_changed(self, text):
        """Handle threat type selection change"""
        threat_type_map = {
            "Missiles": "missiles",
            "Drones": "drones"
        }
        self.threat_type_changed.emit(threat_type_map.get(text, "missiles"))
    
    def on_export_clicked(self):
        """Handle export button click"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.metrics_exporter import MetricsExporter
        
        # Get metrics from main window (will be passed via signal)
        # For now, emit signal and let main window handle it
        self.export_metrics.emit()
        # TODO: Implement export functionality
        print("Export clicked - to be implemented")

