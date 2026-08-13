import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates")

LOG_PATH = Path(os.environ.get("BOT_LOG_PATH", "logs.txt"))
LINKS_PATH = Path(os.environ.get("BOT_LINKS_PATH", "generated_links.json"))


def read_logs(limit: int = 80):
    try:
        if not LOG_PATH.exists():
            return ["Log file not found yet."]
        with LOG_PATH.open("r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()[-limit:]
        return [line.rstrip() for line in lines if line.strip()]
    except Exception as exc:  # pragma: no cover - defensive
        return [f"Unable to read logs: {exc}"]


def ensure_links_file():
    LINKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LINKS_PATH.exists():
        LINKS_PATH.write_text("[]", encoding="utf-8")


def load_links():
    ensure_links_file()
    try:
        with LINKS_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_links(records):
    ensure_links_file()
    with LINKS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)


def add_generated_link(title, link, description="", source="telegram"):
    records = load_links()
    new_id = (records[0]["id"] if records else 0) + 1
    record = {
        "id": new_id,
        "title": title or "Generated link",
        "link": link,
        "description": description,
        "source": source,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    records.insert(0, record)
    save_links(records)
    return record


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


@app.get("/api/links")
def api_links():
    return jsonify(load_links())


@app.post("/api/links")
def add_link():
    payload = request.get_json(silent=True) or {}
    link = (payload.get("link") or "").strip()
    if not link:
        return jsonify({"error": "link is required"}), 400

    records = load_links()
    title = (payload.get("title") or "Generated link").strip() or "Generated link"
    description = (payload.get("description") or "").strip()
    record = add_generated_link(
        title=title,
        link=link,
        description=description,
        source="web",
    )
    return jsonify(record), 201


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
        generated_links=load_links(),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=False)
