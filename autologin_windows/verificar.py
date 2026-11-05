#!/usr/bin/env python3
"""Verifica que autologin.py va a funcionar en esta PC, sin esperar al horario.
 
Va en la misma carpeta que autologin.py. Uso (PowerShell):
 
  py verificar.py                  -> imagenes, horario, dependencias y que se ve en pantalla
  py verificar.py --email          -> ademas envia un correo de prueba
  py verificar.py --dry-run logout -> corre el flujo de verdad pero SIN hacer clic en Submit
                                      (opciones: morning, lunch, postlunch, logout)
 
No marca nada en BMS: el --dry-run se detiene antes del boton Submit.
"""
import argparse
import sys
import time
 
import autologin as a
 
OK = "[ OK ]"
FAIL = "[FALLA]"
WARN = "[AVISO]"
 
 
def check_files(jobs) -> bool:
    print("\n1) Imagenes de referencia")
    names = sorted({name for job in jobs for name in job.image_names})
    all_ok = True
    for name in names:
        exists = (a.BASE_DIR / name).exists()
        all_ok &= exists
        print(f"   {OK if exists else FAIL} {name}")
    return all_ok
 
 
def check_dependencies() -> bool:
    print("\n2) Dependencias (opencv, numpy, pillow)")
    try:
        import cv2, numpy  # noqa: F401
        from PIL import ImageGrab  # noqa: F401
        print(f"   {OK} instaladas")
        return True
    except ImportError as exc:
        print(f"   {FAIL} falta {exc.name}. Instala con: py -m pip install opencv-python numpy pillow")
        return False
 
 
def check_schedule(jobs) -> None:
    print("\n3) Proximas ejecuciones (hora Lima)")
    upcoming = []
    for job in jobs:
        run_at = a.next_run_datetime(job, a.TARGET_TZ)
        if run_at is not None:
            upcoming.append((run_at, job))
    for run_at, job in sorted(upcoming, key=lambda p: p[0]):
        print(f"   {run_at:%a %Y-%m-%d %H:%M}  {job.label}")
 
 
def check_screen(jobs) -> None:
    print("\n4) Que botones se ven AHORA en pantalla")
    print("   (Ten BMS abierto en el navegador. Log In / Lunch / Log Out solo se ven")
    print("    con el menu del nombre abierto; step1/step2 solo si la sesion se cerro.)")
    backend = a.ensure_dependencies()
    names = sorted({name for job in jobs for name in job.image_names})
    for name in names:
        path = a.BASE_DIR / name
        if not path.exists():
            continue
        best = a.best_match(backend, path)
        if best is None:
            print(f"   {FAIL} {name}: no se pudo comparar")
            continue
        _x, _y, score, scale = best
        found = score >= a.MATCH_CONFIDENCE
        print(f"   {OK if found else '[ -- ]'} {name}: score {score:.3f} "
              f"(minimo {a.MATCH_CONFIDENCE:.2f}, escala {scale}x)"
              + ("" if found else "  -> no visible ahora"))
 
 
def dry_run(job_key: str, jobs) -> None:
    job = next((j for j in jobs if j.key == job_key), None)
    if job is None:
        print(f"{FAIL} job desconocido: {job_key}")
        return
    print(f"\nDry-run de '{job.label}': recarga la pagina y hace los clics, SIN Submit.")
    print("Pon el navegador con BMS al frente. Empieza en 5 segundos (Ctrl+C para cancelar)...")
    time.sleep(5)
    images = a.resolve_images(job.image_names)
    _ok, missing, clicked, locked = a.run_sequence(images, skip_last=True, refresh_first=True)
    print("\nResultado:")
    if locked:
        print(f"   {FAIL} la pantalla estaba bloqueada")
    for name in clicked:
        print(f"   {OK} clic en {name}")
    for name in missing:
        print(f"   {WARN} no encontrado: {name}")
    target = job.image_names[-2]  # el boton del evento (Log In / Lunch / Log Out)
    if target in clicked:
        print(f"\n   {OK} El flujo llego hasta {target}. Solo faltaria Submit (omitido a proposito).")
        print("   Cierra/cancela el dialogo de confirmacion a mano.")
    else:
        print(f"\n   {FAIL} No llego a {target}: revisa la imagen o recapturala en Windows.")
    print("   (step1/step2 'no encontrado' es normal si la sesion de BMS seguia abierta)")
 
 
def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica autologin.py en esta PC.")
    parser.add_argument("--email", action="store_true", help="Envia un correo de prueba.")
    parser.add_argument("--dry-run", choices=["morning", "lunch", "postlunch", "logout"],
                        help="Corre ese flujo ahora, sin hacer clic en Submit.")
    args = parser.parse_args()
    a.configure_logging()
    jobs = a.build_jobs()
 
    if args.dry_run:
        dry_run(args.dry_run, jobs)
        return 0
 
    files_ok = check_files(jobs)
    deps_ok = check_dependencies()
    check_schedule(jobs)
    if deps_ok and a.IS_WINDOWS:
        check_screen(jobs)
    if args.email:
        print("\n5) Correo de prueba")
        sent = a.send_email_confirmation(success=True, label="Verificacion", details="Prueba desde verificar.py")
        print(f"   {OK if sent else FAIL} correo {'enviado' if sent else 'NO enviado (mira el error arriba)'}")
    print("\nListo." if files_ok and deps_ok else "\nHay cosas en FALLA arriba; corrigelas antes de dejarlo corriendo.")
    return 0 if files_ok and deps_ok else 1
 
 
if __name__ == "__main__":
    sys.exit(main())