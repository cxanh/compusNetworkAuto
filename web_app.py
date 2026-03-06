#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Web UI for campus network config and login."""

import io
import json
import os
from contextlib import redirect_stdout
from threading import Lock
from typing import Any, Dict

from flask import Flask, redirect, render_template, request, url_for

import auto_login_csxy as login_core

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "campus_login_config.json")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

_LOGIN_LOCK = Lock()


def default_config() -> Dict[str, Any]:
    return {
        "username": "",
        "password": "",
        "url": login_core.DEFAULT_URL,
        "chromedriver_path": login_core.detect_chromedriver(),
        "isp_keyword": "中国联通",
        "headless": True,
        "save_screenshots": True,
    }


def load_config() -> Dict[str, Any]:
    cfg = default_config()
    if not os.path.isfile(CONFIG_FILE):
        return cfg

    with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if isinstance(data, dict):
        cfg.update(data)
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def parse_bool(name: str) -> bool:
    return request.form.get(name) == "on"


def form_to_config(existing: Dict[str, Any]) -> Dict[str, Any]:
    cfg = dict(existing)
    cfg["username"] = request.form.get("username", "").strip()
    cfg["password"] = request.form.get("password", "").strip()
    cfg["url"] = request.form.get("url", "").strip() or login_core.DEFAULT_URL
    cfg["chromedriver_path"] = request.form.get("chromedriver_path", "").strip()
    cfg["isp_keyword"] = request.form.get("isp_keyword", "").strip() or "中国联通"
    cfg["headless"] = parse_bool("headless")
    cfg["save_screenshots"] = parse_bool("save_screenshots")
    return cfg


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", cfg=load_config(), message="", level="")


@app.route("/save", methods=["POST"])
def save():
    cfg = form_to_config(load_config())
    save_config(cfg)
    return render_template("index.html", cfg=cfg, message="配置已保存。", level="success")


@app.route("/login", methods=["POST"])
def login_now():
    cfg = form_to_config(load_config())
    save_config(cfg)

    if not cfg.get("username") or not cfg.get("password"):
        return render_template(
            "index.html",
            cfg=cfg,
            message="账号和密码不能为空。",
            level="error",
            output="",
        )

    if not _LOGIN_LOCK.acquire(blocking=False):
        return render_template(
            "index.html",
            cfg=cfg,
            message="已有任务正在执行，请稍后再试。",
            level="warn",
            output="",
        )

    try:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = login_core.run_login(cfg)
        output = buffer.getvalue().strip()
    except Exception as exc:
        code = 1
        output = f"[ERR] Web 调用异常: {exc}"
    finally:
        _LOGIN_LOCK.release()

    if code == 0:
        msg = "执行完成：已在线或登录成功。"
        level = "success"
    elif code == 2:
        msg = "执行完成：未检测到注销页，可能登录失败。"
        level = "warn"
    elif code == 3:
        msg = "执行完成：页面状态异常，请查看 debug_unknown_state.html。"
        level = "warn"
    else:
        msg = "执行失败，请查看日志输出。"
        level = "error"

    return render_template("index.html", cfg=cfg, message=msg, level=level, output=output)


@app.route("/reset", methods=["POST"])
def reset_config():
    cfg = default_config()
    save_config(cfg)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
