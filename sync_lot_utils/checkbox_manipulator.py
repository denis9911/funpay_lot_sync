import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from config import Config

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

logger.info(f"Config.FP_GOLDEN_KEY = {Config.FP_GOLDEN_KEY!r}")
logger.info(f"Config.SITE_URL = {Config.SITE_URL!r}")

COOKIES = {"golden_key": Config.FP_GOLDEN_KEY}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# Создаем глобальную сессию
session = requests.Session()
session.cookies.update(COOKIES)
session.headers.update(HEADERS)


def safe_get(url, max_retries=5):
    """GET с задержкой и повторной попыткой при 429"""
    for attempt in range(max_retries):
        resp = session.get(url)
        logger.info(f"GET {url} -> {resp.status_code}")
        if resp.status_code == 429:
            wait = 5 * (attempt + 1) + random.uniform(0, 2)
            logger.warning(f"429 Too Many Requests, жду {wait:.1f}s")
            time.sleep(wait)
            continue
        # Всегда делаем небольшую паузу после запроса
        time.sleep(random.uniform(2, 4))
        return resp
    logger.error(f"Не удалось получить {url} после {max_retries} попыток")
    return None


def safe_post(url, data, max_retries=5):
    """POST с задержкой и повторной попыткой при 429"""
    for attempt in range(max_retries):
        resp = session.post(url, data=data)
        logger.info(f"POST {url} -> {resp.status_code}")
        if resp.status_code == 429:
            wait = 5 * (attempt + 1) + random.uniform(0, 2)
            logger.warning(f"429 Too Many Requests при POST, жду {wait:.1f}s")
            time.sleep(wait)
            continue
        time.sleep(random.uniform(2, 4))
        return resp
    logger.error(f"Не удалось отправить POST на {url} после {max_retries} попыток")
    return None


def is_lot_active(lot_url: str) -> bool | None:
    logger.info(f"Проверяю статус лота: {lot_url}")
    resp = safe_get(lot_url)
    if not resp or resp.status_code != 200:
        logger.warning(f"Не удалось открыть {lot_url}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form", class_="form-offer-editor")
    if not form:
        logger.warning("Форма лота не найдена!")
        return None

    active_input = form.find("input", {"name": "active", "type": "checkbox"})
    if not active_input:
        logger.warning("Чекбокс 'active' не найден!")
        return None

    status = active_input.has_attr("checked")
    logger.info(f"Статус лота {lot_url}: {'Активен' if status else 'Выключен'}")
    return status


def set_lot_active(lot_url: str, active: bool):
    """Универсальная функция для активации/деактивации лота."""
    resp = safe_get(lot_url)
    if not resp or resp.status_code != 200:
        return False

    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form", class_="form-offer-editor")
    if not form:
        logger.warning("Форма лота не найдена!")
        return False

    # Собираем все поля формы
    form_data = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        if inp.get("type") == "checkbox":
            if name != "active":
                form_data[name] = "on" if inp.has_attr("checked") else ""
        else:
            form_data[name] = inp.get("value", "")

    form_data["active"] = "on" if active else ""

    for select in form.find_all("select"):
        name = select.get("name")
        if name and name not in form_data:
            option = select.find("option", selected=True)
            if option:
                form_data[name] = option.get("value", "")

    for textarea in form.find_all("textarea"):
        name = textarea.get("name")
        if name:
            form_data[name] = textarea.text

    save_url = form.get("action")
    if not save_url.startswith("http"):
        save_url = "https://funpay.com" + save_url

    resp_save = safe_post(save_url, form_data)
    if resp_save and resp_save.status_code == 200:
        logger.info(f"Лот успешно {'активирован' if active else 'деактивирован'}!")
        return True
    else:
        logger.error(f"Ошибка при сохранении лота: {resp_save.status_code if resp_save else 'нет ответа'}")
        return False


def activate_lot(lot_url: str):
    return set_lot_active(lot_url, True)


def deactivate_lot(lot_url: str):
    return set_lot_active(lot_url, False)
