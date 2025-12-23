"""
Configuration management utilities
"""

import json
import os
import sys


def _get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Running as script, use the directory of this file
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Go up to project root
        base_path = os.path.dirname(os.path.dirname(base_path))
    
    return os.path.join(base_path, relative_path)


def load_config(config_path="config.json"):
    """Load configuration from JSON file"""
    # Try to find config.json in the executable's directory or project root
    if not os.path.isabs(config_path):
        # Try PyInstaller bundle path first
        bundle_path = _get_resource_path(config_path)
        if os.path.exists(bundle_path):
            config_path = bundle_path
        # Fallback to current directory (for development)
        elif not os.path.exists(config_path):
            # Try in the executable's directory
            if hasattr(sys, '_MEIPASS'):
                exe_dir = os.path.dirname(sys.executable)
                exe_config = os.path.join(exe_dir, config_path)
                if os.path.exists(exe_config):
                    config_path = exe_config
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config


def save_config(config, config_path="config.json"):
    """Save configuration to JSON file"""
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

