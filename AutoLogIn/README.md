# Auto Login Mouse Automation

This script automates three mouse clicks to perform your daily login on the BMS page, keeps your screen awake while it runs, and schedules the action for 07:29 America/Lima by default.

## Files
- `AutoLogIn/autologin.py`: main script
- `AutoLogIn/requirements.txt`: Python deps (PyAutoGUI + OpenCV)
- `AutoLogIn/Screenshot1.png`..`Screenshot3.png`: your reference screenshots (provided). For reliable detection, create three small cropped images described below.

## Prepare reference images (important)
Create small, crisp crops (PNG, no scaling) for the exact UI parts to click:
- `AutoLogIn/step1_menu.png`: the top-right profile/menu button that opens the dropdown
- `AutoLogIn/step2_login.png`: the dropdown item for login (you showed a logout example; capture the login item instead)
- `AutoLogIn/step3_submit.png`: the purple `Submit` button within the small popup window

Tips:
- Use your OS screenshot tool to crop only the button/label; avoid full-screen captures.
- Keep the browser zoom constant (100%) and macOS display scaling unchanged.
- Grant screen recording permission to your terminal/IDE so PyAutoGUI can see the screen.

## Install
Create/activate a virtualenv (recommended), then:

```
pip install -r AutoLogIn/requirements.txt
```

On macOS, PyAutoGUI may ask for Accessibility + Screen Recording permissions.

## Run
- Run at the scheduled time (default 07:29 America/Lima):

```
python AutoLogIn/autologin.py schedule --time 07:29 --tz America/Lima --images AutoLogIn
```

- Run immediately:

```
python AutoLogIn/autologin.py now --images AutoLogIn
```

- Dry-run (no clicks, just schedule info):

```
python AutoLogIn/autologin.py schedule --dry-run
```

The script keeps your screen awake automatically (macOS uses `caffeinate` if available; otherwise it jiggles the mouse minimally). Disable with `--no-awake`.

## Troubleshooting
- If images aren’t found, re-crop them smaller and sharper, or reduce/raise confidence by editing `autologin.py` (`confidence=0.8`).
- Keep your browser window visible on the active desktop; do not minimize it.
- Ensure consistent zoom level and UI theme.
- If OpenCV is missing, reinstall requirements.

## Notes
- You provided logout screenshots as examples. Replace step2 with your actual “Login/Clock In” item.
- The script is fail-safe: moving mouse to the upper-left corner aborts PyAutoGUI actions.

