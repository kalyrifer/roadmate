"""
Запуск ngrok туннеля через Python.
Использует уже установленный ngrok.
"""
import subprocess
import time
import requests
import sys

def start_ngrok():
    # Запускаем ngrok в фоне
    print("Запускаю ngrok...")
    process = subprocess.Popen(
        ['ngrok', 'http', '8000'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Даем время ngrok запуститься
    print("Жду запуска ngrok...")
    time.sleep(5)
    
    # Пробуем получить URL через API
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    url = tunnel.get('public_url')
                    print(f"\n✅ Туннель создан!")
                    print(f"🌐 URL: {url}")
                    print(f"📚 Swagger docs: {url}/docs")
                    print(f"\nОтправьте этот URL другу!")
                    return url
    except Exception as e:
        print(f"Не удалось получить URL через API: {e}")
    
    # Если не удалось, пробуем через stderr
    print("Пробую получить URL через вывод ngrok...")
    time.sleep(3)
    
    return None

if __name__ == "__main__":
    url = start_ngrok()
    if not url:
        print("\nНе удалось получить URL автоматически.")
        print("Проверьте терминал с запущенным ngrok вручную.")
    
    print("\nНажмите Ctrl+C для завершения...")
    input()