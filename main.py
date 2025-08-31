"""
Main Application - Terminal Chat Interface for Multi-Agent Dialog System
"""
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.schemas import DialogState
from src.agents import (
    SupervisorAgent,
    InputParameterAgent, 
    ToolChoosingAgent,
    ToolExecutingAgent,
    GenerationAgent
)

# Load environment variables
load_dotenv()

def create_dialog_graph():
    """Create the multi-agent dialog graph"""
    
    # Initialize agents
    supervisor = SupervisorAgent()
    input_parameter = InputParameterAgent()
    tool_choosing = ToolChoosingAgent() 
    tool_executing = ToolExecutingAgent()
    generation = GenerationAgent()
    
    # Create graph
    graph = StateGraph(DialogState)
    
    # Add nodes
    graph.add_node("supervisor", supervisor)
    graph.add_node("input_parameter", input_parameter)
    graph.add_node("tool_choosing", tool_choosing)
    graph.add_node("tool_executing", tool_executing)
    graph.add_node("generation", generation)
    
    # Set entry point
    graph.set_entry_point("supervisor")
    
    # Compile with memory
    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)
    
    return app

def run_chat():
    """Run the interactive chat interface"""
    
    print("🤖 Multi-Agent Dialog System")
    print("=" * 50)
    print("Welcome! I can help you with flight and hotel bookings.")
    print("Try: 'Book a flight from New York to Paris on Dec 25' or 'Book a hotel in London for 3 days'")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("=" * 50)
    
    # Create dialog app
    app = create_dialog_graph()
    
    # Initialize conversation
    thread_id = "user_session"
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n🤖 Assistant: Goodbye! Have a great day!")
                break
            
            if not user_input:
                continue
            
            # Process user input through the graph
            try:
                # Get current state from memory or create initial state
                try:
                    current_state = app.get_state(config)
                    if current_state.values:
                        # Append new user message to existing conversation
                        messages = current_state.values.get("messages", [])
                        messages.append({"role": "user", "content": user_input})
                        
                        # Update state with new message but preserve everything else
                        state_update = {
                            **current_state.values,
                            "messages": messages,
                            "dialog_context": {
                                **current_state.values.get("dialog_context", {}),
                                "needs_clarification": False,  # Reset since user provided new input
                                "last_response_type": "user_input"
                            }
                        }
                    else:
                        # First message - create initial state
                        state_update = {
                            "messages": [{"role": "user", "content": user_input}],
                            "current_intent": None,
                            "paused_intents": [],
                            "extracted_parameters": {},
                            "selected_tools": [],
                            "tool_results": {},
                            "dialog_context": {"last_response_type": "user_input"}
                        }
                except Exception:
                    # Fallback to initial state if memory access fails
                    state_update = {
                        "messages": [{"role": "user", "content": user_input}],
                        "current_intent": None,
                        "paused_intents": [],
                        "extracted_parameters": {},
                        "selected_tools": [],
                        "tool_results": {},
                        "dialog_context": {"last_response_type": "user_input"}
                    }
                
                # Run the graph with updated state
                result = app.invoke(state_update, config)
                
                # Get the assistant's response
                messages = result.get("messages", [])
                if messages and messages[-1]["role"] == "assistant":
                    assistant_response = messages[-1]["content"]
                    print(f"\n🤖 Assistant: {assistant_response}")
                else:
                    print("\n🤖 Assistant: I'm not sure how to help with that. Could you rephrase?")
                
                # Debug info (optional)
                if os.getenv("DEBUG", "false").lower() == "true":
                    print(f"\nDEBUG - Intent: {result.get('current_intent')}")
                    print(f"DEBUG - Parameters: {result.get('extracted_parameters')}")
                    print(f"DEBUG - Tools: {result.get('selected_tools')}")
                    
            except Exception as e:
                print(f"\n🤖 Assistant: Sorry, I encountered an error: {str(e)}")
                print("Please try rephrasing your request.")
                
        except KeyboardInterrupt:
            print("\n\n🤖 Assistant: Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue

if __name__ == "__main__":
    # Check for Google AI API key
    if not os.getenv("GOOGLE_AI_API_KEY"):
        print("❌ Error: GOOGLE_AI_API_KEY not found in environment variables.")
        print("Please create a .env file with your Google AI API key:")
        print("GOOGLE_AI_API_KEY=your_api_key_here")
        print("MODEL_NAME=gemini-2.5-flash")
        exit(1)
    
    # Display model information
    from src.config.llm_config import get_model_info
    model_info = get_model_info()
    print(f"🤖 Using {model_info['provider']} - {model_info['model_name']}")
    
    run_chat()
