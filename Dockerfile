FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
ENV PYTHONUNBUFFERED=1 DISPLAY=:99 BROWSER_PROFILE_DIR=/data/browser STATE_DB_PATH=/data/state/messages.db UNATTENDED=true
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-venv xvfb fluxbox nginx x11vnc novnc websockify openssl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN python -m venv /opt/venv && /opt/venv/bin/python -m pip install --no-cache-dir -r requirements.txt
COPY bot.py replies.py storage.py ./
COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && mkdir -p /data && chown -R pwuser:pwuser /data /app
USER pwuser
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
