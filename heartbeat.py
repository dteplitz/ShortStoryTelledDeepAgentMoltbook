"""Heartbeat runner - Periodically wakes Muse to interact with Moltbook."""
import argparse
import time
from datetime import datetime

from main import run_once

DEFAULT_INTERVAL = 30 * 60  # 30 minutes in seconds

HEARTBEAT_PROMPT = """Heartbeat #{heartbeat_number} — {timestamp}

You're awake. Load your identity, check your social context, browse Moltbook,
and ACT. Do not ask what to do — decide and execute autonomously.

You might write a story and share it, comment on something interesting,
reply to responses on your posts, or just read and absorb.

After you're done interacting, evolve your identity and update your social context.
Complete the full cycle before stopping."""


def run_heartbeat_loop(interval: int = DEFAULT_INTERVAL):
    """Run the heartbeat loop indefinitely."""
    heartbeat_number = 1

    print(f"Starting Muse heartbeat (interval: {interval}s / {interval // 60}min)")
    print("Press Ctrl+C to stop.\n")

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        prompt = HEARTBEAT_PROMPT.format(
            heartbeat_number=heartbeat_number,
            timestamp=timestamp,
        )

        print(f"\n{'=' * 50}")
        print(f"Heartbeat #{heartbeat_number} — {timestamp}")
        print(f"{'=' * 50}\n")

        try:
            run_once(prompt, thread_id=f"heartbeat-{heartbeat_number}")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Heartbeat #{heartbeat_number} failed: {e}")

        heartbeat_number += 1

        if interval > 0:
            print(f"\nSleeping {interval // 60} minutes until next heartbeat...")
            time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Muse Heartbeat - Periodically wakes Muse to interact with Moltbook."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Seconds between heartbeats (default: {DEFAULT_INTERVAL} = 30min)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single heartbeat and exit (good for testing)",
    )
    args = parser.parse_args()

    if args.once:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        run_once(
            HEARTBEAT_PROMPT.format(heartbeat_number=1, timestamp=timestamp),
            thread_id="heartbeat-test",
        )
    else:
        try:
            run_heartbeat_loop(args.interval)
        except KeyboardInterrupt:
            print("\nHeartbeat stopped.")
