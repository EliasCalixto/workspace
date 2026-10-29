#!/usr/bin/env python3
"""Test run variant of the Windows autologin without the final submit click.

--check skips the schedule and clicks nothing: it scans the screen once and
prints, for every template, its best match score and the scale it matched at.
Use it with the BMS portal open to confirm the Mac-captured PNGs are found on
the 2K monitor before trusting a real run.
"""
import argparse
import sys
import autologin


def parse_time(value: str):
    try:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Time must be in HH:MM 24-hour format") from exc
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise argparse.ArgumentTypeError("Hour must be 0-23 and minute 0-59")
    return hour, minute


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the autologin workflow without submitting, at a time you choose.",
    )
    parser.add_argument(
        "--time",
        type=parse_time,
        default=(autologin.TARGET_HOUR, autologin.TARGET_MINUTE),
        help="Schedule time in HH:MM (America/Lima). Default matches production run.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report match score/scale for every template right now; no clicks, no email.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging output.",
    )
    return parser.parse_args()


def check_templates() -> int:
    """Print the best match of every template on screen. 0 if all pass."""
    backend = autologin.ensure_dependencies()
    names = list(dict.fromkeys(autologin.MORNING_SEQUENCE + autologin.LUNCH_SEQUENCE))
    left, top, width, height = autologin._virtual_screen()
    print(f"Escritorio virtual: {width}x{height} en ({left}, {top}); umbral {autologin.MATCH_CONFIDENCE:.2f}")
    all_ok = True
    for image_path in autologin.resolve_images(names):
        if not image_path.exists():
            print(f"  FALTA   {image_path.name}")
            all_ok = False
            continue
        best = autologin.best_match(backend, image_path)
        if best is None:
            print(f"  ERROR   {image_path.name}: no se pudo comparar")
            all_ok = False
            continue
        x, y, score, scale = best
        ok = score >= autologin.MATCH_CONFIDENCE
        all_ok = all_ok and ok
        print(f"  {'OK  ' if ok else 'BAJO'}    {image_path.name:22} score {score:.3f} @ {scale:.3f}x en ({x}, {y})")
    print("Nota: step1/step2 solo aparecen si el portal cerro sesion; step4/lunch/submit solo con el menu abierto.")
    return 0 if all_ok else 1


def main() -> int:
    args = parse_args()
    autologin.configure_logging(verbose=args.verbose)
    if args.check:
        return check_templates()
    images = autologin.resolve_images(autologin.IMAGE_SEQUENCE)

    hour, minute = args.time
    target_dt = autologin.next_run_datetime(hour, minute, autologin.TARGET_TZ)
    autologin.LOGGER.info(
        "Test automation scheduled for %s (skipping final submit click).",
        target_dt.strftime("%Y-%m-%d %H:%M %Z"),
    )

    keepalive_started = False
    run_result_code = 1
    try:
        with autologin.keep_screen_awake():
            try:
                autologin.ensure_images_exist(images)
                autologin.wait_until(target_dt)
                autologin.LOGGER.info("Starting UI automation test steps.")
                _all_steps_ok, missing_steps, clicked_steps, screen_locked = autologin.run_sequence(
                    images,
                    skip_last=True,
                    refresh_first=True,
                )
                autologin.LOGGER.info("Test automation completed without submission.")
                login_clicked = autologin.STEP_LOGIN_IMAGE in clicked_steps
                if login_clicked:
                    run_result_code = 0
                    details = "Test completado correctamente hasta step4_login.png (sin submit)."
                    if missing_steps:
                        details = f"{details} Pasos opcionales no encontrados: {', '.join(missing_steps)}"
                    autologin.send_email_confirmation(
                        success=True,
                        is_test=True,
                        details=details,
                    )
                else:
                    detail_parts = []
                    if screen_locked:
                        detail_parts.append("La pantalla estaba BLOQUEADA (pantalla de bloqueo de Windows); no se pudo continuar.")
                    detail_parts.append(f"No se pudo confirmar click en {autologin.STEP_LOGIN_IMAGE}.")
                    if missing_steps:
                        detail_parts.append(f"Pasos no encontrados en test: {', '.join(missing_steps)}")
                    autologin.send_email_confirmation(
                        success=False,
                        is_test=True,
                        details=" ".join(detail_parts),
                    )
            except KeyboardInterrupt:
                raise
            except SystemExit as exc:
                run_result_code = exc.code if isinstance(exc.code, int) else 1
                autologin.send_email_confirmation(
                    success=False,
                    is_test=True,
                    details=f"Test abortado con codigo: {exc.code}",
                )
            except Exception as exc:
                autologin.LOGGER.exception("Test automation failed with an unexpected error.")
                autologin.send_email_confirmation(
                    success=False,
                    is_test=True,
                    details=f"Error inesperado en test: {exc}",
                )
            keepalive_started = True
            autologin.wait_until_manual_stop()
        return run_result_code
    except KeyboardInterrupt:
        if keepalive_started:
            autologin.LOGGER.info("Test detenido manualmente por el usuario.")
            return run_result_code
        autologin.LOGGER.warning("Interrupted by user. Exiting early.")
        autologin.send_email_confirmation(
            success=False,
            is_test=True,
            details="Ejecucion de test interrumpida por el usuario.",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
