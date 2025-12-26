#!/usr/bin/env python3
"""
Claude Code Hook Notification Script

Called by Claude Code hooks (Notification/Stop) to send Telegram notifications
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


def extract_relevant_context(output, max_lines=30):
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


def escape_html(text):
    """Escape special characters for Telegram HTML."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def send_telegram(config, message, title):
    """Send Telegram notification via Bot API."""
    telegram_config = config.get("telegram", {})

    if not telegram_config.get("enabled", False):
        print("Telegram notifications disabled in config")
        return False

    bot_token = telegram_config.get("bot_token", "")
    chat_id = telegram_config.get("chat_id", "")

    if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Telegram bot token not configured")
        return False

    if not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID_HERE":
        print("Telegram chat ID not configured")
        return False

    # Use Tailscale host if configured, otherwise localhost
    tailscale_host = config.get("tailscale_host", "").strip()
    base_host = tailscale_host if tailscale_host else "localhost"

    # Get current pane ID from environment
    pane_id = os.environ.get("TMUX_PANE", "")

    # Add pane parameter to URL for direct access to this specific instance
    web_url = f"http://{base_host}:{config['server']['port']}?pane={quote(pane_id)}"

    # Truncate message if too long (Telegram limit is 4096 chars)
    # Reserve space for title, URL, and formatting
    max_message_len = 3500
    if len(message) > max_message_len:
        message = message[-max_message_len:]
        message = "[...truncated]\n" + message

    # Build Telegram message with HTML formatting (more reliable than Markdown)
    # Format: Title, Content (code block)
    # Escape HTML entities in the message content
    escaped_message = escape_html(message)
    escaped_title = escape_html(title)
    full_message = f"<b>{escaped_title}</b>\n\n<pre>{escaped_message}</pre>"

    # Telegram API endpoint
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Use inline keyboard button for the URL (works with any URL including local/Tailscale)
    payload = {
        "chat_id": chat_id,
        "text": full_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "Open Remote UI", "url": web_url}
            ]]
        }
    }

    try:
        response = requests.post(api_url, json=payload)
        result = response.json()

        if result.get("ok"):
            print(f"✓ Telegram notification sent: {title}")
            return True
        else:
            print(f"✗ Telegram failed: {result.get('description', 'Unknown error')}")
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

    # Build context title using tailscale host (short name only)
    tailscale_host = config.get("tailscale_host", "").strip()
    if not tailscale_host:
        # Fallback to session if tailscale_host not configured
        short_host = session
    else:
        # Extract short hostname (first part before any dots)
        short_host = tailscale_host.split('.')[0]
    title = f"{short_host}: {window}"

    # Get tmux output
    num_lines = config.get("context_lines", 50)
    output = get_tmux_output(pane, num_lines)

    # Extract relevant context
    message = extract_relevant_context(output, max_lines=30)

    # Send notification
    send_telegram(config, message, title)


if __name__ == "__main__":
    main()
