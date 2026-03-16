import os
import sys
import time
import socket
import threading
import traceback
import webbrowser
from pathlib import Path

from streamlit.web import cli as stcli

PORT = 8501
URL = f"http://localhost:{PORT}"


def get_base_candidates():
    candidates = []

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir)

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass))

        candidates.append(exe_dir / "_internal")
    else:
        candidates.append(Path(__file__).resolve().parent)

    seen = set()
    unique = []
    for c in candidates:
        s = str(c)
        if s not in seen:
            seen.add(s)
            unique.append(c)
    return unique


def get_log_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "launcher_debug.log"
    return Path(__file__).resolve().parent / "launcher_debug.log"


def log(msg):
    with get_log_path().open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def find_app_path():
    for base in get_base_candidates():
        app_path = base / "app" / "app.py"
        log(f"[CHECK] trying app path: {app_path}")
        if app_path.exists():
            log(f"[FOUND] app path: {app_path}")
            return app_path
    raise FileNotFoundError("app/app.py 를 찾지 못했습니다.")


def wait_for_server_and_open_browser():
    for _ in range(60):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=1):
                log(f"[OK] server detected on {URL}")
                webbrowser.open(URL)
                return
        except Exception:
            time.sleep(1)
    log("[WARN] 60초 내에 서버 포트가 열리지 않았습니다.")


if __name__ == "__main__":
    try:
        log("=== launcher start ===")
        log(f"frozen={getattr(sys, 'frozen', False)}")
        log(f"sys.executable={sys.executable}")
        log(f"sys._MEIPASS={getattr(sys, '_MEIPASS', None)}")

        app_path = find_app_path()

        # 핵심: app.py의 상위 루트(app와 engine이 같이 있는 위치)를 sys.path에 추가
        root_dir = app_path.parent.parent
        sys.path.insert(0, str(root_dir))
        sys.path.insert(0, str(app_path.parent))
        os.chdir(root_dir)

        log(f"[ROOT] root_dir={root_dir}")
        log(f"[PATH] sys.path[:5]={sys.path[:5]}")

        threading.Thread(target=wait_for_server_and_open_browser, daemon=True).start()

        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--global.developmentMode=false",
            "--server.headless=true",
            "--server.address=127.0.0.1",
            "--server.port=8501",
            "--browser.serverAddress=localhost",
            "--browser.gatherUsageStats=false",
        ]

        raise SystemExit(stcli.main())

    except Exception:
        log("[ERROR]")
        log(traceback.format_exc())
        raise