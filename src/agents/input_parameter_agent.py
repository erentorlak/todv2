"""
Input Parameter Agent - Slot filling for tool parameters
"""
from typing import Literal, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Command
import json

from ..schemas import DialogState
from ..config.llm_config import get_input_parameter_llm


class InputParameterAgent:
    """Agent for slot filling - extracting specific parameters for tools"""
    
    def __init__(self):
        self.llm = get_input_parameter_llm()
    
    def __call__(self, state: DialogState) -> Command[Literal["supervisor"]]:
        """Extract and fill missing parameters for selected tools"""
        
        # Get the latest user message
        messages = state.get("messages", [])
        current_intent = state.get("current_intent")
        current_params = state.get("extracted_parameters", {})
        selected_tools = state.get("selected_tools", [])
        dialog_context = state.get("dialog_context", {})
        required_parameters = dialog_context.get("required_parameters", [])
        
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break
        
        if not user_message:
            return Command(
                goto="supervisor",
                update={"dialog_context": {"error": "No user message to process"}}
            )
        
        print(f"DEBUG InputParameter - Processing: {user_message}")
        print(f"DEBUG InputParameter - Required params: {required_parameters}")
        print(f"DEBUG InputParameter - Current params: {current_params}")
        
        # Extract parameters using config-driven slot filling
        from ..config import get_missing_parameters, validate_parameter
        
        extracted_params = self._extract_parameters(
            user_message, 
            current_intent, 
            required_parameters, 
            current_params
        )
        
        # Merge with existing parameters
        updated_params = {**current_params, **extracted_params}
        
        # Check what's still missing
        missing_params = [p for p in required_parameters if not updated_params.get(p)]
        
        print(f"DEBUG InputParameter - Extracted: {extracted_params}")
        print(f"DEBUG InputParameter - Updated params: {updated_params}")
        print(f"DEBUG InputParameter - Still missing: {missing_params}")
        
        # Handle retry logic with 5-attempt limit
        retry_counts = dialog_context.get("retry_counts", {})
        max_retries = dialog_context.get("max_retries", 5)
        
        if missing_params:
            # Check retry counts for missing parameters
            needs_clarification = True  # Default to needing clarification when params are missing
            
            for param in missing_params:
                param_retries = retry_counts.get(param, 0)
                if param_retries >= max_retries:
                    print(f"DEBUG InputParameter - Max retries ({max_retries}) reached for parameter '{param}'")
                    # Generate final failure message and end conversation
                    failure_msg = f"I've tried several times to get the {param} from you, but I'm still not clear on what you need. Could you please start over with a complete request? For example: 'Book a flight from New York to Paris on December 25th'"
                    
                    return Command(
                        goto="generation",
                        update={
                            "extracted_parameters": updated_params,
                            "dialog_context": {
                                **dialog_context,
                                "parameter_collection_failed": True,
                                "failed_parameter": param,
                                "last_response_type": "parameter_failure"
                            },
                            "messages": state["messages"] + [{"role": "assistant", "content": failure_msg}]
                        }
                    )
            
            # If we made progress (extracted new params), don't ask for clarification yet
            if len(extracted_params) > 0:
                needs_clarification = False
                
            if needs_clarification:
                # Generate clarification and increment retry counts
                clarification_msg = self._generate_clarification_question(
                    current_intent, updated_params, missing_params
                )
                
                # Increment retry counts for missing parameters
                updated_retry_counts = retry_counts.copy()
                for param in missing_params:
                    updated_retry_counts[param] = updated_retry_counts.get(param, 0) + 1
                
                print(f"DEBUG InputParameter - Asking for clarification (attempt {updated_retry_counts}): {clarification_msg[:100]}...")
                
                return Command(
                    goto="generation",
                    update={
                        "extracted_parameters": updated_params,
                        "dialog_context": {
                            **dialog_context,
                            "needs_clarification": True,
                            "last_missing_params": missing_params,
                            "retry_counts": updated_retry_counts,
                            "last_response_type": "clarification"
                        },
                        "messages": state["messages"] + [{"role": "assistant", "content": clarification_msg}]
                    }
                )
        
        # Parameters complete or progress made - continue to supervisor
        return Command(
            goto="supervisor",
            update={
                "extracted_parameters": updated_params,
                "dialog_context": {
                    **dialog_context,
                    "last_missing_params": missing_params,
                    "needs_clarification": False,
                    "last_response_type": "parameter_progress"
                }
            }
        )
    
    def _extract_parameters(
        self, 
        user_input: str, 
        intent: str, 
        required_params: list, 
        current_params: dict
    ) -> Dict[str, Any]:
        """Extract specific parameters from user input using LLM"""
        
        # Identify missing parameters
        missing_params = [p for p in required_params if not current_params.get(p)]
        
        from ..config import get_intent_config, PARAMETER_TYPES
        
        # Get parameter definitions from config
        intent_config = get_intent_config(intent)
        if not intent_config:
            return {}
            
        param_definitions = []
        for param_name, param_config in intent_config.get("parameters", {}).items():
            param_type = param_config.get("type", "string")
            param_desc = param_config.get("description", param_name)
            type_desc = PARAMETER_TYPES.get(param_type, {}).get("description", "")
            param_definitions.append(f"- {param_name}: {param_desc} ({type_desc})")
        
        param_definitions_text = "\n".join(param_definitions)
        
        system_prompt = f"""You are a parameter extraction specialist. Extract specific parameters from user input for slot filling.

Current Intent: {intent}
Required Parameters: {required_params}
Currently Have: {current_params}
Still Need: {missing_params}

Parameter Definitions:
{param_definitions_text}

Extract ONLY the parameters that are mentioned in the user input. Do not make assumptions.

Respond with a JSON object containing only the extracted parameters:
{{
    "parameter_name": "extracted_value"
}}

If no parameters are found, return: {{}}"""
        
        user_prompt = f"""
User input: "{user_input}"

Extract any parameters mentioned in this input that we still need for the {intent} intent.
Focus on these missing parameters: {missing_params}
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
            
            # Validate extracted parameters are in required list
            valid_params = {k: v for k, v in result.items() if k in required_params}
            
            return valid_params
            
        except Exception as e:
            print(f"Error in parameter extraction: {e}")
            return {}
    
    def _generate_clarification_question(
        self, 
        intent_name: str,
        current_params: dict, 
        missing_params: list
    ) -> str:
        """Generate clarification question for missing parameters using config"""
        
        if not missing_params:
            return "I need some additional information to help you. Could you please provide more details?"
        
        from ..config import get_parameter_question
        
        # Build the question using config-defined questions
        if len(missing_params) == 1:
            param = missing_params[0]
            question = get_parameter_question(intent_name, param)
            return f"I need one more detail: {question}"
        elif len(missing_params) == 2:
            questions = [get_parameter_question(intent_name, p) for p in missing_params]
            return f"I need two more details: {questions[0]} and {questions[1]}"
        else:
            questions = [get_parameter_question(intent_name, p) for p in missing_params]
            return f"I need a few more details: {', '.join(questions[:-1])}, and {questions[-1]}"
