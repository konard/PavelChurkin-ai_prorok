import random
import json
import time
import asyncio
from openai import OpenAI
import os
from dotenv import load_dotenv
import vk_api
import requests
import logging
from typing import List, Tuple
from datetime import datetime, time as dt_time, timedelta
import pytz

"""

Генерация пророчества с отложенной публикацией
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

# Глобальный флаг для остановки
stop_flag = False

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


def get_moscow_time() -> datetime:
    """Возвращает текущее время в московском часовом поясе"""
    return datetime.now(MOSCOW_TZ)


def format_moscow_time(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматирует время в московском поясе"""
    if dt is None:
        dt = get_moscow_time()
    return dt.strftime(format_str)


def dct(my_dict: dict) -> dict:
    """Сортировка словаря по значениям в порядке убывания"""
    return {k: v for k, v in sorted(my_dict.items(), key=lambda item: item[1], reverse=True)}


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

    # Находим элементы, которые не попали в выборку
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
                wait_time = (attempt + 1) * 5
                logger.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
                time.sleep(wait_time)
            else:
                logger.error("Все попытки получить ответ от OpenAI провалились")
                return "Моя магия слов закончилась ровно там, где началась ваша надежда услышать нечто волшебное. Пророчествовать не буду, ибо моя хрустальная сфера сегодня затуманилась по техническим причинам."


async def async_input_listener():
    """Асинхронный слушатель ввода для остановки программы"""
    global stop_flag
    loop = asyncio.get_event_loop()

    while not stop_flag:
        try:
            # Используем асинхронный ввод
            user_input = await loop.run_in_executor(None, input, "Введите 'stop' для остановки программы: ")

            if user_input.strip().lower() in ['stop', '0', 'exit', 'quit']:
                logger.info("Получена команда остановки")
                stop_flag = True
                break

        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            logger.error(f"Ошибка ввода: {e}")
            await asyncio.sleep(1)


async def async_sleep_with_interrupt(seconds: int):
    """Асинхронный sleep с возможностью прерывания"""
    global stop_flag

    interval = 1  # Проверяем флаг каждую секунду
    total_intervals = seconds // interval

    for _ in range(total_intervals):
        if stop_flag:
            break
        await asyncio.sleep(interval)

    # Ждем оставшееся время
    remaining = seconds % interval
    if remaining > 0 and not stop_flag:
        await asyncio.sleep(remaining)


def calculate_next_run_time() -> Tuple[int, str]:
    """Вычисляет время следующего запуска в московском часовом поясе"""
    now_moscow = get_moscow_time()
    tomorrow = now_moscow + timedelta(days=1)

    # Начало и конец завтрашнего дня в московском времени
    start_of_day = MOSCOW_TZ.localize(datetime(
        tomorrow.year, tomorrow.month, tomorrow.day,
        0, 0, 0
    ))
    end_of_day = MOSCOW_TZ.localize(datetime(
        tomorrow.year, tomorrow.month, tomorrow.day,
        23, 59, 30  # минус 30 секунд
    ))

    start_timestamp = int(start_of_day.timestamp())
    end_timestamp = int(end_of_day.timestamp())

    timestamp = random.randint(start_timestamp, end_timestamp)

    # Конвертируем обратно в московское время для читаемого формата
    next_run_dt = datetime.fromtimestamp(timestamp, MOSCOW_TZ)
    readable_date = format_moscow_time(next_run_dt)

    wait_time = timestamp - int(now_moscow.timestamp()) - 10    # задержка 10 сек

    logger.info(f"Текущее время МСК: {format_moscow_time(now_moscow)}")
    logger.info(f"Следующий запуск МСК: {readable_date}")
    logger.info(f"Ожидание: {wait_time} секунд ({wait_time / 3600:.2f} часов)")

    return wait_time, readable_date


async def generate_prophecy_cycle():
    """Основной цикл генерации пророчеств"""
    global stop_flag

    # Загрузка словарей один раз при старте
    try:
        with open("nouns.json", "r", encoding='utf-8') as fh:
            nouns = json.load(fh)
        with open("verbs.json", "r", encoding='utf-8') as fh:
            verbs = json.load(fh)
        with open("adject.json", "r", encoding='utf-8') as fh:
            adjectives = json.load(fh)

        logger.info(
            f"Загружено: существительных - {len(nouns)}, глаголов - {len(verbs)}, прилагательных - {len(adjectives)}")
    except Exception as e:
        logger.error(f"Ошибка загрузки словарей: {e}")
        return

    cycle_count = 0

    while not stop_flag:
        try:
            cycle_count += 1
            current_time_moscow = format_moscow_time()
            logger.info(f"=== Цикл пророчества #{cycle_count} ({current_time_moscow} МСК) ===")

            # Генерация случайных выборок
            sample_size = random.randint(100, 20000)
            logger.info(f"Размер выборки: {sample_size}")

            # Создание случайных выборок
            noun_samples = [random.choice(nouns) for _ in range(sample_size)]
            verb_samples = [random.choice(verbs) for _ in range(sample_size)]
            adjective_samples = [random.choice(adjectives) for _ in range(sample_size)]

            # Анализ частотности с исправленной функцией
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

            # Логирование промпта с московским временем
            with open("prophecies_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"\n{format_moscow_time()}\n{prompt}\n{'+' * 50}\n")

            # Получение ответа от OpenAI
            prophecy = await asyncio.get_event_loop().run_in_executor(None, get_openai_response, prompt)

            # Вывод результата
            print("=" * 50)
            print("ПРОРОЧЕСТВО:")
            print(prophecy)
            print("=" * 50)

            # Вычисление времени следующего запуска
            wait_time, next_prophecy_time = calculate_next_run_time()

            logger.info(f"Следующее пророчество будет в: {next_prophecy_time} МСК (через {wait_time} секунд)")

            # Формирование сообщения для соцсетей с московским временем
            current_time_display = format_moscow_time()
            full_message = f"🔮 Пророчество от бота ({current_time_display} МСК):\n{prophecy}\n\nСледующее пророчество будет {next_prophecy_time} МСК"

            # Отправка в социальные сети
            success_count = 0
            if send_to_telegram(full_message):
                success_count += 1
            if send_to_vk(full_message):
                success_count += 1

            logger.info(f"Сообщение отправлено в {success_count} из 2 социальных сетей")

            # Логирование пророчества с московским временем
            with open("prophecies_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"Пророчество:\n{prophecy}\nВремя: {format_moscow_time()} МСК\n{'-' * 50}\n")

            # Асинхронное ожидание до следующего пророчества
            logger.info(f"Ожидание следующего пророчества...")
            await async_sleep_with_interrupt(wait_time)

            if stop_flag:
                logger.info("Цикл пророчеств остановлен по команде пользователя")
                break

        except Exception as e:
            logger.error(f"Ошибка в цикле пророчества: {e}")
            # В случае ошибки ждем 5 минут перед повторной попыткой
            await async_sleep_with_interrupt(300)


async def main():
    """Основная асинхронная функция"""
    global stop_flag

    logger.info("Запуск программы пророчеств (время МСК)...")
    logger.info(f"Текущее время на сервере: {format_moscow_time()} МСК")

    try:
        # Запускаем обе задачи параллельно
        await asyncio.gather(
            generate_prophecy_cycle(),
            async_input_listener()
        )
    except KeyboardInterrupt:
        logger.info("Программа остановлена по Ctrl+C")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        stop_flag = True
        logger.info("Программа завершена")


if __name__ == "__main__":
    # Убедимся, что pytz установлен
    try:
        import pytz
    except ImportError:
        print("Установите pytz: pip install pytz")
        exit(1)

    asyncio.run(main())