#!/bin/bash
# Automated setup script using uv for cross-platform Python environment setup
# This script will install uv, Python, and all dependencies automatically

set -e  # Exit on error

echo "🚀 Starting automated setup with uv..."

# Check if uv is installed, if not install it
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    else
        # macOS/Linux
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi

    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Create virtual environment with uv (will auto-install Python if needed)
echo "🐍 Creating virtual environment with Python 3.11..."
uv venv --python 3.11

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Install dependencies using uv (much faster than pip)
echo "📚 Installing Python dependencies..."
uv pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright Chromium browser..."
python -m playwright install chromium

# Install system dependencies for Playwright (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔧 Installing Playwright system dependencies..."
    python -m playwright install-deps chromium || echo "⚠️  Could not install system deps (may need sudo)"
fi

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p output logs cache backups

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

echo ""
echo "✨ Setup complete! ✨"
echo ""
echo "To activate the environment:"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "  source .venv/Scripts/activate"
else
    echo "  source .venv/bin/activate"
fi
echo ""
echo "To run the automation:"
echo "  python main.py \"your-file.csv\" --headless"
echo ""
