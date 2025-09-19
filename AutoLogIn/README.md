# Auto Login Mouse Automation

This script automates five mouse clicks to perform your daily login on the BMS page, keeps your screen awake while it runs, and schedules the action for 07:29 America/Lima by default.

## Files
- `AutoLogIn/autologin.py`: main script
- `AutoLogIn/requirements.txt`: Python deps (PyAutoGUI + OpenCV)
- `AutoLogIn/step1_bluelogin.png` .. `AutoLogIn/step5_submit.png`: your reference screenshots (provided). For reliable detection, create the five small cropped images described below.

## Prepare reference images (important)
Create small, crisp crops (PNG, no scaling) for the exact UI parts to click:
- `AutoLogIn/step1_bluelogin.png`: the blue `Log In` button that appears when the session expired
- `AutoLogIn/step2_here.png`: the `here` link/button that continues to the main portal after the blue login
- `AutoLogIn/step3_menu.png`: the top-right profile/menu button that opens the dropdown
- `AutoLogIn/step4_login.png`: the dropdown item for login (capture the login/clock-in entry)
- `AutoLogIn/step5_submit.png`: the `Submit` button within the login modal (older flows may still use `step4_submit.png` or `step3_submit.png`)

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
