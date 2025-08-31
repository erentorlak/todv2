"""
Centralized LLM Configuration
Manages LLM settings for all agents
"""
import os
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

class LLMConfig:
    """Centralized LLM configuration for all agents"""
    
    def __init__(self):
        # Ensure environment variables are loaded
        load_dotenv()
        
        # Load configuration from environment
        self.google_api_key = os.getenv("GOOGLE_AI_API_KEY")
       # self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")  # Default to gemini-2.5-flash
        self.model_name = os.getenv("MODEL_NAME", "gemma-3-27b-it")  # Default to gemini-2.5-flash
        
        # Model-specific configurations
        self.model_configs = {
            "supervisor": {
                "temperature": 0.1,  # Very consistent for routing decisions
                "max_tokens": 50,    # Short responses for routing
            },
            "input_parameter": {
                "temperature": 0.2,  # Consistent for parameter extraction
                "max_tokens": 100,   # JSON parameter responses
            },
            "tool_choosing": {
                "temperature": 0.1,  # Very consistent for tool selection
                "max_tokens": 200,   # Tool selection reasoning
            },
            "generation": {
                "temperature": 0.7,  # More creative for user responses
                "max_tokens": 500,   # Longer responses
            }
        }
        
        # Cache for LLM instances
        self._llm_cache = {}
    
    def get_llm(self, agent_type: str) -> BaseChatModel:
        """Get LLM instance for a specific agent type"""
        
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_AI_API_KEY not found in environment variables. "
                "Please set your Google AI API key in .env file"
            )
        
        # Return cached instance if available
        if agent_type in self._llm_cache:
            return self._llm_cache[agent_type]
        
        # Get agent-specific configuration
        config = self.model_configs.get(agent_type, self.model_configs["generation"])
        
        # Create LLM instance
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.google_api_key,
            convert_system_message_to_human=True  # Required for Gemini
        )
        
        # Cache the instance
        self._llm_cache[agent_type] = llm
        
        return llm
    
    def get_model_info(self) -> dict:
        """Get current model information"""
        return {
            "model_name": self.model_name,
            "provider": "Google AI",
            "api_key_set": bool(self.google_api_key),
            "available_configs": list(self.model_configs.keys())
        }

# Global LLM configuration instance
llm_config = LLMConfig()

# Convenience functions for agents
def get_supervisor_llm() -> BaseChatModel:
    """Get LLM configured for supervisor agent"""
    return llm_config.get_llm("supervisor")

def get_input_parameter_llm() -> BaseChatModel:
    """Get LLM configured for input parameter agent"""
    return llm_config.get_llm("input_parameter")

def get_tool_choosing_llm() -> BaseChatModel:
    """Get LLM configured for tool choosing agent"""
    return llm_config.get_llm("tool_choosing")

def get_generation_llm() -> BaseChatModel:
    """Get LLM configured for generation agent"""
    return llm_config.get_llm("generation")

def get_model_info() -> dict:
    """Get current model information"""
    return llm_config.get_model_info()