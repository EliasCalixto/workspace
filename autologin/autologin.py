#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportFunctionMemberAccess=false
"""macOS autologin: keeps the Mac awake and marks the BMS labor events
(07:25 login, 12:30 lunch, 13:12 back from lunch, and Log Out at 18:15 on
Mondays / 17:45 Tuesday-Friday, Lima time), Monday to Friday.

Runs continuously: after the Log Out it waits for the next working day's
Login, and so on, until stopped manually with Ctrl+C.

Same schedule, templates and email flow as the Windows version
(../autologin_windows), with the macOS OS layer:

- keep awake       -> caffeinate (restarted automatically if it dies) + jiggler
- capture / click  -> Quartz (every display) + OpenCV, pyautogui fallback
- lock state       -> CGSessionCopyCurrentDictionary
- idle time        -> ioreg HIDIdleTime

Probar solo el correo:  python3 autologin.py --test-email
Verificar todo:         python3 verificar.py
"""
import argparse
import logging
import logging.handlers
import os
import dotenv
import re
import subprocess
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
from typing import Optional

from google_token import GOOGLE_TOKEN

try:  # Python 3.9+
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 fallback
    ZoneInfo = None  # type: ignore

LOGGER = logging.getLogger("autologin")
BASE_DIR = Path(__file__).resolve().parent

# --- Email --------------------------------------------------------------------

EMAIL_REMITENTE = "eliascalixto989@gmail.com"
# Contraseña de aplicacion de Gmail (la misma que usa autologin_windows). Los
# espacios se quitan solos. Si existe la variable de entorno
# AUTOLOGIN_GMAIL_APP_PASSWORD, se usa esa en su lugar.
EMAIL_PASSWORD = GOOGLE_TOKEN
EMAIL_DESTINATARIO = "eliascalixto989@gmail.com"
EMAIL_INTENTOS = 3


def send_email_confirmation(success: Optional[bool] = True, *, is_test: bool = False, details: str = "", label=None) -> bool:
    """Envia la notificacion. Devuelve True si se envio. Nunca lanza excepciones."""
    remitente = EMAIL_REMITENTE
    password = EMAIL_PASSWORD.replace(" ", "")
    destinatario = EMAIL_DESTINATARIO

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
    mensaje["Subject"] = Header(f"{status_emoji} {subject_text} [Mac]", "utf-8")  # type: ignore

    body_lines = [
        f"Tipo de ejecucion: {run_type}",
        "Equipo: Mac",
        f"Hora: {executed_at}",
        f"Estado: {status_emoji} {result_text}",
    ]
    if details:
        body_lines.append(f"Detalle: {details}")
    mensaje.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))

    # Prueba 587 (STARTTLS) y, si falla, 465 (SSL). Reintenta varias veces por
    # si la red (o el Wi-Fi recien despertado) falla un momento.
    for intento in range(1, EMAIL_INTENTOS + 1):
        for port in (587, 465):
            servidor = None
            try:
                if port == 465:
                    servidor = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
                else:
                    servidor = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
                    servidor.ehlo()
                    servidor.starttls()
                    servidor.ehlo()
                servidor.login(remitente, password)
                servidor.send_message(mensaje)
                LOGGER.info(
                    "Email enviado (puerto %d, intento %d): %s %s",
                    port, intento, run_type, status_text,
                )
                return True
            except smtplib.SMTPAuthenticationError as exc:
                LOGGER.error(
                    "Gmail rechazo la contraseña de aplicacion (genera una nueva): %s", exc
                )
                return False  # reintentar no sirve si la contraseña es invalida
            except Exception:
                LOGGER.exception("Fallo envio de email por puerto %d (intento %d)", port, intento)
            finally:
                if servidor is not None:
                    try:
                        servidor.quit()
                    except Exception:
                        pass
        if intento < EMAIL_INTENTOS:
            time.sleep(10)
    LOGGER.error("No se pudo enviar el email tras %d intentos.", EMAIL_INTENTOS)
    return False


# Individual template names.
STEP_LOGIN_IMAGE = "step4_login.png"   # "Log In" labor event (clock in / return from lunch)
STEP_SUBMIT_IMAGE = "step5_submit.png"  # magenta "Submit" confirmation button
STEP_LUNCH_IMAGE = "step_lunch.png"     # "Lunch" labor event (start lunch)
STEP_LOGOUT_IMAGE = "step_logout.png"   # "Log Out" labor event (end of day)

# Shared prefix for every labor-event job: refresh + portal re-login (only
# clicked if the session logged out) + open the name dropdown. step1/step2 are
# skipped after the find timeout when the portal is still logged in.
_LOGIN_PREFIX = ["step1_bluelogin.png", "step2_here.png", "step3_menu.png"]
MORNING_SEQUENCE = _LOGIN_PREFIX + [STEP_LOGIN_IMAGE, STEP_SUBMIT_IMAGE]
LUNCH_SEQUENCE = _LOGIN_PREFIX + [STEP_LUNCH_IMAGE, STEP_SUBMIT_IMAGE]
POSTLUNCH_SEQUENCE = _LOGIN_PREFIX + [STEP_LOGIN_IMAGE, STEP_SUBMIT_IMAGE]
LOGOUT_SEQUENCE = _LOGIN_PREFIX + [STEP_LOGOUT_IMAGE, STEP_SUBMIT_IMAGE]

# Kept for backward compatibility (autologintest.py imports IMAGE_SEQUENCE).
IMAGE_SEQUENCE = MORNING_SEQUENCE

TARGET_TZ = "America/Lima"
# Working days for Login / Lunch / back from lunch: 0=lunes ... 4=viernes.
# Saturdays and Sundays nothing is marked; the script just keeps waiting.
WORK_DAYS = (0, 1, 2, 3, 4)
# Morning login.
TARGET_HOUR = 7
TARGET_MINUTE = 25
# Start lunch.
LUNCH_HOUR = 12
LUNCH_MINUTE = 30
# Return from lunch (log back in).
POSTLUNCH_HOUR = 13
POSTLUNCH_MINUTE = 12
# End of day (Log Out), per weekday: 0=lunes ... 6=domingo, (hora, minuto).
# Days not listed (sabado y domingo) have no Log Out.
LOGOUT_TIMES = {
    0: (18, 15),  # lunes 6:15 pm
    1: (17, 45),  # martes 5:45 pm
    2: (17, 45),  # miercoles
    3: (17, 45),  # jueves
    4: (17, 45),  # viernes
}
# Like lunch: if you are using the Mac at that moment, the Log Out is skipped
# (and you get a "Skipped" email) so the script doesn't take over the mouse
# while you work. Set to False to always click Log Out.
LOGOUT_SKIP_IF_USER_ACTIVE = True
# If the Mac was asleep (lid closed, battery) and wakes up long after a job's
# time, the job is skipped with a ⚠️ email instead of marking e.g. Lunch at
# 15:00. Set to None to always run late jobs.
MAX_LATE_MINUTES = 20
FIND_TIMEOUT_SECONDS = 20
# How long to watch for real keyboard/mouse input (with the jiggler paused)
# when deciding whether the user is present and lunch should be skipped.
PRESENCE_PROBE_SECONDS = 20.0
# How often the anti-lock jiggler nudges the cursor. caffeinate keeps the
# display powered but does NOT stop the macOS screen saver from starting, and
# once it starts (askForPassword=1) the screen locks and the login page is no
# longer visible. A cursor move on this interval resets the screen-saver idle
# timer so it never engages during the long waits between jobs.
JIGGLE_INTERVAL_SECONDS = 10.0
# Templates may have been captured on a display with a different pixel density
# (Retina 2x vs external 1x, or on the Windows PC), so sweep several scales and
# keep the best score.
TEMPLATE_SCALES = (1.0, 0.5, 2.0, 0.75, 1.5, 0.625, 1.25)
MATCH_CONFIDENCE = 0.85
MAX_DISPLAYS = 16


class ScheduledJob:
    """One timed labor-event marking (login, lunch, post-lunch login, logout)."""

    def __init__(self, key, label, hour, minute, image_names, success_image,
                 skip_if_user_active=False, requires=None, weekday_times=None):
        self.key = key                          # short id, e.g. "lunch"
        self.label = label                      # human label used in logs/email
        self.hour = hour
        self.minute = minute
        self.image_names = image_names          # click sequence for this job
        self.success_image = success_image      # its click confirms success
        self.skip_if_user_active = skip_if_user_active
        self.requires = requires                # key of a job that must succeed first
        # Optional {weekday: (hour, minute)}; when set it replaces hour/minute
        # and the job only runs on the listed weekdays (0=Monday).
        self.weekday_times = weekday_times

    def time_on(self, weekday: int):
        """(hour, minute) for that weekday, or None if the job doesn't run then."""
        if self.weekday_times is None:
            return (self.hour, self.minute) if weekday in WORK_DAYS else None
        return self.weekday_times.get(weekday)


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
        ScheduledJob("logout", "Logout", None, None,
                     LOGOUT_SEQUENCE, STEP_SUBMIT_IMAGE,
                     skip_if_user_active=LOGOUT_SKIP_IF_USER_ACTIVE,
                     weekday_times=LOGOUT_TIMES),
    ]


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [
        logging.handlers.RotatingFileHandler(
            BASE_DIR / "autologin.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        ),
    ]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())  # type: ignore[arg-type]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
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
            LOGGER.debug("Falling back to fixed offset timezone: %s", exc)
    # Fallback: manual UTC-5 for Lima, no DST
    return timezone(timedelta(hours=-5), name="America/Lima")


def next_run_datetime(job, tz_name: str):
    """Next future occurrence of the job (respecting its weekdays), or None."""
    tz = load_timezone(tz_name)
    now = datetime.now(tz)
    for offset in range(8):
        day = (now + timedelta(days=offset)).date()
        hm = job.time_on(day.weekday())
        if hm is None:
            continue
        target = datetime(day.year, day.month, day.day, hm[0], hm[1], tzinfo=tz)
        if target > now:
            return target
    return None


def next_daily_datetime(hour: int, minute: int, tz_name: str) -> datetime:
    """Next occurrence of HH:MM on any day (used by autologintest.py --time)."""
    tz = load_timezone(tz_name)
    now = datetime.now(tz)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return target


def wait_until(target_dt: datetime) -> None:
    last_log = 0.0
    while True:
        # Re-check caffeinate on every tick: if it died, the Mac could sleep.
        _CAFFEINATE.ensure_running()
        now = datetime.now(target_dt.tzinfo)
        remaining = (target_dt - now).total_seconds()
        if remaining <= 0:
            LOGGER.info("Reached scheduled time: %s", target_dt.strftime("%Y-%m-%d %H:%M %Z"))
            return
        # Short sleeps against the wall clock: on macOS time.sleep() does not
        # advance while the Mac is asleep, so a long sleep could overshoot.
        if time.monotonic() - last_log >= 300:
            LOGGER.info(
                "Waiting %.1f minutes (%.0f seconds) until %s",
                remaining / 60.0,
                remaining,
                target_dt.strftime("%a %H:%M %Z"),
            )
            last_log = time.monotonic()
        time.sleep(min(30.0, max(0.5, remaining)))


def wait_until_manual_stop() -> None:
    LOGGER.info("Autologin finalizado. Manteniendo el script activo. Presiona Ctrl+C para detener.")
    while True:
        _CAFFEINATE.ensure_running()
        time.sleep(60)


# --- Keep awake / anti-lock ---------------------------------------------------


def _nudge_cursor() -> None:
    """Physically move the cursor a couple of pixels to reset the idle timer.

    A purely *synthetic* mouse-moved event (CGEventPost) is unreliable: testing
    showed it can fail to register as activity for nearly a minute at a time,
    letting the idle timer climb past the screen-saver threshold and lock the
    screen. Actually relocating the cursor with CGWarpMouseCursorPosition resets
    the idle timer on every call (measured ceiling < 8s), so we warp the cursor
    and also post an event as a belt-and-suspenders. The move direction
    alternates so the cursor never drifts more than a couple of pixels. Works
    across all monitors (global coordinates); falls back to pyautogui.
    """
    try:
        import Quartz  # type: ignore
    except ImportError:
        try:
            import pyautogui  # type: ignore
            sign = -getattr(_nudge_cursor, "_sign", 1)
            _nudge_cursor._sign = sign
            pyautogui.moveRel(2 * sign, 0, duration=0)
        except Exception as exc:  # pragma: no cover - best-effort keep-awake
            LOGGER.debug("Cursor nudge (pyautogui) failed: %s", exc)
        return
    try:
        sign = -getattr(_nudge_cursor, "_sign", 1)
        _nudge_cursor._sign = sign
        loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
        pt = (loc.x + 2 * sign, loc.y)
        # Real cursor reposition — this is what reliably counts as user activity.
        Quartz.CGWarpMouseCursorPosition(pt)
        event = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventMouseMoved, pt, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        # Keep the physical mouse and the on-screen cursor in sync after warping.
        Quartz.CGAssociateMouseAndMouseCursorPosition(True)
    except Exception as exc:  # pragma: no cover - best-effort keep-awake
        LOGGER.debug("Cursor nudge (Quartz) failed: %s", exc)


class _ActivityJiggler:
    """Background thread that nudges the cursor on an interval to keep the
    screen saver (and therefore the login lock) from ever engaging."""

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


class _Caffeinate:
    """Owns the caffeinate process and restarts it if it ever exits.

    `-w <pid>` makes caffeinate exit on its own if this script dies, so no
    orphan keeps the Mac awake after a crash.
    """

    def __init__(self):
        self.process = None
        self.enabled = False

    def _cmd(self):
        return ["caffeinate", "-d", "-i", "-s", "-w", str(os.getpid())]

    def start(self) -> None:
        self.enabled = True
        self._spawn()

    def _spawn(self) -> None:
        try:
            self.process = subprocess.Popen(self._cmd())
            LOGGER.info("Started caffeinate %s (PID %s).", " ".join(self._cmd()[1:]), self.process.pid)
        except FileNotFoundError:
            LOGGER.warning("caffeinate binary not found; relying on the jiggler to prevent sleep.")
            self.process = None
            self.enabled = False
        except Exception as exc:
            LOGGER.warning("Could not start caffeinate: %s", exc)
            self.process = None

    def ensure_running(self) -> None:
        if not self.enabled:
            return
        if self.process is None or self.process.poll() is not None:
            LOGGER.warning("caffeinate no estaba corriendo; reiniciandolo.")
            self._spawn()

    def stop(self) -> None:
        self.enabled = False
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            LOGGER.info("Stopped caffeinate.")


_CAFFEINATE = _Caffeinate()


def screen_is_locked():
    """True/False if the login lock screen is active, or None if unknown."""
    try:
        import Quartz  # type: ignore
        info = Quartz.CGSessionCopyCurrentDictionary()
        if not info:
            return None
        return bool(info.get("CGSSessionScreenIsLocked", 0))
    except Exception as exc:
        LOGGER.debug("Could not read screen lock state: %s", exc)
        return None


def wake_display() -> None:
    """Wake the display and dismiss an active (but unlocked) screen saver."""
    try:
        # Asserts user activity: turns the display on if it had gone dark.
        subprocess.run(["caffeinate", "-u", "-t", "2"], timeout=10, check=False)
    except Exception as exc:
        LOGGER.debug("caffeinate -u failed: %s", exc)
    _nudge_cursor()
    time.sleep(1.0)


def _hid_idle_seconds():
    """Seconds since the last real HID (keyboard/mouse) event, or None."""
    try:
        out = subprocess.check_output(["ioreg", "-r", "-c", "IOHIDSystem"], text=True, timeout=10)
        match = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
        if match:
            return int(match.group(1)) / 1_000_000_000
    except Exception as exc:
        LOGGER.debug("Could not read HID idle time: %s", exc)
    return None


def user_is_active(probe_seconds: float = PRESENCE_PROBE_SECONDS) -> bool:
    """True if real keyboard/mouse input happened during a short probe window.

    The jiggler is paused first so its own nudges don't count as activity. We
    then wait `probe_seconds` and read the HID idle time: with no user it
    climbs to about `probe_seconds`; if it stays low, the user moved the mouse
    or typed and is therefore using the Mac.
    """
    _JIGGLER.pause()
    try:
        time.sleep(probe_seconds)
        idle = _hid_idle_seconds()
    finally:
        _JIGGLER.resume()
    if idle is None:
        LOGGER.warning(
            "No se pudo leer el tiempo de inactividad; se asume usuario AUSENTE para no bloquear la automatizacion."
        )
        return False
    active = idle < (probe_seconds - 5.0)
    LOGGER.info(
        "Chequeo de presencia: HID idle=%.1fs tras %.0fs con jiggler en pausa -> usuario %s.",
        idle, probe_seconds, "ACTIVO" if active else "ausente",
    )
    return active


@contextmanager
def keep_screen_awake():
    """Hold the display on and block system sleep for the whole run."""
    _CAFFEINATE.start()
    _JIGGLER.start()
    try:
        yield
    finally:
        _JIGGLER.stop()
        _CAFFEINATE.stop()


# --- Screen matching / clicking -----------------------------------------------


class DependencyError(RuntimeError):
    """A required Python package is missing (reported by email, never fatal)."""


def ensure_pyautogui():
    """Return (pyautogui, confidence, scale). Raises DependencyError if missing."""
    try:
        import pyautogui  # type: ignore
    except ImportError as exc:
        raise DependencyError(
            "Falta pyautogui. Corre el script con el python del entorno conda "
            "'workspace' (/opt/homebrew/anaconda3/envs/workspace/bin/python3)."
        ) from exc
    pyautogui.FAILSAFE = False  # a stray corner position must never abort a marking
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
                screen_width, screen_height, shot_width, shot_height, scale_x, scale_y,
            )
    except Exception as exc:  # pragma: no cover - failsafe if screenshot capture broken
        LOGGER.warning("Unable to sample screen size for scaling: %s", exc)
        scale_x = scale_y = 1.0
    try:
        import cv2  # type: ignore  # noqa: F401
    except ImportError:
        return pyautogui, None, (scale_x, scale_y)
    return pyautogui, 0.9, (scale_x, scale_y)


def refresh_browser(pyautogui, wait_seconds: float = 3.0) -> None:
    LOGGER.info("Refreshing browser with command+R and waiting %.1f seconds.", wait_seconds)
    try:
        pyautogui.hotkey("command", "r")
    except Exception as exc:
        LOGGER.warning("pyautogui command+R failed (%s); trying Quartz.", exc)
        try:
            import Quartz  # type: ignore
            key_r = 15  # kVK_ANSI_R
            down = Quartz.CGEventCreateKeyboardEvent(None, key_r, True)
            up = Quartz.CGEventCreateKeyboardEvent(None, key_r, False)
            Quartz.CGEventSetFlags(down, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventSetFlags(up, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
            time.sleep(0.05)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        except Exception as exc2:
            LOGGER.warning("Browser refresh hotkey failed: %s", exc2)
    time.sleep(wait_seconds)


def _load_multimonitor_backend():
    """Return (Quartz, cv2, numpy) when all are importable, else None."""
    try:
        import Quartz  # type: ignore
        import cv2  # type: ignore
        import numpy  # type: ignore
    except ImportError as exc:
        LOGGER.debug("Multi-monitor backend unavailable (%s); using single-screen fallback.", exc)
        return None
    return Quartz, cv2, numpy


def _capture_displays(backend):
    """Capture every active display.

    Yields (origin_x_pts, origin_y_pts, gray_pixels, px_per_pt) per display,
    where origin is the display's top-left corner in global point coordinates.
    """
    Quartz, cv2, np = backend
    err, display_ids, count = Quartz.CGGetActiveDisplayList(MAX_DISPLAYS, None, None)
    if err != 0:
        LOGGER.warning("CGGetActiveDisplayList failed with error %s.", err)
        return
    for display_id in display_ids[:count]:
        bounds = Quartz.CGDisplayBounds(display_id)
        image = Quartz.CGDisplayCreateImage(display_id)
        if image is None:
            LOGGER.warning("Could not capture display %s (screen recording permission?).", display_id)
            continue
        width = Quartz.CGImageGetWidth(image)
        height = Quartz.CGImageGetHeight(image)
        bytes_per_row = Quartz.CGImageGetBytesPerRow(image)
        data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image))
        buf = np.frombuffer(data, dtype=np.uint8)
        if buf.size < bytes_per_row * height:
            LOGGER.warning("Unexpected pixel buffer size for display %s; skipping.", display_id)
            continue
        # Rows may be padded, so reshape by bytes_per_row and crop to real width.
        bgra = buf[: bytes_per_row * height].reshape(height, bytes_per_row // 4, 4)[:, :width, :]
        gray = cv2.cvtColor(bgra, cv2.COLOR_BGRA2GRAY)
        px_per_pt = width / bounds.size.width if bounds.size.width else 1.0
        yield bounds.origin.x, bounds.origin.y, gray, px_per_pt


def best_match(backend, image_path: Path):
    """Best (global_x_pts, global_y_pts, score, template_scale) for the template
    across all displays, whatever its score, or None if nothing was compared."""
    _Quartz, cv2, _np = backend
    template = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if template is None:
        LOGGER.error("Could not read template image %s.", image_path)
        return None
    best = None
    for origin_x, origin_y, gray, px_per_pt in _capture_displays(backend):
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
                center_px_x = max_loc[0] + tpl_w / 2.0
                center_px_y = max_loc[1] + tpl_h / 2.0
                global_x = origin_x + center_px_x / px_per_pt
                global_y = origin_y + center_px_y / px_per_pt
                best = (global_x, global_y, max_val, tpl_scale)
    return best


def _click_global(Quartz, x: float, y: float) -> None:
    """Move and left-click at global point coordinates, valid on any display."""
    point = (x, y)
    Quartz.CGWarpMouseCursorPosition(point)
    move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
    time.sleep(0.3)
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    Quartz.CGAssociateMouseAndMouseCursorPosition(True)


def locate_and_click(pyautogui, image_path: Path, confidence, scale):
    start = time.monotonic()
    deadline = start + FIND_TIMEOUT_SECONDS
    LOGGER.info("Searching for %s (timeout %ss).", image_path.name, FIND_TIMEOUT_SECONDS)
    backend = _load_multimonitor_backend()
    last_log = 0.0
    best = None
    while time.monotonic() < deadline:
        if backend is not None:
            try:
                best = best_match(backend, image_path)
            except Exception as exc:
                LOGGER.error("Error while scanning displays for %s: %s", image_path.name, exc)
                backend = None  # fall back to pyautogui for the rest of this step
                continue
            if best is not None and best[2] >= MATCH_CONFIDENCE:
                global_x, global_y, score, tpl_scale = best
                LOGGER.info(
                    "Found %s at global (%.1f, %.1f) (score %.3f, template scale %.3fx). Moving and clicking.",
                    image_path.name, global_x, global_y, score, tpl_scale,
                )
                _click_global(backend[0], global_x, global_y)
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    LOGGER.info("Waiting %.1f seconds before the next step.", remaining)
                    time.sleep(remaining)
                return True
        else:
            try:
                if confidence is not None:
                    location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)
                else:
                    location = pyautogui.locateOnScreen(str(image_path))
            except Exception as exc:
                # Newer pyautogui raises ImageNotFoundException instead of
                # returning None; treat any error as "not found yet".
                LOGGER.debug("locateOnScreen for %s: %s", image_path.name, exc)
                location = None
            if location is not None:
                point = pyautogui.center(location)
                scale_x, scale_y = scale
                x_coord = float(point.x) * scale_x
                y_coord = float(point.y) * scale_y
                LOGGER.info(
                    "Found %s at raw %s -> scaled (%.1f, %.1f). Moving and clicking.",
                    image_path.name, point, x_coord, y_coord,
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
    if best is not None:
        LOGGER.info(
            "Best candidate for %s scored %.3f at %.3fx (< %.2f threshold).",
            image_path.name, best[2], best[3], MATCH_CONFIDENCE,
        )
    LOGGER.warning("Skipping %s; image not found within %s seconds.", image_path.name, FIND_TIMEOUT_SECONDS)
    return False


def run_sequence(images, skip_last: bool = False, refresh_first: bool = False):
    pyautogui, confidence, scale = ensure_pyautogui()
    # Pause the jiggler so its nudges don't move the cursor mid-click; the
    # clicking itself keeps the machine active during this short window.
    _JIGGLER.pause()
    clicked_steps = []
    missing_steps = []
    try:
        # Make sure the desktop is actually visible before we start clicking.
        wake_display()
        locked = screen_is_locked()
        if locked:
            LOGGER.error(
                "Screen is LOCKED at run time: the macOS login screen is showing, "
                "not the browser, so no steps can be clicked. caffeinate cannot "
                "unlock a password-protected screen; the anti-lock jiggler is meant "
                "to keep this from happening on future runs."
            )
            return False, [image.name for image in images], [], True
        if refresh_first:
            refresh_browser(pyautogui)
        sequence = images[:-1] if skip_last and len(images) > 1 else images
        if skip_last and len(images) > 0:
            LOGGER.info("Skipping final step (%s) in this run.", images[-1].name)
        for image_path in sequence:
            if locate_and_click(pyautogui, image_path, confidence, scale):
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


def parse_args():
    parser = argparse.ArgumentParser(description="Run the scheduled autologin workflow (macOS).")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging output.")
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Solo envia un correo de prueba y termina (no ejecuta los jobs).",
    )
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
        detail = "Omitido: estabas usando la Mac en ese momento (se detecto actividad de teclado/mouse)."
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
        detail_parts.append("La pantalla estaba BLOQUEADA (login de macOS); no se pudo continuar.")
    detail_parts.append(f"No se pudo confirmar click en {job.success_image}.")
    if missing_steps:
        detail_parts.append(f"Pasos no encontrados: {', '.join(missing_steps)}")
    send_email_confirmation(success=False, label=job.label, details=" ".join(detail_parts))
    return False


def preflight(jobs) -> None:
    """Warn early (log + one email) if something would make a job fail later."""
    problems = []
    names = sorted({name for job in jobs for name in job.image_names})
    missing = [name for name in names if not (BASE_DIR / name).exists()]
    if missing:
        problems.append(f"faltan imagenes: {', '.join(missing)}")
    for module in ("pyautogui", "Quartz", "cv2", "numpy"):
        try:
            __import__(module)
        except ImportError:
            problems.append(f"falta el modulo {module}")
    if problems:
        detail = (
            "Autologin arranco con problemas: " + "; ".join(problems)
            + f". Python usado: {sys.executable}. Usa el python del entorno conda 'workspace'."
        )
        LOGGER.error(detail)
        send_email_confirmation(success=False, label="Autologin (arranque)", details=detail)
    else:
        LOGGER.info("Preflight OK: imagenes y dependencias presentes (%s).", sys.executable)


def main() -> int:
    args = parse_args()
    configure_logging(verbose=args.verbose)

    if args.test_email:
        ok = send_email_confirmation(
            success=True, label="Prueba de correo", details="Correo de prueba de autologin (Mac)."
        )
        LOGGER.info("Prueba de correo: %s", "ENVIADO" if ok else "FALLO (revisa el error de arriba)")
        return 0 if ok else 1

    jobs = build_jobs()
    preflight(jobs)
    # Results per (date, job key), so "Lunch Finished" only checks that day's lunch.
    results = {}
    LOGGER.info("Autologin en modo continuo: corre todos los dias laborables. Presiona Ctrl+C para detener.")
    try:
        with keep_screen_awake():
            while True:
                # Always pick the job with the nearest future occurrence. After it
                # runs its time is in the past, so the next pass picks the
                # following one (after Log Out -> next working day's Login).
                upcoming = []
                for job in jobs:
                    run_at = next_run_datetime(job, TARGET_TZ)
                    if run_at is not None:
                        upcoming.append((run_at, job))
                if not upcoming:
                    LOGGER.error("No hay ningun job programado; revisa WORK_DAYS y LOGOUT_TIMES.")
                    return 1
                upcoming.sort(key=lambda pair: pair[0])
                LOGGER.info(
                    "Proximos jobs: %s",
                    "; ".join(f"{job.label} @ {dt.strftime('%a %Y-%m-%d %H:%M')}" for dt, job in upcoming),
                )
                target_dt, job = upcoming[0]
                wait_until(target_dt)
                day = target_dt.date()
                try:
                    late_min = (datetime.now(target_dt.tzinfo) - target_dt).total_seconds() / 60.0
                    if MAX_LATE_MINUTES is not None and late_min > MAX_LATE_MINUTES:
                        detail = (
                            f"Omitido: la Mac desperto {late_min:.0f} min tarde "
                            f"(programado {target_dt:%H:%M}); no se marca fuera de hora."
                        )
                        LOGGER.warning("%s: %s", job.label, detail)
                        send_email_confirmation(success=None, label=job.label, details=detail)
                        results[(day, job.key)] = False
                    elif job.requires and not results.get((day, job.requires)):
                        detail = (
                            f"Omitido: el paso previo '{job.requires}' no se marco, "
                            "asi que no hay lunch del cual regresar."
                        )
                        LOGGER.info("%s: %s", job.label, detail)
                        send_email_confirmation(success=None, label=job.label, details=detail)
                        results[(day, job.key)] = False
                    else:
                        results[(day, job.key)] = run_job(job)
                except KeyboardInterrupt:
                    raise
                except BaseException as exc:  # incl. SystemExit / DependencyError
                    # Never let one failed job stop the script: log, email, continue.
                    LOGGER.exception("%s fallo con un error inesperado.", job.label)
                    send_email_confirmation(success=False, label=job.label, details=f"Error inesperado: {exc!r}")
                    results[(day, job.key)] = False
                # Never re-run the same occurrence even if a job finished in under
                # a second (clock jitter): wait until its minute has passed.
                while datetime.now(target_dt.tzinfo) <= target_dt:
                    time.sleep(1.0)
                # Forget results older than a couple of days.
                for key in [k for k in results if k[0] < day - timedelta(days=2)]:
                    del results[key]
    except KeyboardInterrupt:
        LOGGER.info("Detenido manualmente por el usuario (Ctrl+C).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
