# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Repository shape

This is a **multi-project workspace**, not a single app. Each top-level directory is an independent project. There is no shared build, no shared dependency manifest, and no shared virtualenv. Treat each subdirectory as its own root and `cd` into it before running anything.

- `autologin/` — Python script that schedules itself to perform a UI-automated login on macOS at a fixed wall-clock time (Lima TZ).
- `macro_mac/` — Tkinter desktop app, packaged as a `.app`/`.dmg`, that generates Salesforce-case spreadsheets from templates. Versioned by folder (`v1.0/`, `v1.1/`, `v1.2/`, `beta/`); **`v1.2/` is the current line** — make changes there.
- `templates/` — Non-code reference spreadsheets/CSVs used by support workflows. No build steps here.
- `APM_files/` — Numbered case archives (one folder per Salesforce/APM case). Reference data, not source.

`.gitignore` excludes `SalesForce/sf_private.py`, `__pycache__`, `.ipynb_checkpoints`, `.virtual_documents`, and `.DS_Store`. If you create a `SalesForce/` working area, keep secrets in `sf_private.py`.

## autologin/

A scheduled macOS automation that marks three labor events per day in the Teleperformance BMS portal via `pyautogui`/OpenCV template matching. It holds the Mac awake via `caffeinate` (+ the anti-lock jiggler) for the whole day and emails a confirmation after each event.

- The day's schedule is `build_jobs()` → a list of `ScheduledJob`s, each with a wall-clock time (`America/Lima`), a click sequence, and the image whose click confirms success. `main()` sorts jobs by their next occurrence and runs them in order, so it works whenever it's launched:
  - **Login manana** — 07:25, sequence `MORNING_SEQUENCE`, confirms on `step5_submit.png`.
  - **Lunch** — 12:30, sequence `LUNCH_SEQUENCE` (clicks `step_lunch.png` instead of `step4_login.png`); `skip_if_user_active=True`.
  - **Login post-lunch** — 13:12, same sequence as morning; `skip_if_user_active=True` and `requires="lunch"` (skipped if lunch wasn't marked, so it never logs "back in" from a lunch that never happened).
- All three share `_LOGIN_PREFIX` (`step1_bluelogin` → `step2_here` → `step3_menu`): the portal re-login clicks are attempted but skipped after the find timeout when the session is still logged in. The only labor-event templates that differ are `step4_login.png` ("Log In" — clock in / return from lunch) vs `step_lunch.png` ("Lunch"), both magenta dropdown entries opened by `step3_menu`.
- `skip_if_user_active` calls `user_is_active()`: it pauses the jiggler, waits `PRESENCE_PROBE_SECONDS` (20s), and reads `HIDIdleTime`; if idle stayed low, real keyboard/mouse input happened → the user is present → the job is skipped and emailed as ⚠️ Skipped (email has three states: ✅ success / ❌ fail / ⚠️ `success=None` skip). Morning login has no presence skip.
- `autologin.py` — production run; clicks every step including the final `Submit`.
- `autologintest.py` — imports `autologin` as a library and dry-runs only the **morning** sequence, **skipping the final submit**, with `--time HH:MM` to override the schedule.
- All write to a single `LOGGER` named `"autologin"`; pass `--verbose` for DEBUG output.

Run:

```bash
cd autologin
python3 autologin.py                  # waits until 07:25 Lima, then runs
python3 autologintest.py --time 14:30 # dry-run at chosen time, no submit
```

Notes when editing:
- The PNG filenames in the sequences and in `STEP_LOGIN_IMAGE`/`STEP_SUBMIT_IMAGE`/`STEP_LUNCH_IMAGE` are **load-bearing**: they must match files on disk. Each job keys success off its `success_image` (all three currently `step5_submit.png`); `autologintest.py` keys off `STEP_LOGIN_IMAGE`. A job whose template files are missing is skipped with a ❌ email listing the missing files (it does not abort the other jobs) — this is how a not-yet-captured `step_lunch.png` degrades. Templates are captured from the real screen at native resolution; the multi-scale matcher (1x/0.5x/2x) then handles Retina-vs-1x differences.
- `locate_and_click` first tries a multi-monitor path (Quartz + OpenCV): it captures every active display, template-matches at `TEMPLATE_SCALES` (1x/0.5x/2x, so templates captured on the Retina panel still match on 1x external monitors), and clicks via Quartz events in global coordinates — required because `pyautogui.moveTo` clamps to the main display. If Quartz/cv2 are missing it falls back to the original single-screen `pyautogui.locateOnScreen` path, which applies a screen-vs-screenshot scale factor for Retina/HiDPI. Don't strip either — coordinates from `pyautogui.center()` are in screenshot pixels and need scaling for `moveTo`.
- Run with the `workspace` conda env (`/opt/homebrew/anaconda3/envs/workspace/bin/python3`) — it has `pyautogui`, `opencv`, and `pyobjc`/Quartz; the system `python3` does not.
- `caffeinate -d -i -s` keeps the display powered and blocks system sleep, but on modern macOS it does **not** stop the screen saver from starting, and with `askForPassword=1` the screen then locks — which is why a run can wake to a password lock screen and match zero steps. `keep_screen_awake()` therefore also starts `_JIGGLER` (`_ActivityJiggler`), a daemon thread that moves the cursor every `JIGGLE_INTERVAL_SECONDS` (10s) to reset the HID idle timer so the screen saver never engages during the long wait. `_nudge_cursor` uses `CGWarpMouseCursorPosition` (a real ±2px cursor reposition, direction alternating so it never drifts) + a posted event — **not** a purely synthetic `CGEventPost` move: testing showed synthetic-only events can fail to register as activity for ~55s at a stretch (idle climbed past the lock threshold and the screen locked), whereas the real warp resets idle every call (measured ceiling <10s). Don't revert to synthetic-only, and don't lengthen the interval much. `run_sequence` pauses the jiggler while clicking (so nudges don't move the cursor mid-click) and resumes it after. It also calls `wake_display()` + `screen_is_locked()` first; if the screen is locked it aborts early and the confirmation email says so (the 4th return value, `screen_locked`). The jiggler cannot recover a screen the user locked *manually* before leaving — the Mac must be left unlocked when starting the script.
- After the sequence runs, the script intentionally calls `wait_until_manual_stop()` and blocks forever so `caffeinate` keeps holding the machine awake. This is by design; killing it with Ctrl+C is the expected exit path.
- Gmail credentials are embedded in `send_email_confirmation` as an app password. If it stops working, rotate the app password and update the literal in both `autologin.py` and the email body strings.

## macro_mac/

A Tkinter GUI (`main.py`) that takes a Salesforce Case ID, Account ID, and a list of Hotel IDs, and produces a folder of Excel/CSV deliverables for one of three workflows: **API Onboarding**, **Simple Disconnection**, or **BMC Exports**. Each workflow loads blueprint files from `renatos_macro_templates/<workflow>/`, duplicates the first template row once per hotel ID, fills in the IDs, and writes the result under `<dest>/<case_id>/`.

Architecture worth knowing before editing:

- `TEMPLATES` (top of `main.py`) maps button label → blueprint folder under `renatos_macro_templates/`. Adding a workflow means: add a key here, add a template folder, and add a `create_*` function plus a button in `main()`.
- `_duplicate_rows` is the shared row-expansion engine. It mutates `Hotel ID`, `Expedia ID`, and `SF ID` columns if present on the template's first row — column names in templates must match these exactly or the IDs won't get written.
- `_prefix_name` strips everything before the first `_` in the template filename and replaces it with the case ID. Template files are therefore named like `testapiob_Stop Sell Removal.xlsx`; the `testapiob_` prefix is discarded and `<case_id> Stop Sell Removal.xlsx` is written.
- `_prepare_case_dir` always creates `Exports Results/` and `Imports Results/` subfolders, even though the current `create_*` functions write directly into the case root. The subfolders exist for downstream tooling — don't remove them.
- `Simple Disconnection` renames `Expedia ID` → `Hotel ID` in the output. Onboarding does not. This asymmetry is intentional.

Versioning: `v1.0/`, `v1.1/`, `v1.2/`, and `beta/` each contain a self-contained `main.py` + `renatos_macro_templates/` + `create_dmg.sh`. Older versions are kept for distributed users; **edit only `v1.2/`** unless explicitly working on a back-port or the next beta.

Build/distribute (from `macro_mac/v1.2/`, per `notes.txt`):

```bash
conda deactivate                      # PyInstaller must run outside conda
pyinst                                # the user's alias/wrapper for pyinstaller
./create_dmg.sh                       # bundles dist/CoreOTA_Macro.app into a .dmg
```

`create_dmg.sh` reads `APP_NAME` and `VERSION` at the top of the script. Bump `VERSION` when releasing — the script names the `.dmg` from it and overwrites in place. Requirements (`requirements.txt`): `numpy`, `pandas`, `pillow`, `requests`, `pyinstaller`, `tkinter`.

Run the GUI directly during development:

```bash
cd macro_mac/v1.2
python3 main.py
```

## templates/ and APM_files/

No code, no build. `templates/` holds master spreadsheets referenced by support workflows; `APM_files/` is per-case archive data (numbered folders, some zipped). Don't edit these to "clean up" — they are working references.

When preparing an APM case file, **always load and verify every requested EID before handing it off**. A case folder or copied template is not "prepared" if its `Hotel ID` / `Account ID` rows are blank. Clear any sample data when appropriate, preserve legitimate template defaults, then verify the final list and order against the request before reporting completion.

For `BMC/BMC1/IMPORT 1 BMC Cloud Property.xlsx`, use the contract target model rather than blindly mirroring every PS&NS field. In particular, when the current row is `Merchant`, leave `Commissions Charged for Taxes`, `Commissions Charged for Fees`, and `Commissions Charged for Cancellations` blank; do not copy the EC commission flags from PS&NS. Set target-model fields according to the requested conversion (a `Dual` row may need `Target Hotel Business Model=Merchant`).
