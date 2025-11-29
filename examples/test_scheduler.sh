#!/bin/bash
# Тест работы scheduler

echo "=== Тест Scheduler ==="
echo ""

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено!"
    exit 1
fi

echo "1. Установка времени генерации через 1 минуту..."
FUTURE_GEN=$(python3 -c "from datetime import datetime, timedelta; import pytz; print((datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(minutes=1)).isoformat())")
mkdir -p state
echo $FUTURE_GEN > state/generation_time.txt
echo "Время генерации установлено: $FUTURE_GEN"
echo ""

echo "2. Установка времени публикации через 2 минуты..."
FUTURE_PUB=$(python3 -c "from datetime import datetime, timedelta; import pytz; print((datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(minutes=2)).isoformat())")
echo $FUTURE_PUB > state/publication_time.txt
echo "Время публикации установлено: $FUTURE_PUB"
echo ""

echo "3. Проверка scheduler (check-generate)..."
python scheduler.py check-generate
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "✅ Scheduler говорит: пора генерировать"
else
    echo "ℹ️  Scheduler говорит: ещё не пора генерировать (код: $RESULT)"
fi
echo ""

echo "4. Проверка scheduler (check-publish)..."
python scheduler.py check-publish
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "✅ Scheduler говорит: пора публиковать"
else
    echo "ℹ️  Scheduler говорит: ещё не пора публиковать (код: $RESULT)"
fi
echo ""

echo "5. Ожидание 1 минуты..."
for i in {60..1}; do
    echo -ne "Осталось $i секунд...\r"
    sleep 1
done
echo ""
echo ""

echo "6. Повторная проверка scheduler (check-generate)..."
python scheduler.py check-generate
RESULT=$?
if [ $RESULT -eq 0 ]; then
    echo "✅ Scheduler говорит: пора генерировать!"
else
    echo "⚠️  Scheduler говорит: всё ещё не пора (код: $RESULT)"
fi
echo ""

echo "=== Тест Scheduler завершён ==="
