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
cd c:\Users\anton\code_and_projects\music_composer_assistant
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
