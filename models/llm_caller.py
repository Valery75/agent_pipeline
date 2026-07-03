import base64
import json
from pathlib import Path
import config


def encode_image(image_path: str) -> tuple[str, str]:
    """Кодирует изображение в base64 и определяет media_type"""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_type_map.get(suffix, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def call_llm(system_prompt: str, user_text: str, image_path: str = None) -> str:
    """
    Универсальный вызов LLM.
    Поддерживает OpenAI и Anthropic.
    Если передан image_path — отправляет изображение.
    Возвращает текст ответа.
    """
    client = config.get_llm_client()
    model = config.get_model_name()

    if config.LLM_PROVIDER == "openai":
        return _call_openai(client, model, system_prompt, user_text, image_path)
    else:
        return _call_anthropic(client, model, system_prompt, user_text, image_path)


def _call_openai(client, model: str, system_prompt: str, user_text: str, image_path: str = None) -> str:
    user_content = []

    if image_path:
        image_data, media_type = encode_image(image_path)
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{image_data}",
                "detail": "high"
            }
        })

    user_content.append({"type": "text", "text": user_text})

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(client, model: str, system_prompt: str, user_text: str, image_path: str = None) -> str:
    user_content = []

    if image_path:
        image_data, media_type = encode_image(image_path)
        user_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data,
            }
        })

    user_content.append({"type": "text", "text": user_text})

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
    )
    return response.content[0].text.strip()


def parse_json_response(raw: str) -> dict:
    """
    Извлекает JSON из ответа модели.
    Убирает markdown-обёртки типа ```json ... ```
    """
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Не удалось распарсить JSON из ответа модели.\nОшибка: {e}\nОтвет:\n{raw[:500]}")
