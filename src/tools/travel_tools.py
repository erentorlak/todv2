"""
Travel Tools - Simplified booking tools
"""
from typing import Dict, Any

def search_flights(origin: str, destination: str, date: str) -> Dict[str, Any]:
    """Search for available flights"""
    
    # Mock flight search results
    flight_options = [
        {"flight_id": "FL001", "airline": "SkyAir", "price": 299, "duration": "2h 15m", "departure": "08:30"},
        {"flight_id": "FL002", "airline": "CloudJet", "price": 389, "duration": "2h 45m", "departure": "14:20"},
        {"flight_id": "FL003", "airline": "AirExpress", "price": 450, "duration": "1h 50m", "departure": "18:45"},
    ]
    
    return {
        "status": "success",
        "route": f"{origin} to {destination}",
        "date": date,
        "flight_options": flight_options,
        "message": f"Found {len(flight_options)} flights from {origin} to {destination} on {date}"
    }

def book_flight(origin: str, destination: str, date: str) -> Dict[str, Any]:
    """Book a flight with origin, destination, and date"""
    
    # Mock flight booking examples
    flight_examples = [
        {"flight_id": "FL001", "airline": "SkyAir", "price": 299, "duration": "2h 15m"},
        {"flight_id": "FL002", "airline": "CloudJet", "price": 389, "duration": "2h 45m"},
        {"flight_id": "FL003", "airline": "AirExpress", "price": 450, "duration": "1h 50m"},
        {"flight_id": "FL004", "airline": "QuickFly", "price": 325, "duration": "3h 10m"},
    ]
    
    # Select flight based on route (simple hash for consistency)
    route_hash = hash(f"{origin}_{destination}") % len(flight_examples)
    selected_flight = flight_examples[route_hash]
    
    return {
        "status": "success",
        "booking_id": f"BK{route_hash + 1000}",
        "flight": {
            "origin": origin,
            "destination": destination,
            "date": date,
            **selected_flight
        },
        "message": f"Flight booked successfully from {origin} to {destination} on {date}"
    }

def book_hotel(city: str, days: int) -> Dict[str, Any]:
    """Book a hotel with city and number of days"""
    
    # Convert days to int if it's a string
    if isinstance(days, str):
        try:
            days = int(days)
        except ValueError:
            return {
                "status": "error",
                "message": f"Invalid number of days: {days}"
            }
    
    # Mock hotel booking examples
    hotel_examples = [
        {"hotel_id": "HT001", "name": "Grand Plaza Hotel", "price_per_night": 120, "rating": 4.5},
        {"hotel_id": "HT002", "name": "City Center Inn", "price_per_night": 89, "rating": 4.2},
        {"hotel_id": "HT003", "name": "Luxury Suites", "price_per_night": 250, "rating": 4.8},
        {"hotel_id": "HT004", "name": "Budget Stay", "price_per_night": 65, "rating": 3.9},
    ]
    
    # Select hotel based on city (simple hash for consistency)
    city_hash = hash(city.lower()) % len(hotel_examples)
    selected_hotel = hotel_examples[city_hash]
    
    total_price = selected_hotel["price_per_night"] * days
    
    return {
        "status": "success",
        "booking_id": f"HB{city_hash + 2000}",
        "hotel": {
            "city": city,
            "days": days,
            "total_price": total_price,
            **selected_hotel
        },
        "message": f"Hotel booked successfully in {city} for {days} days"
    }

def search_hotels(destination: str, days: int) -> Dict[str, Any]:
    """Search for available hotels"""
    
    # Mock hotel search results
    hotel_options = [
        {"hotel_id": "HT001", "name": "Grand Plaza Hotel", "price_per_night": 120, "rating": 4.5},
        {"hotel_id": "HT002", "name": "City Center Inn", "price_per_night": 89, "rating": 4.2},
        {"hotel_id": "HT003", "name": "Luxury Suites", "price_per_night": 250, "rating": 4.8},
        {"hotel_id": "HT004", "name": "Budget Stay", "price_per_night": 65, "rating": 3.9},
    ]
    
    return {
        "status": "success", 
        "destination": destination,
        "days": days,
        "hotel_options": hotel_options,
        "message": f"Found {len(hotel_options)} hotels in {destination} for {days} days"
    }

def get_weather(destination: str, date: str) -> Dict[str, Any]:
    """Get weather information for a destination and date"""
    
    # Mock weather data
    weather_options = [
        {"condition": "Sunny", "temperature": "22°C", "humidity": "45%"},
        {"condition": "Partly Cloudy", "temperature": "18°C", "humidity": "60%"},
        {"condition": "Rainy", "temperature": "15°C", "humidity": "85%"},
        {"condition": "Clear", "temperature": "25°C", "humidity": "40%"},
    ]
    
    # Simple hash to get consistent weather for same destination
    weather_hash = hash(destination.lower()) % len(weather_options)
    weather = weather_options[weather_hash]
    
    return {
        "status": "success",
        "destination": destination,
        "date": date,
        "weather": weather,
        "message": f"Weather in {destination} on {date}: {weather['condition']}, {weather['temperature']}"
    }
