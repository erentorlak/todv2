"""
Tool Choosing Agent - Select tools and identify required parameters based on intent
"""
from typing import Literal, List
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command
import json

from ..schemas import DialogState
from ..tools import tool_registry
from ..config.llm_config import get_tool_choosing_llm


class ToolChoosingAgent:
    """Agent for selecting appropriate tools and identifying required parameters"""
    
    def __init__(self):
        self.llm = get_tool_choosing_llm()
    
    def __call__(self, state: DialogState) -> Command[Literal["supervisor"]]:
        """Select tools and identify required parameters based on intent (config-driven)"""
        
        current_intent = state.get("current_intent")
        
        print(f"DEBUG ToolChoosing - Intent: {current_intent}")
        
        if not current_intent:
            return Command(
                goto="supervisor",
                update={"selected_tools": [], "dialog_context": {"error": "No intent to process"}}
            )
        
        # Get tools and parameters directly from config
        from ..config import get_intent_config, get_tool_execution_order
        
        intent_config = get_intent_config(current_intent)
        if not intent_config:
            return Command(
                goto="supervisor",
                update={"selected_tools": [], "dialog_context": {"error": f"Unknown intent: {current_intent}"}}
            )
        
        # Get tools and required parameters from config
        selected_tools = intent_config.get("tools", [])
        required_parameters = list(intent_config.get("parameters", {}).keys())
        
        # Get tool execution order considering dependencies
        tool_execution_order = get_tool_execution_order(current_intent)
        
        print(f"DEBUG ToolChoosing - Selected tools: {selected_tools}")
        print(f"DEBUG ToolChoosing - Required parameters: {required_parameters}")
        print(f"DEBUG ToolChoosing - Execution order: {tool_execution_order}")
        
        return Command(
            goto="supervisor",
            update={
                "selected_tools": selected_tools,
                "dialog_context": {
                    "required_parameters": required_parameters,
                    "tool_execution_order": tool_execution_order,
                    "current_tool_batch": 0,
                    "completed_tools": []
                }
            }
        )
    
    def _select_tools_and_parameters(self, intent: str) -> dict:
        """Use LLM to select appropriate tools and identify required parameters"""
        
        # Get available tools for this intent
        available_tools = tool_registry.get_tools_for_intent(intent)
        available_tool_names = list(available_tools.keys())
        
        system_prompt = """You are a tool selection specialist. Given a user intent, select the appropriate tools and identify required parameters.

Available tools and their purposes:
- book_flight: Books airline tickets (needs: origin, destination, date)
- book_hotel: Books hotel accommodation (needs: city, days)

Your task:
1. Select the most appropriate tool(s) for the given intent
2. Identify what parameters are required for those tools
3. Provide reasoning for your selection

Respond with a JSON object in this exact format:
{
    "tools": ["tool_name"],
    "required_parameters": ["param1", "param2"],
    "reasoning": "Why these tools were selected"
}"""
        
        user_prompt = f"""
Intent: {intent}
Available tools: {available_tool_names}

Select the appropriate tool(s) and identify required parameters for this intent.
"""
        
        messages_for_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages_for_llm)
            content = response.content.strip()
            
            # Clean JSON response
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            result = json.loads(content)
            
            # Validate tools exist
            valid_tools = [tool for tool in result.get("tools", []) if tool in available_tool_names]
            
            return {
                "tools": valid_tools,
                "required_parameters": result.get("required_parameters", []),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"DEBUG: Error in tool selection: {e}")
            # Fallback to simple mapping
            return self._fallback_tool_selection(intent, available_tool_names)
    
    def _fallback_tool_selection(self, intent: str, available_tools: List[str]) -> dict:
        """Fallback tool selection logic"""
        
        tool_mapping = {
            "book_flight": {
                "tools": ["book_flight"],
                "required_parameters": ["origin", "destination", "date"],
                "reasoning": "Flight booking requires origin, destination, and date"
            },
            "book_hotel": {
                "tools": ["book_hotel"],
                "required_parameters": ["city", "days"],
                "reasoning": "Hotel booking requires city and number of days"
            }
        }
        
        return tool_mapping.get(intent, {
            "tools": [],
            "required_parameters": [],
            "reasoning": "Unknown intent"
        })
