# Как создать туннель для друга

## Быстрый способ (рекомендуется)

### Шаг 1: Запустите сервер и туннель

Два варианта:

**Вариант А - Скрипт (самый простой):**
```batch
cd D:\RoadMate
run_with_tunnel.bat
```

**Вариант Б - Вручную:**

1. Откройте новый терминал и запустите сервер:
```batch
cd D:\RoadMate\app
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

2. Откройте второй терминал и запустите туннель:
```batch
D:\RoadMate\cloudflared.exe tunnel --url localhost:8000
```

### Шаг 2: Получите URL

Когда туннель запустится, вы увидите строку:
```
https://something.trycloudflare.com
```

### Шаг 3: Отправьте URL другу

Скажите другу открыть:
```
https://something.trycloudflare.com/api/v1/auth/login
```

## Проверка что всё работает

На вашем компьютере (локально):
```python
import requests
r = requests.post('http://localhost:8000/api/v1/auth/login', 
    json={'email': 'ваш email', 'password': 'ваш пароль'})
print(r.status_code)  # Должно быть 200
```

Через туннель:
```python
import requests
r = requests.post('https://ваш-url.trycloudflare.com/api/v1/auth/login', 
    json={'email': 'ваш email', 'password': 'ваш пароль'})
print(r.status_code)  # Должно быть 200
```

## Если не работает

1. Убедитесь что сервер запущен - откройте http://localhost:8000/docs
2. Проверьте что оба окна терминала открыты (сервер и туннель)
3. Попробуйте перезапустить: закройте терминалы и запустите снова

## Остановка

Нажмите Ctrl+C в обоих терминалах или просто закройте окна.

## Важно

- Туннель работает пока открыт терминал
- URL меняется каждый раз при перезапуске
- Для постоянного URL нужно настроить именованный туннель (см. документацию Cloudflare)