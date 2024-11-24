FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы в контейнер
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir fastapi uvicorn python-multipart requests bs4 textblob playwright

# Устанавливаем браузеры Playwright
RUN playwright install

# Запускаем приложение
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
