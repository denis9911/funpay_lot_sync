import json
import logging
from sync_lot_utils.checkbox_manipulator import deactivate_lot, activate_lot, is_lot_active

MERGED_FILE = "merged.json"
STATUS_FILE = "status.json"
LOG_FILE = "sync_lot_statuses.log"

# Настройка логирования
logger = logging.getLogger("sync_lot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка чтения {filename}")
        return {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def sync_statuses():
    logger.info("🚀 Старт проверки лотов")
    merged_data = load_json(MERGED_FILE)
    status_data = load_json(STATUS_FILE)
    updated = False

    for game, products in merged_data.items():
        if not products or not isinstance(products, dict):
            logger.info(f"Пропуск {game}: нет товаров.")
            continue

        for product_name, lots in products.items():
            if not lots or not isinstance(lots, list):
                logger.info(f"Пропуск {game}/{product_name}: нет лотов.")
                continue

            for lot in lots:
                lot_name = lot.get("name")
                lot_url = lot.get("url")

                if not lot_name or not lot_url:
                    logger.warning(f"Пропуск некорректного лота в {game}/{product_name}.")
                    continue

                merged_active = lot.get("active", False)
                current_status = status_data.get(lot_name)

                actual_active = is_lot_active(lot_url)
                if actual_active is None:
                    logger.warning(f"Не удалось определить статус лота: {lot_name}")
                    continue

                # Проверяем merged.json
                if merged_active != actual_active:
                    lot["active"] = actual_active
                    updated = True
                    logger.info(f"🔄 Исправлен статус в merged.json: {lot_name} → {'active' if actual_active else 'inactive'}")

                # Если статус в status.json не совпадает с реальным → меняем
                if current_status != ("active" if actual_active else "inactive"):
                    if actual_active:
                        activate_lot(lot_url)
                        status_data[lot_name] = "active"
                        lot["active"] = True
                        logger.info(f"✅ Активирован лот: {lot_name}")
                    else:
                        deactivate_lot(lot_url)
                        status_data[lot_name] = "inactive"
                        lot["active"] = False
                        logger.info(f"⛔ Деактивирован лот: {lot_name}")
                    updated = True

    if updated:
        save_json(MERGED_FILE, merged_data)
        save_json(STATUS_FILE, status_data)
        logger.info("✅ Файлы обновлены")

    logger.info("🏁 Проверка завершена")


if __name__ == "__main__":
    try:
        sync_statuses()
    except Exception as e:
        logger.error(f"Ошибка в работе: {e}")
