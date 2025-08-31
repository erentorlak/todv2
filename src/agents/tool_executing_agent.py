"""
Tool Executing Agent - Execute selected tools with minimal LLM usage
"""
from typing import Literal, Dict, Any
from langgraph.types import Command

from ..schemas import DialogState
from ..tools import tool_registry


class ToolExecutingAgent:
    """Agent for executing tools with minimal LLM involvement"""
    
    def __call__(self, state: DialogState) -> Command[Literal["supervisor"]]:
        """Execute the selected tools with parameter validation"""
        
        selected_tools = state.get("selected_tools", [])
        parameters = state.get("extracted_parameters", {})
        dialog_context = state.get("dialog_context", {})
        required_parameters = dialog_context.get("required_parameters", [])
        
        print(f"DEBUG ToolExecuting - Tools: {selected_tools}, Params: {parameters}")
        print(f"DEBUG ToolExecuting - Required params: {required_parameters}")
        
        if not selected_tools:
            return Command(
                goto="supervisor",
                update={
                    "tool_results": {},
                    "dialog_context": {
                        **dialog_context,
                        "execution_error": "No tools selected"
                    }
                }
            )
        
        # Validate that all required parameters are present before execution
        missing_params = [p for p in required_parameters if not parameters.get(p)]
        if missing_params:
            print(f"DEBUG ToolExecuting - Missing required params: {missing_params}")
            return Command(
                goto="supervisor",
                update={
                    "dialog_context": {
                        **dialog_context,
                        "execution_blocked": True,
                        "missing_parameters": missing_params,
                        "last_response_type": "parameter_validation_failed"
                    }
                }
            )
        
        # Execute tools using config-driven conditional execution
        from ..tools import tool_registry
        
        tool_execution_order = dialog_context.get("tool_execution_order", [])
        current_batch = dialog_context.get("current_tool_batch", 0)
        completed_tools = dialog_context.get("completed_tools", [])
        
        print(f"DEBUG ToolExecuting - Execution order: {tool_execution_order}")
        print(f"DEBUG ToolExecuting - Current batch: {current_batch}")
        print(f"DEBUG ToolExecuting - Completed tools: {completed_tools}")
        
        if current_batch >= len(tool_execution_order):
            # All tool batches completed
            return Command(
                goto="supervisor",
                update={
                    "dialog_context": {
                        **dialog_context,
                        "all_tools_completed": True
                    }
                }
            )
        
        # Execute current batch of tools
        current_batch_tools = tool_execution_order[current_batch]
        batch_results = {}
        batch_success = True
        
        for tool_name in current_batch_tools:
            try:
                # Use tool registry validation
                validation_result = tool_registry.validate_tool_parameters(tool_name, parameters)
                if not validation_result["valid"]:
                    batch_results[tool_name] = {
                        "error": f"Parameter validation failed: {validation_result['error']}",
                        "success": False
                    }
                    batch_success = False
                    continue
                
                # Execute the tool
                result = self._execute_tool(tool_name, parameters)
                batch_results[tool_name] = {**result, "success": True}
                completed_tools.append(tool_name)
                print(f"DEBUG ToolExecuting - {tool_name} result: {result}")
                
            except Exception as e:
                batch_results[tool_name] = {
                    "error": str(e),
                    "success": False
                }
                batch_success = False
                print(f"DEBUG ToolExecuting - {tool_name} error: {e}")
        
        # Update results and move to next batch
        all_results = {**state.get("tool_results", {}), **batch_results}
        next_batch = current_batch + 1 if batch_success else current_batch
        
        return Command(
            goto="supervisor",
            update={
                "tool_results": all_results,
                "dialog_context": {
                    **dialog_context,
                    "current_tool_batch": next_batch,
                    "completed_tools": completed_tools,
                    "batch_execution_success": batch_success
                }
            }
        )
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool with parameters using config-driven approach"""
        
        from ..config import get_tool_config
        
        tool_func = tool_registry.get_tool(tool_name)
        if not tool_func:
            return {"error": f"Tool {tool_name} not found"}
        
        tool_config = get_tool_config(tool_name)
        if not tool_config:
            return {"error": f"Tool configuration not found: {tool_name}"}
        
        # Get required parameters from config
        required_params = tool_config.get("parameters", [])
        
        try:
            # Build arguments dynamically from config
            kwargs = {}
            for param in required_params:
                if param in parameters:
                    kwargs[param] = parameters[param]
                else:
                    kwargs[param] = None  # Let the tool handle missing params
            
            # Execute the tool with dynamic parameters
            result = tool_func(**kwargs)
            return result if isinstance(result, dict) else {"result": result}
                
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
