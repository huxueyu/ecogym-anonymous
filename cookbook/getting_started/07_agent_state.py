"""Test session state management with a simple counter"""

from agno.agent import Agent
from agno.db.json import JsonDb
from agno.models.openai import OpenAIChat


def increment_counter(session_state) -> str:
    """Increment the counter in session state."""

    if "count" not in session_state:
        session_state["count"] = 0


    session_state["count"] += 1

    return f"Counter incremented! Current count: {session_state['count']}"


def get_counter(session_state) -> str:
    """Get the current counter value."""
    count = session_state.get("count", 0)
    return f"Current count: {count}"


db = JsonDb(db_path="tmp/json_db")


agent = Agent(
    model=OpenAIChat(
        id="gpt-4o",
        api_key="", 
        base_url="",  
    ),
    db=db,  

    session_state={"count": 0},
    tools=[increment_counter, get_counter],

    instructions="You can increment and check a counter. Current count is: {count}",

    resolve_in_context=True,
    markdown=True,
)


print("Testing counter functionality...")
agent.print_response(
    "Let's increment the counter 3 times and observe the state changes!", stream=True
)


final_state = agent.get_session_state()
print(f"Final session state: {final_state}")
print(f"Session ID: {agent.session_id}")
