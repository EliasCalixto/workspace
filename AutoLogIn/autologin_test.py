#!/usr/bin/env python3
"""
Test runner for autologin that lets you pass time args
but skips the final submit click (step3) so you can test safely.

Usage examples:

  - Run immediately (no waiting), clicking steps 1 and 2 only:
      python test/autologin_test.py now --images AutoLogIn

  - Schedule at a specific time, skipping only the final submit:
      python test/autologin_test.py schedule --time 07:29 --images AutoLogIn

All other flags pass through to autologin (e.g. --tz, --slow, --no-awake).
"""

from __future__ import annotations

import argparse
import sys

import autologin as app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run autologin for testing, skipping the final submit click.",
    )
    parser.add_argument(
        "action",
        choices=["now", "schedule"],
        nargs="?",
        default="now",
        help="Run immediately or wait until --time (default: now)",
    )
    parser.add_argument(
        "--time",
        dest="time_hhmm",
        default="07:29",
        help="Local time HH:MM for schedule mode (default 07:29)",
    )
    parser.add_argument(
        "--tz",
        dest="tz_name",
        default="America/Lima",
        help="IANA timezone name (default America/Lima)",
    )
    parser.add_argument(
        "--images",
        dest="images_dir",
        default="/Users/darkesthj/Dev/workspace/autologin",
        help="Directory with step images (default AutoLogIn)",
    )
    parser.add_argument(
        "--slow",
        dest="slow",
        type=float,
        default=0.2,
        help="Pause between PyAutoGUI actions (default 0.2s)",
    )
    parser.add_argument(
        "--no-awake",
        action="store_true",
        help="Do not force screen awake while running",
    )

    args = parser.parse_args(argv)

    # Monkeypatch only the final submit click by intercepting the image path
    original_click_image = app.click_image

    def click_image_skip_submit(path: str, *cargs, **ckwargs) -> bool:  # type: ignore[override]
        if path.endswith("step3_submit.png"):
            print(f"[test] Skipping final submit click: {path}")
            return True  # Pretend it succeeded so the flow continues/ends cleanly
        return original_click_image(path, *cargs, **ckwargs)

    app.click_image = click_image_skip_submit  # type: ignore[assignment]

    # Build argv for the real app without --dry-run so steps 1 and 2 still click
    forwarded = [
        args.action,
        "--time",
        args.time_hhmm,
        "--tz",
        args.tz_name,
        "--images",
        args.images_dir,
        "--slow",
        str(args.slow),
    ]
    if args.no_awake:
        forwarded.append("--no-awake")

    return app.main(forwarded)


if __name__ == "__main__":
    sys.exit(main())

