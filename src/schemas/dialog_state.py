from typing import TypedDict, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage


class DialogState(TypedDict):
    """Simplified state for the config-driven dialog system"""
    messages: List[BaseMessage]          # Conversation history
    current_intent: Optional[str]        # Active intent (can change)
    paused_intents: List[Dict[str, Any]] # Paused intents with their parameters
    extracted_parameters: Dict[str, Any] # Current intent parameters
    selected_tools: List[str]            # Tools chosen for current intent
    tool_results: Dict[str, Any]         # Latest tool execution results
    dialog_context: Dict[str, Any]       # Simplified session context:
                                        # - retry_counts: Dict[str, int] - Per parameter retry tracking (max 5)
                                        # - awaiting_confirmation: Dict - Intent switch confirmation state
                                        # - current_tool_batch: int - Which batch of tools we're executing
                                        # - completed_tools: List[str] - Successfully completed tools
