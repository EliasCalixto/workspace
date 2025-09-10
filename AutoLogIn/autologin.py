import argparse
import sys
import time
import threading
import subprocess
import platform
from datetime import datetime, timedelta

# Prefer zoneinfo (Python 3.9+) to avoid external deps
try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


AWAKE_JIGGLE_INTERVAL_SEC = 60


def now_in_tz(tz_name: str) -> datetime:
    if ZoneInfo is None:
        # Fallback to naive local time if zoneinfo not available
        return datetime.now()
    return datetime.now(ZoneInfo(tz_name))


def next_time_today_or_tomorrow(tz_name: str, hh: int, mm: int) -> datetime:
    tz_now = now_in_tz(tz_name)
    target = tz_now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= tz_now:
        target = target + timedelta(days=1)
    return target


class ScreenAwake:
    """Keep the screen awake while this object is alive.

    - macOS: spawns `caffeinate -dimsu` and terminates it on exit
    - Windows: uses SetThreadExecutionState in a background thread
    - Linux/others: does a minimal mouse jiggle periodically (non-intrusive)
    """

    def __init__(self):
        self._proc = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._platform = platform.system().lower()

    def start(self):
        if "darwin" in self._platform or self._platform == "mac" or self._platform == "macos":
            try:
                self._proc = subprocess.Popen(["caffeinate", "-dimsu"])  # keep system/display awake
            except FileNotFoundError:
                # Fall back to jiggle thread if caffeinate not present
                self._start_jiggle()
        elif "windows" in self._platform:
            self._start_windows_awake()
        else:
            self._start_jiggle()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def _start_windows_awake(self):  # pragma: no cover - platform specific
        try:
            import ctypes

            ES_AWAYMODE_REQUIRED = 0x00000040
            ES_CONTINUOUS = 0x80000000
            ES_DISPLAY_REQUIRED = 0x00000002
            ES_SYSTEM_REQUIRED = 0x00000001

            def _tick():
                # Call every ~50s to maintain state
                while not self._stop.is_set():
                    ctypes.windll.kernel32.SetThreadExecutionState(
                        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED | ES_AWAYMODE_REQUIRED
                    )
                    self._stop.wait(50)

            self._thread = threading.Thread(target=_tick, daemon=True)
            self._thread.start()
        except Exception:
            self._start_jiggle()

    def _start_jiggle(self):
        try:
            import pyautogui  # imported lazily

            def _jiggle():
                while not self._stop.is_set():
                    try:
                        x, y = pyautogui.position()
                        pyautogui.moveTo(x + 1, y)
                        pyautogui.moveTo(x, y)
                    except Exception:
                        pass
                    self._stop.wait(AWAKE_JIGGLE_INTERVAL_SEC)

            self._thread = threading.Thread(target=_jiggle, daemon=True)
            self._thread.start()
        except Exception:
            # If pyautogui is missing, we simply do nothing rather than fail
            pass


def click_image(path: str, timeout: float = 30.0, confidence: float = 0.8, move_duration: float = 0.15) -> bool:
    """Locate an image on screen and click its center.

    Returns True if clicked, False otherwise.
    Requires OpenCV for confidence matching.
    """
    import pyautogui

    start = time.time()
    last_err: Exception | None = None
    while time.time() - start < timeout:
        try:
            location = pyautogui.locateCenterOnScreen(path, confidence=confidence, grayscale=True)
            if location:
                pyautogui.moveTo(location.x, location.y, duration=move_duration)
                pyautogui.click()
                return True
        except Exception as e:  # Likely OpenCV not available or permissions missing
            last_err = e
            time.sleep(0.5)
        time.sleep(0.4)
    if last_err:
        print(f"[warn] click_image('{path}') last error: {last_err}")
    return False


def perform_login(images_dir: str, slow: float) -> bool:
    """Performs the 3-click login flow using provided reference images.

    Expected files inside `images_dir`:
      - step1_menu.png   : user/profile menu button (top-right)
      - step2_login.png  : 'Log In' (or similar) menu item
      - step3_submit.png : 'Submit' button on the modal
    """
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = slow

    s1 = f"{images_dir}/step1_menu.png"
    s2 = f"{images_dir}/step2_login.png"
    s3 = f"{images_dir}/step3_submit.png"

    print("[info] Step 1: open menu…")
    if not click_image(s1, timeout=25):
        print("[error] Could not find step1_menu.png on screen")
        return False

    print("[info] Step 2: click 'Log In'…")
    if not click_image(s2, timeout=25):
        print("[error] Could not find step2_login.png on screen")
        return False

    print("[info] Waiting modal…")
    time.sleep(1.0)

    print("[info] Step 3: submit…")
    if not click_image(s3, timeout=30):
        print("[error] Could not find step3_submit.png on screen")
        return False

    print("[ok] Login clicks completed")
    return True


def wait_until(target_dt: datetime, tz_name: str):
    while True:
        now = now_in_tz(tz_name)
        delta = (target_dt - now).total_seconds()
        if delta <= 0:
            break
        # Sleep in small chunks to allow Ctrl+C
        time.sleep(min(30, max(1, delta)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Automate BMS login click flow at a scheduled time.")
    parser.add_argument("action", choices=["now", "schedule"], nargs="?", default="schedule",
                        help="Run now or wait until the scheduled time")
    parser.add_argument("--time", default="07:29", dest="time_hhmm",
                        help="Local time in HH:MM for America/Lima (default 07:29)")
    parser.add_argument("--tz", default="America/Lima", dest="tz_name",
                        help="IANA timezone name (default America/Lima)")
    parser.add_argument("--images", default="AutoLogIn", dest="images_dir",
                        help="Directory containing step images (default AutoLogIn)")
    parser.add_argument("--slow", type=float, default=0.2, dest="slow",
                        help="Pause between PyAutoGUI actions (default 0.2s)")
    parser.add_argument("--no-awake", action="store_true", help="Do not force screen awake while running")
    parser.add_argument("--dry-run", action="store_true", help="Do not click; just report schedule and steps")
    args = parser.parse_args(argv)

    hh, mm = map(int, args.time_hhmm.split(":"))

    # Start keep-awake if requested
    awake = ScreenAwake()
    if not args.no_awake:
        awake.start()

    try:
        if args.action == "schedule":
            target = next_time_today_or_tomorrow(args.tz_name, hh, mm)
            print(f"[info] Current time: {now_in_tz(args.tz_name).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"[info] Waiting until: {target.strftime('%Y-%m-%d %H:%M:%S %Z')}… Press Ctrl+C to cancel.")
            wait_until(target, args.tz_name)

        if args.dry_run:
            print("[dry-run] Would perform 3 login clicks using images from:", args.images_dir)
            return 0

        ok = perform_login(args.images_dir, args.slow)
        return 0 if ok else 2
    finally:
        awake.stop()


if __name__ == "__main__":
    sys.exit(main())

