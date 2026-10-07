"""
MediSafe - Native Desktop Application Wrapper
Spawns a native Windows desktop GUI application window powered by pywebview (Edge WebView2).
Runs the Streamlit application engine in the background and cleans up on window exit.
"""

import sys
import time
import socket
import subprocess
import urllib.request
from pathlib import Path
import webview
from config import APP_NAME, APP_SUBTITLE


def find_free_port() -> int:
    """Finds an available local port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server(url: str, timeout: int = 25) -> bool:
    """Polls the local server until it responds with HTTP 200."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MediSafeDesktop/1.0"})
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status in (200, 304):
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    base_dir = Path(__file__).resolve().parent
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    # Command to run Streamlit in headless background mode
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(base_dir / "main.py"),
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.address=127.0.0.1",
    ]

    print(f"[*] Initializing MediSafe background engine on http://127.0.0.1:{port}...")
    server_process = subprocess.Popen(
        cmd,
        cwd=str(base_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        # Wait for the local server to be ready
        ready = wait_for_server(url)
        if not ready:
            print("[!] Server startup timed out.")
            server_process.terminate()
            sys.exit(1)

        print("[+] Engine ready. Launching desktop application window...")
        title = f"{APP_NAME} - {APP_SUBTITLE}"

        # Create native desktop window
        webview.create_window(
            title=title,
            url=url,
            width=1340,
            height=880,
            min_size=(980, 650),
            confirm_close=False,
        )

        # Blocks until window is closed
        webview.start()

    finally:
        print("[*] Closing background engine...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except Exception:
            server_process.kill()
        print("[+] Application closed cleanly.")


if __name__ == "__main__":
    main()
