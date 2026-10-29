# autologin_windows

Versión para Windows de `../autologin` (monitor 2K, 2560x1440). Mismo horario
(Lima), mismas plantillas PNG, mismos emails; solo cambia la capa del sistema:

| macOS (`autologin/`)                 | Windows (`autologin_windows/`)                     |
| ------------------------------------ | -------------------------------------------------- |
| `caffeinate -d -i -s`                | `SetThreadExecutionState` (pantalla + sistema)     |
| Captura/clic con Quartz              | `PIL.ImageGrab` (todos los monitores) + `SendInput` |
| `CGSessionCopyCurrentDictionary`     | `OpenInputDesktop` (escritorio "Winlogon" = bloqueado) |
| `ioreg HIDIdleTime`                  | `GetLastInputInfo`                                 |
| Cmd+R                                | Ctrl+R                                             |

## Instalación (una vez)

```bat
cd autologin_windows
py -m pip install -r requirements.txt
```

No necesita `pyautogui` ni `pyobjc`.

## Verificar las plantillas en la pantalla 2K

Los PNG se capturaron en la Mac (Retina 2x). El buscador prueba varias escalas
(0.5x–2x) para cubrir el escalado de Windows al 100 %, 125 % y 150 %. Antes de
confiar en una corrida real, abre el portal BMS con el menú desplegado y corre:

```bat
py autologintest.py --check
```

Muestra el score y la escala de cada plantilla sin hacer clic. Si alguna sale
`BAJO` estando visible (el texto de Windows se dibuja distinto al de macOS),
recórtala de nuevo en Windows con `Win+Shift+S`, guárdala con el **mismo
nombre** en esta carpeta y vuelve a correr `--check`.

## Uso

```bat
py autologin.py                  :: espera a 07:25 / 12:30 / 13:12 (Lima) y marca
py autologintest.py --time 14:30 :: prueba solo la secuencia de la mañana, sin Submit
```

Igual que en Mac: después de los tres eventos el script queda activo (para
mantener la PC despierta) hasta `Ctrl+C`.

## Notas

- Deja la PC **desbloqueada** al lanzar el script; el jiggler evita que se
  bloquee, pero no puede desbloquear una sesión que bloqueaste tú (`Win+L`).
- Si la PC es de dominio y una política de TI fuerza el bloqueo, el jiggler
  (input real vía `SendInput` cada 10 s) normalmente lo evita; si aun así se
  bloquea, el email dirá "pantalla de bloqueo de Windows".
- No corras la versión de Mac y la de Windows el mismo día: marcarían dos veces.
  Los emails de esta versión llevan `[Windows]` en el asunto.
- El navegador con el portal puede estar en cualquier monitor.
