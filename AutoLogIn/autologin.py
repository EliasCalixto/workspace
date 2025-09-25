import argparse
import sys
import time
import threading
import subprocess
import platform
from datetime import datetime, timedelta
from pathlib import Path

# Prefer zoneinfo (Python 3.9+) to avoid external deps
try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


AWAKE_JIGGLE_INTERVAL_SEC = 60
DEFAULT_IMAGES_DIR = str(Path(__file__).resolve().parent)


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
                    ctypes.windll.kernel32.SetThreadExecutionState( # type: ignore
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

    Tries PyAutoGUI first, then an OpenCV multi-scale search so images taken on
    different resolutions can still be matched. Returns True if clicked.
    """

    import pyautogui

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        has_cv = True
    except Exception:
        has_cv = False

    metrics: dict[str, object] = {}

    def _ensure_display_metrics(require_image: bool = False, refresh_image: bool = False):
        if not metrics:
            logical_w, logical_h = map(int, pyautogui.size())
            ratio_x = ratio_y = 1.0
            try:
                from AppKit import NSScreen  # type: ignore

                screen = NSScreen.mainScreen()
                if screen is not None and hasattr(screen, "backingScaleFactor"):
                    scale = float(screen.backingScaleFactor())
                    if scale > 0:
                        ratio_x = ratio_y = scale
            except Exception:
                pass

            metrics.update(
                {
                    "logical_w": logical_w,
                    "logical_h": logical_h,
                    "ratio_x": ratio_x,
                    "ratio_y": ratio_y,
                    "screenshot": None,
                    "logged": False,
                }
            )

        if refresh_image and metrics:
            metrics["screenshot"] = None

        if (require_image or metrics["ratio_x"] == 1.0 or metrics["ratio_y"] == 1.0) and metrics["screenshot"] is None:
            logical_w = int(metrics["logical_w"])  # type: ignore[assignment]
            logical_h = int(metrics["logical_h"])  # type: ignore[assignment]
            try:
                shot = pyautogui.screenshot(region=(0, 0, logical_w, logical_h))
            except Exception:
                shot = pyautogui.screenshot()
            screen_w, screen_h = shot.size

            if metrics["ratio_x"] == 1.0 or metrics["ratio_y"] == 1.0:
                logical_w = int(metrics["logical_w"])  # type: ignore[assignment]
                logical_h = int(metrics["logical_h"])  # type: ignore[assignment]
                metrics["ratio_x"] = screen_w / logical_w if logical_w else 1.0
                metrics["ratio_y"] = screen_h / logical_h if logical_h else 1.0

            metrics["screenshot"] = shot

        return metrics

    def _pyautogui_locate(threshold: float) -> tuple[float, float] | None:
        """Use built-in locate (convert coordinates for Retina displays)."""

        try:
            if has_cv:
                loc = pyautogui.locateCenterOnScreen(path, confidence=threshold, grayscale=True)
            else:
                loc = pyautogui.locateCenterOnScreen(path)
                if loc is None:
                    try:
                        loc = pyautogui.locateCenterOnScreen(path, grayscale=True)  # type: ignore[arg-type]
                    except TypeError:
                        pass
        except Exception:
            return None

        if loc is None:
            return None

        info = _ensure_display_metrics()
        ratio_x = info["ratio_x"]  # type: ignore[assignment]
        ratio_y = info["ratio_y"]  # type: ignore[assignment]

        # PyAutoGUI may return pixel coordinates on Retina; convert back to logical points.
        x = loc.x / ratio_x if ratio_x and ratio_x != 1.0 else loc.x
        y = loc.y / ratio_y if ratio_y and ratio_y != 1.0 else loc.y
        if not info["logged"] and (ratio_x != 1.0 or ratio_y != 1.0):
            logical_w = info["logical_w"]  # type: ignore[assignment]
            logical_h = info["logical_h"]  # type: ignore[assignment]
            print(
                f"[info] Retina scale: coords {logical_w}x{logical_h}, ratio {ratio_x:.2f}x{ratio_y:.2f}"
            )
            info["logged"] = True
        return (x, y)

    def _opencv_multiscale_locate(threshold: float) -> tuple[float, float] | None:
        if not has_cv:
            return None

        try:
            template = cv2.imread(path, cv2.IMREAD_COLOR)
        except Exception:
            return None

        if template is None or template.size == 0:
            print(f"[warn] '{path}' could not be read by OpenCV. Check that the file exists and is a valid image.")
            return None

        info = _ensure_display_metrics(require_image=True, refresh_image=True)
        screenshot = info["screenshot"]  # type: ignore[assignment]
        if screenshot is None:
            return None
        logical_w = info["logical_w"]  # type: ignore[assignment]
        logical_h = info["logical_h"]  # type: ignore[assignment]
        ratio_x = info["ratio_x"]  # type: ignore[assignment]
        ratio_y = info["ratio_y"]  # type: ignore[assignment]

        if not info["logged"] and (ratio_x != 1.0 or ratio_y != 1.0):
            screen_w, screen_h = screenshot.size
            print(
                f"[info] Retina scale: capture {screen_w}x{screen_h}px vs coords {logical_w}x{logical_h} (ratio {ratio_x:.2f}x{ratio_y:.2f})"
            )
            info["logged"] = True

        screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        scale_candidates: list[float] = [1.0]
        if ratio_x > 0 and abs(ratio_x - 1.0) >= 0.01:
            scale_candidates.append(round(ratio_x, 3))

        for scale in scale_candidates:
            if scale == 1.0:
                scaled_template = template_gray
            else:
                new_w = max(1, int(template_gray.shape[1] * scale))
                new_h = max(1, int(template_gray.shape[0] * scale))
                if new_w > screenshot_gray.shape[1] or new_h > screenshot_gray.shape[0]:
                    continue
                interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
                scaled_template = cv2.resize(template_gray, (new_w, new_h), interpolation=interp)

            result = cv2.matchTemplate(screenshot_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                center_x = max_loc[0] + scaled_template.shape[1] / 2
                center_y = max_loc[1] + scaled_template.shape[0] / 2
                logical_x = center_x / ratio_x
                logical_y = center_y / ratio_y
                print(
                    f"[info] OpenCV match '{path}' scale {scale:.2f} conf {max_val:.2f} -> ({logical_x:.1f},{logical_y:.1f})"
                )
                return (logical_x, logical_y)

        return None

    start = time.time()
    last_err: Exception | None = None
    while time.time() - start < timeout:
        elapsed = time.time() - start
        ratio = elapsed / timeout if timeout else 1.0
        if ratio < 0.4:
            search_conf = confidence
        elif ratio < 0.7:
            search_conf = max(0.6, confidence - 0.15)
        else:
            search_conf = max(0.5, confidence - 0.25)

        try:
            source = "pyautogui"
            location = _pyautogui_locate(search_conf)
            if location is None:
                source = "opencv"
                location = _opencv_multiscale_locate(search_conf)

            if location is not None:
                x, y = location
                print(f"[info] {source} move -> ({x:.1f}, {y:.1f})")
                pyautogui.moveTo(x, y, duration=move_duration)
                pyautogui.click()
                return True
        except Exception as e:
            last_err = e
            time.sleep(0.5)
        time.sleep(0.4)

    if not has_cv:
        print(f"[warn] OpenCV missing; only exact-size match for '{path}'")
    if last_err:
        print(f"[warn] click_image '{path}': {last_err}")
    return False


def perform_login(images_dir: str, slow: float) -> bool:
    import pyautogui

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = slow

    images_root = Path(images_dir).expanduser()
    steps = [
        ("Step 1", "blue login button", images_root / "step1_bluelogin.png", 25),
        ("Step 2", "'click here' link", images_root / "step2_here.png", 25),
        ("Step 3", "menu", images_root / "step3_menu.png", 30),
        ("Step 4", "login option", images_root / "step4_login.png", 30),
        ("Step 5", "submit button", images_root / "step5_submit.png", 30),
    ]

    completed: list[str] = []
    skipped: list[str] = []

    for step_id, description, img_path, timeout in steps:
        print(f"[info] {step_id} - {description}")
        if not img_path.exists():
            print(f"[warn] {step_id} skipped: image file missing ({img_path})")
            skipped.append(f"{step_id} ({description}) - missing file")
            continue

        if click_image(str(img_path), timeout=timeout):
            completed.append(step_id)
            continue

        print(f"[warn] {step_id} skipped: '{img_path.name}' not visible after {timeout}s")
        skipped.append(f"{step_id} ({description}) - not visible")

    if completed:
        if skipped:
            print(
                f"[info] Done {len(completed)} step(s): {', '.join(completed)}. "
                f"Skipped {len(skipped)}: {'; '.join(skipped)}"
            )
        else:
            print("[ok] All steps completed")
        return True

    print("[error] No steps succeeded; please verify the reference images and UI state")
    return False


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
    parser.add_argument("--images", default=DEFAULT_IMAGES_DIR, dest="images_dir",
                        help=f"Directory containing step images (default {DEFAULT_IMAGES_DIR})")
    parser.add_argument("--slow", type=float, default=0.2, dest="slow",
                        help="Pause between PyAutoGUI actions (default 0.2s)")
    parser.add_argument("--no-awake", action="store_true", help="Do not force screen awake while running")
    parser.add_argument("--dry-run", action="store_true", help="Do not click; just report schedule and steps")
    args = parser.parse_args(argv)

    hh, mm = map(int, args.time_hhmm.split(":"))
    images_dir = str(Path(args.images_dir).expanduser())
    images_path = Path(images_dir)
    images_display = str(images_path.resolve()) if images_path.exists() else images_dir
    print(f"[info] Using images directory: {images_display}")

    # Start keep-awake if requested
    awake = ScreenAwake()
    if not args.no_awake:
        awake.start()

    try:
        if args.action == "schedule":
            target = next_time_today_or_tomorrow(args.tz_name, hh, mm)
            print(f"[info] Now: {now_in_tz(args.tz_name).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"[info] Wait until: {target.strftime('%Y-%m-%d %H:%M:%S %Z')} (Ctrl+C to cancel)")
            wait_until(target, args.tz_name)

        if args.dry_run:
            print(f"[dry-run] Would run 5 steps using images from {images_dir}")
            return 0

        ok = perform_login(images_dir, args.slow)
        return 0 if ok else 2
    finally:
        awake.stop()


if __name__ == "__main__":
    sys.exit(main())
