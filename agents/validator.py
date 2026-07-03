from models.llm_caller import call_llm, parse_json_response
from models.schemas import SceneJSON, DirectorPlan
from dataclasses import asdict
import json

SYSTEM_PROMPT_SCENE = """You are a Quality Control agent for a video production AI pipeline.

Your task: validate the Scene Analysis JSON produced by the Scene Analyzer agent.

Check for:
1. COMPLETENESS — are critical fields filled or marked "unknown" with reason?
2. CONSISTENCY — does the data make internal sense? (e.g., shallow depth of field matches telephoto lens)
3. HALLUCINATIONS — are there any invented details that seem too specific for a general analysis?
4. CRITICAL MISSING — are any fields that are essential for video generation left empty?

Critical fields that MUST be filled (not "unknown"):
- description, mood, composition, lighting_type, depth_of_field, exposure

Return ONLY valid JSON:
{
  "passed": true or false,
  "score": 0-100,
  "issues": ["list of specific issues found"],
  "warnings": ["list of non-critical warnings"],
  "suggestions": ["list of improvement suggestions"],
  "critical_missing": ["list of critical fields that are empty or unknown"]
}"""

SYSTEM_PROMPT_PROMPT = """You are a Quality Control agent specializing in AI video generation prompts.

Your task: validate the final video generation prompt for the specified platform.

Platform-specific rules:
- KLING: prefers detailed motion descriptions, supports Chinese aesthetic, max ~500 words
- VEO: Google's model, prefers cinematic language, shot types, precise technical terms
- SEEDANCE: prefers short punchy descriptions, strong action verbs, visual contrasts

Check for:
1. LENGTH — is the prompt appropriate length for the platform?
2. MOTION — does the prompt contain clear motion/movement instructions?
3. TECHNICAL — are camera and lighting terms present?
4. CLARITY — is it free of contradictions or ambiguous instructions?
5. PLATFORM FIT — does it match the platform's known preferences?

Return ONLY valid JSON:
{
  "passed": true or false,
  "score": 0-100,
  "platform": "platform name",
  "issues": ["list of specific issues"],
  "warnings": ["list of non-critical warnings"],
  "word_count": 0,
  "suggestions": ["improvement suggestions"]
}"""


def validate_scene(scene: SceneJSON) -> dict:
    """
    Валидирует выход Агента 1.
    Возвращает словарь с результатами валидации.
    """
    scene_data = json.dumps(asdict(scene), ensure_ascii=False, indent=2)

    user_text = f"""Validate this Scene Analysis JSON:

{scene_data}

Return validation result as JSON."""

    raw = call_llm(
        system_prompt=SYSTEM_PROMPT_SCENE,
        user_text=user_text
    )

    return parse_json_response(raw)


def validate_prompt(prompt: str, platform: str) -> dict:
    """
    Валидирует финальный промпт под конкретную платформу.
    Возвращает словарь с результатами валидации.
    """
    user_text = f"""Validate this video generation prompt for platform: {platform.upper()}

PROMPT:
{prompt}

Return validation result as JSON."""

    raw = call_llm(
        system_prompt=SYSTEM_PROMPT_PROMPT,
        user_text=user_text
    )

    return parse_json_response(raw)
