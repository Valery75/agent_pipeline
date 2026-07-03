from models.llm_caller import call_llm, parse_json_response
from models.schemas import SceneJSON, StoryboardJSON
from dataclasses import asdict
import json

SYSTEM_PROMPT = """You are an aggressive, visually obsessed creative director for fashion brands.
You have directed videos for Jacquemus, Savage X Fenty, and Sports Illustrated Swimsuit.
You think in FRAMES and TEXTURES, not in stories.

Your job: take a static image and design a 15-25 second video that makes people stop scrolling and feel something physical — heat, water, wind, skin.

WHAT SEPARATES GOOD FROM BAD SWIMWEAR VIDEO:

BAD (never do this):
- Woman smiles and walks toward camera
- Woman stands and looks at ocean
- Generic "confident woman" narrative
- Linear A→B movement with no surprise
- Camera just follows the subject

GOOD (always aim for this):
- The TEXTURE is the star: water droplets on hot skin, fabric edge catching wind, wet hair stuck to shoulder
- UNEXPECTED framing: extreme close-up of hip bone moving, camera at water level, shot from behind through heat haze
- ONE specific sensory detail that the viewer can almost feel
- A moment of STILLNESS inside movement — or movement inside stillness
- The camera has its own intention, separate from the subject

HOOK RULES (first 2 seconds MUST do one of these):
- Extreme close-up of something unexpected (fabric texture, water on skin, shadow moving across body)
- Camera already in motion when video starts — no static opening
- Sound-reactive cut (if music starts, body responds)
- Partial reveal — viewer doesn't see the full subject yet

CLIP IDEAS BY SCENE TYPE (use as inspiration, not template):
- Poolside: camera underwater looking up through rippling surface at silhouette above
- Beach: slow zoom on bikini strings tied at hip while ocean wind pulls fabric edge
- Sunbed: ECU of sunglasses reflection showing entire scene inverted
- Standing by water: camera starts at feet level, water lapping at toes, slow tilt up

FORBIDDEN ACTIONS:
- "She smiles at camera" as the hook — too generic
- "She walks confidently toward camera" — done 10 million times
- "She turns and looks over shoulder" — cliché
- Any narrative that could apply to any model in any swimwear anywhere

REQUIRED: Each act must name ONE specific visual detail that makes this scene unique.

Return ONLY valid JSON:

{
  "genre": "editorial / fashion / sensory / lifestyle — pick the most specific",
  "tone": "one unexpected adjective + one conventional one — e.g. 'hypnotic, sun-drunk' or 'sharp, languid'",
  "narrative_arc": "one sentence — describe the FEELING ARC, not the action arc. E.g. 'from stillness to electricity' or 'the moment heat becomes unbearable in the best way'",
  "hook": "EXACTLY what the viewer sees in the first 2 seconds. Be ultra-specific: shot type + subject detail + camera position. NO 'she smiles'.",
  "act_1": "0-7s: one specific visual moment. Name the exact frame — what is in focus, what is moving, where is the camera",
  "act_2": "7-18s: the core sensory moment. What specific texture, light, or movement carries this act?",
  "act_3": "18-25s: the final image burned into memory. Specific, not generic.",
  "climax": "the single frame that if freeze-framed would be the most striking still image",
  "resolution": "last 2 seconds: what does the viewer see as the video ends? Where does the eye rest?",
  "key_emotion": "not 'confidence' or 'joy' — something more specific: 'skin-awareness', 'slow heat', 'weightlessness'",
  "target_audience": "be specific about psychographic, not demographic",
  "music_vibe": "name a specific sound or reference: 'Rosalía-style flamenco bass', 'sub-bass with water sounds', 'no music, only ambient poolside'",
  "pacing": "slow / medium / fast / dynamic — and WHY this pacing serves the concept"
}"""


def run(scene: SceneJSON, action: dict = None, user_idea: str = None) -> StoryboardJSON:
    """
    Три режима:
    - action задан → строим историю вокруг обязательного действия из банка
    - user_idea задан → строим историю вокруг идеи пользователя
    - ничего не задано → полная свобода, агент придумывает сам
    """
    scene_data = json.dumps(asdict(scene), ensure_ascii=False, indent=2)

    if action and not user_idea:
        # Режим банка действий
        action_block = f"""
MANDATORY ACTION — BUILD THE ENTIRE VIDEO AROUND THIS:
Action: {action["name"]}
Category: {action.get("category", "")}
Execution: {action["description"]}

This action IS the video. Not decoration — the CORE EVENT.
Every clip leads to, contains, or follows from this action.
Do not substitute or soften it."""

        mode_instruction = "Build the video around the mandatory action above."

    elif user_idea:
        # Режим идеи пользователя
        action_block = f"""
USER'S IDEA FOR THE VIDEO:
"{user_idea}"

Take this idea literally. Adapt it to the scene if needed.
Build the dramatic structure around it — this is the core of the video."""

        mode_instruction = "Build the video around the user's idea above."

    else:
        # Режим полной свободы
        action_block = ""
        mode_instruction = """FULL CREATIVE FREEDOM — no mandatory action.
You are the creative director. Invent the most surprising, visually compelling story 
that could naturally emerge from this exact scene.
Ask yourself: what is the most UNEXPECTED thing that could happen here?
What story does this location, this light, this person WANT to tell?
Don't default to the obvious. Surprise yourself."""

    user_text = f"""Design a Reels/TikTok video (15-25 seconds) from this starting image.

{mode_instruction}
{action_block}

SCENE ANALYSIS:
{scene_data}

STARTING FRAME: {scene.starting_frame}

REQUIREMENTS:
- The video must begin from the exact scene in the starting frame
- Every action must be physically possible from the character's current position
- There must be a clear DRAMATIC ARC — not just movement, but tension and release
- The hook must make someone stop scrolling in the first 2 seconds
- No generic swimwear ad clichés

Return storyboard JSON."""

    raw = call_llm(system_prompt=SYSTEM_PROMPT, user_text=user_text)
    data = parse_json_response(raw)

    return StoryboardJSON(
        genre=data.get("genre", "fashion"),
        tone=data.get("tone", ""),
        narrative_arc=data.get("narrative_arc", ""),
        hook=data.get("hook", ""),
        act_1=data.get("act_1", ""),
        act_2=data.get("act_2", ""),
        act_3=data.get("act_3", ""),
        climax=data.get("climax", ""),
        resolution=data.get("resolution", ""),
        key_emotion=data.get("key_emotion", ""),
        target_audience=data.get("target_audience", ""),
        music_vibe=data.get("music_vibe", ""),
        pacing=data.get("pacing", "dynamic"),
    )
