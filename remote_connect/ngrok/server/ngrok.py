import os
import time
import socket
import signal
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from consts import ENV
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()

MONGO_URI = ENV["MONGO_URI"]
MONGO_DB = ENV["MONGO_DB"]
MONGO_COLLECTION = ENV["MONGO_COLLECTION"]

NGROK_BIN = ENV["NGROK_BIN"]
LOCAL_SSH_PORT = int(ENV["LOCAL_SSH_PORT"])
CHECK_INTERVAL = int(ENV["CHECK_INTERVAL"])
SERVICE_ID = ENV["SERVICE_ID"]

NGROK_API = "http://127.0.0.1:4040/api/tunnels"


mongo = MongoClient(MONGO_URI)
collection = mongo[MONGO_DB][MONGO_COLLECTION]


ngrok_process = None


def utc_now():
    return datetime.now(timezone.utc)


def upsert_status(status, host=None, port=None, public_url=None, error=None):
    doc = {
        "service": "ssh",
        "status": status,
        "host": host,
        "port": port,
        "public_url": public_url,
        "last_check": utc_now(),
        "error": error,
    }

    collection.update_one(
        {"_id": SERVICE_ID},
        {"$set": doc},
        upsert=True,
    )


def start_ngrok():
    global ngrok_process

    print("[ngrok.py] starting ngrok...")

    upsert_status("restarting", error="starting ngrok")

    ngrok_process = subprocess.Popen(
        [NGROK_BIN, "tcp", str(LOCAL_SSH_PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )

    time.sleep(4)


def stop_ngrok():
    global ngrok_process

    print("[ngrok.py] stopping ngrok...")

    if ngrok_process and ngrok_process.poll() is None:
        try:
            os.killpg(os.getpgid(ngrok_process.pid), signal.SIGTERM)
            time.sleep(2)
        except Exception as e:
            print(f"[ngrok.py] failed to stop ngrok gracefully: {e}")

    # 兜底：杀掉残留 ngrok
    subprocess.run(["pkill", "-f", "ngrok tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ngrok_process = None


def restart_ngrok():
    stop_ngrok()
    time.sleep(2)
    start_ngrok()


def get_ngrok_tcp_url():
    try:
        response = requests.get(NGROK_API, timeout=3)
        response.raise_for_status()
        data = response.json()

        tunnels = data.get("tunnels", [])

        for tunnel in tunnels:
            public_url = tunnel.get("public_url", "")
            proto = tunnel.get("proto", "")

            if public_url.startswith("tcp://") or proto == "tcp":
                parsed = urlparse(public_url)
                host = parsed.hostname
                port = parsed.port

                if host and port:
                    return public_url, host, port

        raise RuntimeError("No TCP tunnel found in ngrok API")

    except Exception as e:
        raise RuntimeError(f"Failed to read ngrok API: {e}")


def tcp_check(host, port, timeout=5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, None
    except Exception as e:
        return False, str(e)


def main():
    print("[ngrok.py] service started")

    start_ngrok()

    while True:
        try:
            public_url, host, port = get_ngrok_tcp_url()
            ok, error = tcp_check(host, port)

            if ok:
                print(f"[ngrok.py] online: {public_url}")
                upsert_status(
                    status="online",
                    host=host,
                    port=port,
                    public_url=public_url,
                    error=None,
                )
            else:
                print(f"[ngrok.py] tcp check failed: {error}")
                upsert_status(
                    status="offline",
                    host=host,
                    port=port,
                    public_url=public_url,
                    error=error,
                )
                restart_ngrok()

        except Exception as e:
            print(f"[ngrok.py] error: {e}")
            upsert_status("error", error=str(e))
            restart_ngrok()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
