# Используем минималистичный базовый образ
FROM python:3.10-slim

# Устанавливаем переменные окружения для Playwright
ENV PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Устанавливаем системные зависимости для Chromium (Playwright)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgdk-pixbuf-2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgobject-2.0-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libwayland-client0 \
    libwayland-server0 \
    libxkbcommon0 \
    libxshmfence1 \
    wget \
    xdg-utils \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и загружаем браузеры
RUN pip install playwright && playwright install

# Копируем код приложения
COPY . .

# Указываем порт для запуска приложения
EXPOSE 8000

# Команда запуска приложения
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
