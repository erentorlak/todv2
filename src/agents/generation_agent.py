"""
Generation Agent - Generate natural language responses and clarification questions
"""
from typing import Literal, List
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command

from ..schemas import DialogState
from ..config.llm_config import get_generation_llm


class GenerationAgent:
    """Agent for generating natural language responses"""
    
    def __init__(self):
        self.llm = get_generation_llm()
    
    def __call__(self, state: DialogState) -> Command[Literal["supervisor", "__end__"]]:
        """Generate response based on state (simplified)"""
        
        current_intent = state.get("current_intent")
        parameters = state.get("extracted_parameters", {})
        tool_results = state.get("tool_results", {})
        dialog_context = state.get("dialog_context", {})
        messages = state.get("messages", [])
        
        print(f"DEBUG Generation - Intent: {current_intent}, Results: {bool(tool_results)}")
        
        # Check if InputParameter already added a message that we should just pass through
        if messages and messages[-1].get("role") == "assistant":
            # InputParameter added a clarification message, just end to wait for user
            print("DEBUG Generation - Passing through message from InputParameter")
            return Command(goto="__end__")
        
        # Generate response based on tool results
        if tool_results:
            response = self._generate_response_from_results(current_intent, tool_results, parameters)
            print(f"DEBUG Generation - Tool results response: {response[:100]}...")
            
            # Check if all tools are completed
            all_tools_completed = dialog_context.get("all_tools_completed", False)
            next_destination = "__end__" if all_tools_completed else "supervisor"
            
            return Command(
                goto=next_destination,
                update={
                    "messages": messages + [{"role": "assistant", "content": response}]
                }
            )
        
        # Generate general acknowledgment response  
        else:
            response = self._generate_general_response(current_intent, parameters)
            print(f"DEBUG Generation - General response: {response[:100]}...")
            
            return Command(
                goto="supervisor",
                update={
                    "messages": messages + [{"role": "assistant", "content": response}]
                }
            )
    
    def _generate_response_from_results(
        self, 
        intent: str, 
        tool_results: dict, 
        parameters: dict
    ) -> str:
        """Generate response based on tool execution results (simplified)"""
        
        # Check if any tools had errors
        has_errors = any(result.get("error") or not result.get("success", True) 
                        for result in tool_results.values() if isinstance(result, dict))
        
        system_prompt = """You are a helpful assistant that summarizes task completion results.
        
        Guidelines:
        - Be conversational and friendly
        - If successful: Confirm what was accomplished with key details
        - If errors: Explain what went wrong and suggest retry
        - Keep response concise but informative
        """
        
        user_prompt = f"""
        User Intent: {intent.replace('_', ' ')}
        Parameters: {parameters}
        Tool Results: {tool_results}
        
        Generate a helpful response summarizing the results.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            # Fallback response if LLM fails
            if has_errors:
                return f"I encountered some issues with your {intent.replace('_', ' ')} request. Please try again."
            else:
                return f"Great! I've completed your {intent.replace('_', ' ')} request."
    
    def _generate_general_response(self, intent: str, parameters: dict) -> str:
        """Generate general response when no specific action is needed"""
        
        system_prompt = """You are a helpful assistant that acknowledges user requests.
        
        Guidelines:
        - Acknowledge what the user is trying to do
        - Explain what will happen next
        - Be encouraging and helpful
        """
        
        user_prompt = f"""
        User Intent: {intent}
        Extracted Parameters: {parameters}
        
        Please generate a helpful acknowledgment of what the user wants to do.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
