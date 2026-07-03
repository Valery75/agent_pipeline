import asyncio
import logging
import os
import sys
import json
import tempfile
from pathlib import Path
from dataclasses import asdict

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from agents import analyzer as _analyzer
from agents import narrator as _narrator
from models.schemas import SceneJSON, ScenePrompts, FullStory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ─────────────────────────────────────────────────────────────────────────────
# FSM состояния
# ─────────────────────────────────────────────────────────────────────────────
class Film(StatesGroup):
    waiting_photo       = State()
    choosing_provider   = State()
    reviewing_story     = State()
    editing_story       = State()
    generating_prompts  = State()


# ─────────────────────────────────────────────────────────────────────────────
# Клавиатуры
# ─────────────────────────────────────────────────────────────────────────────
def kb_provider() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="OpenAI GPT-4o",   callback_data="prov:openai"),
        InlineKeyboardButton(text="Anthropic Claude", callback_data="prov:anthropic"),
    ]])


def kb_story_review() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить — генерировать промпты", callback_data="story:approve")],
        [InlineKeyboardButton(text="✏️ Написать свою историю",           callback_data="story:edit")],
        [InlineKeyboardButton(text="🔄 Придумать другую историю",        callback_data="story:regenerate")],
    ])


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Film.waiting_photo)
    await message.answer(
        "🎬 <b>Swimwear Video Campaign Generator</b>\n\n"
        "Отправь референс фото — я придумаю историю и создам промпты "
        "для каждой сцены (генерация стартового кадра + Kling).\n\n"
        "📸 Жду фото...",
        parse_mode="HTML"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Получение фото
# ─────────────────────────────────────────────────────────────────────────────
@dp.message(Film.waiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    tmp_dir = Path(tempfile.mkdtemp())
    img_path = tmp_dir / "reference.jpg"
    await bot.download_file(file.file_path, destination=str(img_path))
    await state.update_data(image_path=str(img_path))

    await message.answer(
        "✅ Референс получен!\n\nВыбери AI провайдера:",
        reply_markup=kb_provider()
    )
    await state.set_state(Film.choosing_provider)


@dp.message(Film.waiting_photo)
async def no_photo(message: Message):
    await message.answer("📸 Пожалуйста, отправь фотографию.")


# ─────────────────────────────────────────────────────────────────────────────
# Выбор провайдера → анализ → генерация истории
# ─────────────────────────────────────────────────────────────────────────────
@dp.callback_query(Film.choosing_provider, F.data.startswith("prov:"))
async def choose_provider(callback: CallbackQuery, state: FSMContext):
    provider = callback.data.split(":")[1]
    config.LLM_PROVIDER = provider
    provider_name = "OpenAI GPT-4o" if provider == "openai" else "Anthropic Claude"

    await callback.message.edit_text(
        f"✅ Провайдер: <b>{provider_name}</b>\n\n"
        f"🔍 Анализирую референс...",
        parse_mode="HTML"
    )

    data = await state.get_data()
    image_path = data["image_path"]

    try:
        # Анализ сцены
        scene = await asyncio.to_thread(_analyzer.run, image_path)
        await state.update_data(scene_dict=asdict(scene))

        await callback.message.edit_text(
            f"✅ Провайдер: <b>{provider_name}</b>\n"
            f"✅ Референс проанализирован\n\n"
            f"📍 <i>{scene.starting_frame[:150]}</i>\n\n"
            f"✍️ Придумываю историю...",
            parse_mode="HTML"
        )

        # Генерация истории
        story = await asyncio.to_thread(_narrator.generate_story, scene)
        await state.update_data(story=story)

        # Показываем историю на одобрение
        story_text = _narrator.format_story_for_approval(story)
        await callback.message.edit_text(
            f"🎬 <b>Предлагаю историю:</b>\n\n{story_text}\n\n"
            f"Что делаем?",
            parse_mode="Markdown",
            reply_markup=kb_story_review()
        )
        await state.set_state(Film.reviewing_story)

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await callback.message.edit_text(
            f"❌ Ошибка:\n<code>{str(e)[:300]}</code>",
            parse_mode="HTML"
        )
        await state.set_state(Film.waiting_photo)

    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# Одобрение / правка истории
# ─────────────────────────────────────────────────────────────────────────────
@dp.callback_query(Film.reviewing_story, F.data.startswith("story:"))
async def handle_story_decision(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "approve":
        await callback.message.edit_text(
            "✅ История одобрена!\n\n"
            "⏳ Генерирую промпты для каждой сцены...\n"
            "<i>Это займёт 1-2 минуты</i>",
            parse_mode="HTML"
        )
        await state.set_state(Film.generating_prompts)
        await generate_all_prompts(callback.message, state)

    elif action == "edit":
        await callback.message.edit_text(
            "✏️ <b>Напиши свою версию истории</b>\n\n"
            "Опиши сценами что должно происходить.\n"
            "Например:\n"
            "<i>Сцена 1: она стоит у штурвала яхты\n"
            "Сцена 2: на горизонте появляется парусник\n"
            "Сцена 3: она машет рукой с борта\n"
            "...</i>",
            parse_mode="HTML"
        )
        await state.set_state(Film.editing_story)

    elif action == "regenerate":
        await callback.message.edit_text(
            "🔄 Придумываю другую историю...",
            parse_mode="HTML"
        )
        data = await state.get_data()
        scene_dict = data["scene_dict"]
        scene = SceneJSON(**{k: v for k, v in scene_dict.items()
                             if k in SceneJSON.__dataclass_fields__})
        try:
            story = await asyncio.to_thread(_narrator.generate_story, scene)
            await state.update_data(story=story)
            story_text = _narrator.format_story_for_approval(story)
            await callback.message.edit_text(
                f"🎬 <b>Новая история:</b>\n\n{story_text}\n\nЧто делаем?",
                parse_mode="Markdown",
                reply_markup=kb_story_review()
            )
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {str(e)[:200]}", parse_mode="HTML")

    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# Ввод своей истории
# ─────────────────────────────────────────────────────────────────────────────
@dp.message(Film.editing_story)
async def handle_custom_story(message: Message, state: FSMContext):
    custom_text = message.text.strip()
    if not custom_text:
        await message.answer("Напиши историю текстом.")
        return

    # Парсим пользовательский текст в структуру сцен
    data = await state.get_data()
    scene_dict = data["scene_dict"]
    scene = SceneJSON(**{k: v for k, v in scene_dict.items()
                         if k in SceneJSON.__dataclass_fields__})

    status = await message.answer(
        "✅ Принято! Преобразую в сценарий...",
        parse_mode="HTML"
    )

    # Просим агента структурировать пользовательский текст
    try:
        from models.llm_caller import call_llm, parse_json_response
        system = """Convert the user's story description into a structured scene JSON.
The user has described scenes in free text. Structure them properly.
Return JSON with: story_title, story_concept, scenes (array with scene_number, duration_seconds=4, 
title, description, location, new_characters, key_visual, camera, mood)"""

        user_text = f"""Reference scene: {scene.starting_frame}

User's story:
{custom_text}

Structure this into 5-6 scenes as JSON."""

        raw = await asyncio.to_thread(call_llm, system, user_text)
        story = parse_json_response(raw)
        await state.update_data(story=story)

        story_text = _narrator.format_story_for_approval(story)
        await status.edit_text(
            f"📋 <b>Твоя история структурирована:</b>\n\n{story_text}\n\nГенерирую промпты...",
            parse_mode="Markdown"
        )
        await state.set_state(Film.generating_prompts)
        await generate_all_prompts(status, state)

    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {str(e)[:200]}", parse_mode="HTML")
        await state.set_state(Film.waiting_photo)


# ─────────────────────────────────────────────────────────────────────────────
# Генерация промптов для всех сцен
# ─────────────────────────────────────────────────────────────────────────────
async def generate_all_prompts(message: Message, state: FSMContext):
    data = await state.get_data()
    story = data["story"]
    scenes = story.get("scenes", [])
    total = len(scenes)

    results = []

    for i, scene_data in enumerate(scenes, 1):
        # Обновляем прогресс
        await message.edit_text(
            f"⏳ Генерирую промпты: сцена {i}/{total}...\n"
            f"<i>{scene_data.get('title', '')}</i>",
            parse_mode="HTML"
        )

        try:
            prompts = await asyncio.to_thread(
                _narrator.generate_scene_prompts, scene_data
            )
            results.append({
                "scene_number": scene_data.get("scene_number", i),
                "title": scene_data.get("title", ""),
                "description": scene_data.get("description", ""),
                "duration_seconds": scene_data.get("duration_seconds", 4),
                "new_characters": scene_data.get("new_characters", "none"),
                "key_visual": scene_data.get("key_visual", ""),
                "starting_frame_prompt": prompts.get("starting_frame_prompt", ""),
                "kling_prompt": prompts.get("kling_prompt", ""),
            })
        except Exception as e:
            logger.error(f"Ошибка сцены {i}: {e}", exc_info=True)
            results.append({
                "scene_number": i,
                "title": scene_data.get("title", ""),
                "error": str(e),
                "starting_frame_prompt": "",
                "kling_prompt": "",
            })

        await asyncio.sleep(0.5)

    # Отправляем результаты
    await message.edit_text(
        f"✅ <b>Все промпты готовы!</b>\n\n"
        f"🎬 <b>{story.get('story_title', 'История')}</b>\n"
        f"_{story.get('story_concept', '')}_",
        parse_mode="HTML"
    )

    # Отправляем каждую сцену отдельным сообщением
    for r in results:
        num = r.get("scene_number", "?")
        title = r.get("title", "")
        desc = r.get("description", "")
        duration = r.get("duration_seconds", 4)
        new_chars = r.get("new_characters", "none")
        key_visual = r.get("key_visual", "")

        chars_line = f"\n👥 <i>Новые персонажи: {new_chars}</i>" if new_chars and new_chars != "none" else ""
        error = r.get("error", "")

        if error:
            await message.answer(
                f"🎬 <b>СЦЕНА {num}</b> — {title}\n❌ Ошибка: {error}",
                parse_mode="HTML"
            )
            continue

        img_prompt = r.get("starting_frame_prompt", "")
        kling_prompt = r.get("kling_prompt", "")

        await message.answer(
            f"🎬 <b>СЦЕНА {num}</b> ({duration}с) — {title}\n"
            f"<i>{desc}</i>{chars_line}\n"
            f"🎯 <i>{key_visual}</i>",
            parse_mode="HTML"
        )

        await message.answer(
            f"🖼 <b>Промпт генерации стартового кадра:</b>\n\n"
            f"<code>{img_prompt}</code>",
            parse_mode="HTML"
        )

        await message.answer(
            f"🎥 <b>Промпт Kling Image-to-Video:</b>\n\n"
            f"<code>{kling_prompt}</code>",
            parse_mode="HTML"
        )

        await asyncio.sleep(0.3)

    # Финал
    new_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Новый референс", callback_data="new_session")
    ]])
    await message.answer(
        "✅ Готово!\n\n"
        "Используй промпты:\n"
        "1️⃣ Генерируй стартовый кадр в Gemini/Flow/ChatGPT\n"
        "2️⃣ Загружай кадр в Kling как Image-to-Video\n"
        "3️⃣ Вставляй промпт Kling\n"
        "4️⃣ Монтируй сцены в DaVinci",
        reply_markup=new_kb
    )
    await state.set_state(Film.waiting_photo)


# ─────────────────────────────────────────────────────────────────────────────
# Новая сессия
# ─────────────────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "new_session")
async def new_session(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(Film.waiting_photo)
    await callback.message.edit_text("📸 Отправь новый референс фото.")
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────────────────────────────────────
async def main():
    logger.info(f"Бот запущен. Провайдер: {config.LLM_PROVIDER}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
