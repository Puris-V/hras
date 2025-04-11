# config.py

import os

# API ключи и настройки
OPEN_SANCTIONS_API_KEY = os.getenv("OPEN_SANCTIONS_API_KEY", "cd58c6ebfd7434a7283e11d1cac00000")
GOOGLE_NEWS_API_KEY = os.getenv("GOOGLE_NEWS_API_KEY", "7f7803ffc67447478f8d997e7ff19c91")
OPEN_SANCTIONS_API_URL = "https://api.opensanctions.org/match/default"
GOOGLE_NEWS_API_URL = "https://newsapi.org/v2/everything"

# Геополитический риск
GEO_RISK_MAP = {
    "default": 100,
    "Cyprus": 100,
    "USA": 50,
    "Russia": 500,
    "Ukraine": 700,
    # Добавляйте другие страны по мере необходимости
}

# Весовые коэффициенты для расчета риска
SCORE_WEIGHTS = {
    "status": {
        "ACTIVE": 0,
        "DISSOLVED": 100,
        "INACTIVE": 200,
    },
    "base_sanction_risk": 50,
    "judicial_cases": 20,
    "negative_sentiment": 10,
    "geo_risk": 1,
}
