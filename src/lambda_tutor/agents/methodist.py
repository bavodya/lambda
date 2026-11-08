"""Агент-методист: по типу ошибки и условию задачи ищет карточки знаний.

Контракт (CONTRACT.md, раздел 5):
    retrieve(state) -> {"retrieved": [...]}
Функция возвращает ТОЛЬКО поле retrieved, остальной state не трогает.
"""

import json
import re
from pathlib import Path

# --- 1. Путь к базе знаний -------------------------------------------------
# __file__ = .../src/lambda_tutor/agents/methodist.py
# parents[0]=agents, [1]=lambda_tutor, [2]=src, [3]=корень репозитория.
# Так путь работает, откуда бы ни запускали программу.
KNOWLEDGE_PATH = Path(__file__).resolve().parents[3] / "data" / "knowledge" / "knowledge.json"

# Сколько карточек отдаём тьютору (3 хватает, больше — лишний шум для LLM)
TOP_K = 3

# Баллы за совпадения (подбираются экспериментально)
SCORE_ERROR_TYPE = 10  # тип ошибки карточки совпал с error_type из state
SCORE_TOPIC = 5  # тема карточки угадана по условию задачи
SCORE_WORD = 1  # общее слово между задачей и карточкой
MAX_WORD_SCORE = 3  # чтобы слова не перебивали тип ошибки и тему

# --- 2. Определение темы задачи по ключевым словам ---------------------------
# Ключ — тема карточки (поле topic), значение — признаки в тексте задачи.
# Ищем как подстроки в нижнем регистре, поэтому "логарифм" найдёт
# "логарифмическое", "логарифма" и т.д.
TOPIC_TRIGGERS = {
    "логарифмические уравнения": ["log", "lg", "ln", "логарифм"],
    "логарифмические неравенства": ["log", "lg", "ln", "логарифм"],
    "иррациональные уравнения": ["sqrt", "√", "корень", "корн"],
    "рациональные уравнения": ["дроб", "знаменат", "/"],
    "рациональные неравенства": ["неравенств", "<", ">", "≤", "≥"],
    "показательные уравнения": ["^x", "^{x", "показательн", "степен"],
    "уравнения с модулем": ["|", "модул", "abs"],
}

# Слова, которые есть почти в любой задаче: по ним искать бессмысленно
STOP_STEMS = {"решит", "уравн", "нерав", "найди", "наибо", "наиме", "корни",
              "котор", "значе", "перем", "ответ"}

_cards_cache = None  # карточки читаем с диска один раз, а не при каждом вызове


def load_cards() -> list[dict]:
    """Читает knowledge.json и запоминает результат."""
    global _cards_cache
    if _cards_cache is None:
        with open(KNOWLEDGE_PATH, encoding="utf-8") as f:
            _cards_cache = json.load(f)
    return _cards_cache


def _stems(text: str) -> set[str]:
    """Грубая «основа» слова: первые 5 букв.

    Так "логарифма", "логарифму" и "логарифмом" сводятся к "логар".
    Это простейший заменитель лемматизации, для КП2 достаточно.
    """
    words = re.findall(r"[а-яёa-z]+", text.lower())
    return {w[:5] for w in words if len(w) >= 4} - STOP_STEMS


def _detected_topics(task: str) -> set[str]:
    """Какие темы из TOPIC_TRIGGERS встречаются в условии задачи."""
    task_low = task.lower()
    return {
        topic
        for topic, triggers in TOPIC_TRIGGERS.items()
        if any(t in task_low for t in triggers)
    }


def _score_card(card: dict, error_type: str | None, topics: set[str], task_stems: set[str]) -> int:
    """Считает, насколько карточка подходит. Чем больше баллов, тем лучше."""
    score = 0

    # Самый сильный сигнал: тип ошибки, найденный диагностом
    if error_type and error_type != "none" and error_type in card.get("error_types", []):
        score += SCORE_ERROR_TYPE

    # Тема карточки совпала с темой задачи
    if card.get("topic") in topics:
        score += SCORE_TOPIC

    # Пересечение слов задачи со словами карточки (ограничено сверху)
    card_stems = _stems(card.get("title", "") + " " + card.get("text", ""))
    common = len(task_stems & card_stems)
    score += min(common * SCORE_WORD, MAX_WORD_SCORE)

    return score


def retrieve(state) -> dict:
    """Находит самые релевантные карточки знаний.

    Читает из state: error_type, task.
    Возвращает: {"retrieved": [карточка, ...]} — до TOP_K штук, лучшие первыми.
    """
    error_type = state.get("error_type")
    task = state.get("task") or ""

    # Ошибки нет — подсказка не нужна, карточки тоже
    if error_type == "none":
        return {"retrieved": []}

    topics = _detected_topics(task)
    task_stems = _stems(task)

    scored = []
    for card in load_cards():
        score = _score_card(card, error_type, topics, task_stems)
        if score > 0:  # нулевые карточки не берём
            scored.append((score, card))

    # sorted стабильный: при равных баллах сохраняется порядок из файла
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return {"retrieved": [card for _, card in scored[:TOP_K]]}


if __name__ == "__main__":
    # Быстрая проверка: python src/lambda_tutor/agents/methodist.py
    demo = {
        "task": "Решите уравнение log_2(x - 1) + log_2(x - 3) = 3",
        "error_type": "odz",
    }
    for c in retrieve(demo)["retrieved"]:
        print("-", c["id"], "|", c["title"])