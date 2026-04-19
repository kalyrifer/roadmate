#!/usr/bin/env python3
"""
Скрипт для запуска ngrok туннеля и получения публичного URL.
"""
import subprocess
import time
import sys
import os
import signal

# Добавляем путь к ngrok
NGROK_PATH = r"D:\ngrok\ngrok-v3-stable-windows-amd64\ngrok.exe"

def get_ngrok_url():
    """Получение URL через API ngrok."""
    import urllib.request
    import json
    
    try:
        req = urllib.request.Request("http://localhost:4040/api/tunnels")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    return tunnel.get('public_url')
    except Exception as e:
        print(f"Ошибка получения URL: {e}", file=sys.stderr)
    return None

def main():
    print("Запускаю ngrok...")
    
    # Запускаем ngrok
    proc = subprocess.Popen(
        [NGROK_PATH, "http", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    print("Ожидание запуска ngrok (5 секунд)...")
    time.sleep(5)
    
    # Пробуем получить URL
    url = get_ngrok_url()
    if url:
        print(f"\n{'='*50}")
        print(f"✅ ТУННЕЛЬ СОЗДАН!")
        print(f"{'='*50}")
        print(f"🌐 URL: {url}")
        print(f"📚 Docs: {url}/docs")
        print(f"❤️  Health: {url}/health")
        print(f"{'='*50}")
        print("\nОтправьте этот URL другу!")
    else:
        print("URL не получен. Проверьте вывод ниже:")
        print("-" * 30)
        # Читаем оставшийся вывод
        import select
        while True:
            ready, _, _ = select.select([proc.stdout], [], [], 1)
            if ready:
                line = proc.stdout.readline()
                if line:
                    print(line, end='')
                else:
                    break
            else:
                break
    
    print("\nНажмите Ctrl+C для остановки...")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()