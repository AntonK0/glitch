<<<<<<< HEAD
# Music Composer Assistant

A local AI-assisted MIDI and score composition toolkit built on MuseScore + MCP.

This repo includes:

- `composer_agent.py`: a Google ADK Gemini-3-run agent for scoring/harmonization via MCP.
- `mcp-musescore/`: subproject that implements a MuseScore MCP WebSocket server and plugin.

## 🧩 What this does

- Starts a local MuseScore MCP server in Python (`mcp-musescore/server.py`).
- Uses MuseScore plugin (`musescore-mcp-websocket.qml`) to connect via WebSocket.
- Allows AI agents to control MuseScore operations (add notes, lyrics, navigate score, etc.).
- Example agent flows are in `composer_agent.py`.

## ✅ Prerequisites

- MuseScore 3.x or 4.x installed
- Python 3.8+
- `pip` package manager
- Optional: `.env` with keys for ADK/GenAI if using cloud models

## 🚀 Setup

1. Clone repo

```bash
cd path/to/folder/you/want/to/clone/to
# if not already cloned
# git clone <your-repo-url> .
```

2. Create and activate Python venv

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r mcp-musescore/requirements.txt
pip install python-dotenv google-genai mcp  # if using composer_agent.py and ADK
```

4. Install MuseScore plugin

Copy `mcp-musescore/musescore-mcp-websocket.qml` to your MuseScore plugin folder:

- Windows: `%USERPROFILE%\Documents\MuseScore4\Plugins\musescore-mcp-websocket.qml`
- macOS: `~/Documents/MuseScore4/Plugins/musescore-mcp-websocket.qml`
- Linux: `~/Documents/MuseScore4/Plugins/musescore-mcp-websocket.qml`

5. Enable plugin in MuseScore

- Open MuseScore.
- Plugins → Plugin Manager.
- Enable `MuseScore API Server` (or similar name from the QML).
- Restart MuseScore if needed.

6. (Optional) configure environment

Create `.env` with your API key for the ADK connection (if required):

```
OPENAI_API_KEY=your_api_key_here
```

## ▶️ Run the server and agent

1. Start MuseScore and open or create a score.
2. Run the MuseScore API Server plugin from MuseScore: Plugins → MuseScore API Server.
3. Start the Python MCP server (project root):

```bash
cd mcp-musescore
python server.py
```

4. In another terminal, run the AI agent:

```bash
cd ..
python composer_agent.py
```

You should see console logs from your agent planning and executing actions.

## 🛠️ How it works

- `mcp-musescore/server.py` exposes a server endpoint to receive MCP commands.
- `mcp-musescore/src/tools/*` includes helper actions for MuseScore navigation/notation.
- `composer_agent.py` uses `McpToolset` with `StdioConnectionParams` to launch `mcp-musescore/server.py` and run the agent.

## 📄 Examples

- `mcp-musescore/examples/` includes example `.mscz` score files.
- Use these as test targets in MuseScore to validate the toolchain.

## 🐞 Troubleshooting

- If agent can’t connect:
  - Verify MuseScore plugin is enabled and running.
  - Check `server.py` output for WebSocket connection errors.
  - Ensure no firewall blocks port 8765.

- If something fails in `composer_agent.py`:
  - Confirm deps installed: `python-dotenv`, `mcp`, `google-genai`.
  - Ensure `.env` has working API keys (Gemini/ADK if needed).

## 📌 Notes

- This repo is intended for local development and experimental composer workflows.
- Adjust paths in `composer_agent.py` or in `claude_desktop_config.json` for your environment.
=======
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
>>>>>>> f36485980d75f95c9bfcb69cbe6e588b49abf8e1
