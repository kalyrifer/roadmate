import subprocess
import time

print("=" * 50)
print("СОЗДАНИЕ ТУННЕЛЯ ДЛЯ ROADMATE")
print("=" * 50)

print("\nВариант 1: ngrok (если есть аккаунт)")
print("-" * 30)
print("1. Зарегистрируйтесь на ngrok.com")
print("2. Скачайте и настройте ngrok")
print("3. В терминале выполните:")
print("   ngrok http 8000")
print("4. Скопируйте полученный URL (начинается с https://)")

print("\n" + "=" * 50)

print("\nВариант 2: cloudflare (рекомендуется)")
print("-" * 30)
print("1. Скачайте cloudflared:")
print("   https://developers.cloudflare.com/cloudflare-one/tutorials/")
print("   commands/ssh-tunnel/")
print("2. Распакуйте файл cloudflared.exe в папку с проектом")
print("3. В новом терминале выполните:")
print("   cloudflared tunnel --url localhost:8000")
print("4. Скопируйте полученный URL")

print("\n" + "=" * 50)

print("\nВариант 3: LocalTunnel (бесплатно)")
print("-" * 30)
print("1. Убедитесь что сервер запущен (python run_server.py)")
print("2. В новом терминале выполните:")
print("   npx lt --port 8000 --subdomain roadmate-test")
print("3. Подождите пока появится URL (около 10 секунд)")
print("4. URL будет типа: https://roadmate-test.loca.lt")
print("5. Отправьте этот URL другу!")

print("\n" + "=" * 50)

print("\nПосле запуска туннеля проверьте что сервер работает:")
print("1. Откройте https://<ваш-url>.loca.lt/docs")
print("2. Должен открыться Swagger UI")

print("\n" + "=" * 50)
print("ГОТОВО! Теперь попробуйте создать туннель.")