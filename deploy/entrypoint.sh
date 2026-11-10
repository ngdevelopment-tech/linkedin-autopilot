#!/usr/bin/env bash
set -Eeuo pipefail
Xvfb :99 -screen 0 1440x900x24 -nolisten tcp &
sleep 1
fluxbox >/dev/null 2>&1 &
exec python bot.py
