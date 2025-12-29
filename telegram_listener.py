#!/usr/bin/env python3
"""
Telegram Bot Listener for Claude Remote UI

Polls for incoming Telegram messages and sends them to the active Claude tmux pane.
"""

import time
import subprocess
import requests
from pathlib import Path
from utils import load_config, send_to_tmux, tmux_session_exists, get_claude_instances, save_claude_instance


def get_active_target(script_dir):
    """Get the active Claude pane from state file."""
    state_file = script_dir / ".active_target"
    try:
        if state_file.exists():
            with open(state_file, "r") as f:
                lines = f.read().strip().split("\n")
                if lines:
                    return lines[0]  # pane ID
    except Exception:
        pass
    return None


def set_active_target(script_dir, pane, session, window):
    """Set the active Claude pane in state file."""
    state_file = script_dir / ".active_target"
    try:
        with open(state_file, "w") as f:
            f.write(f"{pane}\n{session}\n{window}\n")
        return True
    except Exception:
        return False


def spawn_claude_instance(script_dir, window_name="TGClaude"):
    """Spawn a new Claude instance in a new tmux window."""
    try:
        # Get existing tmux sessions
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # No tmux server running, create new session
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", "claude", "-n", window_name],
                check=True
            )
            session = "claude"
        else:
            # Use first available session
            sessions = result.stdout.strip().split("\n")
            session = sessions[0] if sessions else "claude"

            # Create new window in that session
            subprocess.run(
                ["tmux", "new-window", "-t", session, "-n", window_name],
                check=True
            )

        # Get the pane ID of the new window
        result = subprocess.run(
            ["tmux", "list-panes", "-t", f"{session}:{window_name}", "-F", "#{pane_id}"],
            capture_output=True,
            text=True,
            check=True
        )
        pane_id = result.stdout.strip()

        # Send the claude command to the new pane
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_id, "claude --dangerously-skip-permissions", "Enter"],
            check=True
        )

        # Save as active instance
        save_claude_instance(pane_id, session, window_name)
        set_active_target(script_dir, pane_id, session, window_name)

        return pane_id, session, window_name

    except subprocess.CalledProcessError as e:
        print(f"Error spawning Claude: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None


def send_telegram_message(bot_token, chat_id, text, reply_to_message_id=None):
    """Send a message back to Telegram."""
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    try:
        requests.post(api_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def get_updates(bot_token, offset=None, timeout=30):
    """Get updates from Telegram using long polling."""
    api_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {
        "timeout": timeout,
        "allowed_updates": ["message"]
    }
    if offset:
        params["offset"] = offset

    try:
        response = requests.get(api_url, params=params, timeout=timeout + 10)
        result = response.json()
        if result.get("ok"):
            return result.get("result", [])
    except Exception as e:
        print(f"Error getting updates: {e}")
    return []


def main():
    """Main loop for Telegram listener."""
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.yaml"

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    telegram_config = config.get("telegram", {})
    bot_token = telegram_config.get("bot_token", "")
    chat_id = str(telegram_config.get("chat_id", ""))

    if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Telegram bot token not configured")
        return

    if not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID_HERE":
        print("Telegram chat ID not configured")
        return

    print(f"Starting Telegram listener for chat_id: {chat_id}")

    offset = None

    while True:
        try:
            updates = get_updates(bot_token, offset)

            for update in updates:
                offset = update["update_id"] + 1

                message = update.get("message", {})
                msg_chat_id = str(message.get("chat", {}).get("id", ""))
                text = message.get("text", "")
                message_id = message.get("message_id")

                # Only process messages from the configured chat
                if msg_chat_id != chat_id:
                    continue

                # Handle commands (start with /)
                if text.startswith("/"):
                    if text == "/status":
                        pane = get_active_target(script_dir)
                        if pane and tmux_session_exists(pane):
                            # Find display name from instances
                            instances = get_claude_instances()
                            display = pane
                            for inst in instances:
                                if inst.get("pane") == pane:
                                    display = f"{inst.get('display_name')} ({pane})"
                                    break
                            send_telegram_message(
                                bot_token, chat_id,
                                f"Active: <code>{display}</code>",
                                message_id
                            )
                        else:
                            send_telegram_message(
                                bot_token, chat_id,
                                "No active Claude session",
                                message_id
                            )

                    elif text == "/list" or text == "/panes":
                        instances = get_claude_instances()
                        if not instances:
                            send_telegram_message(
                                bot_token, chat_id,
                                "No Claude sessions found",
                                message_id
                            )
                        else:
                            current_pane = get_active_target(script_dir)
                            lines = ["<b>Claude Sessions:</b>\n"]
                            for i, inst in enumerate(instances, 1):
                                pane = inst.get("pane", "")
                                name = inst.get("display_name", pane)
                                marker = " ✓" if pane == current_pane else ""
                                lines.append(f"{i}. <code>{name}</code>{marker}")
                            lines.append(f"\nUse /switch N to change")
                            send_telegram_message(
                                bot_token, chat_id,
                                "\n".join(lines),
                                message_id
                            )

                    elif text.startswith("/switch"):
                        parts = text.split()
                        if len(parts) != 2:
                            send_telegram_message(
                                bot_token, chat_id,
                                "Usage: /switch N (e.g., /switch 1)",
                                message_id
                            )
                        else:
                            try:
                                idx = int(parts[1]) - 1
                                instances = get_claude_instances()
                                if 0 <= idx < len(instances):
                                    inst = instances[idx]
                                    pane = inst.get("pane")
                                    session = inst.get("session", "")
                                    window = inst.get("window", "")
                                    if tmux_session_exists(pane):
                                        set_active_target(script_dir, pane, session, window)
                                        send_telegram_message(
                                            bot_token, chat_id,
                                            f"Switched to <code>{inst.get('display_name')}</code>",
                                            message_id
                                        )
                                    else:
                                        send_telegram_message(
                                            bot_token, chat_id,
                                            f"Session no longer exists",
                                            message_id
                                        )
                                else:
                                    send_telegram_message(
                                        bot_token, chat_id,
                                        f"Invalid number. Use /list to see available sessions.",
                                        message_id
                                    )
                            except ValueError:
                                send_telegram_message(
                                    bot_token, chat_id,
                                    "Usage: /switch N (e.g., /switch 1)",
                                    message_id
                                )

                    elif text.startswith("/new"):
                        # Parse optional window name
                        parts = text.split(maxsplit=1)
                        window_name = parts[1] if len(parts) > 1 else "TGClaude"

                        send_telegram_message(
                            bot_token, chat_id,
                            f"Spawning new Claude instance...",
                            message_id
                        )

                        pane_id, session, window = spawn_claude_instance(script_dir, window_name)

                        if pane_id:
                            send_telegram_message(
                                bot_token, chat_id,
                                f"Started <code>{session}:{window}</code>\nNow active. Send your prompt!",
                                message_id
                            )
                        else:
                            send_telegram_message(
                                bot_token, chat_id,
                                "Failed to spawn Claude instance. Check logs.",
                                message_id
                            )

                    elif text == "/help":
                        help_text = """<b>Commands:</b>
/status - Show active Claude session
/list - List all Claude sessions
/switch N - Switch to session N
/new [name] - Spawn new Claude instance
/help - Show this help

<b>Usage:</b>
Just type any message to send it to the active Claude session."""
                        send_telegram_message(
                            bot_token, chat_id,
                            help_text,
                            message_id
                        )

                    continue

                if not text:
                    continue

                # Get active pane
                pane = get_active_target(script_dir)

                if not pane:
                    send_telegram_message(
                        bot_token, chat_id,
                        "No active Claude session. Wait for a notification first.",
                        message_id
                    )
                    continue

                if not tmux_session_exists(pane):
                    send_telegram_message(
                        bot_token, chat_id,
                        f"Session <code>{pane}</code> no longer exists.",
                        message_id
                    )
                    continue

                # Send to tmux
                success = send_to_tmux(pane, text)

                if success:
                    send_telegram_message(
                        bot_token, chat_id,
                        f"Sent to Claude",
                        message_id
                    )
                else:
                    send_telegram_message(
                        bot_token, chat_id,
                        "Failed to send to Claude",
                        message_id
                    )

        except KeyboardInterrupt:
            print("\nStopping Telegram listener...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
