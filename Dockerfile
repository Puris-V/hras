# Используем базовый образ Python с Debian Bullseye
FROM python:3.10-bullseye

# Устанавливаем репозитории
RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bullseye-security main" >> /etc/apt/sources.list && \
    echo "deb http://deb.debian.org/debian bullseye-updates main" >> /etc/apt/sources.list && \
    apt-get update

# Устанавливаем системные зависимости для Playwright/Chromium
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
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
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и браузеры
RUN pip install playwright && playwright install

# Копируем приложение
COPY . /app

# Указываем команду для запуска
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
