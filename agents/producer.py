from agents import analyzer, validator, storyboard, director
from agents.action_filter import filter_actions
from models.schemas import PipelineResult
import config


class Producer:
    def __init__(self, image_path: str, action: dict = None,
                 user_idea: str = None, logger=None):
        self.image_path = image_path
        self.platform = "kling"
        self.action = action
        self.user_idea = user_idea
        self.logger = logger
        self.result = PipelineResult(
            image_path=image_path,
            platform="kling",
            llm_provider=config.LLM_PROVIDER,
        )

    def _log(self, message: str):
        if self.logger:
            self.logger(message)

    def run(self) -> PipelineResult:
        try:
            # ── Агент 1: Scene Analyzer ──────────────────────────────────
            # Если main.py уже сделал предварительный анализ — используем его
            if hasattr(self, '_pre_scene') and self._pre_scene:
                self._log("🎬 Агент 1: Используется предварительный анализ сцены...")
                scene = self._pre_scene
            else:
                self._log("🎬 Агент 1: Анализирую изображение...")
                scene = analyzer.run(self.image_path)

            self.result.scene = scene
            self._log(f"   ✓ Уверенность: {scene.confidence_overall}")
            self._log(f"   → Стартовый кадр: {scene.starting_frame[:100]}...")

            # ── Агент 0: Валидация сцены ─────────────────────────────────
            self._log("🔍 Агент 0: Валидирую описание сцены...")
            scene_validation = validator.validate_scene(scene)
            self.result.validation_log.append({"stage": "scene_validation", "result": scene_validation})
            score = scene_validation.get("score", "?")
            if not scene_validation.get("passed", True):
                issues = scene_validation.get("issues", [])
                self._log(f"   ⚠ Score: {score}/100 — {'; '.join(issues)}")
            else:
                self._log(f"   ✓ Валидация пройдена. Score: {score}/100")

            # ── Агент 2: Storyboard Writer ────────────────────────────────
            self._log("✍️  Агент 2: Создаю сценарий...")
            if self.action:
                self._log(f"   → Режим: действие из банка — {self.action['name']}")
                if self.action.get("adaptation"):
                    self._log(f"   → Адаптация: {self.action['adaptation']}")
            elif self.user_idea:
                self._log(f"   → Режим: идея пользователя — {self.user_idea[:80]}")
            else:
                self._log(f"   → Режим: свободный сценарий")
            story = storyboard.run(scene, action=self.action, user_idea=self.user_idea)
            self.result.storyboard = story
            self._log(f"   ✓ Сценарий готов. Жанр: {story.genre}, Тон: {story.tone}")
            self._log(f"   → Hook: {story.hook[:80]}...")

            # ── Агент 3: Director ─────────────────────────────────────────
            self._log("🎥 Агент 3: Создаю режиссёрский план (Kling Image-to-Video)...")
            plan = director.run(
                scene, story,
                platform="kling",
                action=self.action,
                user_idea=self.user_idea,
                logger=self.logger
            )
            self.result.director = plan
            self._log(f"   ✓ Готово: {plan.total_clips} клипа, {plan.total_duration}")

            # ── Агент 0: Валидация промпта + авто-исправление ─────────────
            MAX_RETRIES = 2
            PASS_SCORE = 80
            current_prompt = plan.prompt_kling  # валидируем первый клип

            for attempt in range(1, MAX_RETRIES + 2):
                label = "оригинал" if attempt == 1 else f"исправление #{attempt-1}"
                self._log(f"🔍 Агент 0: Валидирую промпт Clip 1 ({label})...")
                prompt_validation = validator.validate_prompt(current_prompt, "kling")
                score = prompt_validation.get("score", 0)
                passed = prompt_validation.get("passed", False)
                issues = prompt_validation.get("issues", [])
                suggestions = prompt_validation.get("suggestions", [])

                self.result.validation_log.append({
                    "stage": f"prompt_validation_attempt_{attempt}",
                    "result": prompt_validation
                })

                if passed and score >= PASS_SCORE:
                    self._log(f"   ✓ Принят. Score: {score}/100, "
                              f"Слов: {prompt_validation.get('word_count', '?')}")
                    break

                self._log(f"   ✗ Score: {score}/100 — {'; '.join(issues)}")

                if attempt > MAX_RETRIES:
                    self._log(f"   → Исчерпаны попытки. Используем последний вариант.")
                    break

                self._log(f"   ♻ Агент 3: Переписываю промпт (попытка {attempt}/{MAX_RETRIES})...")
                import json as _json
                from dataclasses import asdict as _asdict
                current_prompt = director.rewrite_prompt(
                    platform="kling",
                    original_prompt=current_prompt,
                    issues=issues,
                    suggestions=suggestions,
                    scene_data=_json.dumps(_asdict(scene), ensure_ascii=False),
                    storyboard_data=_json.dumps(_asdict(story), ensure_ascii=False),
                    director_data=_asdict(plan),
                )
                # Обновляем промпт в первом клипе
                if plan.clips:
                    plan.clips[0]["prompt"] = current_prompt
                plan.prompt_kling = current_prompt
                self._log(f"   ✓ Новый вариант готов")

            # Обновляем итоговый display
            plan.prompt_selected = director._format_clips_for_display(plan.clips)
            self.result.final_prompt = plan.prompt_selected
            self.result.success = True
            self._log("✅ Конвейер завершён успешно!")

        except Exception as e:
            self.result.success = False
            self.result.error = str(e)
            self._log(f"❌ Ошибка: {e}")
            import traceback
            self._log(traceback.format_exc())

        return self.result
