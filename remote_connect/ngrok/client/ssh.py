import sys
import socket
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from pymongo import MongoClient
from dotenv import load_dotenv
from consts import ENV


load_dotenv()


MONGO_URI = ENV["MONGO_URI"]
MONGO_DB = ENV["MONGO_DB"]
MONGO_COLLECTION = ENV["MONGO_COLLECTION"]
SERVICE_ID = ENV["SERVICE_ID"]
MAX_STATUS_AGE_SECONDS = ENV["MAX_STATUS_AGE_SECONDS"]
DEFAULT_SSH_USER = ENV["DEFAULT_SSH_USER"]


def get_status():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is missing")

    mongo = MongoClient(MONGO_URI)
    collection = mongo[MONGO_DB][MONGO_COLLECTION]
    return collection.find_one({"_id": SERVICE_ID})


def seconds_since(dt):
    if not dt:
        return 999999

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return (datetime.now(timezone.utc) - dt).total_seconds()

def find_ssh_binary():
    """
    Find the actual SSH executable across platforms.
    Important: On Windows, avoid mistakenly finding ssh.py in the current directory.
    """

    system = platform.system().lower()

    if system == "windows":
        possible_paths = [
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            r"C:\Program Files\Git\usr\bin\ssh.exe",
            r"C:\Program Files\Git\bin\ssh.exe",
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        # As a fallback: Use `where ssh` to find `ssh.exe`.
        try:
            result = subprocess.run(
                ["where", "ssh"],
                capture_output=True,
                text=True,
                shell=True,
            )

            for line in result.stdout.splitlines():
                line = line.strip()
                if line.lower().endswith("ssh.exe") and Path(line).exists():
                    return line

        except Exception:
            pass

        raise RuntimeError(
            "Cannot find ssh.exe. Please install Windows OpenSSH Client or Git for Windows."
        )

    # macOS / Linux
    ssh_path = shutil.which("ssh")

    if ssh_path and not ssh_path.lower().endswith(".py"):
        return ssh_path

    raise RuntimeError("Cannot find ssh command. Please install OpenSSH Client.")



def open_real_ssh_terminal(host, port, username):
    """
    This directly invokes the system SSH connection, 
    allowing the user to access the real terminal.
    This enables the normal use of sudo, nano, vim, and top.
    """
    ssh_bin = find_ssh_binary()

    cmd = [
        ssh_bin,
        "-tt",
        f"{username}@{host}",
        "-p",
        str(port),
    ]

    print("[ssh.py] opening real SSH terminal")
    print("[ssh.py] command:", " ".join(cmd))
    print("-" * 50)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"[ssh.py] ssh exited with code: {result.returncode}")
        sys.exit(result.returncode)


def main():
    try:
        doc = get_status()

        if not doc:
            print("[ssh.py] Error: no ngrok status found in MongoDB")
            sys.exit(1)

        status = doc.get("status")
        host = doc.get("host")
        port = doc.get("port")
        public_url = doc.get("public_url")
        error = doc.get("error")
        last_check = doc.get("last_check")

        if status != "online":
            print("[ssh.py] Error: ngrok is not online")
            print(f"status: {status}")
            print(f"error: {error}")
            sys.exit(1)

        if not host or not port:
            print("[ssh.py] Error: MongoDB record has no host or port")
            sys.exit(1)

        age = seconds_since(last_check)
        if age > MAX_STATUS_AGE_SECONDS:
            print("[ssh.py] Error: ngrok status is stale")
            print(f"last_check: {last_check}")
            print(f"age_seconds: {int(age)}")
            sys.exit(1)

        print(f"[ssh.py] ngrok: {public_url}")

        username = DEFAULT_SSH_USER.strip()
        if not username:
            username = input("SSH username: ").strip()

        if not username:
            print("[ssh.py] Error: username cannot be empty")
            sys.exit(1)

        open_real_ssh_terminal(host, port, username)

    except KeyboardInterrupt:
        print("\n[ssh.py] cancelled by user")
        sys.exit(130)

    except socket.timeout:
        print("[ssh.py] Error: connection timeout")
        sys.exit(1)

    except Exception as e:
        print(f"[ssh.py] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
