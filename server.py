#!/usr/bin/env python3
"""
Claude Remote Web Server

Simple Flask server providing web UI to interact with Claude Code via tmux.
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from pathlib import Path
import argparse
from utils import (
    load_config, get_tmux_output, send_to_tmux, tmux_session_exists,
    get_claude_instances, get_instance_info
)


app = Flask(__name__)
config = None
script_dir = None


def get_active_target(pane_override=None):
    """Get the currently active Claude target.

    Args:
        pane_override: If provided, use this pane instead of reading from state file

    Returns:
        tuple: (pane, session, window)
    """
    # If pane is provided via URL parameter, use it directly
    if pane_override:
        info = get_instance_info(pane_override)
        if info:
            return info["pane"], info["session"], info["window"]
        # If not in history but exists, try to use it anyway
        if tmux_session_exists(pane_override):
            return pane_override, "unknown", "unknown"
        return None, None, None

    # Otherwise read from state file (default behavior)
    state_file = script_dir / ".active_target"
    if not state_file.exists():
        return None, None, None

    try:
        with open(state_file) as f:
            lines = f.read().strip().split("\n")
            if len(lines) >= 3:
                return lines[0], lines[1], lines[2]  # pane, session, window
            elif len(lines) >= 1:
                return lines[0], "unknown", "unknown"
    except Exception:
        pass

    return None, None, None


def set_active_target(pane, session, window):
    """Set the active Claude target in state file."""
    state_file = script_dir / ".active_target"
    try:
        with open(state_file, "w") as f:
            f.write(f"{pane}\n{session}\n{window}\n")
        return True
    except Exception:
        return False


@app.route("/")
def index():
    """Main UI page."""
    # Check for pane query parameter
    pane_param = request.args.get("pane")
    pane, session, window = get_active_target(pane_param)

    # Get list of available instances
    instances = get_claude_instances()

    if not pane:
        return render_template(
            "index.html",
            session_name="No active Claude instance",
            session_active=False,
            output="Waiting for Claude Code hook to trigger...\n\nOnce Claude needs your attention, this will show the output.",
            instances=instances,
            current_pane=None,
        )

    # Check if target still exists
    target_active = tmux_session_exists(pane)

    # Get current output
    output = ""
    display_name = f"{session}:{window}"

    if target_active:
        raw_output = get_tmux_output(pane, num_lines=50)
        if raw_output:
            output = raw_output
    else:
        output = f"Target {pane} is no longer active.\n\nWaiting for next Claude notification..."

    return render_template(
        "index.html",
        session_name=display_name,
        session_active=target_active,
        output=output,
        instances=instances,
        current_pane=pane,
    )


@app.route("/api/output")
def get_output():
    """API endpoint to get current tmux output."""
    pane_param = request.args.get("pane")
    pane, session, window = get_active_target(pane_param)

    if not pane:
        return jsonify({
            "output": "Waiting for Claude Code hook to trigger...",
            "active": False
        })

    if not tmux_session_exists(pane):
        return jsonify({
            "output": f"Target {pane} is no longer active.",
            "active": False
        })

    output = get_tmux_output(pane, num_lines=50)
    return jsonify({"output": output or "", "active": True, "pane": pane})


@app.route("/api/send", methods=["POST"])
def send_input():
    """API endpoint to send input to tmux."""
    data = request.get_json()
    text = data.get("text", "").strip()
    pane_param = data.get("pane")  # Allow pane override in POST body

    if not text:
        return jsonify({"error": "No text provided"}), 400

    pane, session, window = get_active_target(pane_param)

    if not pane:
        return jsonify({"error": "No active Claude target"}), 404

    if not tmux_session_exists(pane):
        return jsonify({"error": "Target no longer active"}), 404

    success = send_to_tmux(pane, text)

    if success:
        return jsonify({"success": True, "message": f"Sent: {text}"})
    else:
        return jsonify({"error": "Failed to send input"}), 500


@app.route("/api/instances")
def list_instances():
    """API endpoint to list available Claude instances."""
    instances = get_claude_instances()
    pane_param = request.args.get("pane")
    current_pane, _, _ = get_active_target(pane_param)

    return jsonify({
        "instances": instances,
        "current": current_pane
    })


@app.route("/api/switch", methods=["POST"])
def switch_instance():
    """API endpoint to switch active Claude instance."""
    data = request.get_json()
    pane = data.get("pane")

    if not pane:
        return jsonify({"error": "No pane provided"}), 400

    # Verify instance exists
    info = get_instance_info(pane)
    if not info:
        return jsonify({"error": "Instance not found"}), 404

    if not tmux_session_exists(pane):
        return jsonify({"error": "Instance no longer active"}), 404

    # Update active target
    success = set_active_target(info["pane"], info["session"], info["window"])

    if success:
        return jsonify({
            "success": True,
            "pane": info["pane"],
            "session": info["session"],
            "window": info["window"]
        })
    else:
        return jsonify({"error": "Failed to switch instance"}), 500


@app.route("/health")
def health():
    """Health check endpoint."""
    pane, session, window = get_active_target()
    return jsonify({
        "status": "ok",
        "target": pane or "none",
        "session": session or "none",
        "window": window or "none",
        "active": tmux_session_exists(pane) if pane else False,
        "timestamp": datetime.now().isoformat(),
    })


def main():
    """Entry point."""
    global config, script_dir

    parser = argparse.ArgumentParser(description="Claude Remote Web Server")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config = load_config(args.config)

    host = config["server"]["host"]
    port = config["server"]["port"]

    print(f"Starting Claude Remote Web Server")
    print(f"Server: http://{host}:{port}")
    print(f"Mode: Dynamic (reads from hook notifications)")

    pane, session, window = get_active_target()
    if pane:
        print(f"Current target: {session}:{window} ({pane})")
    else:
        print(f"Current target: None (waiting for first notification)")

    print("-" * 60)

    app.run(
        host=host,
        port=port,
        debug=False
    )


if __name__ == "__main__":
    main()
