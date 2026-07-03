import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

import config
from agents.producer import Producer
from agents.action_filter import filter_actions
from agents import analyzer as _analyzer

console = Console()

LLM_DESCRIPTIONS = {
    "openai":    f"OpenAI    — {config.OPENAI_MODEL}",
    "anthropic": f"Anthropic — {config.ANTHROPIC_MODEL}",
}


def ask_llm_provider() -> str:
    console.print(Rule("[bold cyan]Шаг 1 / Выбор AI провайдера[/bold cyan]"))
    console.print()
    for i, (key, desc) in enumerate(LLM_DESCRIPTIONS.items(), 1):
        console.print(f"  [bold yellow]{i}.[/bold yellow] {desc}")
    console.print()
    console.print(f"  [dim]Текущий в .env: [bold]{config.LLM_PROVIDER.upper()}[/bold][/dim]")
    console.print()

    choice = console.input(
        "[bold green]Выберите провайдера (1/2) или Enter для текущего: [/bold green]"
    ).strip()

    if choice == "1":
        provider = "openai"
    elif choice == "2":
        provider = "anthropic"
    else:
        provider = config.LLM_PROVIDER

    config.LLM_PROVIDER = provider
    console.print(f"   ✓ [bold cyan]{provider.upper()}[/bold cyan] / {config.get_model_name()}")
    return provider


def ask_image_path() -> str:
    console.print()
    console.print(Rule("[bold cyan]Шаг 2 / Стартовый кадр[/bold cyan]"))
    console.print()
    console.print("  [dim]Этот кадр станет Frame 0 в Kling Image-to-Video[/dim]")
    console.print()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        console.print(f"   → Аргумент: [cyan]{path}[/cyan]")
    else:
        path = console.input("[bold green]Путь к изображению (JPG/PNG): [/bold green]").strip().strip("'\"")

    if not Path(path).exists():
        console.print(f"[red]❌ Файл не найден: {path}[/red]")
        sys.exit(1)

    console.print(f"   ✓ [cyan]{path}[/cyan]")
    return path


def ask_scenario(scene) -> tuple[dict | None, str | None]:
    """
    Возвращает (action, user_idea).
    Один из них будет задан, или оба None (свободный режим).
    """
    console.print()
    console.print(Rule("[bold cyan]Шаг 3 / Режим сценария[/bold cyan]"))
    console.print()
    console.print("  [bold yellow]1.[/bold yellow] [bold]🎨 Свободный сценарий[/bold]  — агент придумывает историю сам")
    console.print("  [bold yellow]2.[/bold yellow] [bold]🎯 Выбрать действие[/bold]    — из банка 52 действий (фильтр по сцене)")
    console.print("  [bold yellow]3.[/bold yellow] [bold]✏️  Своя идея[/bold]           — описываешь что хочешь видеть")
    console.print()

    while True:
        choice = console.input("[bold green]Выберите режим (1/2/3): [/bold green]").strip()
        if choice in ["1", "2", "3"]:
            break
        console.print("   [red]Введите 1, 2 или 3[/red]")

    if choice == "1":
        console.print("   ✓ [cyan]Свободный сценарий[/cyan] — агент решает сам")
        return None, None

    if choice == "3":
        console.print()
        console.print("  [dim]Опишите что должно происходить в видео.[/dim]")
        console.print("  [dim]Пример: она достаёт из сумки зеркало, поправляет помаду и улыбается камере[/dim]")
        console.print()
        idea = console.input("[bold green]Ваша идея: [/bold green]").strip()
        if idea:
            console.print(f"   ✓ Идея принята: [cyan]{idea[:80]}[/cyan]")
            return None, idea
        else:
            console.print("   → [dim]Пустой ввод — переходим в свободный режим[/dim]")
            return None, None

    # Режим 2 — банк действий с фильтром
    console.print()
    console.print("  [dim]Анализирую сцену и подбираю подходящие действия...[/dim]")
    filtered = filter_actions(scene)

    if not filtered:
        console.print("  [yellow]⚠ Фильтр не вернул действий — показываю полный банк[/yellow]")
        from agents.actions_bank import get_all_actions
        filtered = get_all_actions()

    console.print(f"  [green]✓ Подобрано {len(filtered)} подходящих действий[/green]")
    console.print()

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("№", style="bold yellow", width=4)
    table.add_column("Категория", style="dim", width=22)
    table.add_column("Действие", style="bold white", width=26)
    table.add_column("Адаптация к сцене", style="cyan", width=42)

    for i, action in enumerate(filtered, 1):
        adaptation = action.get("adaptation", "")
        table.add_row(
            str(i),
            action.get("category", ""),
            action["name"],
            adaptation[:70] if adaptation else "[dim]—[/dim]",
        )

    console.print(table)
    console.print()
    console.print(f"  [bold yellow]0.[/bold yellow] [bold]🎲 Случайное из подходящих[/bold]")
    console.print(f"  [bold yellow]Enter.[/bold yellow] [dim]Назад → свободный сценарий[/dim]")
    console.print()

    total = len(filtered)
    while True:
        ch = console.input(f"[bold green]Выберите действие (0–{total}) или Enter: [/bold green]").strip()

        if ch == "":
            console.print("   → [dim]Свободный сценарий[/dim]")
            return None, None

        if ch == "0":
            import random
            action = random.choice(filtered)
            console.print(f"   🎲 Случайное: [bold cyan]{action['name']}[/bold cyan]")
            if action.get("adaptation"):
                console.print(f"   → Адаптация: [cyan]{action['adaptation']}[/cyan]")
            if action.get("kling_warning"):
                console.print(f"   [yellow]⚠ Kling: {action['kling_warning']}[/yellow]")
            return action, None

        try:
            num = int(ch)
            if 1 <= num <= total:
                action = filtered[num - 1]
                console.print(f"   ✓ [bold cyan]{action['name']}[/bold cyan]")
                if action.get("adaptation"):
                    console.print(f"   → Адаптация: [cyan]{action['adaptation']}[/cyan]")
                if action.get("kling_warning"):
                    console.print(f"   [yellow]⚠ Kling: {action['kling_warning']}[/yellow]")
                return action, None
        except ValueError:
            pass

        console.print(f"   [red]Введите 0–{total} или Enter[/red]")


def print_results(result, action: dict | None, user_idea: str | None = None):
    console.print()
    console.print(Rule("[bold green]═══ РЕЗУЛЬТАТЫ ═══[/bold green]"))

    if not result.success:
        console.print(Panel(f"[red]{result.error}[/red]", title="❌ Ошибка"))
        return

    # Режим и действие
    if action:
        adaptation = action.get("adaptation", "")
        body = f"[bold cyan]{action['name']}[/bold cyan] [dim](из банка действий)[/dim]"
        if adaptation:
            body += f"\n[cyan]Адаптация:[/cyan] {adaptation}"
        console.print(Panel(body, title="🎯 Сценарий: действие из банка", border_style="cyan"))
    elif user_idea:
        console.print(Panel(
            f"[bold cyan]{user_idea}[/bold cyan]",
            title="✏️  Сценарий: идея пользователя", border_style="cyan"
        ))
    else:
        console.print(Panel(
            "[dim]Агент придумал историю самостоятельно[/dim]",
            title="🎨 Сценарий: свободный", border_style="cyan"
        ))

    # Сцена
    if result.scene:
        s = result.scene
        console.print(Panel(
            f"[cyan]Стартовый кадр:[/cyan] {s.starting_frame}\n"
            f"[cyan]Локация:[/cyan] {s.location} | [cyan]Время:[/cyan] {s.time_of_day}\n"
            f"[cyan]Настроение:[/cyan] {s.mood}\n"
            f"[cyan]Освещение:[/cyan] {s.lighting_type} / {s.lighting_direction}\n"
            f"[cyan]Одежда:[/cyan] {s.clothing[:100]}\n"
            f"[cyan]Поза:[/cyan] {s.pose[:100]}",
            title="🎬 Агент 1: Scene Analysis",
            border_style="blue"
        ))

    # Сценарий
    if result.storyboard:
        sb = result.storyboard
        console.print(Panel(
            f"[cyan]Жанр:[/cyan] {sb.genre}  [cyan]Тон:[/cyan] {sb.tone}\n"
            f"[cyan]Дуга:[/cyan] {sb.narrative_arc}\n"
            f"[cyan]Hook:[/cyan] {sb.hook}\n"
            f"[cyan]Кульминация:[/cyan] {sb.climax}\n"
            f"[cyan]Эмоция:[/cyan] {sb.key_emotion}  [cyan]Темп:[/cyan] {sb.pacing}",
            title="✍️  Агент 2: Storyboard",
            border_style="magenta"
        ))

    # Director
    if result.director:
        d = result.director
        console.print(Panel(
            f"[cyan]Свет (мастер):[/cyan] {d.lighting_master}\n"
            f"[cyan]Клипов:[/cyan] {d.total_clips}  [cyan]Хронометраж:[/cyan] {d.total_duration}\n"
            f"[cyan]Цветокоррекция:[/cyan] {d.color_grading}\n"
            f"[cyan]Переходы:[/cyan] {d.transitions}",
            title="🎥 Агент 3: Director Plan",
            border_style="yellow"
        ))

    # Kling клипы
    if result.director and result.director.clips:
        console.print()
        console.print(Rule(
            f"[bold green]🎬 KLING КЛИПЫ — Image-to-Video "
            f"({result.director.total_clips} шт. / {result.director.total_duration})[/bold green]"
        ))
        for clip in result.director.clips:
            console.print(Panel(
                f"[dim]Старт:[/dim] {clip.get('clip_starting_frame', '')[:100]}\n"
                f"[dim]{clip.get('shot_type','')} | {clip.get('duration_seconds','')}s | "
                f"{clip.get('description','')}[/dim]\n\n"
                f"[bold white]{clip.get('prompt','')}[/bold white]",
                title=f"[bold cyan]CLIP {clip.get('clip_number','?')}[/bold cyan]",
                border_style="green",
                padding=(1, 2)
            ))

    # Лог валидации
    if result.validation_log:
        console.print()
        console.print(Rule("[dim]Лог валидации[/dim]"))
        for entry in result.validation_log:
            vr = entry.get("result", {})
            status = "✓" if vr.get("passed", True) else "✗"
            score = vr.get("score", "?")
            issues = vr.get("issues", [])
            stage = entry.get("stage", "")
            line = f"  {status} [dim]{stage}[/dim] — score: {score}/100"
            if issues:
                line += f" — {'; '.join(issues[:2])}"
            console.print(line)


def save_results(result, image_path: str) -> Path:
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = Path(image_path).stem
    output_path = output_dir / f"pipeline_{image_name}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.to_json())
    return output_path


def main():
    console.print()
    console.print(Panel(
        "[bold cyan]🎬 KLING IMAGE-TO-VIDEO PIPELINE[/bold cyan]\n"
        "[dim]Scene Analyzer → Action Filter → Storyboard → Director → Prompt[/dim]\n"
        "[dim]Mode: Image-to-Video (стартовый кадр = загруженное изображение)[/dim]",
        border_style="cyan"
    ))
    console.print()

    ask_llm_provider()
    image_path = ask_image_path()

    # Анализируем сцену ДО выбора действия — для умного фильтра
    console.print()
    console.print(Rule("[dim]Предварительный анализ сцены для подбора действий...[/dim]"))
    console.print()
    with console.status("[cyan]Агент 1 анализирует изображение...[/cyan]"):
        pre_scene = _analyzer.run(image_path)
    console.print(f"  ✓ Сцена: {pre_scene.starting_frame[:100]}...")

    action, user_idea = ask_scenario(pre_scene)

    console.print()
    console.print(Rule("[bold yellow]▶ Запуск конвейера[/bold yellow]"))
    console.print()

    producer = Producer(
        image_path=image_path,
        action=action,
        user_idea=user_idea,
        logger=lambda msg: console.print(f"  {msg}")
    )
    # Передаём уже проанализированную сцену чтобы не делать это дважды
    producer._pre_scene = pre_scene
    result = producer.run()

    print_results(result, action, user_idea)

    if result.success:
        path = save_results(result, image_path)
        console.print()
        console.print(f"[green]💾 Сохранено:[/green] [cyan]{path}[/cyan]")
    else:
        console.print()
        console.print("[red]❌ Конвейер завершился с ошибкой.[/red]")


if __name__ == "__main__":
    main()
