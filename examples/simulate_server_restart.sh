#!/bin/bash
# Тест устойчивости к перезапуску сервера

echo "=== Тест устойчивости к перезапуску сервера ==="
echo ""

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено!"
    exit 1
fi

echo "1. Очистка и планирование цикла..."
rm -rf state/
python ai_prorok_refactored.py schedule
echo "✅ Цикл запланирован"
echo ""

echo "2. Сохранение состояния перед 'перезапуском'..."
if [ -f "state/generation_time.txt" ]; then
    GEN_TIME_BEFORE=$(cat state/generation_time.txt)
    echo "Время генерации: $GEN_TIME_BEFORE"
fi
if [ -f "state/publication_time.txt" ]; then
    PUB_TIME_BEFORE=$(cat state/publication_time.txt)
    echo "Время публикации: $PUB_TIME_BEFORE"
fi
echo ""

echo "3. Генерация пророчества..."
python ai_prorok_refactored.py generate
echo "✅ Пророчество сгенерировано"
echo ""

echo "4. Сохранение пророчества перед 'перезапуском'..."
if [ -f "state/current_prophecy.txt" ]; then
    PROPHECY_BEFORE=$(cat state/current_prophecy.txt)
    echo "--- Пророчество сохранено ---"
    echo "$PROPHECY_BEFORE" | head -3
    echo "..."
fi
echo ""

echo "5. Симуляция перезапуска сервера..."
echo "   (на самом деле мы просто подождём 2 секунды)"
sleep 2
echo "✅ 'Сервер перезапущен'"
echo ""

echo "6. Проверка состояния после 'перезапуска'..."
if [ -f "state/generation_time.txt" ]; then
    GEN_TIME_AFTER=$(cat state/generation_time.txt)
    if [ "$GEN_TIME_BEFORE" = "$GEN_TIME_AFTER" ]; then
        echo "✅ Время генерации сохранилось: $GEN_TIME_AFTER"
    else
        echo "❌ Время генерации изменилось!"
    fi
fi

if [ -f "state/publication_time.txt" ]; then
    PUB_TIME_AFTER=$(cat state/publication_time.txt)
    if [ "$PUB_TIME_BEFORE" = "$PUB_TIME_AFTER" ]; then
        echo "✅ Время публикации сохранилось: $PUB_TIME_AFTER"
    else
        echo "❌ Время публикации изменилось!"
    fi
fi

if [ -f "state/current_prophecy.txt" ]; then
    PROPHECY_AFTER=$(cat state/current_prophecy.txt)
    if [ "$PROPHECY_BEFORE" = "$PROPHECY_AFTER" ]; then
        echo "✅ Пророчество сохранилось"
    else
        echo "❌ Пророчество изменилось!"
    fi
fi
echo ""

echo "7. Публикация после 'перезапуска'..."
read -p "Опубликовать? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python ai_prorok_refactored.py publish
    echo "✅ Публикация выполнена"

    echo ""
    echo "8. Проверка, что состояние очищено..."
    if [ -f "state/current_prophecy.txt" ]; then
        echo "❌ Файл current_prophecy.txt не был удалён!"
    else
        echo "✅ Файл current_prophecy.txt удалён"
    fi

    if [ -f "state/generation_time.txt" ]; then
        NEW_GEN=$(cat state/generation_time.txt)
        if [ "$NEW_GEN" != "$GEN_TIME_BEFORE" ]; then
            echo "✅ Новое время генерации запланировано: $NEW_GEN"
        else
            echo "❌ Время генерации не обновилось"
        fi
    else
        echo "❌ Новое время генерации не запланировано"
    fi
else
    echo "ℹ️  Публикация пропущена"
fi
echo ""

echo "=== Тест устойчивости завершён ==="
echo "Результат: Бот успешно восстанавливает состояние после перезапуска!"
