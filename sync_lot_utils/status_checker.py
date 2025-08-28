import json
import logging
from checkbox_manipulator import deactivate_lot, activate_lot, is_lot_active
from status_parser import update_status_file
import time

MERGED_FILE = "merged.json"
STATUS_FILE = "status.json"
LOG_FILE = "sync_lot_statuses.log"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def sync_lot_statuses():
    merged = load_json(MERGED_FILE)
    statuses = load_json(STATUS_FILE)
    updated = False

    for game, products in merged.items():
        for product_name, lots in products.items():
            desired_status = statuses.get(game, {}).get(product_name, "Missing")
            should_be_active = desired_status == "Undetected"

            for lot in lots:
                lot_url = lot.get("url")
                
                # Проверяем реальный статус на FunPay
                real_status = None
                try:
                    real_status = is_lot_active(lot_url)
                except Exception as e:
                    logging.error(f"Не удалось определить реальный статус лота: {lot['name']}, {e}")

                # Если статус на FunPay уже как нужно, просто обновляем merged.json
                if real_status is not None and real_status == should_be_active:
                    if lot.get("active") != should_be_active:
                        lot["active"] = should_be_active
                        updated = True
                        logging.info(f"Игра: {game}, Продукт: {product_name}, Лот: {lot['name']}, "
                                     f"статус на FunPay совпадает с желаемым, обновляю merged.json.")
                    continue

                # Если статус отличается, меняем его через POST
                current_active = lot.get("active", False)
                if current_active != should_be_active:
                    logging.info(f"Игра: {game}, Продукт: {product_name}, Лот: {lot['name']}, "
                                 f"статус на сайте: {desired_status}, статус на FunPay: {current_active}, нужно поменять статус.")
                    success = False
                    try:
                        if should_be_active:
                            success = activate_lot(lot_url)
                        else:
                            success = deactivate_lot(lot_url)
                    except Exception as e:
                        logging.error(f"Ошибка при смене статуса лота: {lot['name']}, {e}")
                        success = False

                    if success:
                        lot["active"] = should_be_active
                        updated = True
                        logging.info(f"Игра: {game}, Продукт: {product_name}, Лот: {lot['name']}, "
                                     f"статус на FunPay успешно изменён на {should_be_active}")
                    else:
                        logging.warning(f"Не удалось изменить статус лота: {lot['name']}")
                    time.sleep(2)  # задержка между запросами

    if updated:
        save_json(MERGED_FILE, merged)
        logging.info(f"Локальный файл {MERGED_FILE} обновлён после синхронизации.")
    else:
        logging.info("Изменений в статусах лотов не было, файл merged.json не обновлялся.")

if __name__ == "__main__":
    update_status_file()
    sync_lot_statuses()
