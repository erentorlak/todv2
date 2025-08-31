"""
Config-Driven Tool Registry - Dynamically loads tools based on configuration
"""
from typing import Dict, Callable, Any, List
import importlib
from ..config import TOOLS, get_tool_config, get_intent_config

class ToolRegistry:
    """Config-driven registry for managing tools dynamically"""
    
    def __init__(self):
        self._tool_cache = {}  # Cache loaded tool functions
    
    def get_tool(self, tool_name: str) -> Callable:
        """Get a tool function by name, loading it dynamically"""
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]
        
        tool_config = get_tool_config(tool_name)
        if not tool_config:
            return None
        
        # Load function dynamically: "travel_tools.book_flight" -> travel_tools.book_flight
        function_path = tool_config.get("function")
        if not function_path:
            return None
        
        try:
            module_name, function_name = function_path.rsplit(".", 1)
            module = importlib.import_module(f"src.tools.{module_name}")
            tool_function = getattr(module, function_name)
            
            # Cache the loaded function
            self._tool_cache[tool_name] = tool_function
            return tool_function
            
        except (ImportError, AttributeError, ValueError) as e:
            print(f"Error loading tool {tool_name}: {e}")
            return None
    
    def get_tools_for_intent(self, intent: str) -> List[str]:
        """Get tool names for an intent from config"""
        intent_config = get_intent_config(intent)
        if not intent_config:
            return []
        return intent_config.get("tools", [])
    
    def get_all_tools(self) -> Dict[str, str]:
        """Get all registered tool names and descriptions"""
        result = {}
        for tool_name, tool_config in TOOLS.items():
            result[tool_name] = tool_config.get("description", "")
        return result
    
    def validate_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters for a specific tool"""
        tool_config = get_tool_config(tool_name)
        if not tool_config:
            return {"valid": False, "error": f"Unknown tool: {tool_name}"}
        
        required_params = tool_config.get("parameters", [])
        
        # Check if all required parameters are present
        for param in required_params:
            if not parameters.get(param):
                return {"valid": False, "error": f"Missing required parameter: {param}"}
        
        return {"valid": True}

# Global registry instance
tool_registry = ToolRegistry()
