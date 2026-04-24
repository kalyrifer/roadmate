import subprocess
import time
import sys
import requests

print("Starting server and tunnel...")

print("[1/3] Starting backend server...")
server = subprocess.Popen(
    [sys.executable, "run_server.py"],
    cwd="D:\\RoadMate",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(4)

print("[2/3] Checking server...")
try:
    r = requests.get("http://localhost:8000/docs", timeout=5)
    print(f"      Server OK: {r.status_code}")
except Exception as e:
    print(f"      Server error: {e}")
    sys.exit(1)

print("[3/3] Starting cloudflared tunnel...")
print("      (Keep this window open)")
print()

tunnel = subprocess.Popen(
    ["D:\\RoadMate\\cloudflared.exe", "tunnel", "--url", "localhost:8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

url = None
for line in tunnel.stdout:
    print(f"      {line.strip()}")
    if "https://" in line and "trycloudflare.com" in line:
        url = line.strip().split("https://")[-1].strip()
        if not url.startswith("https://"):
            url = "https://" + url
        break

if url:
    print()
    print("=" * 50)
    print(f"ТУННЕЛЬ РАБОТАЕТ!")
    print(f"URL: {url}")
    print("=" * 50)
    print()
    print("Отправьте этот URL другу!")
    print("Для остановки нажмите Ctrl+C")
else:
    print("Не удалось получить URL туннеля")

input()