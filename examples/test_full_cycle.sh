#!/bin/bash
# Тест полного цикла: планирование -> генерация -> публикация

echo "=== Тест полного цикла AI Prorok ==="
echo ""

# Проверка окружения
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден! Создайте его сначала."
    exit 1
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено! Запустите: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

echo "1. Очистка предыдущего состояния..."
rm -rf state/
echo "✅ Состояние очищено"
echo ""

echo "2. Планирование следующего цикла..."
python ai_prorok_refactored.py schedule
if [ $? -eq 0 ]; then
    echo "✅ Цикл запланирован"
else
    echo "❌ Ошибка планирования"
    exit 1
fi
echo ""

echo "3. Просмотр запланированных времён..."
if [ -f "state/generation_time.txt" ]; then
    echo "Время генерации: $(cat state/generation_time.txt)"
fi
if [ -f "state/publication_time.txt" ]; then
    echo "Время публикации: $(cat state/publication_time.txt)"
fi
echo ""

echo "4. Генерация пророчества (игнорируя время)..."
python ai_prorok_refactored.py generate
if [ $? -eq 0 ]; then
    echo "✅ Пророчество сгенерировано"
else
    echo "❌ Ошибка генерации"
    exit 1
fi
echo ""

echo "5. Просмотр сгенерированного пророчества..."
if [ -f "state/current_prophecy.txt" ]; then
    echo "--- Пророчество ---"
    cat state/current_prophecy.txt
    echo "-------------------"
else
    echo "❌ Файл пророчества не найден"
    exit 1
fi
echo ""

echo "6. Публикация пророчества..."
read -p "Опубликовать в социальные сети? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python ai_prorok_refactored.py publish
    if [ $? -eq 0 ]; then
        echo "✅ Пророчество опубликовано"
    else
        echo "❌ Ошибка публикации"
        exit 1
    fi
else
    echo "ℹ️  Публикация пропущена"
fi
echo ""

echo "7. Проверка лога пророчеств..."
if [ -f "prophecies_log.txt" ]; then
    echo "--- Последние 20 строк лога ---"
    tail -20 prophecies_log.txt
    echo "-------------------------------"
else
    echo "⚠️  Лог не найден"
fi
echo ""

echo "=== Тест завершён успешно! ==="
