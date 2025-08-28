import json
import logging
import time
from sync_lot_utils.checkbox_manipulator import deactivate_lot, activate_lot, is_lot_active
from sync_lot_utils.status_parser import update_status_file

MERGED_FILE = "merged.json"
STATUS_FILE = "status.json"
LOG_FILE = "sync_lot_statuses.log"

# Логгер для терминала (все информационные сообщения)
console_logger = logging.getLogger("console_logger")
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
console_logger.addHandler(console_handler)

# Логгер для файла (только важные события)
file_logger = logging.getLogger("file_logger")
file_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
file_logger.addHandler(file_handler)


def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        file_logger.error(f"Ошибка загрузки {file_path}: {e}")
        return {}


def sync_lots():
    merged = load_json(MERGED_FILE)
    statuses = load_json(STATUS_FILE)

    for game, products in merged.items():
        for product_name, lots in products.items():
            desired_status = statuses.get(game, {}).get(product_name, "Missing")

            for lot in lots:
                lot_url = lot.get("url")
                if not lot_url:
                    continue

                try:
                    current_active = is_lot_active(lot_url)
                except Exception as e:
                    file_logger.error(f"[{game} / {product_name}] Ошибка проверки статуса: {e}")
                    continue

                should_be_active = desired_status == "Undetected"

                # Вывод в терминал только один раз
                console_logger.info(
                    f"[{game} / {product_name}] Лот {lot.get('name')}, "
                    f"текущий статус: {'active' if current_active else 'inactive'}, "
                    f"желаемый: {'active' if should_be_active else 'inactive'}"
                )

                if current_active != should_be_active:
                    file_logger.info(
                        f"[{game} / {product_name}] Лот {lot.get('name')} не в нужном статусе, "
                        f"текущий: {'active' if current_active else 'inactive'}, "
                        f"будет изменён на: {'active' if should_be_active else 'inactive'}"
                    )
                    try:
                        if should_be_active:
                            activate_lot(lot_url)
                        else:
                            deactivate_lot(lot_url)
                        lot["active"] = should_be_active
                    except Exception as e:
                        file_logger.error(f"[{game} / {product_name}] Ошибка при изменении статуса {lot_url}: {e}")

                time.sleep(1.5)


if __name__ == "__main__":
    sync_lots()
    update_status_file()
