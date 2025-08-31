
"""
Supervisor Agent - Orchestrates dialog flow with intent detection and agent selection
"""
from typing import Literal, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command
import json

from ..schemas import DialogState
from ..config.llm_config import get_supervisor_llm


class SupervisorAgent:
    """Supervisor agent that detects intent and orchestrates the dialog flow"""
    
    def __init__(self):
        self.llm = get_supervisor_llm()
    
    def __call__(self, state: DialogState) -> Command[Literal["tool_choosing", "input_parameter", "tool_executing", "generation", "__end__"]]:
        """Detect intent and route to appropriate agent"""
        
        messages = state.get("messages", [])
        current_intent = state.get("current_intent")
        extracted_parameters = state.get("extracted_parameters", {})
        selected_tools = state.get("selected_tools", [])
        tool_results = state.get("tool_results", {})
        dialog_context = state.get("dialog_context", {})
        
        print(f"DEBUG Supervisor - Current Intent: {current_intent}, Tools: {selected_tools}, Results: {bool(tool_results)}")
        
        # Check if conversation should end
        if self._should_end_conversation(state):
            return Command(goto="__end__")
        
        # Check if awaiting user confirmation for intent switch
        awaiting_confirmation = dialog_context.get("awaiting_confirmation")
        if awaiting_confirmation:
            return self._handle_intent_switch_confirmation(state, awaiting_confirmation)
        
        # Detect intent from latest user message (supervisor's primary job)
        detected_intent = self._detect_user_intent(messages)
        print(f"DEBUG Supervisor - Detected intent: '{detected_intent}'")
        
        # Handle initial intent detection (when current_intent is None)
        if current_intent is None and detected_intent is not None:
            print(f"DEBUG Supervisor - Initial intent detected: '{detected_intent}'")
            return Command(goto="tool_choosing", update={"current_intent": detected_intent})
        
        # Check for intent change (when switching from one intent to another)
        intent_changed = detected_intent != current_intent and detected_intent is not None and current_intent is not None
        
        if intent_changed:
            print(f"DEBUG Supervisor - Intent change detected: '{current_intent}' → '{detected_intent}'")
            # Ask for confirmation before switching
            return self._request_intent_switch_confirmation(state, current_intent, detected_intent)
        
        # Decide next action based on current state
        next_action = self._decide_next_action(state)
        print(f"DEBUG Supervisor - Next Action: {next_action}")
        
        if next_action == "tool_choosing":
            return Command(goto="tool_choosing", update={"current_intent": detected_intent or current_intent})
        elif next_action == "input_parameter":
            return Command(goto="input_parameter")
        elif next_action == "tool_executing":
            return Command(goto="tool_executing")
        elif next_action == "generation":
            return Command(goto="generation")
        else:
            return Command(goto="__end__")
    
    def _detect_user_intent(self, messages: list) -> str:
        """Detect user intent from the latest message using LLM"""
        
        if not messages or messages[-1]["role"] != "user":
            return None
        
        user_message = messages[-1]["content"]
        
        # Get available intents from config
        from ..config import get_available_intents, INTENTS, detect_intent_from_keywords
        
        # Try keyword-based detection first (faster)
        detected = detect_intent_from_keywords(user_message)
        if detected:
            return detected
        
        # Fall back to LLM-based detection
        available_intents = get_available_intents()
        intent_descriptions = []
        for intent in available_intents:
            intent_config = INTENTS.get(intent, {})
            description = intent_config.get("description", intent)
            intent_descriptions.append(f"- {intent}: {description}")
        
        intents_list = "\n".join(intent_descriptions)
        
        system_prompt = f"""You are an intent detection specialist. Analyze the user's message and detect their primary intent.

Available intents:
{intents_list}
- general: General conversation, questions, or unclear intent

Respond with ONLY the intent name from the list above, or 'general' if unclear."""
        
        user_prompt = f"User message: '{user_message}'\n\nWhat is the user's intent?"
        
        messages_for_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages_for_llm)
            intent = response.content.strip().lower()
            
            valid_intents = get_available_intents() + ["general"]
            if intent in valid_intents:
                return intent if intent != "general" else None
            else:
                return None
                
        except Exception as e:
            print(f"DEBUG: Error in intent detection: {e}")
            return None
    
    def _decide_next_action(self, state: DialogState) -> str:
        """Decide next action based on conversation state"""
        
        current_intent = state.get("current_intent")
        selected_tools = state.get("selected_tools", [])
        tool_results = state.get("tool_results", {})
        extracted_parameters = state.get("extracted_parameters", {})
        dialog_context = state.get("dialog_context", {})
        
        # Priority logic exactly as you specified:
        
        # 1. New Tool Needed? - If no tools selected but have intent
        if current_intent and not selected_tools:
            return "tool_choosing"
        
        # 2. Parameters Ready? - If tool selected but parameters incomplete
        if selected_tools and current_intent:
            # Get required parameters from dialog context (set by tool_choosing agent)
            required_params = dialog_context.get("required_parameters", [])
            missing_params = [p for p in required_params if not extracted_parameters.get(p)]
            if missing_params:
                # Check if this is a repeated attempt with no new parameters extracted
                if dialog_context.get("last_missing_params") == missing_params:
                    # Same missing params as before - input_parameter agent should handle clarification
                    return "input_parameter"
                else:
                    # Try to extract parameters one more time
                    return "input_parameter"
        
        # 3. Execute Tool? - If tool selected and parameters complete
        if selected_tools and not tool_results:
            # Check if all required parameters are available
            required_params = dialog_context.get("required_parameters", [])
            complete_params = all(extracted_parameters.get(p) for p in required_params)
            if complete_params:
                return "tool_executing"
        
        # 4. Generate Response? - If tool results exist
        if tool_results:
            # Check if we already generated a response
            last_response_type = dialog_context.get("last_response_type")
            if last_response_type == "generated":
                return "__end__"  # Already generated response, end conversation
            else:
                return "generation"
        
        # Default - no clear action, end conversation
        return "__end__"
    
    def _should_end_conversation(self, state: DialogState) -> bool:
        """Determine if conversation should end"""
        
        # End if explicitly requested
        dialog_context = state.get("dialog_context", {})
        if dialog_context.get("end_conversation"):
            return True
        
        # End if user says goodbye
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]["content"].lower()
            goodbye_words = ["bye", "goodbye", "exit", "quit", "thanks", "thank you"]
            if any(word in last_message for word in goodbye_words):
                return True
        
        return False
    
    def _request_intent_switch_confirmation(self, state: DialogState, current_intent: str, new_intent: str) -> Command:
        """Request user confirmation for intent switch"""
        
        # Generate confirmation message using config
        from ..config import get_intent_config
        
        current_config = get_intent_config(current_intent)
        new_config = get_intent_config(new_intent)
        
        current_name = current_config.get("description", current_intent) if current_config else current_intent
        new_name = new_config.get("description", new_intent) if new_config else new_intent
        
        confirmation_msg = f"I notice you want to start {new_name}, but we were working on {current_name}. Would you like me to pause the {current_name} and start {new_name}? (Reply with 'yes' to switch or 'no' to continue with {current_name})"
        
        return Command(
            goto="__end__",
            update={
                "messages": state["messages"] + [{"role": "assistant", "content": confirmation_msg}],
                "dialog_context": {
                    **state.get("dialog_context", {}),
                    "awaiting_confirmation": {
                        "type": "intent_switch",
                        "from": current_intent,
                        "to": new_intent
                    },
                    "last_response_type": "confirmation_request"
                }
            }
        )
    
    def _handle_intent_switch_confirmation(self, state: DialogState, awaiting_confirmation: dict) -> Command:
        """Handle user's response to intent switch confirmation"""
        
        messages = state.get("messages", [])
        if not messages or messages[-1]["role"] != "user":
            return Command(goto="__end__")
        
        user_response = messages[-1]["content"].lower().strip()
        from_intent = awaiting_confirmation["from"]
        to_intent = awaiting_confirmation["to"]
        
        # Check user's response
        if any(word in user_response for word in ["yes", "y", "switch", "pause"]):
            # User confirmed switch - pause current intent and switch
            return self._execute_intent_switch(state, from_intent, to_intent)
        elif any(word in user_response for word in ["no", "n", "continue", "keep"]):
            # User wants to continue with current intent - clear confirmation state
            return Command(
                goto="input_parameter",  # Continue with current intent
                update={
                    "dialog_context": {
                        **state.get("dialog_context", {}),
                        "awaiting_confirmation": None,
                        "last_response_type": "user_input"
                    }
                }
            )
        else:
            # Unclear response - ask again
            clarification_msg = "Please respond with 'yes' to switch or 'no' to continue with the current task."
            return Command(
                goto="__end__",
                update={
                    "messages": state["messages"] + [{"role": "assistant", "content": clarification_msg}]
                }
            )
    
    def _execute_intent_switch(self, state: DialogState, from_intent: str, to_intent: str) -> Command:
        """Execute the intent switch by pausing current and starting new"""
        
        current_params = state.get("extracted_parameters", {})
        current_tools = state.get("selected_tools", [])
        paused_intents = state.get("paused_intents", [])
        
        # Create paused intent entry
        paused_intent = {
            "intent": from_intent,
            "parameters": current_params,
            "tools": current_tools,
            "paused_at": "parameter_collection"  # Could be extended for other pause points
        }
        
        # Add to paused intents (remove any existing entry for this intent first)
        updated_paused = [pi for pi in paused_intents if pi.get("intent") != from_intent]
        updated_paused.append(paused_intent)
        
        print(f"DEBUG Supervisor - Paused '{from_intent}' with params: {current_params}")
        print(f"DEBUG Supervisor - Starting '{to_intent}'")
        
        return Command(
            goto="tool_choosing",
            update={
                "current_intent": to_intent,
                "extracted_parameters": {},
                "selected_tools": [],
                "tool_results": {},
                "paused_intents": updated_paused,
                "dialog_context": {
                    "intent_switched": True,
                    "previous_intent": from_intent,
                    "awaiting_confirmation": None,
                    "retry_counts": {},  # Reset retry counts for new intent
                    "max_retries": 5,
                    "last_response_type": "intent_switch"
                }
            }
        )
