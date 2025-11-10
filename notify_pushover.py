#!/usr/bin/env python3
"""
Claude Code Hook Notification Script

Called by Claude Code hooks (Notification/Stop) to send Pushover notifications
with the actual Claude output from the tmux session.
"""

import os
import sys
import requests
import subprocess
from pathlib import Path
from urllib.parse import quote
from utils import load_config, strip_decorative_lines, save_claude_instance


def get_tmux_context():
    """Get the current tmux session and pane from environment."""
    tmux_pane = os.environ.get("TMUX_PANE")
    if not tmux_pane:
        return None, None, None

    try:
        # Get session name
        session = subprocess.run(
            ["tmux", "display-message", "-p", "-t", tmux_pane, "#S"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        # Get window name
        window = subprocess.run(
            ["tmux", "display-message", "-p", "-t", tmux_pane, "#W"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        return session, window, tmux_pane
    except subprocess.CalledProcessError:
        return None, None, None


def get_tmux_output(pane, num_lines=15):
    """Capture output from the specific tmux pane."""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t", pane, "-S", f"-{num_lines}"],
            capture_output=True,
            text=True,
            check=True
        )
        # Strip decorative lines for cleaner notifications
        return strip_decorative_lines(result.stdout).strip()
    except subprocess.CalledProcessError:
        return None


def extract_relevant_context(output, max_lines=10):
    """Extract the most relevant lines from tmux output."""
    if not output:
        return "Claude Code activity detected"

    lines = output.split("\n")

    # Get last N non-empty lines
    relevant = []
    for line in reversed(lines):
        if line.strip():
            relevant.insert(0, line)
            if len(relevant) >= max_lines:
                break

    return "\n".join(relevant) if relevant else output


def send_pushover(config, message, title):
    """Send Pushover notification."""
    if not config["pushover"]["enabled"]:
        print("Pushover notifications disabled in config")
        return False

    url = "https://api.pushover.net/1/messages.json"

    # Truncate message if too long (Pushover limit is 1024 chars)
    if len(message) > 900:
        message = message[-900:] + "\n[...truncated]"

    # Use Tailscale host if configured, otherwise localhost
    tailscale_host = config.get("tailscale_host", "").strip()
    base_host = tailscale_host if tailscale_host else "localhost"

    # Get current pane ID from environment
    pane_id = os.environ.get("TMUX_PANE", "")

    # Add pane parameter to URL for direct access to this specific instance
    # URL-encode the pane ID since it contains % character
    web_url = f"http://{base_host}:{config['server']['port']}?pane={quote(pane_id)}"

    data = {
        "token": config["pushover"]["app_token"],
        "user": config["pushover"]["user_key"],
        "message": message,
        "title": title,
        "url": web_url,
        "url_title": "Open Remote UI",
        "priority": 0,
        "monospace": 1,  # Use monospace font for code
    }

    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print(f"✓ Pushover notification sent: {title}")
            return True
        else:
            print(f"✗ Pushover failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error sending notification: {e}")
        return False


def save_active_target(script_dir, pane, session, window):
    """Save the active Claude pane to state file for web UI."""
    state_file = script_dir / ".active_target"
    try:
        with open(state_file, "w") as f:
            f.write(f"{pane}\n{session}\n{window}\n")
        print(f"✓ Active target saved: {pane}")
    except Exception as e:
        print(f"Warning: Could not save active target: {e}")


def main():
    """Entry point for hook script."""
    # Load configuration
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.yaml"

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Get tmux context
    session, window, pane = get_tmux_context()

    if not pane:
        print("Not running in tmux - skipping notification")
        sys.exit(0)

    # Save this as the active target for the web UI
    save_active_target(script_dir, pane, session, window)

    # Also save to instance history
    save_claude_instance(pane, session, window)

    # Build context title
    cwd = os.path.basename(os.getcwd())
    title = f"{session}: {window} - {cwd}"

    # Get tmux output
    num_lines = config.get("context_lines", 15)
    output = get_tmux_output(pane, num_lines)

    # Extract relevant context
    message = extract_relevant_context(output, max_lines=10)

    # Send notification
    send_pushover(config, message, title)


if __name__ == "__main__":
    main()
