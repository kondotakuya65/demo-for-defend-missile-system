# Defensive Missile System Simulation

A professional 3D visualization application comparing two missile defense algorithms (Old vs New) across three key phases: **Tracing**, **Warning**, and **Destroy**.

## Features

- **3D OpenGL Visualization**: Impressive 3D graphics for client demonstrations
- **Side-by-Side Comparison**: Real-time comparison of old vs new algorithms
- **Three-Phase Simulation**: Tracing → Warning → Destroy
- **Performance Metrics**: Real-time CPU usage, response times, and success rates
- **Multiple Scenarios**: Single threat, wave attack, saturation attack
- **Interactive Controls**: Camera rotation, zoom, simulation controls

## Requirements

- Python 3.8 or higher
- OpenGL 3.3+ support (usually available on modern systems)
- Graphics drivers up to date

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

## Project Structure

```
missile_demo/
├── src/
│   ├── algorithms/      # Algorithm implementations
│   ├── simulation/      # Simulation engine
│   ├── visualization/   # 3D rendering
│   │   └── opengl/      # OpenGL renderer
│   ├── ui/              # User interface
│   └── utils/           # Utilities
├── resources/           # Shaders, textures, models
├── config.json          # Configuration file
├── requirements.txt     # Python dependencies
└── main.py             # Application entry point
```

## Configuration

Edit `config.json` to customize:
- Window size and visualization settings
- Algorithm parameters
- Simulation parameters
- Camera settings
- Model appearances
- Effect parameters

## Development

See `DEVELOPMENT_PLAN.md` for detailed development steps.

## Documentation

- `REQUIREMENTS.md` - Complete requirements specification
- `DEVELOPMENT_PLAN.md` - Step-by-step development plan
- `RESOURCES.md` - Resource requirements
- `3D_APPROACH.md` - Technical overview of 3D approach

## License

[Add your license here]

## Author

[Add your name/company here]

