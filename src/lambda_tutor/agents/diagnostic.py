import json

from lambda_tutor.llm import call_llm


ERROR_TYPES = [
    "odz",
    "non_equivalent",
    "sign",
    "arithmetic",
    "none"
]


def diagnose(state):
    task = state.get("task", "")
    steps = state.get("steps", [])

    numbered_steps = "\n".join(
        f"{i}. {step}"
        for i, step in enumerate(steps, start=1)
    )

    prompt = f"""
Ты — агент диагностики ошибок в решении математических задач.

Условие задачи:
{task}

Решение ученика:
{numbered_steps}

Найди ПЕРВЫЙ ошибочный шаг.

Возможные типы ошибок:
- odz — потеря ОДЗ или появление постороннего корня;
- non_equivalent — неравносильный переход;
- sign — ошибка знака;
- arithmetic — вычислительная ошибка;
- none — ошибок нет.

Правила:
1. Проверяй шаги последовательно.
2. Если ошибка есть, укажи номер первого ошибочного шага.
3. Нумерация начинается с 1.
4. Если ошибок нет, укажи error_step: null и error_type: "none".
5. Не исправляй решение.
6. Не добавляй пояснений вне JSON.

Верни строго JSON следующего формата:
{{
    "error_step": 2,
    "error_type": "sign"
}}

Если ошибок нет, верни:
{{
    "error_step": null,
    "error_type": "none"
}}
"""

    response = call_llm(prompt, fast=True)

    if not isinstance(response, str):
        raise ValueError("Диагност не вернул текстовый ответ")

    response = response.strip()

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
        raise ValueError("Не удалось получить JSON от диагноста")

    error_step = result.get("error_step")
    error_type = result.get("error_type")

    if error_type not in ERROR_TYPES:
        raise ValueError("Диагност вернул неизвестный тип ошибки")

    if error_type == "none":
        if error_step is not None:
            raise ValueError("При отсутствии ошибки error_step должен быть null")

        return {
            "error_step": None,
            "error_type": "none"
        }

    if type(error_step) is not int:
        raise ValueError("Номер ошибочного шага должен быть целым числом")

    if error_step < 1 or error_step > len(steps):
        raise ValueError("Номер ошибочного шага находится вне диапазона")

    return {
        "error_step": error_step,
        "error_type": error_type
    }
