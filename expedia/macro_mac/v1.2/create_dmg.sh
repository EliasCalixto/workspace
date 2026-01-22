#!/bin/bash

APP_NAME="CoreOTA_Macro"
VERSION="v1.2"
DMG_NAME="${APP_NAME}_${VERSION}.dmg"
VOL_NAME="${APP_NAME} Installer"

# Eliminar versiones anteriores
rm -f "$DMG_NAME"
rm -rf ./dmg_temp

# Crear carpeta temporal
mkdir dmg_temp
cp -R "dist/${APP_NAME}.app" dmg_temp/

# Crear el .dmg
hdiutil create "$DMG_NAME" \
  -volname "$VOL_NAME" \
  -srcfolder "dmg_temp" \
  -ov -format UDZO

# Limpiar
rm -rf dmg_temp
