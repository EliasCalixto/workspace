# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository shape

This is a **multi-project workspace**, not a single app. Each top-level directory is an independent project. There is no shared build, no shared dependency manifest, and no shared virtualenv. Treat each subdirectory as its own root and `cd` into it before running anything.

- `autologin/` — Python script that schedules itself to perform a UI-automated login on macOS at a fixed wall-clock time (Lima TZ).
- `macro_mac/` — Tkinter desktop app, packaged as a `.app`/`.dmg`, that generates Salesforce-case spreadsheets from templates. Versioned by folder (`v1.0/`, `v1.1/`, `v1.2/`, `beta/`); **`v1.2/` is the current line** — make changes there.
- `templates/` — Non-code reference spreadsheets/CSVs used by support workflows. No build steps here.
- `APM_files/` — Numbered case archives (one folder per Salesforce/APM case). Reference data, not source.

`.gitignore` excludes `SalesForce/sf_private.py`, `__pycache__`, `.ipynb_checkpoints`, `.virtual_documents`, and `.DS_Store`. If you create a `SalesForce/` working area, keep secrets in `sf_private.py`.

## autologin/

A scheduled macOS automation. `autologin.py` waits until `TARGET_HOUR:TARGET_MINUTE` in `America/Lima` (currently 07:25), then uses `pyautogui` to find and click through the `step1_*.png` → `step5_*.png` reference image sequence in order. It holds the Mac awake via `caffeinate` for the duration and emails a confirmation to a hardcoded Gmail account at the end.

- `autologin.py` — production run; clicks every step including `step5_submit.png`.
- `autologintest.py` — imports `autologin` as a library and reuses its functions; runs the same sequence but **skips the final submit step** and accepts `--time HH:MM` to override the schedule. Use this for dry runs.
- Both write to a single `LOGGER` named `"autologin"`; pass `--verbose` for DEBUG output.

Run:

```bash
cd autologin
python3 autologin.py                  # waits until 07:25 Lima, then runs
python3 autologintest.py --time 14:30 # dry-run at chosen time, no submit
```

Notes when editing:
- The PNG filenames in `IMAGE_SEQUENCE`, `STEP_LOGIN_IMAGE`, and `STEP_SUBMIT_IMAGE` are **load-bearing**: they must match files on disk, and `autologintest.py` keys its success check off `STEP_LOGIN_IMAGE` while `autologin.py` keys success off `STEP_SUBMIT_IMAGE`. Renaming a PNG without updating those constants silently breaks email confirmation logic.
- `locate_and_click` applies a screen-vs-screenshot scale factor to handle Retina/HiDPI. Don't strip this — coordinates from `pyautogui.center()` are in screenshot pixels and need scaling for `moveTo`.
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
