from models.llm_caller import call_llm, parse_json_response
from models.schemas import SceneJSON

SYSTEM_PROMPT = """You are a professional cinematographer and photographer acting as a Scene Analyzer.

Your task: analyze the provided image and return a detailed structured description in JSON format.

STRICT RULES:
- Describe ONLY what is actually visible in the image. Do NOT invent or assume details.
- If a parameter cannot be determined from the image, set its value to "unknown".
- For any field you cannot determine, add the field name to the "unknown_fields" array.
- Be precise and technical, as a cinematographer would describe a shot.
- All values must be strings (or boolean for subject_present, list for unknown_fields).

IMPORTANT — starting_frame:
This field is critical. It must describe the image in ONE sentence as if telling Kling:
"This video begins with [exact description of what is visible]"
Example: "A woman in a charcoal bikini and sarong walks along a sunlit stone promenade toward camera, 
straw tote over right shoulder, Mediterranean sea visible to the left"
This is used as the opening anchor for Image-to-Video generation.

Return ONLY valid JSON with this exact structure:

{
  "description": "overall scene description in 2-3 sentences",
  "location": "interior/exterior + specific place if visible",
  "time_of_day": "morning/noon/afternoon/evening/night/unknown",
  "weather": "sunny/cloudy/overcast/rainy/unknown (for exteriors)",
  "mood": "emotional tone of the image",
  "composition": "rule of thirds / centered / leading lines / etc",
  "camera_angle": "eye level / low angle / high angle / dutch angle / birds eye / etc",
  "lens": "wide / standard / telephoto / macro / fisheye / unknown",
  "focal_length": "estimated mm or unknown",
  "aperture": "estimated f-stop or unknown",
  "shutter_speed": "estimated or unknown",
  "iso": "estimated or unknown",
  "exposure": "underexposed / correct / overexposed / high key / low key",
  "depth_of_field": "shallow / deep / medium",
  "lighting_type": "natural / artificial / mixed / studio / golden hour / etc",
  "lighting_direction": "front / side / back / top / Rembrandt / butterfly / unknown",
  "shadows": "hard / soft / dramatic / minimal / none visible",
  "highlights": "blown / controlled / soft / dramatic",
  "color_temperature": "warm / neutral / cool / mixed / unknown",
  "subject_present": true or false,
  "subject_description": "age range, gender, physical appearance if visible",
  "pose": "detailed description of body position, limbs, weight distribution",
  "gaze_direction": "to camera / away / down / up / distance / unknown",
  "clothing": "detailed clothing description including colors, materials, fit",
  "expression": "facial expression and emotional state",
  "background": "background description",
  "foreground_elements": "elements in the foreground if any",
  "props": "visible props or objects",
  "color_palette": "dominant colors in the scene",
  "starting_frame": "ONE sentence describing the exact starting frame for Kling Image-to-Video",
  "confidence_overall": "high / medium / low",
  "unknown_fields": ["list of field names that could not be determined"]
}"""

USER_PROMPT = """Analyze this image and return the JSON scene description exactly as specified.
Remember: only describe what you can actually see. Use "unknown" for anything uncertain.
Pay special attention to starting_frame — it must be one precise sentence describing what Kling sees as frame 0."""


def run(image_path: str) -> SceneJSON:
    raw = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_text=USER_PROMPT,
        image_path=image_path
    )
    data = parse_json_response(raw)

    return SceneJSON(
        description=data.get("description", "unknown"),
        location=data.get("location", "unknown"),
        time_of_day=data.get("time_of_day", "unknown"),
        weather=data.get("weather", "unknown"),
        mood=data.get("mood", "unknown"),
        composition=data.get("composition", "unknown"),
        camera_angle=data.get("camera_angle", "unknown"),
        lens=data.get("lens", "unknown"),
        focal_length=data.get("focal_length", "unknown"),
        aperture=data.get("aperture", "unknown"),
        shutter_speed=data.get("shutter_speed", "unknown"),
        iso=data.get("iso", "unknown"),
        exposure=data.get("exposure", "unknown"),
        depth_of_field=data.get("depth_of_field", "unknown"),
        lighting_type=data.get("lighting_type", "unknown"),
        lighting_direction=data.get("lighting_direction", "unknown"),
        shadows=data.get("shadows", "unknown"),
        highlights=data.get("highlights", "unknown"),
        color_temperature=data.get("color_temperature", "unknown"),
        subject_present=bool(data.get("subject_present", False)),
        subject_description=data.get("subject_description", "unknown"),
        pose=data.get("pose", "unknown"),
        gaze_direction=data.get("gaze_direction", "unknown"),
        clothing=data.get("clothing", "unknown"),
        expression=data.get("expression", "unknown"),
        background=data.get("background", "unknown"),
        foreground_elements=data.get("foreground_elements", "unknown"),
        props=data.get("props", "unknown"),
        color_palette=data.get("color_palette", "unknown"),
        starting_frame=data.get("starting_frame", ""),
        confidence_overall=data.get("confidence_overall", "medium"),
        unknown_fields=data.get("unknown_fields", []),
    )
