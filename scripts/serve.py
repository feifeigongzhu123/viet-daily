"""Local preview server for the VietDaily PWA.

Run from the project root:
    python scripts/serve.py

Open http://127.0.0.1:8765/ on the same computer. The LAN URL is also printed,
so an Android phone on the same Wi-Fi can open the app for a quick look. Note
that service-worker installation normally requires HTTPS (or localhost), so
use a real static host for "Add to Home screen" on the phone.
"""
from __future__ import annotations

import os
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".webmanifest": "application/manifest+json",
        ".mp3": "audio/mpeg",
        ".png": "image/png",
        ".svg": "image/svg+xml",
    }

    def end_headers(self) -> None:
        # Avoid stale assets while editing locally.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()} - {fmt % args}")


def local_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return None


def main() -> None:
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("越词 · VietDaily 本地预览")
    print(f"  电脑:  http://127.0.0.1:{PORT}/")
    ip = local_ip()
    if ip:
        print(f"  手机:  http://{ip}:{PORT}/  （同一 Wi-Fi；安装功能请用 HTTPS 部署）")
    print("按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
