"""Shared utilities for Claude Remote UI."""

import yaml
import subprocess
import json
from pathlib import Path
from datetime import datetime


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            "Please copy config.yaml.example to config.yaml and configure it."
        )

    with open(config_file) as f:
        return yaml.safe_load(f)


def strip_decorative_lines(text):
    """Strip box-drawing characters and decorative lines from text."""
    import re

    # Remove lines that are purely decorative (box-drawing characters, dashes, etc.)
    lines = text.split('\n')
    filtered_lines = []

    for line in lines:
        # Skip lines that are only box-drawing characters, spaces, and common decorative chars
        # Box-drawing Unicode range: U+2500-U+257F
        # Also remove lines with only dashes, equals, underscores
        stripped = line.strip()
        if not stripped:
            filtered_lines.append(line)
            continue

        # Check if line is purely decorative
        is_decorative = all(
            c in ' \t─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬▀▄█▌▐░▒▓■□▪▫-_=~'
            for c in stripped
        )

        if not is_decorative:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def get_tmux_output(target, num_lines=100):
    """Capture output from tmux target (session, window, or pane)."""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t", target, "-S", f"-{num_lines}"],
            capture_output=True,
            text=True,
            check=True
        )
        # Strip decorative lines for cleaner mobile display
        return strip_decorative_lines(result.stdout)
    except subprocess.CalledProcessError:
        return None


def send_to_tmux(target, text):
    """Send text input to tmux target (session, window, or pane)."""
    try:
        # Send text literally, then send Enter key separately
        # Using -l flag to send text literally (handles special characters)
        subprocess.run(
            ["tmux", "send-keys", "-t", target, "-l", text],
            check=True
        )
        # Now send the Enter key explicitly
        subprocess.run(
            ["tmux", "send-keys", "-t", target, "Enter"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def tmux_session_exists(target):
    """Check if tmux target exists (session, window, or pane)."""
    try:
        # Try to list the pane - works for sessions, windows, and panes
        subprocess.run(
            ["tmux", "list-panes", "-t", target],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_instance_history_file():
    """Get path to instance history file."""
    return Path(__file__).parent / ".claude_instances"


def save_claude_instance(pane, session, window):
    """Save Claude instance to history."""
    history_file = get_instance_history_file()

    # Load existing history
    instances = []
    if history_file.exists():
        try:
            with open(history_file) as f:
                instances = json.load(f)
        except (json.JSONDecodeError, Exception):
            instances = []

    # Create instance entry
    instance = {
        "pane": pane,
        "session": session,
        "window": window,
        "last_active": datetime.now().isoformat(),
        "display_name": f"{session}:{window}"
    }

    # Remove duplicate if exists (same pane)
    instances = [i for i in instances if i.get("pane") != pane]

    # Add to front (most recent)
    instances.insert(0, instance)

    # Keep only last 10 instances
    instances = instances[:10]

    # Save
    try:
        with open(history_file, "w") as f:
            json.dump(instances, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save instance history: {e}")


def get_claude_instances():
    """Get list of recent Claude instances, filtering out inactive ones."""
    history_file = get_instance_history_file()

    if not history_file.exists():
        return []

    try:
        with open(history_file) as f:
            instances = json.load(f)
    except (json.JSONDecodeError, Exception):
        return []

    # Filter to only active instances
    active_instances = []
    for instance in instances:
        pane = instance.get("pane")
        if pane and tmux_session_exists(pane):
            active_instances.append(instance)

    return active_instances


def get_instance_info(pane):
    """Get info about a specific Claude instance."""
    instances = get_claude_instances()
    for instance in instances:
        if instance.get("pane") == pane:
            return instance
    return None
