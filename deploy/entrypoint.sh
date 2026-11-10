#!/usr/bin/env bash
set -Eeuo pipefail

export DISPLAY=:99
mkdir -p /data/browser /data/state
chown -R pwuser:pwuser /data
# A Railway restart changes the host identity; Chromium's old singleton symlinks become stale.
# Remove only process-lock links after confirming this container has no running Chromium.
if ! pgrep -f '/ms-playwright/.*/chrome-linux64/chrome' >/dev/null; then
  rm -f /data/browser/SingletonLock /data/browser/SingletonSocket /data/browser/SingletonCookie
  echo '[startup] cleared stale Chromium singleton links (profile contents preserved)' >&2
fi
if [[ "${BROWSER_HEADLESS:-false}" == "true" ]]; then
  echo "[startup] headless mode: no Xvfb, desktop manager or VNC processes" >&2
  # A tiny authenticated-free readiness endpoint; never expose browser profile or secrets.
  cat >/tmp/health-nginx.conf <<'EOF'
user www-data;
worker_processes 1;
pid /tmp/health-nginx.pid;
error_log /dev/stderr warn;
events { worker_connections 128; }
http {
  access_log off;
  server {
    listen 8080;
    server_name _;
    location = /healthz { default_type text/plain; return 200 "worker process booted\n"; }
    location / { return 404; }
  }
}
EOF
  nginx -c /tmp/health-nginx.conf -g 'daemon off;' &
else
# Create a private X11 socket directory and start a fresh display.
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix
if [[ -e /tmp/.X99-lock ]] && ! pgrep -x Xvfb >/dev/null; then rm -f /tmp/.X99-lock; fi
if ! pgrep -x Xvfb >/dev/null; then
  runuser -u pwuser -- Xvfb :99 -screen 0 1024x720x16 -nolisten tcp &
fi
for attempt in $(seq 1 30); do
  if runuser -u pwuser -- xdpyinfo -display :99 >/dev/null 2>&1; then break; fi
  sleep 1
done
if ! runuser -u pwuser -- xdpyinfo -display :99 >/dev/null 2>&1; then
  echo "[startup] Xvfb did not become ready" >&2
  exit 1
fi
echo "[startup] X display :99 ready" >&2
runuser -u pwuser -- fluxbox >/dev/null 2>&1 &

if [[ -n "${BROWSER_ACCESS_PASSWORD:-}" ]]; then
  x11vnc -noshm -display :99 -rfbport 5901 -localhost -nopw -forever -shared -o /tmp/x11vnc.log &
  websockify --web=/usr/share/novnc/ 127.0.0.1:6080 localhost:5901 > /tmp/websockify.log 2>&1 &
  AUTH_HASH="$(openssl passwd -apr1 "${BROWSER_ACCESS_PASSWORD}")"
  printf '%s:%s\n' "${BROWSER_ACCESS_USER:-naim}" "$AUTH_HASH" >/tmp/browser.htpasswd
  chown root:www-data /tmp/browser.htpasswd
  chmod 640 /tmp/browser.htpasswd
  WS_TOKEN="$(printf 'remote-browser-session:v1:%s' "$BROWSER_ACCESS_PASSWORD" | openssl dgst -sha256 -r | cut -d' ' -f1)"

  cat >/tmp/browser-nginx.conf <<EOF
user www-data;
worker_processes 1;
pid /tmp/browser-nginx.pid;
error_log /dev/stderr warn;
events { worker_connections 256; }
http {
  access_log /dev/stdout combined;
  client_body_temp_path /tmp/nginx-client;
  proxy_temp_path /tmp/nginx-proxy;
  fastcgi_temp_path /tmp/nginx-fastcgi;
  uwsgi_temp_path /tmp/nginx-uwsgi;
  scgi_temp_path /tmp/nginx-scgi;
  server {
    listen 8080;
    server_name _;
    add_header Cache-Control "no-store" always;
    location = /websockify {
      auth_basic off;
      if (\$cookie_browser_session != "$WS_TOKEN") { return 403; }
      proxy_pass http://127.0.0.1:6080/;
      proxy_http_version 1.1;
      proxy_set_header Upgrade \$http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_read_timeout 86400;
      proxy_buffering off;
    }
    location / {
      add_header Cache-Control "no-store" always;
      auth_basic "Browser access";
      auth_basic_user_file /tmp/browser.htpasswd;
      add_header Set-Cookie "browser_session=$WS_TOKEN; Secure; HttpOnly; SameSite=Lax; Path=/" always;
      proxy_pass http://127.0.0.1:6080;
      proxy_http_version 1.1;
      proxy_set_header Upgrade \$http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_read_timeout 86400;
      proxy_buffering off;
    }
  }
}
EOF
  nginx -c /tmp/browser-nginx.conf -g 'daemon off;' &
  (sleep 3; echo "[browser] VNC diagnostics:" >&2; tail -n 22 /tmp/x11vnc.log /tmp/websockify.log >&2 || true; echo "[browser] local service probes:" >&2; /opt/venv/bin/python -c 'import socket; [(print(f"{h}:{p} "+str(socket.socket().connect_ex((h,p))),flush=True)) for h,p in [("127.0.0.1",5901),("127.0.0.1",6080)]]' >&2) &
  echo "[browser] authenticated remote display enabled" >&2
else
  echo "[browser] remote display disabled: configure BROWSER_ACCESS_PASSWORD" >&2
fi

fi

exec runuser -u pwuser -- /opt/venv/bin/python bot.py
