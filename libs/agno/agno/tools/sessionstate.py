import json
from typing import Any, Callable, Dict, List, Optional

from agno.tools import Toolkit
from agno.utils.log import log_debug, log_error


class SessionStateTools(Toolkit):
    def __init__(
        self,
        enable_get_state: bool = True,
        enable_get_all_state: bool = True,
        enable_list_keys: bool = True,
        **kwargs,
    ):
        """Initialize the SessionStateTools toolkit.
        
        Args:
            enable_get_state: If True, enable the get_state tool to retrieve specific key values
            enable_get_all_state: If True, enable the get_all_state tool to retrieve the entire session state
            enable_list_keys: If True, enable the list_keys tool to list all keys in session state
        """
        tools: List[Callable] = []
        
        if enable_get_state:
            tools.append(self.get_state)
        if enable_get_all_state:
            tools.append(self.get_all_state)
        if enable_list_keys:
            tools.append(self.list_keys)

        # Initialize the toolkit with auto-registration enabled
        super().__init__(name="session_state_tools", tools=tools, **kwargs)

    def get_state(self, session_state: Dict[str, Any], key: str) -> str:
        """Retrieve the value of a specific key from the session state.

        Args:
            key (str): The key to retrieve from the session state.

        Returns:
            str: JSON string containing the key and its value, or an error message if the key doesn't exist.
        """
        try:
            if session_state is None:
                log_error("Session state is None")
                return json.dumps({
                    "success": False,
                    "key": key,
                    "error": "Session state is not initialized"
                }, indent=2)

            if key not in session_state:
                log_debug(f"Key '{key}' not found in session state")
                return json.dumps({
                    "success": False,
                    "key": key,
                    "error": f"Key '{key}' not found in session state",
                    "available_keys": list(session_state.keys())
                }, indent=2)

            value = session_state[key]
            log_debug(f"Retrieved value for key '{key}': {value}")
            
            return json.dumps({
                "success": True,
                "key": key,
                "value": value
            }, indent=2, default=str)

        except Exception as e:
            log_error(f"Error retrieving state for key '{key}': {e}")
            return json.dumps({
                "success": False,
                "key": key,
                "error": str(e)
            }, indent=2)

    def get_all_state(self, session_state: Dict[str, Any]) -> str:
        """Retrieve the entire session state as a JSON string.

        Returns:
            str: JSON string containing the entire session state.
        """
        try:
            if session_state is None:
                log_error("Session state is None")
                return json.dumps({
                    "success": False,
                    "error": "Session state is not initialized"
                }, indent=2)

            log_debug("Retrieved entire session state")
            
            return json.dumps({
                "success": True,
                "session_state": session_state
            }, indent=2, default=str)

        except Exception as e:
            log_error(f"Error retrieving entire session state: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)

    def list_keys(self, session_state: Dict[str, Any]) -> str:
        """List all available keys in the session state.

        Returns:
            str: JSON string containing a list of all keys in the session state.
        """
        try:
            if session_state is None:
                log_error("Session state is None")
                return json.dumps({
                    "success": False,
                    "error": "Session state is not initialized"
                }, indent=2)

            keys = list(session_state.keys())
            log_debug(f"Listed {len(keys)} keys from session state")
            
            return json.dumps({
                "success": True,
                "keys": keys,
                "count": len(keys)
            }, indent=2)

        except Exception as e:
            log_error(f"Error listing session state keys: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)

