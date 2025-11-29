import random
import json
import os
import sys
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from openai import OpenAI
from dotenv import load_dotenv
import vk_api
import requests

"""
Генерация и публикация пророчеств с поддержкой перезапуска сервера
Два режима работы:
1. generate - генерация пророчества (за 10 минут до публикации)
2. publish - публикация пророчества
"""

# Настройка логирования с московским временем
class MoscowTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        moscow_tz = pytz.timezone('Europe/Moscow')
        dt = datetime.fromtimestamp(record.created, moscow_tz)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.isoformat()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Устанавливаем московское время для всех логов
for handler in logging.root.handlers:
    handler.setFormatter(MoscowTimeFormatter())

load_dotenv()

# Загрузка переменных окружения
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VK_TOKEN = os.getenv('VK_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHAT_ID = "@prorochestva_ot_bota"

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Пути к файлам состояния
STATE_DIR = Path("state")
STATE_DIR.mkdir(exist_ok=True)

GENERATION_TIME_FILE = STATE_DIR / "generation_time.txt"
PUBLICATION_TIME_FILE = STATE_DIR / "publication_time.txt"
CURRENT_PROPHECY_FILE = STATE_DIR / "current_prophecy.txt"
PROPHECY_METADATA_FILE = STATE_DIR / "prophecy_metadata.json"


def get_moscow_time() -> datetime:
    """Возвращает текущее время в московском часовом поясе"""
    return datetime.now(MOSCOW_TZ)


def format_moscow_time(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматирует время в московском поясе"""
    if dt is None:
        dt = get_moscow_time()
    return dt.strftime(format_str)


def save_generation_time(gen_time: datetime):
    """Сохраняет время генерации в файл"""
    with open(GENERATION_TIME_FILE, 'w', encoding='utf-8') as f:
        f.write(gen_time.isoformat())
    logger.info(f"Время генерации сохранено: {format_moscow_time(gen_time)}")


def save_publication_time(pub_time: datetime):
    """Сохраняет время публикации в файл"""
    with open(PUBLICATION_TIME_FILE, 'w', encoding='utf-8') as f:
        f.write(pub_time.isoformat())
    logger.info(f"Время публикации сохранено: {format_moscow_time(pub_time)}")


def save_current_prophecy(prophecy: str, metadata: dict = None):
    """Сохраняет текущее пророчество в файл"""
    with open(CURRENT_PROPHECY_FILE, 'w', encoding='utf-8') as f:
        f.write(prophecy)

    if metadata:
        with open(PROPHECY_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"Пророчество сохранено в {CURRENT_PROPHECY_FILE}")


def load_generation_time() -> Optional[datetime]:
    """Загружает время генерации из файла"""
    if not GENERATION_TIME_FILE.exists():
        return None
    try:
        with open(GENERATION_TIME_FILE, 'r', encoding='utf-8') as f:
            time_str = f.read().strip()
            return datetime.fromisoformat(time_str)
    except Exception as e:
        logger.error(f"Ошибка загрузки времени генерации: {e}")
        return None


def load_publication_time() -> Optional[datetime]:
    """Загружает время публикации из файла"""
    if not PUBLICATION_TIME_FILE.exists():
        return None
    try:
        with open(PUBLICATION_TIME_FILE, 'r', encoding='utf-8') as f:
            time_str = f.read().strip()
            return datetime.fromisoformat(time_str)
    except Exception as e:
        logger.error(f"Ошибка загрузки времени публикации: {e}")
        return None


def load_current_prophecy() -> Optional[Tuple[str, dict]]:
    """Загружает текущее пророчество из файла"""
    if not CURRENT_PROPHECY_FILE.exists():
        return None
    try:
        with open(CURRENT_PROPHECY_FILE, 'r', encoding='utf-8') as f:
            prophecy = f.read()

        metadata = {}
        if PROPHECY_METADATA_FILE.exists():
            with open(PROPHECY_METADATA_FILE, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

        return prophecy, metadata
    except Exception as e:
        logger.error(f"Ошибка загрузки пророчества: {e}")
        return None


def clear_state_files():
    """Очищает файлы состояния после успешной публикации"""
    for file in [GENERATION_TIME_FILE, PUBLICATION_TIME_FILE, CURRENT_PROPHECY_FILE, PROPHECY_METADATA_FILE]:
        if file.exists():
            file.unlink()
    logger.info("Файлы состояния очищены")


def optimized_choice_lst(lst: list, max_iterations: int = 20000) -> Tuple[list, list]:
    """
    Оптимизированная версия choice_lst
    Возвращает кортеж: (список выборок, список отсутствующих элементов)
    """
    if not lst:
        return [], []

    unique_elements = set(lst)
    lst_choice = []
    found_elements = set()

    logger.info(f"Начало выборки из {len(unique_elements)} уникальных элементов")

    for i in range(max_iterations):
        if len(found_elements) == len(unique_elements):
            break

        choice = random.choice(lst)
        lst_choice.append(choice)
        found_elements.add(choice)

    missing_elements = list(unique_elements - found_elements)

    if missing_elements:
        logger.info(f"Элементы, не попавшие в выборку: {missing_elements[:5]} (всего: {len(missing_elements)})")

    logger.info(f"Выполнено итераций: {len(lst_choice)}, найдено уникальных: {len(found_elements)}")

    return lst_choice, random.sample(missing_elements, min(2, len(missing_elements)))


def create_dct(sampled_lst: list) -> List[Tuple[str, int]]:
    """
    Создает отсортированный список кортежей (слово, частота) для топ-3 самых частых слов
    """
    frequency_dict = {}
    for word in sampled_lst:
        frequency_dict[word] = frequency_dict.get(word, 0) + 1

    sorted_items = sorted(frequency_dict.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:3]


def send_to_telegram(message: str) -> bool:
    """Отправляет сообщение в Telegram канал"""
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {
            'chat_id': TG_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()

        logger.info("Сообщение успешно отправлено в Telegram")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False


def send_to_vk(message: str) -> bool:
    """Отправляет сообщение в группу VK"""
    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()

        group_id = -229101116

        result = vk.wall.post(
            owner_id=group_id,
            message=message,
            from_group=1
        )
        logger.info(f"Ответ VK: {result}")

        logger.info("Сообщение успешно отправлено в VK")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки в VK: {e}")
        return False


def get_openai_response(prompt: str, max_retries: int = 3) -> str:
    """Получает ответ от OpenAI API с обработкой ошибок"""
    openai_client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url="https://api.proxyapi.ru/openai/v1",
        timeout=30
    )

    system_message = f"Ты пророк, который предсказывает будущее. Сочини пророчество на указанный день ({get_moscow_time().ctime()}) по указанным словам, не цитируя их при этом, но передавая смысл. В конце пророчества резюмируй двустишием"

    for attempt in range(max_retries):
        try:
            logger.info(f"Попытка {attempt + 1} получить ответ от OpenAI...")

            chat_completion = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f'{prompt}'}
                ],
                timeout=30
            )

            response = chat_completion.choices[0].message.content
            logger.info("Успешно получен ответ от OpenAI")
            return response

        except Exception as e:
            logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
            if attempt < max_retries - 1:
                import time
                wait_time = (attempt + 1) * 5
                logger.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)
            else:
                logger.error("Все попытки получить ответ от OpenAI провалились")
                return "Моя магия слов закончилась ровно там, где началась ваша надежда услышать нечто волшебное. Пророчествовать не буду, ибо моя хрустальная сфера сегодня затуманилась по техническим причинам."


def calculate_next_publication_time() -> Tuple[datetime, datetime]:
    """
    Вычисляет время следующей публикации и генерации в московском часовом поясе
    Возвращает: (время генерации, время публикации)
    """
    now_moscow = get_moscow_time()
    tomorrow = now_moscow + timedelta(days=1)

    # Начало и конец завтрашнего дня в московском времени
    start_of_day = MOSCOW_TZ.localize(datetime(
        tomorrow.year, tomorrow.month, tomorrow.day,
        0, 0, 0
    ))
    end_of_day = MOSCOW_TZ.localize(datetime(
        tomorrow.year, tomorrow.month, tomorrow.day,
        23, 59, 30
    ))

    start_timestamp = int(start_of_day.timestamp())
    end_timestamp = int(end_of_day.timestamp())

    pub_timestamp = random.randint(start_timestamp, end_timestamp)
    publication_time = datetime.fromtimestamp(pub_timestamp, MOSCOW_TZ)

    # Генерация за 10 минут до публикации
    generation_time = publication_time - timedelta(minutes=10)

    logger.info(f"Текущее время МСК: {format_moscow_time(now_moscow)}")
    logger.info(f"Время генерации МСК: {format_moscow_time(generation_time)}")
    logger.info(f"Время публикации МСК: {format_moscow_time(publication_time)}")

    return generation_time, publication_time


def generate_prophecy():
    """Генерирует пророчество и сохраняет его в файл состояния"""
    logger.info("=== РЕЖИМ ГЕНЕРАЦИИ ПРОРОЧЕСТВА ===")

    try:
        # Загрузка словарей
        with open("nouns.json", "r", encoding='utf-8') as fh:
            nouns = json.load(fh)
        with open("verbs.json", "r", encoding='utf-8') as fh:
            verbs = json.load(fh)
        with open("adject.json", "r", encoding='utf-8') as fh:
            adjectives = json.load(fh)

        logger.info(
            f"Загружено: существительных - {len(nouns)}, глаголов - {len(verbs)}, прилагательных - {len(adjectives)}")

        # Генерация случайных выборок
        sample_size = random.randint(100, 20000)
        logger.info(f"Размер выборки: {sample_size}")

        # Создание случайных выборок
        noun_samples = [random.choice(nouns) for _ in range(sample_size)]
        verb_samples = [random.choice(verbs) for _ in range(sample_size)]
        adjective_samples = [random.choice(adjectives) for _ in range(sample_size)]

        # Анализ частотности
        choice_nouns, rare_nouns = optimized_choice_lst(noun_samples)
        choice_verbs, rare_verbs = optimized_choice_lst(verb_samples)
        choice_adjectives, rare_adjectives = optimized_choice_lst(adjective_samples)

        top_nouns = create_dct(choice_nouns)
        top_verbs = create_dct(choice_verbs)
        top_adjectives = create_dct(choice_adjectives)

        logger.info(f"Топ существительные: {top_nouns}, редкие: {rare_nouns}")
        logger.info(f"Топ глаголы: {top_verbs}, редкие: {rare_verbs}")
        logger.info(f"Топ прилагательные: {top_adjectives}, редкие: {rare_adjectives}")

        # Формирование промпта для OpenAI
        prompt = f"Существительные: {top_nouns} / {rare_nouns}\n" \
                 f"Глаголы: {top_verbs} / {rare_verbs}\n" \
                 f"Прилагательные: {top_adjectives} / {rare_adjectives}"

        # Логирование промпта
        with open("prophecies_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"\n{format_moscow_time()}\n{prompt}\n{'+' * 50}\n")

        # Получение ответа от OpenAI
        prophecy = get_openai_response(prompt)

        # Вывод результата
        print("=" * 50)
        print("ПРОРОЧЕСТВО:")
        print(prophecy)
        print("=" * 50)

        # Сохранение пророчества и метаданных
        generation_time = get_moscow_time()
        publication_time = load_publication_time()

        metadata = {
            "generation_time": generation_time.isoformat(),
            "publication_time": publication_time.isoformat() if publication_time else None,
            "prompt": prompt,
            "sample_size": sample_size
        }

        save_current_prophecy(prophecy, metadata)
        save_generation_time(generation_time)

        # Логирование пророчества
        with open("prophecies_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"Пророчество:\n{prophecy}\nВремя генерации: {format_moscow_time()} МСК\n{'-' * 50}\n")

        logger.info("✅ Пророчество успешно сгенерировано и сохранено")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка генерации пророчества: {e}")
        import traceback
        traceback.print_exc()
        return False


def publish_prophecy():
    """Публикует ранее сгенерированное пророчество"""
    logger.info("=== РЕЖИМ ПУБЛИКАЦИИ ПРОРОЧЕСТВА ===")

    # Загружаем пророчество из файла
    prophecy_data = load_current_prophecy()

    if not prophecy_data:
        logger.error("❌ Пророчество не найдено! Возможно, оно ещё не было сгенерировано.")
        return False

    prophecy, metadata = prophecy_data

    logger.info("Пророчество загружено из файла состояния")
    print("=" * 50)
    print("ПУБЛИКУЕМОЕ ПРОРОЧЕСТВО:")
    print(prophecy)
    print("=" * 50)

    # Вычисление следующих времён
    next_generation_time, next_publication_time = calculate_next_publication_time()

    # Сохранение времён следующего цикла
    save_generation_time(next_generation_time)
    save_publication_time(next_publication_time)

    # Формирование сообщения для соцсетей
    current_time = get_moscow_time()
    full_message = f"🔮 Пророчество от бота ({format_moscow_time(current_time)} МСК):\n{prophecy}\n\nСледующее пророчество будет {format_moscow_time(next_publication_time)} МСК"

    # Отправка в социальные сети
    success_count = 0
    if send_to_telegram(full_message):
        success_count += 1
    if send_to_vk(full_message):
        success_count += 1

    logger.info(f"Сообщение отправлено в {success_count} из 2 социальных сетей")

    # Логирование публикации
    with open("prophecies_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"Опубликовано:\n{prophecy}\nВремя публикации: {format_moscow_time()} МСК\n")
        log_file.write(f"Следующая генерация: {format_moscow_time(next_generation_time)} МСК\n")
        log_file.write(f"Следующая публикация: {format_moscow_time(next_publication_time)} МСК\n")
        log_file.write('=' * 50 + '\n')

    # Очищаем файлы состояния после успешной публикации
    clear_state_files()

    logger.info("✅ Пророчество успешно опубликовано")
    return True


def schedule_next_cycle():
    """Планирует следующий цикл генерации и публикации"""
    logger.info("=== ПЛАНИРОВАНИЕ СЛЕДУЮЩЕГО ЦИКЛА ===")

    generation_time, publication_time = calculate_next_publication_time()

    save_generation_time(generation_time)
    save_publication_time(publication_time)

    logger.info(f"✅ Следующая генерация: {format_moscow_time(generation_time)} МСК")
    logger.info(f"✅ Следующая публикация: {format_moscow_time(publication_time)} МСК")

    return True


def main():
    """Основная функция - определяет режим работы"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python ai_prorok_refactored.py generate  - генерация пророчества")
        print("  python ai_prorok_refactored.py publish   - публикация пророчества")
        print("  python ai_prorok_refactored.py schedule  - планирование следующего цикла")
        sys.exit(1)

    mode = sys.argv[1].lower()

    logger.info(f"Запуск в режиме: {mode}")
    logger.info(f"Текущее время: {format_moscow_time()} МСК")

    if mode == "generate":
        success = generate_prophecy()
        sys.exit(0 if success else 1)

    elif mode == "publish":
        success = publish_prophecy()
        sys.exit(0 if success else 1)

    elif mode == "schedule":
        success = schedule_next_cycle()
        sys.exit(0 if success else 1)

    else:
        logger.error(f"Неизвестный режим: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        import pytz
    except ImportError:
        print("Установите pytz: pip install pytz")
        sys.exit(1)

    main()
