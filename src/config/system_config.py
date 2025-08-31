"""
System Configuration - Defines intents, tools, and their relationships
This file makes the system truly modular - add new intents/tools here
"""
from typing import Dict, List, Any, Optional, Callable
import re
from datetime import datetime

# =============================================================================
# PARAMETER VALIDATION FUNCTIONS
# =============================================================================

def validate_string(value: Any) -> bool:
    """Validate string parameter"""
    return isinstance(value, str) and len(value.strip()) > 0

def validate_int(value: Any) -> bool:
    """Validate integer parameter"""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False

def validate_date(value: Any) -> bool:
    """Validate date parameter (accepts various formats)"""
    if not isinstance(value, str):
        return False
    
    # Common date patterns
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # 2023-12-25
        r'\d{2}/\d{2}/\d{4}',  # 12/25/2023
        r'\d{1,2}/\d{1,2}/\d{4}',  # 1/1/2023
        r'[A-Za-z]+ \d{1,2}',  # December 25, Jan 1
        r'\d{1,2} [A-Za-z]+',  # 25 December, 1 Jan
    ]
    
    return any(re.search(pattern, value) for pattern in date_patterns)

# =============================================================================
# PARAMETER TYPE REGISTRY
# =============================================================================

PARAMETER_TYPES = {
    "string": {
        "validator": validate_string,
        "description": "Text value"
    },
    "int": {
        "validator": validate_int,
        "description": "Numeric value"
    },
    "date": {
        "validator": validate_date,
        "description": "Date in various formats (YYYY-MM-DD, MM/DD/YYYY, December 25, etc.)"
    }
}

# =============================================================================
# TOOLS CONFIGURATION
# =============================================================================

TOOLS = {
    "search_flights": {
        "function": "travel_tools.search_flights",  # Module.function path
        "description": "Search for available flights",
        "parameters": ["origin", "destination", "date"],
        "returns": "flight_options"  # What this tool produces
    },
    
    "book_flight": {
        "function": "travel_tools.book_flight", 
        "description": "Book a specific flight",
        "parameters": ["origin", "destination", "date"],
        "requires": ["flight_options"],  # Depends on search_flights output
        "returns": "booking_confirmation"
    },
    
    "search_hotels": {
        "function": "travel_tools.search_hotels",
        "description": "Search for hotels",
        "parameters": ["destination", "days"],
        "returns": "hotel_options"
    },
    
    "book_hotel": {
        "function": "travel_tools.book_hotel",
        "description": "Book a specific hotel", 
        "parameters": ["destination", "days"],
        "requires": ["hotel_options"],
        "returns": "hotel_booking"
    },
    
    "get_weather": {
        "function": "travel_tools.get_weather",
        "description": "Get weather information",
        "parameters": ["destination", "date"],
        "returns": "weather_info"
    }
}

# =============================================================================
# INTENTS CONFIGURATION  
# =============================================================================

INTENTS = {
    "book_flight": {
        "description": "Book airline tickets",
        "tools": ["search_flights", "book_flight"],  # Sequential execution
        "parameters": {
            "origin": {
                "type": "string",
                "description": "Departure city or airport",
                "question": "Which city or airport are you departing from?",
                "required": True
            },
            "destination": {
                "type": "string", 
                "description": "Arrival city or airport",
                "question": "Where would you like to fly to?",
                "required": True
            },
            "date": {
                "type": "date",
                "description": "Travel date",
                "question": "What date would you like to travel?",
                "required": True
            }
        }
    },
    
    "book_hotel": {
        "description": "Book hotel accommodation",
        "tools": ["search_hotels", "book_hotel"],
        "parameters": {
            "destination": {
                "type": "string",
                "description": "City or location for hotel",
                "question": "Which city do you need a hotel in?",
                "required": True
            },
            "days": {
                "type": "int",
                "description": "Number of days to stay", 
                "question": "How many days will you be staying?",
                "required": True
            }
        }
    },
    
    "plan_vacation": {
        "description": "Plan a complete vacation with flights, hotel, and weather",
        "tools": ["search_flights", "search_hotels", "get_weather", "book_flight", "book_hotel"],
        "parameters": {
            "origin": {
                "type": "string",
                "description": "Where you're traveling from",
                "question": "Where are you traveling from?",
                "required": True
            },
            "destination": {
                "type": "string",
                "description": "Vacation destination", 
                "question": "Where would you like to go on vacation?",
                "required": True
            },
            "date": {
                "type": "date",
                "description": "Travel start date",
                "question": "When would you like to start your vacation?",
                "required": True
            },
            "days": {
                "type": "int",
                "description": "Length of vacation",
                "question": "How many days will your vacation be?",
                "required": True
            }
        }
    }
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_intent_config(intent_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific intent"""
    return INTENTS.get(intent_name)

def get_tool_config(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific tool"""
    return TOOLS.get(tool_name)

def get_available_intents() -> List[str]:
    """Get list of all available intents"""
    return list(INTENTS.keys())

def get_available_tools() -> List[str]:
    """Get list of all available tools"""
    return list(TOOLS.keys())

def validate_parameter(param_name: str, value: Any, intent_name: str) -> bool:
    """Validate a parameter value for a given intent"""
    intent_config = get_intent_config(intent_name)
    if not intent_config:
        return False
    
    param_config = intent_config.get("parameters", {}).get(param_name)
    if not param_config:
        return False
    
    param_type = param_config.get("type", "string")
    type_config = PARAMETER_TYPES.get(param_type)
    if not type_config:
        return False
    
    return type_config["validator"](value)

def get_tool_execution_order(intent_name: str) -> List[List[str]]:
    """Get tool execution order considering dependencies
    Returns list of lists - each inner list can be executed in parallel"""
    
    intent_config = get_intent_config(intent_name)
    if not intent_config:
        return []
    
    tools = intent_config.get("tools", [])
    if not tools:
        return []
    
    # Build dependency graph
    remaining_tools = set(tools)
    execution_order = []
    
    while remaining_tools:
        # Find tools that can run now (no unmet dependencies)
        ready_tools = []
        for tool in remaining_tools:
            tool_config = get_tool_config(tool)
            if not tool_config:
                continue
                
            requires = tool_config.get("requires", [])
            # Tool is ready if all its dependencies are already executed
            if all(dep in [t for batch in execution_order for t in batch] for dep in requires):
                ready_tools.append(tool)
        
        if not ready_tools:
            # No tools can run - break circular dependency by taking first remaining
            ready_tools = [list(remaining_tools)[0]]
        
        execution_order.append(ready_tools)
        remaining_tools -= set(ready_tools)
    
    return execution_order

def get_missing_parameters(intent_name: str, current_params: Dict[str, Any]) -> List[str]:
    """Get list of missing required parameters for an intent"""
    intent_config = get_intent_config(intent_name)
    if not intent_config:
        return []
    
    missing = []
    for param_name, param_config in intent_config.get("parameters", {}).items():
        if param_config.get("required", False) and not current_params.get(param_name):
            missing.append(param_name)
    
    return missing

def get_parameter_question(intent_name: str, param_name: str) -> str:
    """Get the question to ask for a specific parameter"""
    intent_config = get_intent_config(intent_name)
    if not intent_config:
        return f"Could you please provide the {param_name}?"
    
    param_config = intent_config.get("parameters", {}).get(param_name, {})
    return param_config.get("question", f"Could you please provide the {param_name}?")

# =============================================================================
# INTENT DETECTION PATTERNS
# =============================================================================

INTENT_DETECTION_KEYWORDS = {
    "book_flight": [
        "book flight", "flight booking", "airline ticket", "plane ticket",
        "fly to", "flight to", "book airplane", "air travel"
    ],
    "book_hotel": [
        "book hotel", "hotel booking", "hotel room", "accommodation",
        "stay in", "hotel in", "reserve hotel"
    ],
    "plan_vacation": [
        "plan vacation", "vacation planning", "trip planning", "holiday planning",
        "organize trip", "plan trip", "vacation package", "plan my vacation"
    ]
}

def detect_intent_from_keywords(user_message: str) -> Optional[str]:
    """Simple keyword-based intent detection fallback"""
    user_message_lower = user_message.lower()
    
    # Score each intent based on keyword matches
    intent_scores = {}
    for intent, keywords in INTENT_DETECTION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in user_message_lower)
        if score > 0:
            intent_scores[intent] = score
    
    if intent_scores:
        # Return intent with highest score
        return max(intent_scores, key=intent_scores.get)
    
    return None