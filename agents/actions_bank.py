import random

# ─────────────────────────────────────────────────────────────────────────────
# БАНК ДЕЙСТВИЙ — сгруппирован по категориям
# Каждое действие: name + description (что именно делает персонаж)
# ─────────────────────────────────────────────────────────────────────────────

ACTIONS_BANK = {
    "💧 Вода": [
        {
            "name": "Прыжок в воду",
            "description": "Character runs 3-4 steps and jumps into pool or sea feet-first, full body submerges, resurfaces with water streaming down face and hair"
        },
        {
            "name": "Вход в море",
            "description": "Character walks slowly into sea — water rises from ankles to thighs, she pauses waist-deep, arms spread wide on water surface, looks down at her reflection"
        },
        {
            "name": "Выходит из воды",
            "description": "Character emerges from pool or sea, water cascading off body, pushes wet hair back from face with both hands, opens eyes slowly"
        },
        {
            "name": "Брызги руками",
            "description": "Character crouches at pool edge and sweeps both hands through water creating a wide arc of spray catching sunlight, laughs or smiles at the explosion of droplets"
        },
        {
            "name": "Ныряет под воду",
            "description": "Character takes breath, slides underwater — camera stays above surface showing her distorted silhouette beneath, she rolls slowly, hair floating"
        },
        {
            "name": "Ложится на воду",
            "description": "Character leans back into water, floats on her back, arms out, face to sky, hair spreading around her head, completely still as water holds her"
        },
    ],

    "🏃 Движение": [
        {
            "name": "Бег по берегу",
            "description": "Character runs along shoreline, feet splashing in shallow water, hair flying behind her, looking straight ahead with pure speed and energy"
        },
        {
            "name": "Резкий разворот",
            "description": "Character walks away from camera, suddenly spins 180 degrees to face lens, stops dead — direct eye contact, slight smile, hair swings from momentum"
        },
        {
            "name": "Прыжок на месте",
            "description": "Character jumps straight up with arms raised overhead, at peak of jump body is fully extended, lands soft, hair and fabric airborne for a moment"
        },
        {
            "name": "Танцевальное движение",
            "description": "Character does one sharp isolated dance move — hip drop, shoulder roll, or arm sweep — not choreography, just one raw instinctive movement, then stills"
        },
        {
            "name": "Бежит к камере",
            "description": "Character starts 10 meters back and runs directly toward camera, growing from full shot to extreme close-up, stops just before lens, out of breath, laughing"
        },
        {
            "name": "Кружится",
            "description": "Character spins slowly in place, arms slightly out, fabric of swimwear or wrap fans outward, hair lifts, she closes eyes mid-spin then opens them to camera"
        },
    ],

    "👗 Одежда и тело": [
        {
            "name": "Снимает парео",
            "description": "Character slowly unties sarong or wrap from waist, fabric falls away revealing bikini underneath, she lets it drop or catches it at last moment"
        },
        {
            "name": "Надевает или снимает шляпу",
            "description": "Character removes wide-brim hat in one smooth motion, hair falls loose, she holds hat at arm's length and lets ocean wind take it slightly, catches it"
        },
        {
            "name": "Поправляет бретельку",
            "description": "Character reaches back and adjusts bikini strap with precision — slow deliberate movement, rolls shoulder, tests fit, a private gesture made visible"
        },
        {
            "name": "Встряхивает волосы",
            "description": "Character bends forward, flips hair down, then whips head back — hair fans in full arc, lands across shoulders or back, she settles it with both hands"
        },
        {
            "name": "Расстёгивает верх бикини",
            "description": "Character reaches behind neck or back, slowly unclips bikini top, holds fabric against chest, turns toward camera — suggestive, not explicit"
        },
        {
            "name": "Натирается маслом",
            "description": "Character pours oil or sunscreen into palm, applies it slowly across collarbone and shoulder — skin catches light differently where oil touches, glistens"
        },
    ],

    "😎 Эмоция и взгляд": [
        {
            "name": "Смех запрокидывая голову",
            "description": "Character laughs genuinely — head tilts back, throat exposed, eyes close, body shakes slightly with laughter, then she catches herself and looks back at camera"
        },
        {
            "name": "Прямой взгляд в камеру",
            "description": "Character turns slowly to face camera, holds direct eye contact for 3 full seconds — no smile, no expression shift, just absolute presence, then slow blink"
        },
        {
            "name": "Укусить губу или потянуться",
            "description": "Character stretches both arms overhead, arches back, closes eyes — a completely unselfconscious moment, fabric pulls taut across body, then relaxes"
        },
        {
            "name": "Игривый взгляд через плечо",
            "description": "Character walks away from camera, after 4-5 steps turns her head sharply to look back over one shoulder — not coy, more like a challenge — then continues walking"
        },
    ],

    "🌊 Среда": [
        {
            "name": "Бросает шляпу в воздух",
            "description": "Character tosses wide-brim hat straight up — camera follows hat rising against sky, it reaches peak and begins to fall, character catches or misses it"
        },
        {
            "name": "Кормит птиц",
            "description": "Character holds out flat palm with food, seagulls or pigeons land or hover — chaotic energy, wings and wind, she laughs or stays perfectly still"
        },
        {
            "name": "Ложится на песок",
            "description": "Character deliberately lets herself fall backward onto sand, arms spread, cloud of sand rises around impact, she lies still looking at sky, then turns face to camera"
        },
        {
            "name": "Держит ткань на ветру",
            "description": "Character holds lightweight fabric — pareo, sarong, sheer cover-up — at arm's length and lets wind fully extend it like a flag, her body as anchor"
        },
    ],

    "💃 Тело и поза — лёжа": [
        {
            "name": "Арка спины лёжа",
            "description": "Character lies on back, pelvis grounded, spine arches upward — shoulders and hips as anchor points, ribcage lifts, abdomen elongates, head tilts back slightly, held for 3 seconds then releases slowly"
        },
        {
            "name": "S-изгиб на боку",
            "description": "Character lies on side, bottom hip pushed back, top hip rolled forward, creating S-curve from shoulder through waist to hip — one arm under head, top leg slightly forward, camera shoots from front"
        },
        {
            "name": "Опора на локти лёжа",
            "description": "Character lies on stomach, props upper body on forearms, chest lifted, shoulders back and down, chin slightly forward — legs relaxed or ankles crossed, gaze direct at camera"
        },
        {
            "name": "Перекат на бок",
            "description": "Character starts on back, slowly rolls to side — movement initiates through ribcage, hip follows last, hair sweeps across surface, ends in S-curve position facing camera"
        },
        {
            "name": "Подъём бедра лёжа",
            "description": "Character lies on back, one knee bent foot flat on surface — slowly lifts pelvis into bridge position, holds 2 seconds, fabric of bikini bottom pulls taut across hip bones, then lowers"
        },
        {
            "name": "Потяжка всем телом лёжа",
            "description": "Character lying down stretches full body — arms extend overhead, toes point away, spine lengthens maximally, every body line extends, fabric pulls taut, then full release and body softens"
        },
    ],

    "💃 Тело и поза — у стены": [
        {
            "name": "Опора спиной о стену",
            "description": "Character leans back against wall, one shoulder slightly more contact than other, hips pushed slightly forward from wall — slow weight shift from center to one hip, head falls back against wall"
        },
        {
            "name": "Сползание по стене",
            "description": "Character starts standing against wall, slowly slides down — spine in full contact throughout, ends in low seated position with knees up, head rests back on wall, eyes close"
        },
        {
            "name": "Разворот к стене",
            "description": "Character faces wall, one hand flat against surface at shoulder height, forehead resting on back of hand, opposite hip pushed out — camera shoots from behind at 45-degree angle"
        },
        {
            "name": "Прогиб от стены",
            "description": "Character stands with back to wall, walks feet forward 30cm, arches spine away — only shoulders and hips maintain wall contact, ribcage and abdomen lift forward, arms hang or reach back"
        },
    ],

    "💃 Тело и поза — стоя": [
        {
            "name": "S-стойка контрапост",
            "description": "Character shifts full weight onto one leg, opposite hip drops and pushes out, torso counter-rotates slightly — classic contrapposto stance, one shoulder lower, head tilts to high shoulder side"
        },
        {
            "name": "Изоляция бёдер",
            "description": "Character performs slow isolated hip movement — figure-eight path, upper body stays relatively still, weight transfers heel to heel in continuous motion, arms loose at sides"
        },
        {
            "name": "Волна торсом",
            "description": "Character initiates body-roll from pelvis — wave travels up through waist, ribcage, chest, shoulders, head follows last — one fluid continuous motion, shot from profile or front"
        },
        {
            "name": "Шаг с изгибом",
            "description": "Character takes one slow deliberate step forward — at moment of weight transfer hip pushes out to side, torso leans slightly opposite, S-curve appears mid-stride, camera catches the peak"
        },
        {
            "name": "Руки вдоль тела",
            "description": "Character standing, both hands start at waist — slowly slide down along outer thighs to mid-thigh and back up, deliberate framing gesture that draws the eye along the full body line"
        },
        {
            "name": "Запрокинуть голову стоя",
            "description": "Character standing, chin lifts slowly, head drops back, throat fully exposed, eyes close — arms float slightly out to sides, held for 3 seconds, then head returns forward and eyes open to camera"
        },
        {
            "name": "Спуск на пол",
            "description": "Character standing, descends to floor in one fluid movement — one knee first, then other, sits back on heels, then reclines onto side — camera follows the full descent"
        },
        {
            "name": "Поворот 360",
            "description": "Character turns slowly one full rotation in place — camera stays fixed, viewer sees all angles of body and garment in sequence — one rotation takes 4-5 seconds, ends facing camera"
        },
    ],

    "👁 Мимика и взгляд": [
        {
            "name": "Томный взгляд",
            "description": "ECU on face — heavy-lidded eyes at half-mast, gaze locks directly into lens, slow deliberate eye contact sustained for 4 seconds, lips slightly parted, no other movement"
        },
        {
            "name": "Взгляд из-под ресниц",
            "description": "Character's chin lowers 15 degrees, eyes angle upward through lashes directly at camera — whites visible below iris, held for 3 seconds, then slow return to neutral"
        },
        {
            "name": "Взгляд искоса",
            "description": "Character's head turns 40 degrees away from camera, eyes slide to extreme inner corner toward lens — sideways gaze, white of far eye visible, held then slow return"
        },
        {
            "name": "Медленное моргание",
            "description": "ECU on face — character holds direct eye contact, performs one single slow deliberate blink: lids descend over 1.5 seconds, brief pause closed, rise over 1.5 seconds — loaded and intentional"
        },
        {
            "name": "Прикусить губу",
            "description": "CU on lower face — lower lip caught lightly between teeth, held for 2 seconds, released slowly — eyes remain on camera throughout, jaw relaxed, minimal other facial movement"
        },
        {
            "name": "Улыбка одним углом",
            "description": "CU on face — one corner of mouth lifts slowly into asymmetric half-smile while other stays neutral, eyes narrow slightly on smiling side — knowing expression held for 3 seconds"
        },
        {
            "name": "Кончик языка",
            "description": "CU on lips — tip of tongue touches center of upper lip slowly, traces it, withdraws — deliberate and unhurried, 2 seconds total, eyes on camera throughout"
        },
        {
            "name": "Подмигивание",
            "description": "ECU on face — right eye closes slowly in deliberate wink while left eye stays fully open, right lid descends over 1 second and rises over 1 second, lips form slight smile at same moment. NOTE: Kling may not render single-eye movement accurately — consider using 'медленное моргание' as alternative",
            "kling_warning": "low reliability — both eyes may close"
        },
    ],
}


def get_all_actions() -> list[dict]:
    """Возвращает плоский список всех действий с категорией."""
    result = []
    for category, actions in ACTIONS_BANK.items():
        for action in actions:
            result.append({
                "category": category,
                "name": action["name"],
                "description": action["description"],
                "kling_warning": action.get("kling_warning", ""),
            })
    return result


def get_random_action() -> dict:
    """Возвращает случайное действие из банка."""
    all_actions = get_all_actions()
    return random.choice(all_actions)


def get_action_by_index(index: int) -> dict | None:
    """Возвращает действие по порядковому номеру (1-based)."""
    all_actions = get_all_actions()
    if 1 <= index <= len(all_actions):
        return all_actions[index - 1]
    return None


def format_actions_for_display() -> list[tuple[int, str, str, str]]:
    """
    Возвращает список (номер, категория, название, описание) для отображения.
    """
    result = []
    idx = 1
    for category, actions in ACTIONS_BANK.items():
        for action in actions:
            result.append((idx, category, action["name"], action["description"]))
            idx += 1
    return result
