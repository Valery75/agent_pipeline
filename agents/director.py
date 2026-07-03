from models.llm_caller import call_llm, parse_json_response
from models.schemas import SceneJSON, StoryboardJSON, DirectorPlan, KlingClip
from dataclasses import asdict
import json

# ─────────────────────────────────────────────────────────────────────────────
# GUARDRAILS — две группы, вставляются в разные места промпта
# ─────────────────────────────────────────────────────────────────────────────

# Группа 1: Тело и кожа — вставляется ПОСЛЕ описания действия персонажа
KLING_GUARDRAILS_BODY = (
    "Body and skin consistency: natural healthy body proportions maintained throughout movement, "
    "full healthy weight unchanged, no thinning or elongation during motion. "
    "No visible bones, no protruding ribs, no protruding collar bones, no visible hip bones. "
    "Soft natural muscle tone only, no exaggerated muscle definition, no visible veins. "
    "Consistent warm skin tone across all frames, no darkening, no color shift, "
    "no bronzing or bleaching during movement or camera angle changes. "
    "Consistent facial features and face geometry at all angles, no morphing, no distortion. "
    "Natural hand anatomy, correct finger count, no fused or missing fingers."
)

# Группа 2: Свет и экспозиция — вставляется ПОСЛЕ lighting_master в конце
KLING_GUARDRAILS_LIGHT = (
    "Lighting and exposure consistency: exposure level unchanged throughout clip, "
    "no flicker, no brightness shifts, no sudden darkening or overexposure. "
    "Lighting direction fixed — shadows fall consistently at the same angle across all frames. "
    "No shadow flickering or shadow direction changes during movement. "
    "Garment color unchanged throughout — no hue shift, no saturation change. "
    "Fabric pattern and texture consistent, no warping or distortion of clothing details. "
    "Smooth motion throughout, no smearing, no ghosting, no motion blur artifacts."
)


# ─────────────────────────────────────────────────────────────────────────────
# РЕЖИССЁРСКИЙ ПЛАН
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT_DIRECTOR = """You are a cinematographer specializing in fashion video for Kling AI Image-to-Video.

CRITICAL CONTEXT:
- The user provides a STARTING IMAGE. Kling uses it as frame 0 — it cannot be changed.
- Your job is to plan what happens AFTER frame 0, not describe frame 0 itself.
- Every clip continues from the last frame of the previous clip.
- Never invent a new starting position — always continue from where the character is.

YOUR ROLE:
1. Plan 2-3 clips that flow naturally from the starting image
2. Write lighting_master — one consistent lighting line for all clips
3. Define clip-by-clip breakdown: one action, one camera move per clip
4. Each clip must have a clip_starting_frame — what Kling sees at the start of THAT clip

CLIP RULES:
- Clip 1 starts from the provided starting_frame (from scene analysis)
- Clip 2 starts from the last frame of Clip 1
- Clip 3 starts from the last frame of Clip 2
- ONE camera movement per clip (dolly OR pan OR tilt OR static — never combined)
- ONE character action per clip
- Duration: 5-8 seconds per clip

DO NOT include character appearance descriptions in clips — the starting image locks appearance.
DO describe: movement, camera, environment reactions, fabric, lighting.

Return ONLY valid JSON:
{
  "lighting_master": "one sentence, max 25 words: light source + direction + quality + color temp — this will appear in every clip",
  "camera_movement": "overall camera arc across all clips",
  "camera_start_position": "camera position at frame 0",
  "camera_end_position": "camera position at final frame",
  "shot_types": "sequence e.g. MS → CU → MS",
  "character_movement": "overall character movement across full video",
  "character_start_position": "character at frame 0",
  "character_end_position": "character at final frame",
  "micro_movements": "micro-movements used throughout",
  "fabric_behavior": "how clothing moves across the video",
  "hair_behavior": "hair movement throughout",
  "wind": "wind presence, direction, strength",
  "eye_contact": "moments of eye contact with camera",
  "lighting_plan": "full lighting description",
  "color_grading": "color palette, contrast, film look",
  "transitions": "between-clip transitions",
  "focus_pulls": "focus changes",
  "depth_changes": "bokeh changes",
  "pacing_notes": "edit rhythm",
  "total_clips": 2,
  "total_duration": "12-18 seconds",
  "clips": [
    {
      "clip_number": 1,
      "duration_seconds": "5-7",
      "clip_starting_frame": "exact description of what Kling sees at start of this clip",
      "description": "what happens: first state → last state",
      "shot_type": "MS / CU / ECU / LS etc",
      "camera_movement": "one movement: type + direction + speed",
      "character_action": "one action: body part + movement + speed",
      "micro_movements": "breath + one other micro detail",
      "fabric_behavior": "how clothing moves in this clip",
      "lighting_note": "copy lighting_master here exactly",
      "last_frame": "exact description of the final frame — becomes clip_starting_frame for next clip"
    }
  ]
}"""

# ─────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАТОР ПРОМПТА ДЛЯ ОДНОГО KLING КЛИПА (Image-to-Video)
# ─────────────────────────────────────────────────────────────────────────────
KLING_CLIP_SYSTEM = """You write prompts for Kling AI in Image-to-Video mode.

CRITICAL: Frame 0 is already set by the uploaded image.
Your prompt describes ONLY what happens AFTER frame 0 — motion, action, camera, environment.
DO NOT describe who the character is or what they look like — the image handles that.

PROMPT STRUCTURE (follow this order):
1. SCENE ANCHOR (1 sentence): ground the starting position — where is the character, what surrounds them
2. CAMERA (1 sentence): one specific movement with direction and speed
3. CHARACTER ACTION (1-2 sentences): what the character does — specific body part, movement, speed
4. BODY GUARDRAILS (insert here — provided separately)
5. ENVIRONMENT RESPONSE (1 sentence): fabric, hair, surroundings reacting to the action
6. LIGHTING (1 sentence): the lighting_master line exactly as provided
7. LIGHT GUARDRAILS (insert here — provided separately)

LENGTH: 200-300 words. Do not cut content to meet a shorter limit — full detail produces better results.

WHAT WORKS IN KLING IMAGE-TO-VIDEO:
- Simple continuous actions: walking → stopping, reaching → touching, turning → facing camera
- Environmental reactions: fabric flutter, hair shift, water surface response, shadow movement
- Camera moves that feel like a natural observer: slow push in, gentle pan, static hold with subject moving
- Micro-movements that show life: breath lifting fabric, fingers releasing grip, weight shifting heel to heel

WHAT BREAKS KLING IMAGE-TO-VIDEO:
- Multiple unconnected actions in one clip
- Jump-cutting to a completely new position
- Describing appearance instead of movement
- Vague instructions like "she moves gracefully" — always specify body part and direction

OUTPUT: prompt text only. No JSON. No section headers. No word count note."""


# ─────────────────────────────────────────────────────────────────────────────
# ОСНОВНАЯ ФУНКЦИЯ
# ─────────────────────────────────────────────────────────────────────────────
def run(scene: SceneJSON, storyboard: StoryboardJSON, platform: str = "kling",
        action: dict = None, user_idea: str = None, logger=None) -> DirectorPlan:

    def _log(msg):
        if logger:
            logger(msg)

    scene_data = json.dumps(asdict(scene), ensure_ascii=False, indent=2)
    storyboard_data = json.dumps(asdict(storyboard), ensure_ascii=False, indent=2)

    # Блок действия — только если выбрано из банка
    action_block = ""
    if action and not user_idea:
        action_block = f"""
MANDATORY ACTION (assign to the most impactful clip):
Name: {action["name"]}
Execution: {action["description"]}

Build clips around this action. Other clips lead to or follow from it.
Execute exactly as described — do not soften or replace."""
    elif user_idea:
        action_block = f"""
USER'S IDEA FOR THE VIDEO:
{user_idea}

Interpret this idea literally and build clips around it.
Adapt it to the scene if needed, but keep the core intention intact."""

    _log("   → Шаг 1: Создаю режиссёрский план...")
    user_text = f"""Create a Director's Plan for Kling Image-to-Video.

STARTING IMAGE (this is frame 0 — the video begins exactly here):
{scene.starting_frame}

FULL SCENE ANALYSIS:
{scene_data}

STORYBOARD:
{storyboard_data}
{action_block}
Mode: Image-to-Video (frame 0 = uploaded image, cannot change)
Total: 2-3 clips, each 5-8 seconds
Rules: one action per clip, one camera move per clip, continue from previous clip's last frame

Return Director Plan as JSON."""

    raw = call_llm(system_prompt=SYSTEM_PROMPT_DIRECTOR, user_text=user_text)
    data = parse_json_response(raw)
    total_clips = len(data.get("clips", []))
    _log(f"   ✓ План: {total_clips} клипа, {data.get('total_duration', '?')}")

    plan = DirectorPlan(
        lighting_master=data.get("lighting_master", ""),
        camera_movement=data.get("camera_movement", ""),
        camera_start_position=data.get("camera_start_position", ""),
        camera_end_position=data.get("camera_end_position", ""),
        shot_types=data.get("shot_types", ""),
        character_movement=data.get("character_movement", ""),
        character_start_position=data.get("character_start_position", ""),
        character_end_position=data.get("character_end_position", ""),
        micro_movements=data.get("micro_movements", ""),
        fabric_behavior=data.get("fabric_behavior", ""),
        hair_behavior=data.get("hair_behavior", ""),
        wind=data.get("wind", ""),
        eye_contact=data.get("eye_contact", ""),
        lighting_plan=data.get("lighting_plan", ""),
        color_grading=data.get("color_grading", ""),
        transitions=data.get("transitions", ""),
        focus_pulls=data.get("focus_pulls", ""),
        depth_changes=data.get("depth_changes", ""),
        pacing_notes=data.get("pacing_notes", ""),
        total_clips=data.get("total_clips", total_clips),
        total_duration=data.get("total_duration", ""),
        platform="kling",
    )

    # Генерируем промпт для каждого клипа
    raw_clips = data.get("clips", [])
    kling_clips = []

    for clip_data in raw_clips:
        clip_num = clip_data.get("clip_number", len(kling_clips) + 1)
        _log(f"   → Шаг {clip_num + 1}: Промпт Clip {clip_num} "
             f"({clip_data.get('shot_type', '?')} / {clip_data.get('duration_seconds', '?')}s)...")

        clip = KlingClip(
            clip_number=clip_num,
            duration_seconds=clip_data.get("duration_seconds", "5-7"),
            description=clip_data.get("description", ""),
            shot_type=clip_data.get("shot_type", ""),
            camera_movement=clip_data.get("camera_movement", ""),
            character_action=clip_data.get("character_action", ""),
            micro_movements=clip_data.get("micro_movements", ""),
            fabric_behavior=clip_data.get("fabric_behavior", ""),
            lighting_note=clip_data.get("lighting_note", plan.lighting_master),
            clip_starting_frame=clip_data.get("clip_starting_frame", scene.starting_frame),
        )
        clip.prompt = _generate_clip_prompt(clip, plan)
        words = len(clip.prompt.split())
        _log(f"   ✓ Clip {clip_num} готов ({words} слов)")
        kling_clips.append(asdict(clip))

    plan.clips = kling_clips
    plan.total_clips = len(kling_clips)
    plan.prompt_kling = kling_clips[0]["prompt"] if kling_clips else ""
    plan.prompt_selected = _format_clips_for_display(kling_clips)

    return plan


def _generate_clip_prompt(clip: KlingClip, plan: DirectorPlan) -> str:
    """Генерирует Image-to-Video промпт для одного клипа с двумя группами guardrails."""
    user_text = f"""Write a Kling Image-to-Video prompt for Clip {clip.clip_number}.
Target length: 200-300 words. Do not cut content to be shorter.

CLIP STARTING FRAME:
{clip.clip_starting_frame}

THIS CLIP:
- Shot type: {clip.shot_type}
- Duration: {clip.duration_seconds} seconds
- Camera: {clip.camera_movement}
- Character action: {clip.character_action}
- Micro-movements: {clip.micro_movements}
- Fabric behavior: {clip.fabric_behavior}
- What happens: {clip.description}

BODY GUARDRAILS — insert after character action section:
{KLING_GUARDRAILS_BODY}

LIGHTING — insert near end:
{clip.lighting_note}

LIGHT GUARDRAILS — insert after lighting:
{KLING_GUARDRAILS_LIGHT}

Follow the structure: Scene Anchor → Camera → Character Action → Body Guardrails → Environment → Lighting → Light Guardrails.
No character appearance descriptions. No headers in output. Prompt text only."""

    return call_llm(system_prompt=KLING_CLIP_SYSTEM, user_text=user_text)


def _format_clips_for_display(clips: list) -> str:
    lines = []
    for c in clips:
        lines.append(
            f"━━━ CLIP {c['clip_number']} "
            f"({c['duration_seconds']}s | {c['shot_type']}) ━━━\n"
            f"{c['prompt']}"
        )
    return "\n\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# АВТО-ИСПРАВЛЕНИЕ
# ─────────────────────────────────────────────────────────────────────────────
def rewrite_prompt(platform: str, original_prompt: str, issues: list, suggestions: list,
                   scene_data: str, storyboard_data: str, director_data: dict) -> str:
    issues_text = "\n".join(f"- {i}" for i in issues)
    suggestions_text = "\n".join(f"- {s}" for s in suggestions)

    user_text = f"""The Kling Image-to-Video prompt was rejected by quality validator. Rewrite it.
Target length: 200-300 words.

ISSUES TO FIX:
{issues_text}

SUGGESTIONS:
{suggestions_text}

ORIGINAL PROMPT:
{original_prompt}

BODY GUARDRAILS (must appear after character action):
{KLING_GUARDRAILS_BODY}

LIGHT GUARDRAILS (must appear at the end):
{KLING_GUARDRAILS_LIGHT}

Fix all issues. Keep structure: Scene Anchor → Camera → Action → Body Guardrails → Environment → Lighting → Light Guardrails.
No character appearance descriptions. Prompt text only."""

    return call_llm(system_prompt=KLING_CLIP_SYSTEM, user_text=user_text)
