#!/usr/bin/env python3
"""Test run variant of autologin without the final submit click."""
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
        "--verbose",
        action="store_true",
        help="Enable debug logging output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    autologin.configure_logging(verbose=args.verbose)
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
                _all_steps_ok, missing_steps, clicked_steps = autologin.run_sequence(
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
                    detail_parts = [f"No se pudo confirmar click en {autologin.STEP_LOGIN_IMAGE}."]
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
