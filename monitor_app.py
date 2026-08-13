import os
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template

app = Flask(__name__, template_folder="templates")

LOG_PATH = Path(os.environ.get("BOT_LOG_PATH", "logs.txt"))


def read_logs(limit: int = 80):
    try:
        if not LOG_PATH.exists():
            return ["Log file not found yet."]
        with LOG_PATH.open("r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()[-limit:]
        return [line.rstrip() for line in lines if line.strip()]
    except Exception as exc:  # pragma: no cover - defensive
        return [f"Unable to read logs: {exc}"]


def determine_bot_name(log_lines):
    for line in reversed(log_lines):
        if "Username:" in line:
            match = re.search(r"Username:\s*@?(\S+)", line)
            if match:
                return match.group(1)
    return "Unknown"


def status_payload():
    log_lines = read_logs(100)
    active = any("BERHASIL DIAKTIFKAN" in line for line in log_lines)
    last_update = LOG_PATH.stat().st_mtime if LOG_PATH.exists() else 0
    last_seen = datetime.fromtimestamp(last_update).strftime("%Y-%m-%d %H:%M:%S") if last_update else "never"

    return {
        "status": "online" if active else "offline",
        "bot": determine_bot_name(log_lines),
        "last_seen": last_seen,
        "log_path": str(LOG_PATH),
        "recent_logs": log_lines[-20:],
    }


@app.get("/health")
def health():
    return jsonify(status_payload())


@app.get("/api/status")
def api_status():
    return jsonify(status_payload())


@app.get("/")
def index():
    payload = status_payload()
    return render_template(
        "monitor.html",
        title="Bot Monitor",
        status=payload["status"],
        bot=payload["bot"],
        last_seen=payload["last_seen"],
        logs=payload["recent_logs"],
        log_path=payload["log_path"],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=False)
