#!/usr/bin/env bash
set -Eeuo pipefail
Xvfb :99 -screen 0 1440x900x24 -nolisten tcp &
sleep 1
fluxbox >/dev/null 2>&1 &
x11vnc -display :99 -rfbport 5900 -localhost -nopw -forever -shared -quiet >/dev/null 2>&1 &
websockify --web=/usr/share/novnc/ 0.0.0.0:6080 localhost:5900 >/dev/null 2>&1 &
exec python bot.py
