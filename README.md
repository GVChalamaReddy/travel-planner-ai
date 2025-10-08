# Travel Planner AI Chatbot - Complete Implementation Guide

## Overview

The Travel Planner AI Chatbot is an advanced travel planning assistant built with Python, Flask, OpenAI API, and comprehensive security features. It provides intelligent travel recommendations, itinerary planning, budget estimation, and more.

## Key Features

### **Advanced Travel Planning**
- **Smart Hotel Search**: Find accommodations with advanced filtering (price, category, availability)
- **Attraction Discovery**: Explore top-rated tourist spots with detailed information
- **Custom Itineraries**: Create detailed day-by-day travel plans
- **Budget Estimation**: Comprehensive cost breakdowns for trips
- **Weather Recommendations**: Optimal travel timing based on climate data

### **Enterprise Security**
- **Content Moderation**: Advanced threat detection and inappropriate content filtering
- **Travel-Only Restrictions**: Strict validation ensuring only travel-related queries
- **Progressive Warning System**: Three-strike policy with automatic chat reset
- **Session Management**: Rate limiting and security monitoring
- **Automatic Reset**: Self-healing system for security violations

### **AI-Powered Intelligence**
- **OpenAI Integration**: GPT-3.5-turbo with function calling capabilities
- **Natural Language Processing**: Understanding complex travel queries
- **Context Awareness**: Maintains conversation history and preferences
- **Intelligent Routing**: Automatic function selection based on user intent

### **Modern Web Interface**
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Real-time Updates**: Live status indicators and typing animations
- **Interactive Elements**: Quick action buttons and destination cards
- **Function Logging**: Transparent AI function call monitoring
- **Examples Modal**: Comprehensive query examples and tutorials

### Travel Planning Functions
1. **Hotel Search (`search_hotels`)**
    - Search by city, budget, category, and availability
    - Filter by luxury, mid-range, or budget categories
    - Real-time availability checking

2. **Attraction Discovery (`get_attractions`)**
    - Find attractions by city and category
    - Filter by entry fee and duration
    - Comprehensive attraction details with ratings

3. **Itinerary Creation (`create_itinerary`)**
    - Generate detailed day-by-day travel plans
    - Template-based and custom itinerary generation
    - Activity scheduling with meal recommendations

4. **Budget Estimation (`get_travel_budget_estimate`)**
    - Comprehensive trip cost calculation
    - Breakdown by accommodation, attractions, meals, transport
    - Category-based pricing analysis

5. **Weather Recommendations (`check_weather_recommendation`)**
    - Optimal travel timing advice
    - Seasonal weather insights
    - Best months recommendations

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# pip package manager
pip --version
```

### Installation
```bash
# 1. Clone or download the project files
git clone <repository-url>
cd travel-planner-ai
# 2. Install required packages
pip install requirements.txt

# 3. Run the application
python travel_chatbot.py

# or start shell script
.\start.sh

# 4. Open your browser
# Navigate to: http://localhost:5000
```

### First Run
1. **Start the Server**: `python travel_chatbot.py`
2. **Open Browser**: Go to `http://localhost:5000`
3. **Try Examples**: Click "Examples" button for query samples
4. **Start Planning**: Ask about hotels, attractions, or trip planning!

## 📂 Project Structure

```
travel-planner-ai/
├── travel_chatbot.py               # Main Flask application
├── templates/
│   └── travel_chatbot.html         # Modern web interface
├── travel_hotels.csv               # Hotels database (200 hotels)
├── travel_attractions.csv          # Attractions database (300 attractions)
├── travel_itinerary_templates.json # Pre-built itinerary templates
├── travel_chatbot.log              # Application logs
└── README.md                       # This documentation
```

## Configuration

### Environment Variables
```bash
# Optional
export FLASK_ENV="development"      # or "production"
export FLASK_DEBUG="True"           # Enable debug mode
export LOG_LEVEL="INFO"             # Logging level
```

### Application Settings
```python
# In travel_chatbot.py

# Server Configuration
app.run(debug=True, port=5000, host='0.0.0.0')
```

## Usage Examples

### Hotel Search
```python
# User Query: "Find luxury hotels in Paris under $400"
# Function Called: search_hotels
# Parameters: {city: "Paris", budget_max: 400, category: "luxury"}
# Result: List of luxury hotels with prices, ratings, amenities
```

### Attraction Discovery
```python
# User Query: "Top museums in London"
# Function Called: get_attractions  
# Parameters: {city: "London", category: "Museum"}
# Result: Museums with ratings, entry fees, descriptions
```

### Itinerary Creation
```python
# User Query: "Create a 5-day Tokyo itinerary"
# Function Called: create_itinerary
# Parameters: {city: "Tokyo", duration_days: 5}
# Result: Day-by-day plan with activities, costs, timing
```

### Budget Estimation
```python
# User Query: "What's the budget for a Barcelona trip?"
# Function Called: get_travel_budget_estimate
# Parameters: {city: "Barcelona", duration_days: 7, accommodation_category: "mid-range"}
# Result: Detailed cost breakdown by category
```

### Weather Recommendations
```python
# User Query: "Best time to visit Dubai?"
# Function Called: check_weather_recommendation
# Parameters: {city: "Dubai", travel_month: "December"}
# Result: Weather analysis and optimal timing advice
```

### Basic Trip Planning
    - User: "I want to visit Paris"
    - Bot: Asks for budget and duration
    - User: "My budget is $200 per night for 3 days"
    - Bot: Provides hotel recommendations, attractions, and itinerary

### Specific Requests
    - "Show me luxury hotels in Tokyo"
    - "What are the top attractions in Barcelona?"
    - "Create a 5-day itinerary for Dubai"

## Security Features

### Content Moderation
- **Threat Detection**: Identifies violent, illegal, or inappropriate content
- **Travel Focus**: Blocks non-travel queries with helpful redirection
- **Progressive Warnings**: 3-strike system before automatic reset
- **Real-time Monitoring**: Live security status indicators

### Session Management
```python
# Security Limits
SECURITY_VIOLATIONS = 2     # Auto-reset threshold

# Session Tracking
session = {
    'messages': [],
    'created_at': datetime.now(),
    'message_count': 0,
    'off_topic_warnings': 0,
    'security_violations': 0
}
```

### Input Validation
- **Content Analysis**: Multi-layer security scanning
- **Topic Validation**: Travel relevance scoring (0.0-1.0)
- **Rate Limiting**: Prevents spam and abuse
- **Automatic Reset**: Self-healing on security violations

## Data Sources

### Hotels Database (200 entries)
- **Cities**: Paris, London, Tokyo, New York, Dubai, Barcelona, Rome, Bangkok, Sydney, Mumbai
- **Categories**: Luxury, Mid-range, Budget
- **Attributes**: Price, rating, amenities, availability, location

### Attractions Database (300 entries)
- **Categories**: Historical, Museum, Religious, Landmark, Shopping, Cultural, Entertainment, Nature
- **Attributes**: Entry fee, duration, rating, description, opening hours

### Itinerary Templates
- **Pre-built Plans**: Paris (3,5 days), Tokyo (3,4 days), London (3 days)
- **Custom Generation**: Dynamic creation from attractions data
- **Cost Estimation**: Integrated budget calculations

## API Endpoints

### Chat Interface
```
POST /api/chat
Content-Type: application/json

{
    "message": "Find hotels in Paris",
    "session_id": "travel_session_123"
}

Response:
{
    "success": true,
    "message": "AI response text",
    "function_called": "search_hotels",
    "function_result": {...},
    "session_id": "travel_session_123"
}
```

### Session Management
```
POST /api/reset-chat
Content-Type: application/json

{
    "session_id": "travel_session_123"
}

Response:
{
    "success": true,
    "message": "Chat reset successfully",
    "session_reset": true
}
```

### Destinations
```
GET /api/travel-destinations

Response:
{
    "success": true,
    "destinations": [
        {
            "city": "Paris",
            "country": "France", 
            "hotels_available": 20,
            "attractions_available": 30
        }
    ]
}
```

### Function Information
```
GET /api/functions

Response:
{
    "functions": [
        {
            "name": "search_hotels",
            "description": "Search for hotels...",
            "parameters": {...}
        }
    ]
}
```

### Monitoring
- **Logging**: Comprehensive application and security logs
- **Metrics**: Response times, function call rates, error rates
- **Health Checks**: `/api/health` endpoint for monitoring
- **Alerts**: Security violation notifications

## Troubleshooting

### Common Issues

#### "OpenAI API Key Not Found"
```bash
# add to your text file
OpenAI_API_Key.txt
```

## Technologies Used

- **Backend**: Flask, Python
- **AI**: OpenAI GPT-3.5/4
- **Data**: Pandas, JSON
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Modern responsive design

## Conclusion

The Travel Planner AI Chatbot represents a complete solution for intelligent travel planning assistance. With comprehensive security, advanced AI integration, and modern web interface, it provides an excellent foundation for travel technology applications.

---

**Built using OpenAI Function Calling, Flask, and modern web technologies.**
