#!/usr/bin/env python3
"""啟動計時器：自動開啟本地伺服器並在瀏覽器顯示 timer.html"""

import http.server
import socketserver
import threading
import webbrowser
import time
import os
import sys

PORT = 8080
HOST = "localhost"
FILE = "timer.html"


def find_free_port(start=8080):
    import socket
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, port)) != 0:
                return port
    return start


def main():
    # 切換到 timer.html 所在目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if not os.path.exists(FILE):
        print(f"找不到 {FILE}，請確認檔案存在於 {script_dir}")
        sys.exit(1)

    port = find_free_port(PORT)
    url = f"http://{HOST}:{port}/{FILE}"

    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # 關閉 request log

    with socketserver.TCPServer((HOST, port), handler) as httpd:
        print(f"計時器已啟動：{url}")
        print("按 Ctrl+C 停止伺服器\n")

        # 稍等一下再開啟瀏覽器，確保伺服器已就緒
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n伺服器已停止。")


if __name__ == "__main__":
    main()
