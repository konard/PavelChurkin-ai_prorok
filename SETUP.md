# Инструкция по установке AI Prorok на Ubuntu сервере

## Обзор решения

Новая версия бота разделяет процесс на два этапа:
1. **Генерация пророчества** - выполняется за 10 минут до публикации
2. **Публикация пророчества** - выполняется в запланированное время

Все времена и пророчества сохраняются в файлы состояния, что позволяет боту корректно работать после перезапуска сервера.

## Структура файлов

```
ai_prorok/
├── ai_prorok.py              # Оригинальный файл (оставлен для совместимости)
├── ai_prorok_refactored.py   # Новая версия с поддержкой перезапусков
├── scheduler.py              # Скрипт проверки времени
├── nouns.json                # Словарь существительных
├── verbs.json                # Словарь глаголов
├── adject.json               # Словарь прилагательных
├── requirements.txt          # Зависимости Python
├── .env                      # Переменные окружения (создать вручную)
├── state/                    # Директория состояния (создаётся автоматически)
│   ├── generation_time.txt   # Время следующей генерации
│   ├── publication_time.txt  # Время следующей публикации
│   ├── current_prophecy.txt  # Текущее пророчество
│   └── prophecy_metadata.json # Метаданные пророчества
├── systemd/                  # Файлы systemd
│   ├── ai-prorok-generate.service
│   ├── ai-prorok-generate.timer
│   ├── ai-prorok-publish.service
│   └── ai-prorok-publish.timer
└── prophecies_log.txt        # Лог всех пророчеств
```

## Шаг 1: Подготовка окружения

### 1.1. Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/PavelChurkin/ai_prorok.git
sudo chown -R $USER:$USER /opt/ai_prorok
cd /opt/ai_prorok
```

### 1.2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3. Настройка переменных окружения

Создайте файл `.env`:

```bash
nano .env
```

Содержимое файла:

```env
OPENAI_API_KEY=your_openai_api_key_here
VK_TOKEN=your_vk_token_here
TG_TOKEN=your_telegram_bot_token_here
```

Сохраните и закройте файл (Ctrl+O, Enter, Ctrl+X).

## Шаг 2: Первичная инициализация

Запланируйте первый цикл генерации и публикации:

```bash
source venv/bin/activate
python ai_prorok_refactored.py schedule
```

Эта команда создаст файлы в директории `state/` с временем следующей генерации и публикации.

## Шаг 3: Настройка systemd

### 3.1. Редактирование файлов сервисов

Отредактируйте файлы сервисов, заменив пути и пользователя:

```bash
cd systemd
nano ai-prorok-generate.service
```

Замените:
- `YOUR_USERNAME` → ваше имя пользователя (например, `ubuntu`)
- `YOUR_GROUP` → ваша группа (обычно совпадает с именем пользователя)
- `/path/to/ai_prorok` → `/opt/ai_prorok`
- `/path/to/venv` → `/opt/ai_prorok/venv`

Повторите для `ai-prorok-publish.service`.

### 3.2. Копирование файлов в systemd

```bash
sudo cp ai-prorok-generate.service /etc/systemd/system/
sudo cp ai-prorok-generate.timer /etc/systemd/system/
sudo cp ai-prorok-publish.service /etc/systemd/system/
sudo cp ai-prorok-publish.timer /etc/systemd/system/
```

### 3.3. Активация таймеров

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-prorok-generate.timer
sudo systemctl enable ai-prorok-publish.timer
sudo systemctl start ai-prorok-generate.timer
sudo systemctl start ai-prorok-publish.timer
```

## Шаг 4: Проверка работы

### 4.1. Статус таймеров

```bash
sudo systemctl status ai-prorok-generate.timer
sudo systemctl status ai-prorok-publish.timer
```

### 4.2. Просмотр логов

```bash
# Логи генерации
sudo journalctl -u ai-prorok-generate.service -f

# Логи публикации
sudo journalctl -u ai-prorok-publish.service -f

# Логи scheduler
sudo journalctl -t ai-prorok-generate -t ai-prorok-publish -f
```

### 4.3. Проверка состояния

```bash
cd /opt/ai_prorok
cat state/generation_time.txt
cat state/publication_time.txt
```

## Шаг 5: Ручное тестирование (опционально)

### 5.1. Тестирование генерации

```bash
cd /opt/ai_prorok
source venv/bin/activate

# Запланировать цикл
python ai_prorok_refactored.py schedule

# Сгенерировать пророчество
python ai_prorok_refactored.py generate

# Проверить результат
cat state/current_prophecy.txt
```

### 5.2. Тестирование публикации

```bash
# Опубликовать пророчество
python ai_prorok_refactored.py publish

# Проверить лог
tail -50 prophecies_log.txt
```

## Как это работает

### Механизм работы

1. **Инициализация** (`schedule`):
   - Вычисляется случайное время публикации на следующий день
   - Вычисляется время генерации (за 10 минут до публикации)
   - Времена сохраняются в `state/generation_time.txt` и `state/publication_time.txt`

2. **Генерация** (выполняется таймером каждую минуту):
   - Scheduler проверяет, наступило ли время генерации
   - Если да, генерируется пророчество с помощью OpenAI
   - Пророчество сохраняется в `state/current_prophecy.txt`
   - Время генерации логируется

3. **Публикация** (выполняется таймером каждую минуту):
   - Scheduler проверяет, наступило ли время публикации
   - Если да, загружается пророчество из файла
   - Пророчество публикуется в VK и Telegram
   - Планируется следующий цикл (новые времена генерации и публикации)
   - Файлы состояния очищаются

### Устойчивость к перезапускам

- Все критичные данные хранятся в файлах в директории `state/`
- При перезапуске сервера таймеры продолжат работу
- Scheduler будет проверять актуальные времена из файлов
- Если сервер перезапустился во время генерации/публикации, следующая проверка обнаружит, что время прошло, и выполнит действие

## Управление сервисом

### Остановка

```bash
sudo systemctl stop ai-prorok-generate.timer
sudo systemctl stop ai-prorok-publish.timer
```

### Запуск

```bash
sudo systemctl start ai-prorok-generate.timer
sudo systemctl start ai-prorok-publish.timer
```

### Перезапуск

```bash
sudo systemctl restart ai-prorok-generate.timer
sudo systemctl restart ai-prorok-publish.timer
```

### Отключение автозапуска

```bash
sudo systemctl disable ai-prorok-generate.timer
sudo systemctl disable ai-prorok-publish.timer
```

## Устранение неполадок

### Проблема: Таймер не запускается

```bash
sudo systemctl status ai-prorok-generate.timer
sudo journalctl -xe
```

Проверьте пути в файлах сервисов.

### Проблема: Сервис падает с ошибкой

```bash
sudo journalctl -u ai-prorok-generate.service -n 50
```

Проверьте:
- Существование файла `.env` с правильными ключами
- Права доступа к файлам
- Установлены ли все зависимости

### Проблема: Пророчество не публикуется

Проверьте:
1. Было ли сгенерировано пророчество: `cat state/current_prophecy.txt`
2. Логи публикации: `sudo journalctl -u ai-prorok-publish.service`
3. Токены VK и Telegram в `.env`

### Проблема: Время неправильное

Бот использует московское время (Europe/Moscow). Проверьте:

```bash
# Текущее время на сервере
date

# Время в Москве
TZ='Europe/Moscow' date

# Время в файлах состояния
cat state/generation_time.txt
cat state/publication_time.txt
```

## Дополнительная информация

### Логи пророчеств

Все пророчества сохраняются в `prophecies_log.txt` с временными метками.

### Ручное планирование

Можно вручную установить время генерации и публикации:

```bash
# Создайте файл state/publication_time.txt со временем в формате ISO 8601
echo "2025-11-30T15:30:00+03:00" > state/publication_time.txt
echo "2025-11-30T15:20:00+03:00" > state/generation_time.txt
```

### Мониторинг

Рекомендуется настроить мониторинг логов:

```bash
# Добавьте в crontab для отправки уведомлений при ошибках
*/10 * * * * journalctl -u ai-prorok-*.service --since "10 minutes ago" | grep ERROR && echo "Ошибка в AI Prorok" | mail -s "AI Prorok Alert" admin@example.com
```

## Заключение

После выполнения этих шагов бот будет автоматически:
1. Генерировать пророчества за 10 минут до публикации
2. Публиковать пророчества в запланированное время
3. Корректно восстанавливаться после перезапуска сервера
4. Планировать следующий цикл после каждой публикации
