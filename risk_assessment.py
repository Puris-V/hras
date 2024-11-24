import logging
from bs4 import BeautifulSoup
from textblob import TextBlob
import config
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
import requests
from datetime import datetime, timedelta
from config import SCORE_WEIGHTS
import time

# Диапазоны уровней риска
RISK_LEVELS = [
    (0, 150, "Low"),
    (151, 400, "Moderate"),
    (401, 800, "High"),
    (801, float("inf"), "Critical"),
]


# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RiskAssessment")

COMPANY_REGISTRY_URL = "https://efiling.drcor.mcit.gov.cy/DrcorPublic/SearchForm.aspx?sc=0"
JUDICIAL_REGISTRY_URL = "https://www.cylaw.org/cgi-bin/open.pl"

async def fetch_company_details(company_name):
    """Асинхронная функция для получения данных о компании."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page()
        
        # Проверка доступности сайта
        try:
            response = requests.get(COMPANY_REGISTRY_URL, timeout=300)
            response.raise_for_status()
            logger.info(f"Сайт доступен. Код ответа: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Сайт недоступен. Ошибка: {e}")
            return None, None

        # Основная логика взаимодействия с сайтом
        try:
            logger.info("Navigating to the company registry site.")
            await page.goto(COMPANY_REGISTRY_URL, timeout=6000)
            if await page.locator("#lnkEnglish").is_visible():
                logger.info("Switching site to English.")
                await page.click("#lnkEnglish")
                await page.wait_for_load_state("networkidle")
            await page.fill("#ctl00_cphMyMasterCentral_ucSearch_txtName", company_name)
            await page.click("#ctl00_cphMyMasterCentral_ucSearch_lbtnSearch")
            await page.wait_for_load_state("networkidle")
            if not await page.locator("#ctl00_cphMyMasterCentral_GridView1").is_visible():
                logger.error("Result table not found.")
                return None, None
            logger.info("Accessing company card.")
            await page.locator("#ctl00_cphMyMasterCentral_GridView1 tr.basket").first.click()
            await page.wait_for_load_state("networkidle")
            html_content = await page.content()
            await page.click("#ctl00_cphMyMasterCentral_directors")
            await page.wait_for_load_state("networkidle")
            directors_content = await page.content()
            return html_content, directors_content
        except Exception as e:
            logger.error(f"Error interacting with the registry: {e}")
            return None, None
        finally:
            await browser.close()
        

def parse_company_details(html_content, directors_content):
    """Парсит информацию о компании и её директорах."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        directors_soup = BeautifulSoup(directors_content, 'html.parser')

        def safe_get_text(soup, selector_id, field_name):
            element = soup.find("span", {"id": selector_id})
            if element:
                return element.text.strip()
            logger.warning(f"Не найден элемент {field_name} с ID: {selector_id}")
            return None

        company_info = {
            "name": safe_get_text(soup, "ctl00_cphMyMasterCentral_ucOrganizationDetailsSummary_lblName", "Имя компании"),
            "registration_number": safe_get_text(soup, "ctl00_cphMyMasterCentral_ucOrganizationDetailsSummary_lblNumber", "Регистрационный номер"),
            "status": safe_get_text(soup, "ctl00_cphMyMasterCentral_ucOrganizationDetailsSummary_lblStatus", "Статус"),
            "address": safe_get_text(soup, "ctl00_cphMyMasterCentral_ucOrganizationDetailsSummary_lblAddress", "Адрес"),
            "registration_date": safe_get_text(soup, "ctl00_cphMyMasterCentral_ucOrganizationDetailsSummary_lblRegistrationDate", "Дата регистрации"),
            "directors": []
        }

        directors_table = directors_soup.find("table", {"id": "ctl00_cphMyMasterCentral_OfficialsGrid"})
        if directors_table:
            for row in directors_table.find_all("tr")[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    company_info["directors"].append({
                        "name": cells[0].text.strip(),
                        "position": cells[1].text.strip(),
                        "appointed_date": cells[2].text.strip() if len(cells) > 2 else "N/A"
                    })
        else:
            logger.warning("Таблица директоров не найдена.")
        return company_info
    except Exception as e:
        logger.error(f"Ошибка при парсинге данных компании: {e}")
        return None
    
def check_open_sanctions(names):
    """
    Проверяет имена в OpenSanctions API.
    """
    logger.info(f"Проверка через OpenSanctions API для имён: {names}")

    # Формируем запрос для API
    queries = {
        f"q{i+1}": {"schema": "Person", "properties": {"name": [name]}}
        for i, name in enumerate(names)
    }
    query_data = {"queries": queries}
    logger.debug(f"Отправка данных в OpenSanctions API: {query_data}")

    # Установка заголовков для авторизации
    headers = {
        "Authorization": f"Bearer {config.OPEN_SANCTIONS_API_KEY}",
    }

    try:
        # Выполняем POST-запрос к OpenSanctions API
        response = requests.post(
            config.OPEN_SANCTIONS_API_URL, headers=headers, json=query_data
        )
        response.raise_for_status()  # Вызывает исключение для статусов >= 400

        # Обрабатываем ответ
        results = []
        for query_id, query_response in response.json()["responses"].items():
            for result in query_response.get("results", []):
                results.append({
                    "name": result.get("properties", {}).get("name"),
                    "match_type": result.get("match_type"),
                    "dataset": result.get("dataset"),
                    "score": result.get("score"),
                })

        logger.info(f"Найдено совпадений в санкционных списках: {len(results)}")
        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к OpenSanctions API: {e}")
        return []


def analyze_news_sentiment(company_name):
    """
    Анализирует тональность новостей для заданной компании.
    """
    logger.info(f"Анализ тональности новостей для компании: {company_name}")

    # Параметры запроса
    params = {
        "q": company_name.split()[0],  # Упрощение до первого слова
        "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),  # Последние 30 дней
        "sortBy": "popularity",
        "language": "en",
        "pageSize": 10,
        "apiKey": config.GOOGLE_NEWS_API_KEY,
    }
    logger.debug(f"Параметры запроса к NewsAPI: {params}")

    try:
        response = requests.get(config.GOOGLE_NEWS_API_URL, params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])

        if not articles:
            logger.warning("Статьи не найдены.")
            return []

        # Анализ тональности
        sentiments = []
        for article in articles:
            content = f"{article.get('title', '')} {article.get('description', '')}"
            sentiment = TextBlob(content).sentiment.polarity
            sentiments.append(sentiment)

        logger.info(f"Проанализировано {len(sentiments)} статей.")
        return sentiments
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к NewsAPI: {e}")
        return []



def check_judicial_cases(name):
    """Проверка судебных дел для указанного имени."""
    logger.info(f"Проверка судебных дел для: {name}")
    base_url = "https://cylaw.org/cgi-bin/sinocgi.pl"
    search_params = {
        "searchoption": "1",
        "query": name,
        "hitsnom": "20",
        "nexthit": "1",
    }
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # Шаг 1: Поиск дел
        response = requests.get(base_url, params=search_params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Шаг 2: Извлечение ссылок на дела
        case_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "case" in href:  # Фильтруем ссылки на дела
                case_links.append(href)

        logger.info(f"Найдено судебных дел: {len(case_links)}")
        return len(case_links)
    except requests.RequestException as e:
        logger.error(f"Ошибка при проверке судебных дел: {e}")
        return 0


def calculate_risk_score(company_data, sanctions_matches, metrics):
    """
    Рассчитывает итоговый риск компании на основе данных.
    """
    logger.info("Начало расчёта риска")
    weights = SCORE_WEIGHTS
    score = 0
    details = {}

    # Риск по статусу компании
    status_risk = weights["status"].get(company_data["status"].upper(), 100)
    score += status_risk
    details["status"] = status_risk

    # Риск по санкциям
    sanctioned_count = metrics.get("sanctioned_count", 0)
    if sanctioned_count > 0:
        sanction_risk = weights["base_sanction_risk"] * sanctioned_count
    else:
        sanction_risk = 0
    score += sanction_risk
    details["pep_sanctions"] = sanction_risk


    # Риск по судебным делам
    judicial_risk = metrics.get("judicial_cases", 0) * weights["judicial_cases"]
    score += judicial_risk
    details["judicial_cases"] = judicial_risk

    # Риск по тональности новостей
    news_sentiments = metrics.get("news_sentiments", [])
    if news_sentiments:
        negative_news_count = sum(1 for s in news_sentiments if s < 0)
        sentiment_risk = negative_news_count * weights["negative_sentiment"]
    else:
        sentiment_risk = 0  # Если новостей нет, риск по ним = 0
    score += sentiment_risk
    details["negative_sentiment"] = sentiment_risk

    # Геополитический риск
    geo_risk = metrics.get("geo_risk", 0) * weights["geo_risk"]
    score += geo_risk
    details["geo_risk"] = geo_risk

    # Определение уровня риска
    for lower, upper, level in RISK_LEVELS:
        if lower <= score <= upper:
            details["risk_level"] = level
            break

    logger.info(f"Итоговый риск компании: {score} ({details['risk_level']})")
    return score, details
    
def analyze_company(company_name):
    """Анализирует риск компании по названию и возвращает результат."""
    logger.info(f"Начало проверки для компании: {company_name}")
    html_content, directors_content = fetch_company_details(company_name)
    if not html_content or not directors_content:
        return {"error": "Не удалось загрузить данные компании."}

    company_data = parse_company_details(html_content, directors_content)
    if not company_data:
        return {"error": "Ошибка парсинга данных компании."}

    logger.info(f"Данные компании: {company_data}")
    all_names = [company_data["name"]] + [d["name"] for d in company_data["directors"]]
    sanctions_matches = check_open_sanctions(all_names)
    sentiments = analyze_news_sentiment(company_data["name"])
    judicial_cases_count = sum(check_judicial_cases(name) for name in all_names)
    
    risk_score, details = calculate_risk_score(
        company_data,
        sanctions_matches,
        {
            "sanctioned_count": len(sanctions_matches),
            "news_sentiments": sentiments,
            "geo_risk": config.GEO_RISK_MAP.get("Cyprus", config.GEO_RISK_MAP["default"]),
            "judicial_cases": judicial_cases_count,
        },
    )
    return {
        "company_name": company_data["name"],
        "risk_level": details["risk_level"],
        "total_risk": risk_score,
        "sanctions_count": len(sanctions_matches),
        "judicial_cases": judicial_cases_count,
    }



async def main(company_name: str):
    """Основная логика анализа риска."""
    html_content, directors_content = await fetch_company_details(company_name)
    if not html_content or not directors_content:
        return {"error": "Не удалось загрузить данные компании"}

    company_data = parse_company_details(html_content, directors_content)
    if not company_data:
        return {"error": "Ошибка парсинга данных компании"}

    logger.info(f"Данные компании: {company_data}")
    all_names = [company_data["name"]] + [d["name"] for d in company_data["directors"]]
    
    sanctions_matches = check_open_sanctions(all_names)
    sentiments = analyze_news_sentiment(company_data["name"])
    judicial_cases_count = sum(check_judicial_cases(name) for name in all_names)
    
    risk_score, details = calculate_risk_score(
        company_data,
        sanctions_matches,
        {
            "sanctioned_count": len(sanctions_matches),
            "news_sentiments": sentiments,
            "geo_risk": config.GEO_RISK_MAP.get("Cyprus", config.GEO_RISK_MAP["default"]),
            "judicial_cases": judicial_cases_count,
        },
    )

    return {
        "company_data": company_data,
        "sanctions_matches": sanctions_matches,
        "news_sentiments": sentiments,
        "judicial_cases": judicial_cases_count,
        "risk_score": risk_score,
        "risk_details": details,
    }


if __name__ == "__main__":
    main()
