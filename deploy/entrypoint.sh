#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p /data/browser /data/state
chown -R pwuser:pwuser /data
runuser -u pwuser -- Xvfb :99 -screen 0 1440x900x24 -nolisten tcp &
sleep 1
runuser -u pwuser -- fluxbox >/dev/null 2>&1 &

if [[ -n "${BROWSER_ACCESS_PASSWORD:-}" ]]; then
  x11vnc -display :99 -rfbport 5900 -localhost -nopw -forever -shared -o /tmp/x11vnc.log &
  websockify --web=/usr/share/novnc/ 127.0.0.1:6080 localhost:5900 > /tmp/websockify.log 2>&1 &
  AUTH_HASH="$(openssl passwd -apr1 "${BROWSER_ACCESS_PASSWORD}")"
  printf '%s:%s\n' "${BROWSER_ACCESS_USER:-naim}" "$AUTH_HASH" >/tmp/browser.htpasswd
  chown root:www-data /tmp/browser.htpasswd
  chmod 640 /tmp/browser.htpasswd

  cat >/tmp/browser-nginx.conf <<EOF
user www-data;
worker_processes 1;
pid /tmp/browser-nginx.pid;
error_log /dev/stderr warn;
events { worker_connections 256; }
http {
  access_log off;
  client_body_temp_path /tmp/nginx-client;
  proxy_temp_path /tmp/nginx-proxy;
  fastcgi_temp_path /tmp/nginx-fastcgi;
  uwsgi_temp_path /tmp/nginx-uwsgi;
  scgi_temp_path /tmp/nginx-scgi;
  server {
    listen ${PORT:-8080};
    server_name _;
    add_header Cache-Control "no-store" always;
    location / {
      auth_basic "Browser access";
      auth_basic_user_file /tmp/browser.htpasswd;
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
  (sleep 3; echo "[browser] VNC diagnostics:" >&2; tail -n 22 /tmp/x11vnc.log /tmp/websockify.log >&2 || true; echo "[browser] local service probes:" >&2; /opt/venv/bin/python -c 'import socket; [(print(f"{h}:{p} "+str(socket.socket().connect_ex((h,p))),flush=True)) for h,p in [("127.0.0.1",5900),("127.0.0.1",6080)]]' >&2) &
  echo "[browser] authenticated remote display enabled" >&2
else
  echo "[browser] remote display disabled: configure BROWSER_ACCESS_PASSWORD" >&2
fi

exec runuser -u pwuser -- /opt/venv/bin/python bot.py
