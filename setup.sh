#!/bin/bash

# Homework Agent MCP Server Setup Script

echo "🏫 Setting up Homework Agent MCP Server..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file from template..."
    cp env.example .env
    echo "📝 Please edit .env with your school portal credentials"
else
    echo "✓ .env file already exists"
fi

# Make test script executable
chmod +x test_server.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your school portal details"
echo "2. Customize selectors in server.py for your portal"
echo "3. Test with: python test_server.py"
echo "4. Run server with: python server.py"
echo ""
echo "For detailed instructions, see README.md"
