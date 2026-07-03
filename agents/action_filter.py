from models.llm_caller import call_llm, parse_json_response
from models.schemas import SceneJSON
from agents.actions_bank import get_all_actions
from dataclasses import asdict
import json

SYSTEM_PROMPT = """You are a creative director reviewing a list of possible actions for a fashion video.

You receive:
1. A scene analysis JSON — what is in the image (location, pose, clothing, props, environment)
2. A full list of possible actions numbered 1-N

Your task: select 6-10 actions that are PHYSICALLY POSSIBLE and VISUALLY INTERESTING given this exact scene.

FILTERING RULES:
- The character must be able to perform this action from their current position/pose
- The action must make sense in this location and environment
- Props must be available or naturally acquirable in this scene
- Prefer actions that create CONTRAST with the starting frame (movement vs stillness, etc.)
- If the scene is outdoors near water → water actions are valid
- If the character is standing → lying down actions require transition (include if interesting)
- If the character is already walking → movement actions are natural continuations
- If there are environmental props (bags, hats, fabric) → actions using them are preferred

ADAPTATION NOTE: Some actions need environmental adaptation.
Example: "Кормит птиц" near the sea → seagull catching bread mid-air, not pigeon on ground.
Note such adaptations in your reasoning.

Return ONLY valid JSON:
{
  "selected_indices": [1, 5, 12, 18, 23],
  "reasoning": {
    "1": "Character is walking — running is natural continuation",
    "5": "Sarong wrap visible — removing it is physically possible and visually interesting"
  },
  "adaptations": {
    "23": "Кормит птиц — adapt to seagull catching bread mid-air (sea location)"
  }
}"""


def filter_actions(scene: SceneJSON) -> list[dict]:
    """
    Фильтрует банк действий под конкретную сцену.
    Возвращает список подходящих действий с адаптациями.
    """
    all_actions = get_all_actions()
    scene_data = json.dumps(asdict(scene), ensure_ascii=False, indent=2)

    # Формируем нумерованный список для модели
    actions_list = "\n".join(
        f"{i+1}. [{a['category']}] {a['name']}: {a['description'][:120]}"
        for i, a in enumerate(all_actions)
    )

    user_text = f"""Filter this action list for the given scene.

SCENE ANALYSIS:
{scene_data}

AVAILABLE ACTIONS:
{actions_list}

Select 6-10 actions that are physically possible and visually interesting for this exact scene.
Return JSON with selected_indices (1-based), reasoning, and adaptations."""

    raw = call_llm(system_prompt=SYSTEM_PROMPT, user_text=user_text)
    data = parse_json_response(raw)

    selected_indices = data.get("selected_indices", [])
    adaptations = data.get("adaptations", {})

    result = []
    for idx in selected_indices:
        if 1 <= idx <= len(all_actions):
            action = dict(all_actions[idx - 1])
            action["original_index"] = idx
            # Применяем адаптацию если есть
            adaptation = adaptations.get(str(idx), "")
            if adaptation:
                action["adaptation"] = adaptation
                # Добавляем адаптацию к описанию для агентов
                action["description"] = f"{action['description']} SCENE ADAPTATION: {adaptation}"
            result.append(action)

    return result
