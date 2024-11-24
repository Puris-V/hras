# Используем базовый образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgobject-2.0-0 \
    libnss3 \
    libnssutil3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgio2.0-0 \
    libexpat1 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libdrm2 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    lsb-release \
    wget \
    xdg-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и скачиваем браузеры
RUN pip install playwright && playwright install --with-deps

# Копируем приложение в контейнер
COPY . .

# Указываем команду для запуска приложения
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
