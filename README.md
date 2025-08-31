# Multi-Agent Dialog System

A sophisticated multi-agent conversational AI system built with LangGraph and Google AI (Gemini) that handles complex travel booking conversations through intelligent agent orchestration.

## 🚀 Features

- **Multi-Agent Architecture**: Five specialized agents working together
- **Intent Detection**: Smart understanding of user goals (flight/hotel booking)
- **Parameter Extraction**: Automatic extraction of booking details
- **Tool Selection**: Intelligent choice of appropriate tools
- **Conversation Memory**: Persistent chat history and context
- **Interactive Terminal Interface**: Easy-to-use command-line chat

## 🏗️ Architecture

### Agent System
The system uses a **StateGraph** with five specialized agents:

1. **SupervisorAgent** - Orchestrates the conversation flow and detects user intent
2. **InputParameterAgent** - Extracts and validates booking parameters
3. **ToolChoosingAgent** - Selects appropriate tools for the current intent
4. **ToolExecutingAgent** - Executes the chosen tools
5. **GenerationAgent** - Generates natural language responses

### Data Flow
```
User Input → Supervisor → Intent Detection → Tool Selection → Parameter Extraction → Tool Execution → Response Generation
```

## 📋 Prerequisites

- Python 3.8+
- Google AI API key
- Windows PowerShell (for Windows users)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd todv2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and add your Google AI API key:
   ```
   GOOGLE_AI_API_KEY=your_actual_api_key_here
   MODEL_NAME=gemini-2.5-flash
   ```

## 🚀 Usage

### Running the Application
```bash
python main.py
```

### Example Conversations

**Flight Booking:**
```
👤 You: Book a flight from New York to Paris on December 25th
🤖 Assistant: I'll help you book a flight from New York to Paris on December 25th. Let me search for available flights...
```

**Hotel Booking:**
```
👤 You: I need a hotel in London for 3 days
🤖 Assistant: I'll help you find a hotel in London for 3 days. Let me search for available options...
```

**Exit the application:**
```
👤 You: quit
🤖 Assistant: Goodbye! Have a great day!
```

## 🔧 Configuration

### Environment Variables
- `GOOGLE_AI_API_KEY`: Your Google AI API key (required)
- `MODEL_NAME`: AI model to use (default: gemini-2.5-flash)
- `DEBUG`: Enable debug mode (true/false)
- `LANGSMITH_TRACING`: Enable LangSmith tracing for debugging

### Available Models
- `gemini-2.5-flash` (recommended)
- `gemma-3-27b-it`
- Other Google AI models

## 🏗️ Project Structure

```
todv2/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your environment variables (create this)
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── supervisor_agent.py      # Main orchestrator
│   │   ├── input_parameter_agent.py # Parameter extraction
│   │   ├── tool_choosing_agent.py   # Tool selection
│   │   ├── tool_executing_agent.py  # Tool execution
│   │   └── generation_agent.py      # Response generation
│   ├── tools/            # Available tools
│   │   ├── travel_tools.py          # Flight/hotel booking tools
│   │   └── tool_registry.py         # Tool management
│   ├── schemas/          # Data structures
│   │   └── dialog_state.py          # Conversation state
│   └── config/           # Configuration files
│       └── llm_config.py            # LLM setup
```

## 🎯 How It Works

### 1. Intent Detection
The SupervisorAgent analyzes user input to determine the primary goal:
- Flight booking
- Hotel booking
- General conversation

### 2. Parameter Extraction
The InputParameterAgent extracts relevant details:
- **Flights**: Origin, destination, date
- **Hotels**: City, duration, dates

### 3. Tool Selection
The ToolChoosingAgent selects appropriate tools:
- `search_flights()` - Find available flights
- `book_flight()` - Book a specific flight
- `search_hotels()` - Find available hotels
- `book_hotel()` - Book a specific hotel

### 4. Tool Execution
The ToolExecutingAgent runs the selected tools and returns results.

### 5. Response Generation
The GenerationAgent creates natural language responses based on tool results.

## 🔍 Debug Mode

Enable debug mode by setting `DEBUG=true` in your `.env` file:

```bash
DEBUG=true
```

This will show:
- Current intent
- Extracted parameters
- Selected tools
- Agent routing decisions

## 🛠️ Available Tools

### Flight Tools
- **`search_flights(origin, destination, date)`** - Search available flights
- **`book_flight(origin, destination, date)`** - Book a flight

### Hotel Tools
- **`search_hotels(destination, days)`** - Search available hotels
- **`book_hotel(city, days)`** - Book a hotel

## 🚨 Troubleshooting

### Common Issues

1. **API Key Error**
   ```
   ❌ Error: GOOGLE_AI_API_KEY not found in environment variables.
   ```
   **Solution**: Ensure your `.env` file contains the correct API key.

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'langgraph'
   ```
   **Solution**: Install dependencies with `pip install -r requirements.txt`

3. **Model Not Found**
   ```
   Error: Model not found
   ```
   **Solution**: Check your `MODEL_NAME` in `.env` and ensure it's a valid Google AI model.

### Debug Tips

- Use `DEBUG=true` to see detailed agent decisions
- Check the console output for routing information
- Verify your API key has sufficient quota

## 🔮 Future Enhancements

- **Real API Integration**: Replace mock tools with actual booking APIs
- **Payment Processing**: Add payment gateway integration
- **Multi-language Support**: Internationalization for different languages
- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Mobile App**: React Native or Flutter mobile application
- **Web Interface**: React-based web dashboard

## 📚 Dependencies

- **LangGraph**: Multi-agent orchestration framework
- **LangChain**: LLM integration and tool management
- **Google AI**: Gemini models for natural language understanding
- **Python-dotenv**: Environment variable management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section
2. Enable debug mode for detailed logs
3. Verify your API key and configuration
4. Open an issue with detailed error information

---

**Happy Travel Planning! ✈️🏨**
