# 🎬 Video Prompt Pipeline

Система из 4 AI-агентов для автоматической генерации промптов видео по одному изображению.

## Архитектура

```
Изображение
    │
    ▼
Агент 1: Scene Analyzer     → JSON описание сцены
    │
    ▼
Агент 0: Validator          → Проверка качества
    │
    ▼
Агент 2: Storyboard Writer  → Сценарий ролика
    │
    ▼
Агент 3: Director           → Режиссёрский план + промпты
    │
    ▼
Агент 0: Validator          → Проверка финального промпта
    │
    ▼
Финальный промпт (Kling / Veo / Seedance)
```

## Установка

### 1. Создайте виртуальное окружение

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте .env файл

```bash
cp .env.example .env
```

Откройте `.env` и заполните:

```
LLM_PROVIDER=openai          # или anthropic
OPENAI_API_KEY=sk-...        # если используете OpenAI
ANTHROPIC_API_KEY=sk-ant-... # если используете Anthropic
```

## Запуск

```bash
# Вариант 1: путь к изображению через аргумент
python main.py /путь/к/фото.jpg

# Вариант 2: интерактивный ввод
python main.py
```

После запуска система спросит:
1. Путь к изображению (если не передан аргументом)
2. Платформу: Kling / Veo / Seedance

## Результат

- Вывод в консоль с разбивкой по агентам
- JSON файл в папке `outputs/` с полными данными всех агентов

## Структура проекта

```
agent_pipeline/
├── main.py              # Точка входа
├── config.py            # Настройки и LLM клиент
├── requirements.txt
├── .env.example
├── agents/
│   ├── producer.py      # Оркестратор
│   ├── analyzer.py      # Агент 1: Scene Analyzer
│   ├── validator.py     # Агент 0: Validator
│   ├── storyboard.py    # Агент 2: Storyboard Writer
│   └── director.py      # Агент 3: Director + Prompt Generator
├── models/
│   ├── schemas.py       # Датаклассы JSON-схем
│   └── llm_caller.py    # Универсальный вызов LLM
└── outputs/             # Сохранённые результаты
```

## Переключение между OpenAI и Anthropic

В файле `.env`:

```
# Для OpenAI (рекомендуется: GPT-4o умеет видеть изображения)
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o

# Для Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-opus-4-6
```

## Требования

- Python 3.10+
- API ключ OpenAI или Anthropic
- Изображение JPG / PNG / WebP
"# agent_pipeline" 
