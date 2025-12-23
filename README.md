# Missile Defense System Simulation

A professional visual demonstration application comparing two missile defense algorithms (**CONVENTIONAL APPROACH** vs **SA+H APPROACH**) across three key phases: **Tracing**, **Warning**, and **Destroy**. The application emphasizes the SA+H algorithm's advantages in speed, efficiency, and reliability.

**Target Audience**: Client demonstrations, technical presentations  
**Platform**: Windows (primary), cross-platform Python application

---

## Features

### Core Functionality
- **2D Radar/Sonar Visualization**: Real-time radar-style visualization with rotating sweep animation
- **Side-by-Side Comparison**: Real-time comparison of Conventional vs SA+H algorithms
- **Three-Phase Simulation System**: 
  - **Tracing Phase**: Detect and track incoming threats
  - **Warning Phase**: Alert system activation and trajectory calculation
  - **Destroy Phase**: Interceptor launch and interception
- **Distance-Based Phase Transitions**: Phases change based on missile proximity to defense system

### Performance Metrics
- **Real-Time CPU Usage**: Dynamic CPU usage tracking (0% when idle, increases with active threats)
- **Response Time Tracking**: Per-phase and total interception time measurements
- **Success Rate Monitoring**: Interception success rate with missed missile tracking
- **Performance Graphs**: Latency vs. measurements comparison with log scale
- **Metrics Export**: Export simulation data to CSV or JSON format

### Simulation Scenarios
- **Single Threat**: One missile at a time
- **Wave Attack**: Multiple missiles in waves
- **Saturation Attack**: High-intensity continuous threat
- **Custom**: User-configurable threat count and spawn rate

### Visual Features
- **Phase-Based Color Coding**: 
  - Yellow: Tracing phase
  - Orange: Warning phase
  - Red: Destroy phase
- **Explosion Effects**: Visual feedback when missiles are intercepted
- **Missed Missile Alerts**: Visual indicators when missiles are missed (Conventional approach)
- **Trail Effects**: Fading trails for missiles and interceptors
- **Digital Clocks**: Per-missile interception time display
- **Missile Counters**: Intercepted/Missed/Success Rate statistics

### Algorithm Comparison
- **CONVENTIONAL APPROACH**:
  - Slower response times
  - Higher CPU overhead (70% base)
  - Lower success rate (~85%)
  - May miss some missiles under stress
  
- **SA+H APPROACH**:
  - Faster response times (2.5x speed multiplier)
  - Lower CPU overhead (35% base)
  - Higher success rate (~95%)
  - 100% interception success

---

## Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows (primary), Linux/Mac (cross-platform compatible)
- **Dependencies**: See `requirements.txt`

---

## Installation

### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
python main.py
```

The application will start maximized at 1920x1080 resolution.

---

## Building Executable

To create a standalone Windows executable:

```bash
pyinstaller MissileDefenseDemo.spec
```

The executable will be created in the `dist/MissileDefenseDemo/` directory. Make sure `config.json` is included in the distribution (it should be automatically included by the spec file).

---

## Configuration

Edit `config.json` to customize simulation parameters:

### Visualization Settings
- `window_width`, `window_height`: Application window size
- `radar_range`: Maximum radar detection range
- `show_grid`, `show_trails`: Visual display options

### Algorithm Parameters
- `old/new.response_delay`: Response delay in milliseconds
- `old/new.cpu_overhead`: Base CPU overhead (0.0-1.0)
- `old/new.success_rate`: Interception success rate (0.0-1.0)

### Simulation Parameters
- `default_threat_count`: Initial number of threats
- `tracing_range`, `warning_range`, `destroy_range`: Distance thresholds for phase transitions
- `interceptor_speed_multiplier`: Speed multiplier for interceptors
- `detection_range`: Maximum detection range

---

## Project Structure

```
missile_demo/
├── src/
│   ├── simulation/          # Simulation engine
│   │   ├── simulation_engine.py
│   │   ├── missile.py
│   │   └── interceptor.py
│   ├── ui/                  # User interface components
│   │   ├── main_window.py
│   │   ├── radar_widget.py
│   │   ├── control_panel.py
│   │   ├── metrics_panel.py
│   │   └── performance_graph.py
│   ├── utils/               # Utilities
│   │   ├── config.py
│   │   └── metrics_exporter.py
│   └── visualization/       # Visualization (OpenGL - reserved for future 3D)
│       └── opengl/
├── resources/               # Resources (shaders, textures)
├── config.json              # Configuration file
├── requirements.txt         # Python dependencies
├── main.py                  # Application entry point
└── MissileDefenseDemo.spec  # PyInstaller spec file
```

---

## Usage

### Starting a Simulation

1. **Select Scenario**: Choose from Single Threat, Wave Attack, Saturation Attack, or Custom
2. **Set Threat Count**: Adjust the threat count slider (for Custom scenario)
3. **Set Speed**: Choose simulation speed (Slow, Normal, Fast)
4. **Click Start**: Begin the simulation

### During Simulation

- **Pause**: Click "Pause" to freeze the simulation (radar sweep stops)
- **Reset**: Click "Reset" to clear all missiles and reset metrics
- **Monitor Metrics**: Watch real-time CPU usage, response times, and success rates
- **View Graphs**: Performance graphs update automatically showing latency vs. measurements

### Exporting Data

1. Click the **"Export"** button in the control panel
2. Choose export format (CSV or JSON)
3. Select save location
4. Data includes:
   - Phase response times
   - Interception times
   - Success rates
   - CPU usage statistics
   - Missile counts

---

## Key Features Explained

### Phase System
Missiles transition through three phases based on distance from the defense system center:
- **Tracing** (>70 units): Initial detection and tracking
- **Warning** (40-70 units): Alert activation and trajectory calculation
- **Destroy** (<40 units): Interceptor launch and interception

### Continuous Spawning
Missiles spawn continuously to maintain a constant threat count. When a missile is intercepted or missed, a new one spawns at a random position on the radar perimeter.

### Algorithm Differences
The SA+H algorithm demonstrates:
- **2.5x faster** missile and interceptor speeds
- **Reduced processing delays** in all phases
- **100% interception rate** vs. ~85% for Conventional approach
- **Lower CPU usage** under load

### Performance Graph
The bottom graph shows:
- **Y-axis**: Latency per scan (ms) - log scale
- **X-axis**: Reflections/measurements per scan (meters)
- Auto-scaling to accommodate values over 5000
- Continuous progression showing algorithm performance over time

---

## Troubleshooting

### Application Won't Start
- Ensure `config.json` exists in the project root
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)

### Executable Issues
- Ensure `config.json` is included in the distribution
- Check that all DLLs are bundled (PyQt6, NumPy, etc.)
- Run from the `dist/MissileDefenseDemo/` directory

### Performance Issues
- Reduce `particle_count` in `config.json`
- Lower `default_threat_count` for fewer simultaneous missiles
- Close other applications to free up system resources

---

## Development

See `DEVELOPMENT_PLAN.md` for detailed development steps and architecture.

---

## Documentation

- `REQUIREMENTS.md` - Complete requirements specification
- `DEVELOPMENT_PLAN.md` - Step-by-step development plan
- `RESOURCES.md` - Resource requirements and dependencies
- `3D_APPROACH.md` - Technical overview (deprecated - currently using 2D)

---

## Version History

### Current Version
- 2D radar/sonar visualization
- Distance-based phase transitions
- Continuous missile spawning
- Performance graphs with auto-scaling
- Metrics export (CSV/JSON)
- Visual feedback for missed missiles
- Dynamic CPU usage tracking

### Future Enhancements
- Optional 3D visualization mode
- Additional scenario types
- Networked multi-system simulation
- Advanced analytics dashboard

---

## License

[Add your license here]

---

## Author

[Add your name/company here]
