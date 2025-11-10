# Claude Remote UI

A simple, beautiful web interface to interact with Claude Code running in tmux sessions from anywhere via Tailscale. Get push notifications when Claude needs your attention and respond from your iPhone, iPad, or any device.

**Platforms**: macOS and Linux (Ubuntu/Debian)

## Features

- 🔔 **Hook-Based Notifications**: Get Pushover notifications only when Claude needs you (no polling!)
- 📱 **Multi-Instance Support**: Switch between multiple Claude sessions with a dropdown
- 🔗 **Direct Links**: Notification links open the exact Claude instance that needs attention
- 🎨 **Beautiful UI**: Clean, modern web interface that works on mobile and desktop
- ↔️ **Bidirectional Communication**: Send responses and commands back to Claude from anywhere
- 🔄 **Auto-refresh**: Output updates automatically every 3 seconds
- 🔒 **Tailscale Integration**: Secure access across all your devices
- 🧹 **Clean Output**: Decorative box-drawing characters stripped for mobile readability

## How It Works

```
Claude Code (any tmux pane)
    ↓ (Hook: Notification/Stop)
notify_pushover.py
    ↓ (saves pane info + history)
    ↓ (sends notification with direct link)
Pushover → Your Phone
    ↓ (tap "Open Remote UI")
Flask Web Server
    ↓ (shows that specific instance)
    ↓ (dropdown to switch between instances)
You send response → Claude Code
```

**Key Features**:
- ✅ No configuration needed - works with any tmux session
- ✅ Automatic instance detection and tracking
- ✅ Direct notification links to specific Claude instances
- ✅ Web dropdown to switch between active instances
- ✅ Works with unlimited Claude sessions simultaneously

## Quick Start (5 Minutes)

### 1. Install Prerequisites

**macOS:**
```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 tmux
```

**Ubuntu/Debian Linux:**
```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv tmux
```

### 2. Install Tailscale (for remote access)

**Both platforms:**
```bash
# Visit https://tailscale.com/download and follow instructions
# Or use quick install:

# macOS:
brew install tailscale

# Linux:
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale
sudo tailscale up
```

### 3. Install Claude Remote UI

```bash
# Clone or download this repository
cd /path/to/claude-remote-ui

# Run the installer (works on both macOS and Linux)
./install.sh
```

The installer will:
- ✅ Detect your OS automatically
- ✅ Create a Python virtual environment
- ✅ Install all dependencies
- ✅ Create config template
- ✅ Show next steps

### 4. Get Pushover Account

1. Go to [pushover.net](https://pushover.net) and create account ($5 one-time fee)
2. Download the Pushover app on your phone
3. Create an application/API token at https://pushover.net/apps/build
4. Note your **User Key** and **App Token**

### 5. Configure

Edit `config.yaml`:

```yaml
# Flask server settings
server:
  host: "0.0.0.0"  # Listen on all interfaces (required for Tailscale)
  port: 5001

# Your Tailscale hostname (for mobile notification links)
# Find it with: tailscale status
tailscale_host: "your-machine-name"  # e.g., "macbook-air" or "ubuntu-server"

# Pushover credentials
pushover:
  app_token: "YOUR_APP_TOKEN_HERE"      # From step 4
  user_key: "YOUR_USER_KEY_HERE"        # From step 4
  enabled: true

# How many lines to show in notification (default: 15)
context_lines: 15
```

**To find your Tailscale hostname:**
```bash
tailscale status
# Look for your machine name (e.g., "macbook-air", "ubuntu-server")
# Use just the name, not the full domain
```

### 6. Setup Claude Code Hooks

Edit your Claude Code config file:

**macOS:** `~/.claude/settings.json`
**Linux:** `~/.claude/settings.json`

Add this (replace `/path/to/claude-remote-ui` with your actual path):

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-remote-ui/notify"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/claude-remote-ui/notify"
          }
        ]
      }
    ]
  }
}
```

**Example paths:**
- macOS: `/Users/yourname/Projects/claude-remote-ui/notify`
- Linux: `/home/yourname/projects/claude-remote-ui/notify`

### 7. Start Everything

```bash
# Start the web server
./start.sh

# In a tmux session, start Claude
tmux new-session -s my-claude
claude

# That's it! When Claude needs attention, you'll get notified.
```

## Usage

### Starting the Server

```bash
./start.sh   # Starts in background
```

### Checking Status

```bash
./status.sh  # Shows if server is running
```

### Stopping the Server

```bash
./stop.sh    # Stops the server
```

### Viewing Logs

```bash
tail -f logs/server.log  # Web server logs
tail -f logs/hook.log    # Hook execution logs
```

### Accessing the UI

- **Local**: http://localhost:5001
- **Remote**: http://your-machine-name:5001 (via Tailscale)

### Using with Multiple Claude Instances

1. **Start multiple Claude sessions** in different tmux panes/windows:
   ```bash
   tmux new-window -n "project-1"
   claude

   tmux new-window -n "project-2"
   claude
   ```

2. **Each gets tracked automatically** - no configuration needed

3. **Notifications link directly** to the specific instance that needs attention

4. **Switch via dropdown** in the web UI to see other active instances

## Advanced Configuration

### Config File Reference

The `config.yaml` file supports these options:

```yaml
# Web server settings
server:
  host: "0.0.0.0"    # Listen on all interfaces (0.0.0.0) or localhost only (127.0.0.1)
  port: 5001          # Port number (default: 5001)

# Tailscale hostname for remote access
# Find with: tailscale status
# Use short name (e.g., "macbook-air") or full name (e.g., "macbook-air.tailnet-name.ts.net")
tailscale_host: "your-machine-name"

# Pushover notification settings
pushover:
  app_token: "YOUR_APP_TOKEN"   # From https://pushover.net/apps/build
  user_key: "YOUR_USER_KEY"      # From https://pushover.net
  enabled: true                   # Set to false to disable notifications

# Number of lines to capture in notifications (default: 15)
context_lines: 15
```

### Firewall Configuration

If using a firewall, allow the server port:

**Ubuntu/Linux (ufw):**
```bash
sudo ufw allow 5001
```

**macOS:**
System Preferences → Security & Privacy → Firewall → Allow connections for Python

### Running as Background Service (Optional)

#### Using the Start Script (Recommended)

The `./start.sh` script automatically runs the server in the background - this is the easiest method and works on both platforms.

#### Using systemd (Linux Only)

For automatic startup on Linux servers, create `/etc/systemd/system/claude-remote.service`:

```ini
[Unit]
Description=Claude Remote Web Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/claude-remote-ui
Environment="PATH=/path/to/claude-remote-ui/venv/bin"
ExecStart=/path/to/claude-remote-ui/venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable claude-remote
sudo systemctl start claude-remote
sudo systemctl status claude-remote
```

## API Reference

The server provides these REST API endpoints:

### GET /

Main web UI interface

### GET /api/output

Get current tmux output from active or specified pane

**Query Parameters:**
- `pane` (optional): Specific pane ID (e.g., `%392`)

**Response:**
```json
{
  "output": "tmux session output...",
  "active": true,
  "pane": "%392"
}
```

### POST /api/send

Send input to active or specified tmux pane

**Request:**
```json
{
  "text": "your response here",
  "pane": "%392"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sent: your response here"
}
```

### GET /api/instances

List all active Claude instances

**Response:**
```json
{
  "instances": [
    {
      "pane": "%392",
      "session": "0",
      "window": "BM",
      "display_name": "0:BM",
      "last_active": "2025-11-10T18:23:28.111768"
    }
  ],
  "current": "%392"
}
```

### POST /api/switch

Switch active Claude instance

**Request:**
```json
{
  "pane": "%392"
}
```

**Response:**
```json
{
  "success": true,
  "pane": "%392",
  "session": "0",
  "window": "BM"
}
```

### GET /health

Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "target": "%392",
  "session": "0",
  "window": "BM",
  "active": true,
  "timestamp": "2025-11-10T10:30:00"
}
```

## How Multi-Instance Switching Works

### Direct Notification Links

1. **Claude needs attention** in pane `%392`
2. **Hook fires** and captures pane ID
3. **Notification sent** with URL: `http://your-machine:5001?pane=%25392`
4. **Tap notification** → Opens web UI showing **that specific pane**
5. **Your response** goes to the correct Claude instance

### Web UI Dropdown

When you have multiple Claude instances active:

1. **Dropdown appears** showing all active instances
2. **Select instance** from dropdown (e.g., "0:BM (%392)")
3. **Page reloads** showing that instance's output
4. **Responses go** to the selected instance

### Instance Tracking

- Tracks up to 10 recent Claude instances
- Automatically removes inactive/closed instances
- Stores: pane ID, session, window, last active time
- No manual configuration needed

## Troubleshooting

### Installation Issues

**Python version error:**
```bash
# Check Python version (needs 3.7+)
python3 --version

# macOS: Update Python
brew upgrade python3

# Linux: Install newer Python
sudo apt install python3.9
```

**Permission denied on scripts:**
```bash
chmod +x install.sh start.sh stop.sh status.sh notify
```

### Runtime Issues

**Server won't start:**
```bash
# Check if port is already in use
netstat -an | grep 5001  # macOS/Linux
lsof -i :5001            # Alternative

# Check logs
tail -n 50 logs/server.log

# Try different port in config.yaml
```

**Can't access from Tailscale:**
```bash
# Verify Tailscale is running
tailscale status

# Test local access first
curl http://localhost:5001/health

# Check server is listening on all interfaces
netstat -an | grep 5001
# Should show: *.5001 or 0.0.0.0:5001

# Firewall (Linux)
sudo ufw allow 5001
sudo ufw status
```

**Notifications not working:**
```bash
# Test notification manually
./notify

# Check hook.log
tail -f logs/hook.log

# Verify Pushover credentials
cat config.yaml | grep -A 3 pushover

# Test from Claude Code hooks
# The hook should trigger when Claude stops or needs input
```

**Multiple instances not showing:**
```bash
# Check instance history file
cat .claude_instances | python3 -m json.tool

# Verify panes are still active
tmux list-panes -a

# Force a notification from each instance to register them
```

**URL encoding issues with pane IDs:**
```bash
# Pane IDs contain % which must be URL-encoded
# %392 should become %25392 in URLs
# This is handled automatically by the system

# Check server logs for proper encoding
tail -f logs/server.log
```

### Testing the Setup

**Test notification system:**
```bash
# 1. Start server
./start.sh

# 2. In tmux, test notify script
./notify

# 3. Check your phone for Pushover notification
# 4. Check logs
tail logs/hook.log
```

**Test multi-instance:**
```bash
# 1. Create multiple tmux windows with Claude
tmux new-window -n "test-1"
claude

tmux new-window -n "test-2"
claude

# 2. Trigger hooks in each by asking Claude something
# 3. Check web UI - dropdown should show both instances
# 4. Try switching between them
```

## Project Structure

```
claude-remote-ui/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── config.yaml.example    # Example configuration
├── config.yaml            # Your configuration (created during setup)
├── install.sh             # Installation script (cross-platform)
├── start.sh               # Start web server in background
├── stop.sh                # Stop web server
├── status.sh              # Check server status
├── notify                 # Notification wrapper (called by hooks)
├── notify_pushover.py     # Pushover notification implementation
├── server.py              # Flask web server
├── utils.py               # Shared utilities (output parsing, tmux, etc.)
├── templates/
│   └── index.html         # Web UI template
├── static/
│   └── style.css          # UI styles
├── logs/                  # Created automatically
│   ├── server.log         # Web server logs
│   └── hook.log           # Hook execution logs
├── .pids/                 # Created automatically
│   └── server.pid         # Server process ID
├── .active_target         # Current active Claude instance
└── .claude_instances      # Instance history (JSON)
```

## Development

### Running in Development Mode

```bash
# Terminal 1: Run server in foreground with debug
source venv/bin/activate
FLASK_DEBUG=1 python server.py

# Terminal 2: Start Claude in tmux
tmux new-session -s dev
claude

# Terminal 3: Watch logs
tail -f logs/server.log logs/hook.log
```


### Testing Notifications Manually

Test the notification system without Claude:

```bash
# Start server
./start.sh

# In any tmux pane
./notify

# Check your phone - you should get a notification!
# Check logs
tail logs/hook.log
```

## Security

- **Tailscale Protected**: Server listens on `0.0.0.0` but access is controlled by Tailscale
- **No Public Exposure**: All traffic stays within your private Tailscale network
- **No Authentication Needed**: Tailscale handles device authentication
- **No Tunneling Required**: Direct peer-to-peer connections via Tailscale

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this however you'd like!

## Credits

Built for seamless Claude Code interaction from anywhere, because being tied to your laptop is so 2020.

**Made with** ❤️ **for the Claude Code community**
