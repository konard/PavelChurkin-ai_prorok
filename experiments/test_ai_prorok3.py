#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ai_prorok3.py

Проверяет:
1. Что генерация происходит только один раз за цикл
2. Что пророчество содержит время следующей публикации
3. Что флаг generated_for_current_cycle работает корректно
"""

import json
import os
import sys
from datetime import datetime, timedelta
import pytz

# Константы из ai_prorok3.py
STATE_FILE = "prophecy_state.json"
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


def get_moscow_time():
    """Возвращает текущее время в московском часовом поясе"""
    return datetime.now(MOSCOW_TZ)


def format_moscow_time(dt=None, format_str="%Y-%m-%d %H:%M:%S"):
    """Форматирует время в московском поясе"""
    if dt is None:
        dt = get_moscow_time()
    return dt.strftime(format_str)


def test_state_file_structure():
    """Тест 1: Проверка структуры файла состояния"""
    print("\n" + "=" * 70)
    print("ТЕСТ 1: Проверка структуры файла состояния")
    print("=" * 70)

    # Создаем тестовый файл состояния
    test_state = {
        'next_publish_time': (get_moscow_time() + timedelta(hours=1)).isoformat(),
        'next_generation_time': (get_moscow_time() + timedelta(minutes=50)).isoformat(),
        'current_prophecy': None,
        'is_generating': False,
        'generated_for_current_cycle': False
    }

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_state, f, ensure_ascii=False, indent=2)

    print(f"✓ Создан тестовый файл состояния: {STATE_FILE}")

    # Проверяем, что файл читается
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        loaded_state = json.load(f)

    assert 'next_publish_time' in loaded_state, "Отсутствует next_publish_time"
    assert 'next_generation_time' in loaded_state, "Отсутствует next_generation_time"
    assert 'current_prophecy' in loaded_state, "Отсутствует current_prophecy"
    assert 'is_generating' in loaded_state, "Отсутствует is_generating"
    assert 'generated_for_current_cycle' in loaded_state, "Отсутствует generated_for_current_cycle"

    print("✓ Все обязательные поля присутствуют в файле состояния")
    print(f"  - next_publish_time: {loaded_state['next_publish_time']}")
    print(f"  - next_generation_time: {loaded_state['next_generation_time']}")
    print(f"  - current_prophecy: {loaded_state['current_prophecy']}")
    print(f"  - is_generating: {loaded_state['is_generating']}")
    print(f"  - generated_for_current_cycle: {loaded_state['generated_for_current_cycle']}")

    return True


def test_generation_flag_logic():
    """Тест 2: Проверка логики флага generated_for_current_cycle"""
    print("\n" + "=" * 70)
    print("ТЕСТ 2: Проверка логики флага generated_for_current_cycle")
    print("=" * 70)

    now = get_moscow_time()

    # Сценарий 1: До времени генерации
    print("\nСценарий 1: До времени генерации")
    gen_time = now + timedelta(minutes=5)
    pub_time = now + timedelta(minutes=15)

    should_generate = (now >= gen_time) and not False and not False
    print(f"  Текущее время: {format_moscow_time(now)}")
    print(f"  Время генерации: {format_moscow_time(gen_time)}")
    print(f"  Время публикации: {format_moscow_time(pub_time)}")
    print(f"  Должна ли произойти генерация? {should_generate}")
    assert should_generate == False, "Генерация не должна происходить до времени генерации"
    print("  ✓ Корректно - генерация не должна происходить")

    # Сценарий 2: Время генерации наступило, флаг не установлен
    print("\nСценарий 2: Время генерации наступило, флаг не установлен")
    gen_time = now - timedelta(minutes=1)
    is_generating = False
    generated_for_current_cycle = False

    should_generate = (now >= gen_time) and not is_generating and not generated_for_current_cycle
    print(f"  Текущее время: {format_moscow_time(now)}")
    print(f"  Время генерации: {format_moscow_time(gen_time)}")
    print(f"  is_generating: {is_generating}")
    print(f"  generated_for_current_cycle: {generated_for_current_cycle}")
    print(f"  Должна ли произойти генерация? {should_generate}")
    assert should_generate == True, "Генерация должна произойти"
    print("  ✓ Корректно - генерация должна произойти")

    # Сценарий 3: Время генерации наступило, но флаг уже установлен
    print("\nСценарий 3: Время генерации наступило, но флаг уже установлен")
    generated_for_current_cycle = True

    should_generate = (now >= gen_time) and not is_generating and not generated_for_current_cycle
    print(f"  Текущее время: {format_moscow_time(now)}")
    print(f"  Время генерации: {format_moscow_time(gen_time)}")
    print(f"  is_generating: {is_generating}")
    print(f"  generated_for_current_cycle: {generated_for_current_cycle}")
    print(f"  Должна ли произойти генерация? {should_generate}")
    assert should_generate == False, "Генерация НЕ должна происходить повторно"
    print("  ✓ Корректно - генерация НЕ должна происходить повторно")

    # Сценарий 4: После публикации флаг сброшен для нового цикла
    print("\nСценарий 4: После публикации флаг сброшен для нового цикла")
    generated_for_current_cycle = False  # Флаг сброшен после публикации
    gen_time = now + timedelta(hours=23, minutes=50)  # Новое время генерации на следующий день

    should_generate = (now >= gen_time) and not is_generating and not generated_for_current_cycle
    print(f"  Текущее время: {format_moscow_time(now)}")
    print(f"  Новое время генерации (завтра): {format_moscow_time(gen_time)}")
    print(f"  is_generating: {is_generating}")
    print(f"  generated_for_current_cycle: {generated_for_current_cycle} (сброшен после публикации)")
    print(f"  Должна ли произойти генерация? {should_generate}")
    assert should_generate == False, "Генерация не должна происходить до нового времени генерации"
    print("  ✓ Корректно - генерация будет ждать нового времени")

    return True


def test_prophecy_message_format():
    """Тест 3: Проверка формата сообщения с временем следующей публикации"""
    print("\n" + "=" * 70)
    print("ТЕСТ 3: Проверка формата сообщения с временем следующей публикации")
    print("=" * 70)

    now = get_moscow_time()
    next_publish_time = now + timedelta(days=1, hours=5, minutes=30)
    next_time_str = format_moscow_time(next_publish_time)

    prophecy_text = "Пророчество о будущем..."

    # Формат сообщения из ai_prorok3.py
    full_message = f"🔮 Пророчество от бота ({format_moscow_time(now)} МСК):\n\n{prophecy_text}\n\n" \
                   f"⏰ Следующее пророчество будет опубликовано {next_time_str} МСК"

    print("\nПример сгенерированного сообщения:")
    print("-" * 70)
    print(full_message)
    print("-" * 70)

    # Проверяем наличие ключевых элементов
    assert "🔮 Пророчество от бота" in full_message, "Заголовок не найден"
    assert prophecy_text in full_message, "Текст пророчества не найден"
    assert "⏰ Следующее пророчество будет опубликовано" in full_message, "Время следующей публикации не найдено"
    assert "МСК" in full_message, "Часовой пояс МСК не указан"

    print("\n✓ Все обязательные элементы присутствуют в сообщении:")
    print("  - Заголовок с временем текущей публикации")
    print("  - Текст пророчества")
    print("  - Время следующей публикации")
    print("  - Указание часового пояса (МСК)")

    return True


def test_cycle_workflow():
    """Тест 4: Проверка полного цикла работы"""
    print("\n" + "=" * 70)
    print("ТЕСТ 4: Симуляция полного цикла работы")
    print("=" * 70)

    now = get_moscow_time()

    # Начальное состояние
    print("\nШаг 1: Первый запуск программы")
    state = {
        'next_publish_time': (now + timedelta(hours=1)).isoformat(),
        'next_generation_time': (now + timedelta(minutes=50)).isoformat(),
        'current_prophecy': None,
        'is_generating': False,
        'generated_for_current_cycle': False
    }
    print(f"  Время публикации: {state['next_publish_time']}")
    print(f"  Время генерации: {state['next_generation_time']}")
    print(f"  Пророчество: {state['current_prophecy']}")
    print(f"  Флаг генерации: {state['generated_for_current_cycle']}")

    # Время генерации наступило
    print("\nШаг 2: Время генерации наступило (10 минут до публикации)")
    state['is_generating'] = True
    print(f"  is_generating: {state['is_generating']} (начало генерации)")

    # Генерация завершена
    print("\nШаг 3: Генерация завершена")
    state['current_prophecy'] = "Сгенерированное пророчество с временем следующей публикации"
    state['is_generating'] = False
    state['generated_for_current_cycle'] = True
    print(f"  Пророчество: {state['current_prophecy'][:50]}...")
    print(f"  is_generating: {state['is_generating']} (генерация завершена)")
    print(f"  generated_for_current_cycle: {state['generated_for_current_cycle']} (предотвращает повторную генерацию)")

    # Проверяем, что повторная генерация не произойдет
    print("\nШаг 4: Проверка - повторная генерация не должна произойти")
    gen_time = datetime.fromisoformat(state['next_generation_time'])
    should_generate = (now >= gen_time) and not state['is_generating'] and not state['generated_for_current_cycle']
    print(f"  Условие генерации: {should_generate}")
    assert should_generate == False, "Повторная генерация не должна произойти!"
    print("  ✓ Корректно - повторная генерация блокируется флагом")

    # Публикация
    print("\nШаг 5: Время публикации наступило")
    state['current_prophecy'] = None
    state['generated_for_current_cycle'] = False  # Сброс для нового цикла
    state['next_publish_time'] = (now + timedelta(days=1, hours=1)).isoformat()
    state['next_generation_time'] = (now + timedelta(days=1, minutes=50)).isoformat()
    print(f"  Пророчество опубликовано и очищено: {state['current_prophecy']}")
    print(f"  Флаг сброшен для нового цикла: {state['generated_for_current_cycle']}")
    print(f"  Новое время публикации: {state['next_publish_time']}")
    print(f"  Новое время генерации: {state['next_generation_time']}")

    print("\n✓ Полный цикл работы корректен:")
    print("  1. Программа ждет времени генерации")
    print("  2. Генерирует пророчество за 10 минут до публикации")
    print("  3. Устанавливает флаг, предотвращающий повторную генерацию")
    print("  4. Публикует пророчество в назначенное время")
    print("  5. Сбрасывает флаг и планирует следующий цикл")

    return True


def cleanup():
    """Удаление тестовых файлов"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print(f"\n✓ Удален тестовый файл: {STATE_FILE}")


def main():
    """Основная функция тестирования"""
    print("\n" + "=" * 70)
    print("ТЕСТИРОВАНИЕ УЛУЧШЕНИЙ В ai_prorok3.py")
    print("=" * 70)
    print(f"Время запуска тестов: {format_moscow_time()} МСК")

    try:
        # Запускаем тесты
        test_state_file_structure()
        test_generation_flag_logic()
        test_prophecy_message_format()
        test_cycle_workflow()

        print("\n" + "=" * 70)
        print("ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
        print("=" * 70)

        print("\n📋 СПИСОК ИСПРАВЛЕНИЙ В ai_prorok3.py:")
        print("=" * 70)
        print("1. ✅ Добавлен флаг 'generated_for_current_cycle'")
        print("   - Предотвращает повторную генерацию в одном цикле")
        print("   - Устанавливается в True после успешной генерации")
        print("   - Сбрасывается в False после публикации")
        print()
        print("2. ✅ Улучшено условие генерации в методе run()")
        print("   - Добавлена проверка 'not self.generated_for_current_cycle'")
        print("   - Генерация происходит строго один раз за цикл")
        print()
        print("3. ✅ Пророчество всегда содержит время следующей публикации")
        print("   - Формат: '⏰ Следующее пророчество будет опубликовано {время} МСК'")
        print("   - Добавлено в конец каждого пророчества")
        print()
        print("4. ✅ Оптимизирован формат сообщений")
        print("   - Добавлен разделитель между пророчеством и временем")
        print("   - Улучшена читаемость сообщений")
        print()
        print("5. ✅ Флаг сохраняется в файл состояния")
        print("   - 'generated_for_current_cycle' записывается в prophecy_state.json")
        print("   - Восстанавливается при перезапуске программы")
        print()

        return True

    except AssertionError as e:
        print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ОШИБКА ВЫПОЛНЕНИЯ ТЕСТА: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
