#!/bin/bash
# Travel Planner AI Chatbot Startup Script

echo "Starting Travel Planner AI Chatbot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/Scripts/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the Flask application
echo "Starting application..."
python travel_chatbot.py
