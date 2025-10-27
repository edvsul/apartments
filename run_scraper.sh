#!/bin/bash

# Script to run the hotel scraper with virtual environment activated

echo "🏨 Hotel Price Scraper"
echo "====================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Run the scraper
echo "🚀 Running hotel scraper..."
python example_usage.py

# Deactivate virtual environment
deactivate

echo "✅ Done!"
