from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class SceneJSON:
    """Выход Агента 1 — Scene Analyzer"""
    description: str = ""
    location: str = ""
    time_of_day: str = ""
    weather: str = ""
    mood: str = ""
    composition: str = ""
    camera_angle: str = ""
    lens: str = ""
    focal_length: str = ""
    aperture: str = ""
    shutter_speed: str = ""
    iso: str = ""
    exposure: str = ""
    depth_of_field: str = ""
    lighting_type: str = ""
    lighting_direction: str = ""
    shadows: str = ""
    highlights: str = ""
    color_temperature: str = ""
    subject_present: bool = False
    subject_description: str = ""
    pose: str = ""
    gaze_direction: str = ""
    clothing: str = ""
    expression: str = ""
    background: str = ""
    foreground_elements: str = ""
    props: str = ""
    color_palette: str = ""
    # Описание стартового кадра одной фразой — используется в Image-to-Video промптах
    starting_frame: str = ""
    confidence_overall: str = "high"
    unknown_fields: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class StoryboardJSON:
    """Выход Агента 2 — Storyboard Writer"""
    genre: str = ""
    tone: str = ""
    narrative_arc: str = ""
    hook: str = ""
    act_1: str = ""
    act_2: str = ""
    act_3: str = ""
    climax: str = ""
    resolution: str = ""
    key_emotion: str = ""
    target_audience: str = ""
    music_vibe: str = ""
    pacing: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class KlingClip:
    """Один клип для Kling Image-to-Video"""
    clip_number: int = 0
    duration_seconds: str = "5-7"
    description: str = ""
    shot_type: str = ""
    camera_movement: str = ""
    character_action: str = ""
    micro_movements: str = ""
    fabric_behavior: str = ""
    lighting_note: str = ""
    # Для клипов 2+ — описание стартового кадра этого клипа
    # (последний кадр предыдущего клипа)
    clip_starting_frame: str = ""
    prompt: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class DirectorPlan:
    """Выход Агента 3 — Director (только Kling Image-to-Video)"""
    camera_movement: str = ""
    camera_start_position: str = ""
    camera_end_position: str = ""
    shot_types: str = ""
    character_movement: str = ""
    character_start_position: str = ""
    character_end_position: str = ""
    micro_movements: str = ""
    fabric_behavior: str = ""
    hair_behavior: str = ""
    wind: str = ""
    eye_contact: str = ""
    lighting_plan: str = ""
    lighting_master: str = ""
    color_grading: str = ""
    transitions: str = ""
    focus_pulls: str = ""
    depth_changes: str = ""
    pacing_notes: str = ""

    # Kling клипы
    clips: list = field(default_factory=list)
    total_clips: int = 0
    total_duration: str = ""

    # Для валидатора — промпт первого клипа
    prompt_kling: str = ""
    prompt_selected: str = ""
    platform: str = "kling"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class PipelineResult:
    """Полный результат конвейера"""
    image_path: str = ""
    platform: str = "kling"
    llm_provider: str = ""
    scene: Optional[SceneJSON] = None
    storyboard: Optional[StoryboardJSON] = None
    director: Optional[DirectorPlan] = None
    final_prompt: str = ""
    validation_log: list = field(default_factory=list)
    success: bool = False
    error: str = ""

    def to_json(self) -> str:
        data = {
            "image_path": self.image_path,
            "platform": self.platform,
            "llm_provider": self.llm_provider,
            "scene": asdict(self.scene) if self.scene else None,
            "storyboard": asdict(self.storyboard) if self.storyboard else None,
            "director": asdict(self.director) if self.director else None,
            "final_prompt": self.final_prompt,
            "validation_log": self.validation_log,
            "success": self.success,
            "error": self.error,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


@dataclass
class ScenePrompts:
    """Промпты для одной сцены"""
    scene_number: int = 0
    scene_title: str = ""
    scene_description: str = ""
    duration_seconds: int = 4
    new_characters: str = "none"
    key_visual: str = ""
    starting_frame_prompt: str = ""
    kling_prompt: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class FullStory:
    """Полный сценарий с промптами для всех сцен"""
    story_title: str = ""
    story_concept: str = ""
    scene_prompts: list = field(default_factory=list)  # список ScenePrompts как dict
    total_scenes: int = 0
    total_duration: str = ""
    success: bool = False
    error: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
