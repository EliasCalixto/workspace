#!/usr/bin/env python3
"""Test run variant of autologin without the final submit click."""
import argparse
import sys

import autologin


def parse_time(value: str):
    try:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Time must be in HH:MM 24-hour format") from exc
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise argparse.ArgumentTypeError("Hour must be 0-23 and minute 0-59")
    return hour, minute


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the autologin workflow without submitting, at a time you choose.",
    )
    parser.add_argument(
        "--time",
        type=parse_time,
        default=(autologin.TARGET_HOUR, autologin.TARGET_MINUTE),
        help="Schedule time in HH:MM (America/Lima). Default matches production run.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    autologin.configure_logging(verbose=args.verbose)
    images = autologin.resolve_images(autologin.IMAGE_SEQUENCE)
    autologin.ensure_images_exist(images)

    hour, minute = args.time
    target_dt = autologin.next_run_datetime(hour, minute, autologin.TARGET_TZ)
    autologin.LOGGER.info(
        "Test automation scheduled for %s (skipping final submit click).",
        target_dt.strftime("%Y-%m-%d %H:%M %Z"),
    )

    try:
        with autologin.keep_screen_awake():
            autologin.wait_until(target_dt)
            autologin.LOGGER.info("Starting UI automation test steps.")
            autologin.run_sequence(images, skip_last=True)
            autologin.LOGGER.info("Test automation completed without submission.")
    except KeyboardInterrupt:
        autologin.LOGGER.warning("Interrupted by user. Exiting early.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
