#!/usr/bin/env python3
"""Scheduled UI automation to keep the Mac awake and run at 07:29 Lima time."""
import argparse
import logging
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 fallback
    ZoneInfo = None  # type: ignore

LOGGER = logging.getLogger("autologin")
BASE_DIR = Path(__file__).resolve().parent
IMAGE_SEQUENCE = [
    "step1_bluelogin.png",
    "step2_here.png",
    "step3_menu.png",
    "step4_login.png",
    "step5_submit.png",
]
TARGET_TZ = "America/Lima"
TARGET_HOUR = 7
TARGET_MINUTE = 25
FIND_TIMEOUT_SECONDS = 20


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def resolve_images(sequence):
    return [BASE_DIR / name for name in sequence]


def ensure_images_exist(images):
    missing = [str(path) for path in images if not path.exists()]
    if missing:
        LOGGER.error("Missing reference image files: %s", ", ".join(missing))
        raise SystemExit(1)


def load_timezone(name: str):
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception as exc:  # pragma: no cover - rare platform issue
            LOGGER.warning("Falling back to fixed offset timezone: %s", exc)
    # Fallback: manual UTC-5 for Lima, no DST
    return timezone(timedelta(hours=-5), name="America/Lima")


def next_run_datetime(hour: int, minute: int, tz_name: str) -> datetime:
    tz = load_timezone(tz_name)
    now = datetime.now(tz)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return target


def wait_until(target_dt: datetime) -> None:
    while True:
        now = datetime.now(target_dt.tzinfo)
        remaining = (target_dt - now).total_seconds()
        if remaining <= 0:
            LOGGER.info("Reached scheduled time: %s", target_dt.strftime("%Y-%m-%d %H:%M %Z"))
            return
        sleep_for = min(300.0, max(1.0, remaining))
        LOGGER.info(
            "Waiting %.1f minutes (%.0f seconds) until %s",
            remaining / 60.0,
            remaining,
            target_dt.strftime("%H:%M %Z"),
        )
        time.sleep(sleep_for)


@contextmanager
def keep_screen_awake():
    process = None
    try:
        process = subprocess.Popen(["caffeinate"])
        LOGGER.info("Started caffeinate to keep the Mac awake (PID %s).", process.pid)
    except FileNotFoundError:
        LOGGER.warning("caffeinate binary not found; relying on natural activity to prevent sleep.")
    try:
        yield
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            LOGGER.info("Stopped caffeinate.")


def ensure_pyautogui():
    try:
        import pyautogui  # type: ignore
    except ImportError as exc:
        LOGGER.error("PyAutoGUI is required. Install it with 'pip install pyautogui pillow opencv-python'.")
        raise SystemExit(1) from exc
    pyautogui.FAILSAFE = True  # Move the mouse to a corner to abort safely.
    pyautogui.PAUSE = 0.5
    scale_x = scale_y = 1.0
    try:
        screen_width, screen_height = pyautogui.size()
        screenshot = pyautogui.screenshot()
        shot_width, shot_height = screenshot.size
        if shot_width and shot_height:
            scale_x = screen_width / shot_width
            scale_y = screen_height / shot_height
            LOGGER.debug(
                "Screen vs screenshot dimensions: (%s, %s) vs (%s, %s) -> scale (%.3f, %.3f)",
                screen_width,
                screen_height,
                shot_width,
                shot_height,
                scale_x,
                scale_y,
            )
            if not (0.95 <= scale_x <= 1.05 and 0.95 <= scale_y <= 1.05):
                LOGGER.info(
                    "Applying coordinate scale factors (%.3f, %.3f) for high-DPI display.",
                    scale_x,
                    scale_y,
                )
    except Exception as exc:  # pragma: no cover - failsafe if screenshot capture broken
        LOGGER.warning("Unable to sample screen size for scaling: %s", exc)
        scale_x = scale_y = 1.0
    try:
        import cv2  # type: ignore
    except ImportError:
        return pyautogui, None, (scale_x, scale_y)
    return pyautogui, 0.9, (scale_x, scale_y)


def refresh_browser(pyautogui, wait_seconds: float = 3.0) -> None:
    modifier = "command" if sys.platform == "darwin" else "ctrl"
    LOGGER.info("Refreshing browser with %s+R and waiting %.1f seconds.", modifier, wait_seconds)
    try:
        pyautogui.hotkey(modifier, "r")
        time.sleep(wait_seconds)
    except Exception as exc:
        LOGGER.warning("Browser refresh hotkey failed: %s", exc)


def locate_and_click(pyautogui, image_path: Path, confidence, scale):
    start = time.monotonic()
    deadline = start + FIND_TIMEOUT_SECONDS
    LOGGER.info("Searching for %s (timeout %ss).", image_path.name, FIND_TIMEOUT_SECONDS)
    location = None
    last_log = 0.0
    while time.monotonic() < deadline:
        try:
            if confidence is not None:
                location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)
            else:
                location = pyautogui.locateOnScreen(str(image_path))
        except Exception as exc:
            LOGGER.error("Error while scanning for %s: %s", image_path.name, exc)
            break
        if location is not None:
            point = pyautogui.center(location)
            scale_x, scale_y = scale
            x_coord = float(point.x) * scale_x
            y_coord = float(point.y) * scale_y
            LOGGER.info(
                "Found %s at raw %s -> scaled (%.1f, %.1f). Moving and clicking.",
                image_path.name,
                point,
                x_coord,
                y_coord,
            )
            pyautogui.moveTo(x_coord, y_coord, duration=0.5)
            pyautogui.click()
            remaining = deadline - time.monotonic()
            if remaining > 0:
                LOGGER.info("Waiting %.1f seconds before the next step.", remaining)
                time.sleep(remaining)
            return True
        now = time.monotonic()
        if now - last_log >= 5:
            LOGGER.debug("Still searching for %s...", image_path.name)
            last_log = now
        time.sleep(1.0)
    LOGGER.warning("Skipping %s; image not found within %s seconds.", image_path.name, FIND_TIMEOUT_SECONDS)
    return False


def run_sequence(images, skip_last: bool = False, refresh_first: bool = False):
    pyautogui, confidence, scale = ensure_pyautogui()
    if refresh_first:
        refresh_browser(pyautogui)
    sequence = images[:-1] if skip_last and len(images) > 1 else images
    if skip_last and len(images) > 0:
        LOGGER.info("Skipping final step (%s) in this run.", images[-1].name)
    for image_path in sequence:
        locate_and_click(pyautogui, image_path, confidence, scale)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the scheduled autologin workflow.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(verbose=args.verbose)
    images = resolve_images(IMAGE_SEQUENCE)
    ensure_images_exist(images)
    target_dt = next_run_datetime(TARGET_HOUR, TARGET_MINUTE, TARGET_TZ)
    LOGGER.info(
        "Automation configured for %s targeting %s.",
        target_dt.strftime("%Y-%m-%d %H:%M %Z"),
        ", ".join(image.name for image in images),
    )
    try:
        with keep_screen_awake():
            wait_until(target_dt)
            LOGGER.info("Starting UI automation steps.")
            run_sequence(images, refresh_first=True)
            LOGGER.info("Automation completed.")
    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user. Exiting early.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
