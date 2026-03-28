# Glitch - AI Music Composition Assistant

Glitch is an interactive, AI-powered music composition application designed to help composers brainstorm, demo, and transcribe musical ideas in real-time. By leveraging the **Gemini Live API** and advanced pitch detection, Glitch bridges the gap between vocal ideas and musical notation.

## 🚀 Key Features

- **🎙️ Voice Prompting**: Speak naturally to the assistant. Glitch uses the **Gemini 2.5 Flash Native Audio** model for real-time transcription and intent understanding.
- **🎹 Intelligent Composition**: AI agents generate musical suggestions, demos, and structural ideas based on your voice or text prompts.
- **🎸 Accompaniment Generation**: Automatically create musical accompaniments that match your composition's style and melody.
- **🎶 Humming to Notation**: Record yourself humming or singing. Glitch uses **CREPE** (high-performance pitch tracking) to convert monophonic audio into musical notation (MIDI/Score).
- **🎼 MuseScore Integration**: Seamlessly export and visualize your AI-generated ideas in MuseScore via a custom MCP (Model Context Protocol) bridge.

## 🏛️ Architecture: Dual Virtual Environments

This project uses a **dual virtual environment architecture** to manage different library requirements and Python version compatibility:

1. **Python 3.11 (Transcription)**: Handles audio processing and pitch detection using libraries like `librosa` and `crepe`. This environment is dedicated to `src/audio/` scripts.
2. **Python 3.14 (Main Agent & UI)**: Coordinates the composition task using Google Gemini APIs and manages the PySide6 UI. This is the main application environment.

## 📂 Project Structure

```text
glitch/
├── main.py                 # Application entry point (runs in venv_314)
├── .env                    # API keys (Gemini, etc.)
├── src/
│   ├── ui/                 # UI Backend (PySide6) and QML interface
│   ├── agents/             # AI orchestration (Composer, Accompaniment)
│   └── audio/              # Pitch detection and notation conversion (runs in venv_311)
├── scripts/                # Helper scripts for running components
├── mcp-musescore/          # MuseScore integration bridge
├── requirements_311.txt    # Transcription engine dependencies (Python 3.11)
├── requirements_314.txt    # UI and Agent dependencies (Python 3.14)
└── README.md               # You are here
```

## ⚙️ Prerequisites

- **Python 3.11** and **Python 3.14** installed on your system.
- **Python Launcher (`py`)** is recommended for Windows users to manage multiple versions.
- **Gemini API Key**: Required for AI features. Place it in a `.env` file as `GOOGLE_API_KEY`.
- **MuseScore 4**: (Optional) For notation visualization.

## 🔨 Setup & Installation

To set up the project, you must initialize both virtual environments:

### 1. Create the Virtual Environments

#### Windows (PowerShell)
```powershell
# Create environment for transcription (3.11)
py -3.11 -m venv venv_311

# Create environment for the main application (3.14)
py -3.14 -m venv venv_314
```

#### macOS / Linux
```bash
# Create environment for transcription (3.11)
python3.11 -m venv venv_311

# Create environment for the main application (3.14)
python3.14 -m venv venv_314
```

### 2. Install Dependencies

#### Windows (PowerShell)
```powershell
# Install dependencies for Python 3.11
.\venv_311\Scripts\pip.exe install -r requirements_311.txt

# Install dependencies for Python 3.14
.\venv_314\Scripts\pip.exe install -r requirements_314.txt
```

#### macOS / Linux
```bash
# Install dependencies for Python 3.11
./venv_311/bin/pip install -r requirements_311.txt

# Install dependencies for Python 3.14
./venv_314/bin/pip install -r requirements_314.txt
```

### 3. Configure Environment
Create a `.env` file in the root directory:
```text
GOOGLE_API_KEY=your_api_key_here
```

## 🏃 Running the Application

Launch the main application using the **Python 3.14** environment:

```bash
# Windows
.\venv_314\Scripts\python.exe main.py

# macOS / Linux
./venv_314/bin/python main.py
```

The application automatically bridges to the Python 3.11 environment for transcription tasks via internal scripts.

## 📄 License

[Insert License Information Here]
