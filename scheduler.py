#!/usr/bin/env python3
"""
Scheduler для AI Prorok - проверяет, пора ли запускать генерацию или публикацию
Этот скрипт вызывается systemd таймерами каждую минуту
"""
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MOSCOW_TZ = pytz.timezone('Europe/Moscow')

STATE_DIR = Path("state")
GENERATION_TIME_FILE = STATE_DIR / "generation_time.txt"
PUBLICATION_TIME_FILE = STATE_DIR / "publication_time.txt"


def get_moscow_time() -> datetime:
    """Возвращает текущее время в московском часовом поясе"""
    return datetime.now(MOSCOW_TZ)


def load_time_from_file(filepath: Path) -> datetime:
    """Загружает время из файла"""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            time_str = f.read().strip()
            dt = datetime.fromisoformat(time_str)
            # Убедимся, что время в московской зоне
            if dt.tzinfo is None:
                dt = MOSCOW_TZ.localize(dt)
            return dt
    except Exception as e:
        logger.error(f"Ошибка загрузки времени из {filepath}: {e}")
        return None


def should_generate() -> bool:
    """Проверяет, пора ли генерировать пророчество"""
    generation_time = load_time_from_file(GENERATION_TIME_FILE)

    if not generation_time:
        logger.info("Время генерации не задано")
        return False

    now = get_moscow_time()

    # Проверяем, наступило ли время генерации (с точностью ±1 минута)
    time_diff = (now - generation_time).total_seconds()

    if -60 <= time_diff <= 60:
        logger.info(f"Время генерации наступило! Запланировано: {generation_time}, сейчас: {now}")
        return True
    elif time_diff < -60:
        logger.info(f"До генерации еще {-time_diff/60:.1f} минут")
        return False
    else:
        logger.info(f"Время генерации прошло {time_diff/60:.1f} минут назад")
        return False


def should_publish() -> bool:
    """Проверяет, пора ли публиковать пророчество"""
    publication_time = load_time_from_file(PUBLICATION_TIME_FILE)

    if not publication_time:
        logger.info("Время публикации не задано")
        return False

    now = get_moscow_time()

    # Проверяем, наступило ли время публикации (с точностью ±1 минута)
    time_diff = (now - publication_time).total_seconds()

    if -60 <= time_diff <= 60:
        logger.info(f"Время публикации наступило! Запланировано: {publication_time}, сейчас: {now}")
        return True
    elif time_diff < -60:
        logger.info(f"До публикации еще {-time_diff/60:.1f} минут")
        return False
    else:
        logger.info(f"Время публикации прошло {time_diff/60:.1f} минут назад")
        return False


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python scheduler.py check-generate  - проверить, пора ли генерировать")
        print("  python scheduler.py check-publish   - проверить, пора ли публиковать")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "check-generate":
        if should_generate():
            logger.info("✅ Пора генерировать пророчество")
            sys.exit(0)  # Вернуть 0 = да, пора
        else:
            sys.exit(1)  # Вернуть 1 = нет, не пора

    elif mode == "check-publish":
        if should_publish():
            logger.info("✅ Пора публиковать пророчество")
            sys.exit(0)
        else:
            sys.exit(1)

    else:
        logger.error(f"Неизвестный режим: {mode}")
        sys.exit(2)


if __name__ == "__main__":
    main()
