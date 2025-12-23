#!/usr/bin/env python3
"""
Defensive Missile System Simulation
Main application entry point
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.utils.config import load_config


def main():
    """Main application entry point"""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Missile Defense Simulation")
    
    # Note: High DPI scaling is enabled by default in PyQt6
    
    try:
        # Load configuration
        config = load_config()
        
        # Create and show main window
        window = MainWindow(config)
        window.show()
        window.showMaximized()  # Maximize window at startup
        
        # Run application event loop
        return app.exec()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure config.json exists in the project root.")
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

