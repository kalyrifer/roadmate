import subprocess
import time
import threading
import sys

def run_ssh_tunnel():
    """Запуск SSH туннеля через localhost.run"""
    process = subprocess.Popen(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-R', '80:localhost:8000', 'localhost.run'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in process.stdout:
        print(line, end='')
        sys.stdout.flush()

if __name__ == "__main__":
    print("Запускаю туннель через localhost.run...")
    thread = threading.Thread(target=run_ssh_tunnel)
    thread.daemon = True
    thread.start()
    
    print("Туннель запущен. Нажми Ctrl+C для выхода.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка туннеля...")