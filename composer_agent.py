import asyncio
from dotenv import load_dotenv
from mcp import StdioServerParameters

# ADK Imports
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams # Updated import
from google.adk.runners import InMemoryRunner
from google.genai import types

# 1. Load the API key from your .env file
load_dotenv()

# 2. Configure the connection to your local MuseScore MCP server
musescore_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python", 
            args=["mcp-musescore/server.py"]
        )
    )
)

# 3. Create the ADK Agent powered by Gemini (The Blueprint)
agent = Agent(
    model='gemini-3-flash-preview',
    name="MuseScore_Composer",
    instruction="""You are an expert AI music composer and orchestrator. 
    You have access to MuseScore via an MCP server. Use your tools to navigate scores, 
    read existing notes, and write new music. Always explain what you are about to do 
    before executing the tool commands.""",
    tools=[musescore_mcp]
)

if __name__ == "__main__":
    print("Agent is thinking...")
    
    user_prompt = "Use the currently opened score and add harmonization."
    
    # 4. Initialize the Runner (The Engine)
    runner = InMemoryRunner(agent=agent, app_name="musescore_app")
    
    # 5. Create a session to keep track of conversation memory
    session = asyncio.run(runner.session_service.create_session(
        app_name="musescore_app", 
        user_id="local_user"
    ))
    
    # 6. Format the user prompt into ADK/GenAI Content types
    content = types.Content(
        role="user", 
        parts=[types.Part.from_text(text=user_prompt)]
    )
    
    print("\nAgent Response:")
    
    # 7. Execute the run loop and process the event stream
    for event in runner.run(
        user_id="local_user", 
        session_id=session.id, 
        new_message=content
    ):
        # Extract and print the text from the event stream
        if getattr(event, "content", None) and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="")
    print() # Add a final newline

    # testing pr
    # testing pr 2