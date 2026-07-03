from models.llm_caller import call_llm, parse_json_response
from models.schemas import SceneJSON
from dataclasses import asdict
import json

# ─────────────────────────────────────────────────────────────────────────────
# БАЗОВЫЙ ПРОМПТ — неизменная часть для генерации стартового кадра
# ─────────────────────────────────────────────────────────────────────────────
BASE_IMAGE_PROMPT = """Generate a professional fashion campaign photograph.
The woman wears the exact swimsuit shown in the reference image.
PRIMARY OBJECTIVE: Preserve the exact identity, face, hairstyle, and facial proportions of the woman from the reference image.
Identity preservation is the highest priority in this image.
Character consistency takes precedence over pose, clothing, environment, lighting, composition, styling, and artistic interpretation.
Preserve all swimsuit construction details: identical cut, identical silhouette, identical fabric texture, identical stitching, identical trims and hardware, identical color and print.
The character should closely match the appearance, body proportions, hair color, age range, and overall visual style shown in the reference image."""

SYSTEM_PROMPT_STORY = """You are a creative director for fashion video campaigns. 
You specialize in short-form social media video (Reels, TikTok) for swimwear brands.

You receive a scene analysis of a reference photo and must create a compelling short film concept.

YOUR CREATIVE PHILOSOPHY:
- Every story emerges ORGANICALLY from what is already in the frame
- You never impose a template — a city terrace suggests different stories than a yacht or a beach
- Stories can include other characters: a man, a friend, a waiter, a stranger
- Unexpected elements create the best content: a delivery person rings the bell while she's in a swimsuit, she washes a Ferrari in a bikini, she tries swimwear on in a luxury hotel room
- The story has a clear beginning, middle, and surprising or satisfying end
- Each scene is 3-5 seconds — short, punchy, visual

STORY STRUCTURE:
- 5-6 scenes maximum
- Scene 1: establish the world and character
- Scenes 2-4: the story unfolds, something happens
- Scene 5-6: resolution, surprising final image, or memorable last frame

FORBIDDEN:
- Generic "she smiles at camera" scenes
- Wind in hair as a scene
- Deep breath as a scene  
- Any scene that is just a pose with no event
- Stories that could apply to any photo anywhere

REQUIRED:
- At least one unexpected element or event
- At least one scene with clear physical action
- At least one scene that would make someone stop scrolling

Return ONLY valid JSON:
{
  "story_title": "short catchy title for this story",
  "story_concept": "2-3 sentences describing the full story arc",
  "scenes": [
    {
      "scene_number": 1,
      "duration_seconds": 4,
      "title": "short scene title",
      "description": "what happens in this scene — specific, visual, physical",
      "location": "exact location for this scene",
      "new_characters": "any new characters entering this scene, or 'none'",
      "key_visual": "the single most striking visual moment of this scene",
      "camera": "camera position and movement for this scene",
      "mood": "emotional tone of this scene"
    }
  ]
}"""

SYSTEM_PROMPT_SCENE_PROMPTS = """You are an expert at writing prompts for AI image generation (Gemini, Google Flow, ChatGPT image) and Kling AI video generation.

You receive a story scene description and must write two prompts:
1. A prompt to generate the STARTING FRAME image for this scene
2. A Kling Image-to-Video prompt to animate that starting frame

STARTING FRAME PROMPT RULES:
- Start with the BASE_PROMPT (provided) — never modify it
- Add scene-specific details: location, pose, lighting, camera angle, mood, accessories, other characters if any
- Be specific about pose and position — this is what the image generator will create
- If there are new characters in this scene, describe them after the main character
- Natural language, no special tags needed (works for Gemini/Flow/ChatGPT)
- Length: 150-250 words total

KLING IMAGE-TO-VIDEO RULES:
- Frame 0 is already set by the starting image — DO NOT describe appearance
- Describe ONLY what happens AFTER frame 0: motion, action, camera, environment
- Duration: 3-5 seconds per clip
- ONE camera movement + ONE main action
- Include body/skin guardrails after action description
- Include lighting/exposure guardrails at the end
- Length: 100-180 words

BODY GUARDRAILS (insert after action):
Natural healthy body proportions maintained throughout, full healthy weight unchanged, no thinning during motion. No visible bones, no protruding ribs or collar bones. Soft natural muscle tone, no visible veins. Consistent warm skin tone, no darkening, no color shift. Consistent facial features at all angles, natural hand anatomy, correct finger count.

LIGHT GUARDRAILS (insert at end):
Exposure unchanged throughout, no flicker, no brightness shifts. Lighting direction fixed, shadows consistent. Garment color unchanged, no hue shift. Fabric texture consistent, no warping. Smooth motion, no smearing, no ghosting.

Return ONLY valid JSON:
{
  "scene_number": 1,
  "starting_frame_prompt": "full prompt for image generation",
  "kling_prompt": "full Kling Image-to-Video prompt"
}"""


def generate_story(scene: SceneJSON) -> dict:
    """
    Генерирует историю из 5-6 сцен на основе анализа референса.
    Возвращает dict с story_title, story_concept, scenes.
    """
    scene_data = json.dumps(asdict(scene), ensure_ascii=False, indent=2)

    user_text = f"""Look at this reference photo analysis and create a compelling short film story.

REFERENCE PHOTO ANALYSIS:
{scene_data}

STARTING FRAME: {scene.starting_frame}

Create a story that emerges ORGANICALLY from this specific image.
What world does this person inhabit? What could naturally happen here?
Think about: who else could appear, what unexpected event could occur,
what is the surprising or memorable last frame?

Return the story as JSON with 5-6 scenes of 3-5 seconds each."""

    raw = call_llm(system_prompt=SYSTEM_PROMPT_STORY, user_text=user_text)
    return parse_json_response(raw)


def generate_scene_prompts(scene_data: dict, base_prompt: str = BASE_IMAGE_PROMPT) -> dict:
    """
    Генерирует промпты для одной сцены:
    - промпт для генерации стартового кадра
    - промпт для Kling Image-to-Video
    """
    user_text = f"""Generate prompts for this scene.

BASE_PROMPT (use this at the start of starting_frame_prompt, unchanged):
{base_prompt}

SCENE:
{json.dumps(scene_data, ensure_ascii=False, indent=2)}

Write:
1. starting_frame_prompt: BASE_PROMPT + scene-specific details (location, pose, lighting, camera, mood, other characters if any)
2. kling_prompt: Kling Image-to-Video prompt (motion only, no appearance description)

Return as JSON."""

    raw = call_llm(system_prompt=SYSTEM_PROMPT_SCENE_PROMPTS, user_text=user_text)
    return parse_json_response(raw)


def format_story_for_approval(story: dict) -> str:
    """Форматирует историю для показа пользователю на одобрение."""
    lines = [
        f"🎬 *{story.get('story_title', 'История')}*\n",
        f"_{story.get('story_concept', '')}_\n"
    ]
    for scene in story.get("scenes", []):
        num = scene.get("scene_number", "?")
        title = scene.get("title", "")
        desc = scene.get("description", "")
        duration = scene.get("duration_seconds", 4)
        new_chars = scene.get("new_characters", "none")
        chars_note = f" _(+ {new_chars})_" if new_chars and new_chars != "none" else ""
        lines.append(f"*Сцена {num}* ({duration}с) — {title}{chars_note}\n{desc}\n")
    return "\n".join(lines)
