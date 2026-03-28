# AI Music Composition Agent

This project is an AI-assisted music composition application that coordinates audio transcription, generative music logic, and MuseScore notation. It uses a dual-Python architecture to manage different library requirements.

## Project Structure

```text
.
├── .env                # API keys and shared environment variables
├── .gitignore          # Git exclusion rules
├── README.md           # This file
├── audio_parser.py     # Audio-to-MIDI transcription (Python 3.11)
├── composer_agent.py   # Main AI orchestration logic (Python 3.14)
├── demo_agent.py       # Demonstration and testing script (Python 3.14)
├── mcp-musescore/      # MuseScore MCP Server and QML Plugin
├── venv_311/           # Virtual environment for Python 3.11
├── venv_314/           # Virtual environment for Python 3.14
├── requirements_311.txt # Dependencies for Python 3.11
└── requirements_314.txt # Dependencies for Python 3.14
```

## Architecture

- **Python 3.11 (Transcription)**: Handles audio processing and pitch detection using libraries like `librosa` and `basic-pitch`.
- **Python 3.14 (Main Agent)**: Coordinates the composition task using Google ADK, Gemini, and communicating with the transcription service via MCP.
- **MuseScore Integration**: A QML plugin that bridges the AI agent to the MuseScore notation software via WebSockets.

## Prerequisites

- **Python 3.11** and **Python 3.14** must be installed on your system.
- The **Python Launcher (`py`)** is recommended for Windows users to manage multiple versions.

## Initial Setup

### 1. Create the Virtual Environments

Run these commands from the project root depending on your operating system:

#### Windows (PowerShell)

```powershell
# Create Python 3.11 environment
py -3.11 -m venv venv_311

# Create Python 3.14 environment
py -3.14 -m venv venv_314
```

#### macOS / Linux (Terminal)

```bash
# Create Python 3.11 environment
python3.11 -m venv venv_311

# Create Python 3.14 environment
python3.14 -m venv venv_314
```

### 2. Install Dependencies

Install the specific requirements into their respective environments:

#### Windows (PowerShell)

```powershell
# Install for Python 3.11
.\venv_311\Scripts\pip.exe install -r requirements_311.txt

# Install for Python 3.14
.\venv_314\Scripts\pip.exe install -r requirements_314.txt
```

#### macOS / Linux (Terminal)

```bash
# Install for Python 3.11
./venv_311/bin/pip install -r requirements_311.txt

# Install for Python 3.14
./venv_314/bin/pip install -r requirements_314.txt
```

## Running Scripts

To ensure you use the correct Python version and environment, call the interpreter directly from the environment's bin/Scripts folder:

### Windows (PowerShell)

**Run Python 3.11 script:**

```powershell
.\venv_311\Scripts\python.exe your_script_311.py
```

**Run Python 3.14 script:**

```powershell
.\venv_314\Scripts\python.exe your_script_314.py
```

### macOS / Linux (Terminal)

**Run Python 3.11 script:**

```bash
./venv_311/bin/python your_script_311.py
```

**Run Python 3.14 script:**

```bash
./venv_314/bin/python your_script_314.py
```

## Development in Cursor

To get the correct IntelliSense and linting for each file:

1. Open the `.py` file you are working on.
2. Press `Ctrl+Shift+P` and type **"Python: Select Interpreter"**.
3. Select the `python` or `python.exe` located in the corresponding `venv_*/` folder:
   - **Windows**: `venv_*/Scripts/python.exe`
   - **macOS/Linux**: `venv_*/bin/python`
