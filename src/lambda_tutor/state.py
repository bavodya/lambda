from typing import TypedDict


class TutorState(TypedDict, total=False):
    task: str
    steps: list[str]

    error_step: int | None
    error_type: str | None

    retrieved: list[dict]

    hint: str
    hint_level: int


def make_initial_state(task: str, steps: list[str]) -> TutorState:
    return {
        "task": task,
        "steps": steps,
        "error_step": None,
        "error_type": None,
        "retrieved": [],
        "hint": "",
        "hint_level": 0,
    }