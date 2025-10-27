#!/bin/bash

# Hotel Price Scraper Setup Script
# This script sets up a Python virtual environment and installs dependencies

echo "🏨 Setting up Hotel Price Scraper..."
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the scraper:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the example: python example_usage.py"
echo "3. When done, deactivate: deactivate"
echo ""
echo "Happy scraping! 🚀"
