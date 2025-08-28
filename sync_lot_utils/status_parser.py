import json
import requests
from bs4 import BeautifulSoup
import sys
import os
from config import Config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

URL = Config.SITE_URL
STATUS_FILE = "status.json"

def get_statuses():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    result = {}

    # Ищем все блоки с играми
    games = soup.find_all("div", class_="cheat-page-link")
    for game in games:
        game_name = game.get("title")
        if not game_name:
            continue

        result[game_name] = {}
        # Ищем все li внутри игры
        product_list = game.find_all("li")
        for li in product_list:
            a_tag = li.find("a", href=True, title=True)
            if not a_tag:
                continue
            product_name = a_tag.find("span").text.strip()
            status = a_tag.get("title").strip()
            result[game_name][product_name] = status

    return result

def update_status_file():
    statuses = get_statuses()
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(statuses, f, ensure_ascii=False, indent=4)
    return statuses

if __name__ == "__main__":
    statuses = update_status_file()
    for game, products in statuses.items():
        print(f"{game}:")
        for name, status in products.items():
            print(f"  - {name} [{status}]")
