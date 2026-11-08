import json

from lambda_tutor.llm import call_llm


def tutor(state):
    task = state.get("task", "")
    steps = state.get("steps", [])

    error_step = state.get("error_step")
    error_type = state.get("error_type", "none")

    retrieved = state.get("retrieved", [])

    # Получаем уровень подсказки
    hint_level = state.get("hint_level", 0)

    try:
        hint_level = int(hint_level)
    except (ValueError, TypeError):
        hint_level = 1

    # Уровень должен быть от 1 до 3
    hint_level = max(1, min(hint_level, 3))

    # Превращаем карточки знаний в текст
    knowledge = json.dumps(
        retrieved,
        ensure_ascii=False,
        indent=2
    )

    # Нумеруем шаги ученика
    numbered_steps = "\n".join(
        f"{i}. {step}"
        for i, step in enumerate(steps, start=1)
    )

    prompt = f"""
Ты — сократический тьютор по математике.

Твоя задача — помочь ученику самостоятельно исправить решение.

Условие задачи:
{task}

Решение ученика:
{numbered_steps}

Номер ошибочного шага:
{error_step}

Тип ошибки:
{error_type}

Карточки знаний:
{knowledge}

Текущий уровень подсказки:
{hint_level}

Правила работы:

1. Не выдавай готовое решение.
2. Не пиши правильный ответ задачи.
3. Не исправляй ошибочный шаг за ученика.
4. Используй карточки знаний, если они подходят к задаче.
5. Обращайся к ученику с наводящим вопросом.

Уровни подсказок:

Уровень 1:
Задай общий вопрос, который поможет ученику задуматься.

Уровень 2:
Укажи на математическое правило или свойство, которое нужно проверить.

Уровень 3:
Дай более конкретную подсказку о том, что нужно проверить или изменить,
но не сообщай готовый ответ.

Верни только JSON следующего формата:

{{
    "hint": "Проверь, правильно ли изменился знак при переносе слагаемого.",
    "hint_level": {hint_level}
}}
"""

    response = call_llm(prompt, fast=True)

    if not isinstance(response, str):
        raise ValueError("Тьютор не вернул текстовый ответ")

    response = response.strip()

    # Ищем JSON в ответе модели
    decoder = json.JSONDecoder()
    result = None

    for i, character in enumerate(response):
        if character == "{":
            try:
                result, _ = decoder.raw_decode(response[i:])
                break
            except json.JSONDecodeError:
                continue

    if not isinstance(result, dict):
        raise ValueError("Не удалось получить JSON от тьютора")

    hint = result.get("hint")

    if not isinstance(hint, str) or not hint.strip():
        raise ValueError("Тьютор вернул пустую подсказку")

    return {
        "hint": hint.strip(),
        "hint_level": hint_level
    }
