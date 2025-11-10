#!/bin/bash
#
# Claude Remote UI Installation Script
# Works on both macOS and Ubuntu/Linux
#

set -e

echo "========================================"
echo "  Claude Remote UI - Installation"
echo "========================================"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
fi

echo "Detected OS: $OS"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found"
    echo "Please install Python 3 and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Python: $PYTHON_VERSION"
echo ""

# Check for tmux
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required but not found"
    echo ""
    if [[ "$OS" == "macos" ]]; then
        echo "Install with: brew install tmux"
    elif [[ "$OS" == "linux" ]]; then
        echo "Install with: sudo apt install tmux"
    fi
    exit 1
fi

TMUX_VERSION=$(tmux -V)
echo "Tmux: $TMUX_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Copy config file:"
echo "   cp config.yaml.example config.yaml"
echo ""
echo "2. Edit config.yaml with your settings:"
echo "   - Set your Pushover app_token and user_key"
echo "   - Configure tmux session name (default: claude-remote)"
echo ""
echo "3. Get Pushover credentials:"
echo "   - Sign up at https://pushover.net"
echo "   - Create an app/API token"
echo "   - Get your user key from the dashboard"
echo ""
echo "4. Setup Claude Code Hooks:"
echo "   Edit ~/.claude/settings.json and add:"
echo '   "hooks": {'
echo '     "Notification": [{"matcher": "", "hooks": [{"type": "command", "command": "'$(pwd)'/notify"}]}],'
echo '     "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "'$(pwd)'/notify"}]}]'
echo '   }'
echo ""
echo "5. Start the web server:"
echo "   cd $(pwd)"
echo "   ./start.sh"
echo ""
echo "6. Start Claude in tmux:"
echo "   tmux new-session -s my-claude"
echo "   claude"
echo ""
echo "7. Access the UI:"
echo "   - Local: http://localhost:5001"
echo "   - Tailscale: http://<your-machine>.ts.net:5001"
echo ""
echo "========================================"
