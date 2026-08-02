"""Tiny Flask web server so UptimeRobot / Render can keep the bot alive."""

import os
from threading import Thread
from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Rules bot is alive."


@app.route("/health")
def health():
    return {"status": "ok"}


def _run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    Thread(target=_run, daemon=True).start()
