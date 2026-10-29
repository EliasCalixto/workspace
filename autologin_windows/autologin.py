#!/usr/bin/env python3
"""Windows port of autologin: keeps the PC awake and marks the BMS labor events
(07:25 login, 12:30 lunch, 13:12 back from lunch, Lima time).

Same templates, schedule and email flow as the macOS version (../autologin),
but every macOS-only piece is replaced by its Win32 equivalent via ctypes:

- caffeinate            -> SetThreadExecutionState
- Quartz capture/click  -> PIL ImageGrab (all monitors) + SetCursorPos/SendInput
- CGSession lock state  -> OpenInputDesktop (desktop name != "Default")
- ioreg HIDIdleTime     -> GetLastInputInfo

Tuned for a 2K (2560x1440) monitor: the PNGs were captured on a Retina Mac, so
the matcher sweeps several template scales (0.5x..2x) to cover Windows display
scaling of 100%/125%/150%.
"""
import argparse
import ctypes
import logging
import sys
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


def send_email_confirmation(success=True, *, is_test: bool = False, details: str = "", label=None) -> None:
    remitente = "eliascalixto989@gmail.com"
    password = "memf ogpf rwbl qcdk"
    destinatario = "eliascalixto989@gmail.com"

    run_type = label or ("Test" if is_test else "Autologin")
    if success is None:  # intentionally skipped, not an error
        status_emoji, status_text, result_text = "⚠️", "Skipped", "Se omitio."
    elif success:
        status_emoji, status_text, result_text = "✅", "Succeeded", "Se ejecuto correctamente."
    else:
        status_emoji, status_text, result_text = "❌", "Failed", "No se ejecuto correctamente."
    executed_at = datetime.now(load_timezone(TARGET_TZ)).strftime("%Y-%m-%d %H:%M:%S %Z")

    # On success the subject is just the event label (e.g. "✅ Login",
    # "✅ Lunch Started"); on failure/skip the status is appended for clarity.
    subject_text = run_type if success else f"{run_type} ({status_text})"

    mensaje = MIMEMultipart()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = Header(f"{status_emoji} {subject_text} [Windows]", "utf-8") # type: ignore

    body_lines = [
        f"Tipo de ejecucion: {run_type}",
        "Equipo: PC Windows",
        f"Hora: {executed_at}",
        f"Estado: {status_emoji} {result_text}",
    ]
    if details:
        body_lines.append(f"Detalle: {details}")
    cuerpo = "\n".join(body_lines)
    mensaje.attach(MIMEText(cuerpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as servidor:
            servidor.starttls()
            servidor.login(remitente, password)
            servidor.send_message(mensaje)
        LOGGER.info("Email notification sent: %s %s", run_type, status_text)
    except Exception as exc:
        LOGGER.error("Unable to send email notification: %s", exc)

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 fallback
    ZoneInfo = None  # type: ignore

LOGGER = logging.getLogger("autologin")
BASE_DIR = Path(__file__).resolve().parent
IS_WINDOWS = sys.platform == "win32"

# Individual template names.
STEP_LOGIN_IMAGE = "step4_login.png"   # "Log In" labor event (clock in / return from lunch)
STEP_SUBMIT_IMAGE = "step5_submit.png"  # magenta "Submit" confirmation button
STEP_LUNCH_IMAGE = "step_lunch.png"     # "Lunch" labor event (start lunch)

# Shared prefix for every labor-event job: refresh + portal re-login (only
# clicked if the session logged out) + open the name dropdown. step1/step2 are
# skipped after the find timeout when the portal is still logged in.
_LOGIN_PREFIX = ["step1_bluelogin.png", "step2_here.png", "step3_menu.png"]
MORNING_SEQUENCE = _LOGIN_PREFIX + [STEP_LOGIN_IMAGE, STEP_SUBMIT_IMAGE]
LUNCH_SEQUENCE = _LOGIN_PREFIX + [STEP_LUNCH_IMAGE, STEP_SUBMIT_IMAGE]
POSTLUNCH_SEQUENCE = _LOGIN_PREFIX + [STEP_LOGIN_IMAGE, STEP_SUBMIT_IMAGE]

# Kept for parity with the macOS version (autologintest.py imports IMAGE_SEQUENCE).
IMAGE_SEQUENCE = MORNING_SEQUENCE

TARGET_TZ = "America/Lima"
# Morning login.
TARGET_HOUR = 7
TARGET_MINUTE = 25
# Start lunch.
LUNCH_HOUR = 12
LUNCH_MINUTE = 30
# Return from lunch (log back in).
POSTLUNCH_HOUR = 13
POSTLUNCH_MINUTE = 12
FIND_TIMEOUT_SECONDS = 20
# How long to watch for real keyboard/mouse input (with the jiggler paused)
# when deciding whether the user is present and lunch should be skipped.
PRESENCE_PROBE_SECONDS = 20.0
# SetThreadExecutionState keeps the display on and blocks sleep, but (per the
# Win32 docs) it does NOT stop the screen saver, and a screen saver with "On
# resume, display logon screen" — or a domain inactivity-lock policy — locks
# the PC. The jiggler injects a mouse move on this interval so GetLastInputInfo
# never reports enough idle time for either to kick in.
JIGGLE_INTERVAL_SECONDS = 10.0
# The PNGs were captured on a Retina Mac (144 dpi = 2x; step_lunch.png at 1x).
# On a 2K monitor the same page renders at 0.5x of a Retina capture with 100%
# Windows scaling, 0.625x at 125% and 0.75x at 150% (and 1x/1.25x/1.5x for 1x
# captures), so sweep all of them and keep the best score.
TEMPLATE_SCALES = (1.0, 0.5, 0.5625, 0.625, 0.6875, 0.75, 0.875, 1.25, 1.5, 2.0)
# Slightly below the Mac's 0.85: Windows (ClearType) renders text a little
# differently from the macOS captures. Run `autologintest.py --check` to see
# the real scores; if they are low, recapture the PNGs on Windows.
MATCH_CONFIDENCE = 0.80

# --- Win32 plumbing -----------------------------------------------------------

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_R = 0x52

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

DESKTOP_SWITCHDESKTOP = 0x0100
UOI_NAME = 2

if IS_WINDOWS:
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    ULONG_PTR = ctypes.c_size_t

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    user32.SetCursorPos.argtypes = (ctypes.c_int, ctypes.c_int)
    user32.GetCursorPos.argtypes = (ctypes.POINTER(wintypes.POINT),)
    user32.GetSystemMetrics.argtypes = (ctypes.c_int,)
    user32.GetLastInputInfo.argtypes = (ctypes.POINTER(LASTINPUTINFO),)
    user32.OpenInputDesktop.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    user32.OpenInputDesktop.restype = wintypes.HANDLE
    user32.CloseDesktop.argtypes = (wintypes.HANDLE,)
    user32.GetUserObjectInformationW.argtypes = (
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
    )
    kernel32.GetTickCount.restype = wintypes.DWORD
    kernel32.SetThreadExecutionState.argtypes = (wintypes.DWORD,)
    kernel32.SetThreadExecutionState.restype = wintypes.DWORD


def _enable_dpi_awareness() -> None:
    """Work in physical pixels on every monitor.

    Without this, Windows display scaling (125%/150% on a 2K panel) makes the
    process see a virtualized, smaller desktop: screenshots come back
    downscaled and SetCursorPos coordinates no longer match them. Must run
    before anything creates a window or grabs the screen.
    """
    if not IS_WINDOWS:
        return
    try:  # Windows 10 1703+: per-monitor v2.
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except Exception:
        pass
    try:  # Windows 8.1+: per-monitor.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


_enable_dpi_awareness()


def _virtual_screen():
    """(left, top, width, height) of the desktop spanning every monitor."""
    return (
        user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
    )


def _cursor_pos():
    point = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def _send_inputs(*inputs) -> int:
    array = (INPUT * len(inputs))(*inputs)
    return user32.SendInput(len(inputs), array, ctypes.sizeof(INPUT))


def _mouse_input(flags: int, dx: int = 0, dy: int = 0):
    return INPUT(type=INPUT_MOUSE, u=_INPUTUNION(mi=MOUSEINPUT(dx, dy, 0, flags, 0, 0)))


def _key_input(vk: int, up: bool = False):
    flags = KEYEVENTF_KEYUP if up else 0
    return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(vk, 0, flags, 0, 0)))


def _absolute_move(x: int, y: int):
    """A SendInput move to (x, y) in virtual-desktop pixels (any monitor)."""
    left, top, width, height = _virtual_screen()
    ax = int(round((x - left) * 65535 / max(width - 1, 1)))
    ay = int(round((y - top) * 65535 / max(height - 1, 1)))
    return _mouse_input(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK, ax, ay)


# --- Schedule -----------------------------------------------------------------


class ScheduledJob:
    """One timed labor-event marking (morning login, lunch, post-lunch login)."""

    def __init__(self, key, label, hour, minute, image_names, success_image,
                 skip_if_user_active=False, requires=None):
        self.key = key                          # short id, e.g. "lunch"
        self.label = label                      # human label used in logs/email
        self.hour = hour
        self.minute = minute
        self.image_names = image_names          # click sequence for this job
        self.success_image = success_image      # its click confirms success
        self.skip_if_user_active = skip_if_user_active
        self.requires = requires                # key of a job that must succeed first


def build_jobs():
    """The daily schedule, in definition order."""
    return [
        ScheduledJob("morning", "Login", TARGET_HOUR, TARGET_MINUTE,
                     MORNING_SEQUENCE, STEP_SUBMIT_IMAGE),
        ScheduledJob("lunch", "Lunch Started", LUNCH_HOUR, LUNCH_MINUTE,
                     LUNCH_SEQUENCE, STEP_SUBMIT_IMAGE, skip_if_user_active=True),
        ScheduledJob("postlunch", "Lunch Finished", POSTLUNCH_HOUR, POSTLUNCH_MINUTE,
                     POSTLUNCH_SEQUENCE, STEP_SUBMIT_IMAGE,
                     skip_if_user_active=True, requires="lunch"),
    ]


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
        except Exception as exc:  # Windows without the tzdata package
            LOGGER.debug("Falling back to fixed offset timezone: %s", exc)
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


# --- Keep awake / anti-lock ---------------------------------------------------


def _nudge_cursor() -> None:
    """Move the cursor a couple of pixels so Windows registers user input.

    SetCursorPos alone relocates the pointer but does not count as input for
    GetLastInputInfo (so the screen saver / lock timer keeps running); the
    SendInput move to the same point is what resets the idle timer. Doing both
    mirrors the macOS lesson: a real reposition plus an injected event. The
    direction alternates so the cursor never drifts more than a couple of
    pixels. Coordinates are virtual-desktop pixels, so it works on any monitor.
    """
    if not IS_WINDOWS:
        return
    try:
        sign = -getattr(_nudge_cursor, "_sign", 1)
        _nudge_cursor._sign = sign
        x, y = _cursor_pos()
        target = (x + 2 * sign, y)
        user32.SetCursorPos(*target)
        _send_inputs(_absolute_move(*target))
    except Exception as exc:  # pragma: no cover - best-effort keep-awake
        LOGGER.debug("Cursor nudge failed: %s", exc)


class _ActivityJiggler:
    """Background thread that nudges the cursor on an interval to keep the
    screen saver (and therefore the Windows lock screen) from ever engaging."""

    def __init__(self, interval: float = JIGGLE_INTERVAL_SECONDS):
        self.interval = interval
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread = None

    def _run(self) -> None:
        # Nudge immediately so a screen saver that is about to start is reset.
        while True:
            if not self._paused.is_set():
                _nudge_cursor()
            if self._stop.wait(self.interval):
                return

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._paused.clear()
        self._thread = threading.Thread(target=self._run, name="anti-lock-jiggler", daemon=True)
        self._thread.start()
        LOGGER.info("Anti-lock jiggler started (cursor nudge every %.0fs).", self.interval)

    def pause(self) -> None:
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        LOGGER.info("Anti-lock jiggler stopped.")


_JIGGLER = _ActivityJiggler()


def screen_is_locked():
    """True/False if the Windows lock screen is active, or None if unknown.

    While locked (or on a UAC secure desktop) the input desktop is "Winlogon"
    and a normal process cannot open it; when usable it is "Default".
    """
    if not IS_WINDOWS:
        return None
    try:
        hdesk = user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
        if not hdesk:
            return True
        try:
            buf = ctypes.create_unicode_buffer(256)
            needed = wintypes.DWORD()
            if not user32.GetUserObjectInformationW(hdesk, UOI_NAME, buf, ctypes.sizeof(buf), ctypes.byref(needed)):
                return None
            return buf.value.lower() != "default"
        finally:
            user32.CloseDesktop(hdesk)
    except Exception as exc:
        LOGGER.debug("Could not read screen lock state: %s", exc)
        return None


def wake_display() -> None:
    """Dismiss an active (but unlocked) screen saver by injecting activity."""
    _nudge_cursor()
    time.sleep(1.0)


def _idle_seconds():
    """Seconds since the last keyboard/mouse input (GetLastInputInfo), or None."""
    if not IS_WINDOWS:
        return None
    try:
        info = LASTINPUTINFO(cbSize=ctypes.sizeof(LASTINPUTINFO))
        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        # Both are 32-bit millisecond tick counts; mask handles the 49-day wrap.
        return ((kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0
    except Exception as exc:
        LOGGER.debug("Could not read idle time: %s", exc)
    return None


def user_is_active(probe_seconds: float = PRESENCE_PROBE_SECONDS) -> bool:
    """True if real keyboard/mouse input happened during a short probe window.

    The jiggler is paused first so its own injected nudges don't count as
    activity. We then wait `probe_seconds` and read the idle time: with no
    user it climbs to about `probe_seconds`; if it stays low, the user moved the
    mouse or typed and is therefore using the PC.
    """
    _JIGGLER.pause()
    try:
        time.sleep(probe_seconds)
        idle = _idle_seconds()
    finally:
        _JIGGLER.resume()
    if idle is None:
        LOGGER.warning(
            "No se pudo leer el tiempo de inactividad; se asume usuario AUSENTE para no bloquear la automatizacion."
        )
        return False
    active = idle < (probe_seconds - 5.0)
    LOGGER.info(
        "Chequeo de presencia: idle=%.1fs tras %.0fs con jiggler en pausa -> usuario %s.",
        idle, probe_seconds, "ACTIVO" if active else "ausente",
    )
    return active


@contextmanager
def keep_screen_awake():
    """Hold the display on and block system sleep (Windows' caffeinate)."""
    held = False
    if IS_WINDOWS:
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        if kernel32.SetThreadExecutionState(flags):
            held = True
            LOGGER.info("SetThreadExecutionState activo: pantalla y sistema no se suspenderan.")
        else:
            LOGGER.warning("SetThreadExecutionState failed; relying on the jiggler to prevent sleep.")
    else:
        LOGGER.warning("Not running on Windows; keep-awake and input injection are disabled.")
    _JIGGLER.start()
    try:
        yield
    finally:
        _JIGGLER.stop()
        if held:
            kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            LOGGER.info("SetThreadExecutionState liberado.")


# --- Screen matching / clicking -----------------------------------------------


def ensure_dependencies():
    """Return (cv2, numpy, ImageGrab) or exit with install instructions."""
    try:
        import cv2  # type: ignore
        import numpy  # type: ignore
        from PIL import ImageGrab  # type: ignore
    except ImportError as exc:
        LOGGER.error(
            "Faltan dependencias (%s). Instala con: py -m pip install -r requirements.txt", exc
        )
        raise SystemExit(1) from exc
    return cv2, numpy, ImageGrab


def refresh_browser(wait_seconds: float = 3.0) -> None:
    LOGGER.info("Refreshing browser with ctrl+R and waiting %.1f seconds.", wait_seconds)
    try:
        _send_inputs(_key_input(VK_CONTROL), _key_input(VK_R))
        time.sleep(0.05)
        _send_inputs(_key_input(VK_R, up=True), _key_input(VK_CONTROL, up=True))
        time.sleep(wait_seconds)
    except Exception as exc:
        LOGGER.warning("Browser refresh hotkey failed: %s", exc)


def _capture_desktop(backend):
    """Grab every monitor at once.

    Returns (origin_x, origin_y, gray_pixels): origin is the virtual-desktop
    top-left (negative when a monitor sits left of/above the primary one).
    """
    cv2, np, ImageGrab = backend
    shot = ImageGrab.grab(all_screens=True)
    left, top, _width, _height = _virtual_screen()
    gray = cv2.cvtColor(np.asarray(shot.convert("RGB")), cv2.COLOR_RGB2GRAY)
    return left, top, gray


def best_match(backend, image_path: Path):
    """Best (x, y, score, template_scale) for the template across all monitors,
    whatever its score, or None if nothing could be compared."""
    cv2, _np, _ImageGrab = backend
    template = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        LOGGER.error("Could not read template image %s.", image_path)
        return None
    origin_x, origin_y, gray = _capture_desktop(backend)
    best = None
    for tpl_scale in TEMPLATE_SCALES:
        if tpl_scale == 1.0:
            resized = template
        else:
            interp = cv2.INTER_AREA if tpl_scale < 1.0 else cv2.INTER_LINEAR
            resized = cv2.resize(template, None, fx=tpl_scale, fy=tpl_scale, interpolation=interp)
        tpl_h, tpl_w = resized.shape
        if tpl_h > gray.shape[0] or tpl_w > gray.shape[1] or tpl_h < 4 or tpl_w < 4:
            continue
        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if best is None or max_val > best[2]:
            x = origin_x + max_loc[0] + tpl_w // 2
            y = origin_y + max_loc[1] + tpl_h // 2
            best = (x, y, max_val, tpl_scale)
    return best


def _click_at(x: int, y: int) -> None:
    """Move and left-click at virtual-desktop pixel coordinates (any monitor)."""
    user32.SetCursorPos(x, y)
    _send_inputs(_absolute_move(x, y))
    time.sleep(0.3)
    _send_inputs(_mouse_input(MOUSEEVENTF_LEFTDOWN))
    time.sleep(0.05)
    _send_inputs(_mouse_input(MOUSEEVENTF_LEFTUP))


def locate_and_click(backend, image_path: Path):
    start = time.monotonic()
    deadline = start + FIND_TIMEOUT_SECONDS
    LOGGER.info("Searching for %s (timeout %ss).", image_path.name, FIND_TIMEOUT_SECONDS)
    last_log = 0.0
    best = None
    while time.monotonic() < deadline:
        try:
            best = best_match(backend, image_path)
        except Exception as exc:
            LOGGER.error("Error while scanning the screen for %s: %s", image_path.name, exc)
            break
        if best is not None and best[2] >= MATCH_CONFIDENCE:
            x, y, score, tpl_scale = best
            LOGGER.info(
                "Found %s at (%d, %d) (score %.3f, template scale %.3fx). Moving and clicking.",
                image_path.name,
                x,
                y,
                score,
                tpl_scale,
            )
            _click_at(x, y)
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
    if best is not None:
        LOGGER.debug(
            "Best candidate for %s scored %.3f at %.3fx (< %.2f threshold).",
            image_path.name,
            best[2],
            best[3],
            MATCH_CONFIDENCE,
        )
    LOGGER.warning("Skipping %s; image not found within %s seconds.", image_path.name, FIND_TIMEOUT_SECONDS)
    return False


def run_sequence(images, skip_last: bool = False, refresh_first: bool = False):
    backend = ensure_dependencies()
    # Pause the jiggler so its nudges don't move the cursor mid-click; the
    # clicking itself keeps the machine active during this short window.
    _JIGGLER.pause()
    try:
        # Make sure the desktop is actually visible before we start clicking.
        wake_display()
        locked = screen_is_locked()
        if locked:
            LOGGER.error(
                "Screen is LOCKED at run time: the Windows lock screen is showing, "
                "not the browser, so no steps can be clicked. SetThreadExecutionState "
                "cannot unlock it; the anti-lock jiggler is meant to keep this from "
                "happening on future runs."
            )
            return False, [image.name for image in images], [], True
        if refresh_first:
            refresh_browser()
        sequence = images[:-1] if skip_last and len(images) > 1 else images
        if skip_last and len(images) > 0:
            LOGGER.info("Skipping final step (%s) in this run.", images[-1].name)
        clicked_steps = []
        missing_steps = []
        for image_path in sequence:
            if locate_and_click(backend, image_path):
                clicked_steps.append(image_path.name)
            else:
                missing_steps.append(image_path.name)
    finally:
        _JIGGLER.resume()
    if missing_steps:
        LOGGER.warning("Sequence completed with missing steps: %s", ", ".join(missing_steps))
    else:
        LOGGER.info("Sequence completed successfully.")
    return len(missing_steps) == 0, missing_steps, clicked_steps, False


def wait_until_manual_stop() -> None:
    LOGGER.info("Autologin finalizado. Manteniendo el script activo. Presiona Ctrl+C para detener.")
    while True:
        time.sleep(300)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the scheduled autologin workflow (Windows).")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging output.")
    return parser.parse_args()


def run_job(job) -> bool:
    """Run one scheduled job (presence check, sequence, email). True on success."""
    images = resolve_images(job.image_names)
    missing_files = [p.name for p in images if not p.exists()]
    if missing_files:
        detail = f"Faltan archivos de imagen: {', '.join(missing_files)}"
        LOGGER.error("%s: %s", job.label, detail)
        send_email_confirmation(success=False, label=job.label, details=detail)
        return False

    if job.skip_if_user_active and user_is_active():
        detail = "Omitido: estabas usando la PC en ese momento (se detecto actividad de teclado/mouse)."
        LOGGER.info("%s: %s", job.label, detail)
        send_email_confirmation(success=None, label=job.label, details=detail)
        return False

    LOGGER.info("Iniciando job: %s", job.label)
    _all_ok, missing_steps, clicked_steps, screen_locked = run_sequence(images, refresh_first=True)
    if job.success_image in clicked_steps:
        details = "Marcacion confirmada (Submit ejecutado)."
        if missing_steps:
            details += f" Pasos opcionales no encontrados: {', '.join(missing_steps)}"
        send_email_confirmation(success=True, label=job.label, details=details)
        return True
    detail_parts = []
    if screen_locked:
        detail_parts.append("La pantalla estaba BLOQUEADA (pantalla de bloqueo de Windows); no se pudo continuar.")
    detail_parts.append(f"No se pudo confirmar click en {job.success_image}.")
    if missing_steps:
        detail_parts.append(f"Pasos no encontrados: {', '.join(missing_steps)}")
    send_email_confirmation(success=False, label=job.label, details=" ".join(detail_parts))
    return False


def main() -> int:
    args = parse_args()
    configure_logging(verbose=args.verbose)
    jobs = build_jobs()
    # Schedule each job at its next future occurrence and run them in
    # chronological order, so the script works no matter when it is launched.
    scheduled = sorted(
        ((next_run_datetime(job.hour, job.minute, TARGET_TZ), job) for job in jobs),
        key=lambda pair: pair[0],
    )
    LOGGER.info(
        "Jobs programados: %s",
        "; ".join(f"{job.label} @ {dt.strftime('%Y-%m-%d %H:%M %Z')}" for dt, job in scheduled),
    )
    keepalive_started = False
    results = {}
    try:
        with keep_screen_awake():
            try:
                for target_dt, job in scheduled:
                    wait_until(target_dt)
                    if job.requires and not results.get(job.requires):
                        detail = (
                            f"Omitido: el paso previo '{job.requires}' no se marco, "
                            "asi que no hay lunch del cual regresar."
                        )
                        LOGGER.info("%s: %s", job.label, detail)
                        send_email_confirmation(success=None, label=job.label, details=detail)
                        results[job.key] = False
                        continue
                    results[job.key] = run_job(job)
                LOGGER.info("Todos los jobs del dia procesados.")
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                LOGGER.exception("Automation failed with an unexpected error.")
                send_email_confirmation(success=False, details=f"Error inesperado: {exc}")
            keepalive_started = True
            wait_until_manual_stop()
        return 0 if any(results.values()) else 1
    except KeyboardInterrupt:
        if keepalive_started:
            LOGGER.info("Detenido manualmente por el usuario.")
            return 0 if any(results.values()) else 1
        LOGGER.warning("Interrupted by user. Exiting early.")
        send_email_confirmation(
            success=False,
            is_test=False,
            details="Ejecucion interrumpida por el usuario.",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
