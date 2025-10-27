#!/bin/bash

# Script to run the multi-country hotel scraper with NordVPN

echo "🌍 Multi-Country Hotel Price Scraper"
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Check if NordVPN is installed
if ! command -v nordvpn &> /dev/null; then
    echo "❌ NordVPN CLI not found. Please install NordVPN first."
    echo "   Visit: https://nordvpn.com/download/"
    exit 1
fi

# Check if logged into NordVPN
nordvpn_status=$(nordvpn account 2>&1)
if [[ $nordvpn_status == *"You are not logged in"* ]]; then
    echo "❌ Not logged into NordVPN. Please login first:"
    echo "   nordvpn login"
    exit 1
fi

echo "✅ NordVPN check passed"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install pandas if not already installed
echo "📦 Checking dependencies..."
pip install pandas==2.1.4 --quiet

# Create necessary directories
mkdir -p screenshots
mkdir -p hotel_prices
mkdir -p temp_chrome_sessions

# Run the multi-country scraper
echo "🚀 Starting multi-country hotel price scraper..."
echo "⚠️  This will test hotel prices across multiple countries using NordVPN"
echo "⏱️  This may take 15-30 minutes depending on the number of countries"
echo ""

python multi_country_hotel_scraper.py

# Deactivate virtual environment
deactivate

echo ""
echo "✅ Multi-country scraping completed!"
echo "📊 Check the hotel_prices/ directory for results"
echo "📸 Check the screenshots/ directory for visual evidence"
