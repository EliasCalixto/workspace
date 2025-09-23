# Auto Login Mouse Automation

This script automates five mouse clicks to run the daily BMS login flow, keeps the screen awake while it waits, and can run immediately or at a scheduled time (default 07:29 America/Lima).

## Files
- `autologin.py`: main script
- `autologin_test.py`: helper runner that skips the final submit click for safe dry testing
- `requirements.txt`: Python dependencies (`pyautogui`, `opencv-python`)
- `step1_bluelogin.png` .. `step5_submit.png`: reference images used for matching

## Reference images
Provide five crisp PNG crops of the UI elements you need to click. Cada paso es opcional: si la imagen no aparece en pantalla dentro del tiempo de espera, el script pasa al siguiente paso automáticamente.
1. `step1_bluelogin.png`: blue login button on the landing page
2. `step2_here.png`: "click here" link that opens the BMS login frame
3. `step3_menu.png`: menu/profile button that reveals the login option
4. `step4_login.png`: the login/clock-in menu entry
5. `step5_submit.png`: the final submit/confirm button

Tips:
- Crop tightly around the button/text; avoid full-screen screenshots.
- Capture the images at normal browser zoom (100%).
- Grant Accessibility + Screen Recording permissions to the terminal/IDE on macOS so PyAutoGUI can see the screen.
- OpenCV is required for best results: the script now performs multi-scale template matching so the same images work across different resolutions and HiDPI monitors. Without OpenCV it falls back to exact-size matching only.

## Install
Create/activate a virtualenv (recommended), then run:

```
pip install -r requirements.txt
```

## Run
Run immediately using the default images directory:

```
python autologin.py now
```

Schedule the flow for a specific time:

```
python autologin.py schedule --time 07:29 --tz America/Lima
```

Use alternative images or slow down the actions if needed:

```
python autologin.py now --images /path/to/images --slow 0.4
```

Add `--dry-run` to skip the clicks but verify scheduling, or `--no-awake` to disable the keep-awake helper.

## Troubleshooting
- If a step fails, verify the image file exists and matches the current UI (color theme, zoom, etc.).
- On macOS Retina/high-DPI monitors, keep the browser window fully visible. The OpenCV fallback reports the scale it used; use that information when recapturing images.
- Reinstall requirements if you see errors about missing OpenCV or PyAutoGUI.
- La automatización está calibrada para la pantalla principal Retina del MacBook Pro; desconecta monitores externos o ajusta el código antes de usar múltiples displays.

## Testing without submitting
`autologin_test.py` forwards all arguments to `autologin.py` but skips the final submit click so you can verify the first four interactions safely:

```
python autologin_test.py now
```
