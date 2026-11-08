import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Any

# Импорт графа проекта
try:
    from lambda_tutor.graph import build_graph
except ImportError:
    print("Предупреждение: lambda_tutor.graph не найден, используем заглушку build_graph")
    def build_graph():
        class MockApp:
            def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "error_step": state.get("error_step"),
                    "error_type": "none" if state.get("error_step") is None else "odz",
                    "hint": "Проверь ОДЗ",
                    "hint_level": 1
                }
        return MockApp()

ALL_ERROR_TYPES = ["odz", "non_equivalent", "sign", "arithmetic", "none"]

def calculate_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / total if total > 0 else 0.0

    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    support = defaultdict(int)

    for yt, yp in zip(y_true, y_pred):
        support[yt] += 1
        if yt == yp:
            tp[yt] += 1
        else:
            fp[yp] += 1
            fn[yt] += 1

    per_class = {}
    macro_f1_sum = 0.0
    weighted_f1_sum = 0.0

    for cls in ALL_ERROR_TYPES:
        c_tp = tp[cls]
        c_fp = fp[cls]
        c_fn = fn[cls]
        c_sup = support[cls]

        precision = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        recall = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        per_class[cls] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": c_sup
        }

        macro_f1_sum += f1
        weighted_f1_sum += f1 * c_sup

    macro_f1 = macro_f1_sum / len(ALL_ERROR_TYPES) if ALL_ERROR_TYPES else 0.0
    weighted_f1 = weighted_f1_sum / total if total > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class
    }

def run_benchmark(dataset_path: str = "data/dataset.json", output_path: str = "results/metrics.json"):
    print(f"=== Запуск бенчмарка на датасете: {dataset_path} ===")
    
    if not os.path.exists(dataset_path):
        print(f"Ошибка: файл {dataset_path} не найден!")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    app = build_graph()

    y_true = []
    y_pred = []
    step_matches = 0
    detailed_results = []

    for task in tasks:
        # State графа согласно Разделу 4 CONTRACT.md
        input_state = {
            "task": task["task"],
            "steps": task["student_steps"],
            "error_step": None,
            "error_type": None,
            "retrieved": [],
            "hint": "",
            "hint_level": 1
        }

        output_state = app.invoke(input_state)

        pred_type = output_state.get("error_type", "none")
        pred_step = output_state.get("error_step", None)

        true_type = task["error_type"]
        true_step = task["error_step"]

        y_true.append(true_type)
        y_pred.append(pred_type)

        if pred_step == true_step:
            step_matches += 1

        detailed_results.append({
            "task_id": task["id"],
            "true_error_type": true_type,
            "pred_error_type": pred_type,
            "true_error_step": true_step,
            "pred_error_step": pred_step,
            "hint": output_state.get("hint", "")
        })

    metrics = calculate_metrics(y_true, y_pred)
    step_accuracy = step_matches / len(tasks) if tasks else 0.0
    metrics["step_accuracy"] = round(step_accuracy, 4)

    # Вывод сводной таблицы в терминал
    print("\n" + "=" * 55)
    print(f"{'Класс (error_type)':<18} | {'P':<6} | {'R':<6} | {'F1':<6} | {'Support':<6}")
    print("-" * 55)
    for cls, vals in metrics["per_class"].items():
        print(f"{cls:<18} | {vals['precision']:<6.2f} | {vals['recall']:<6.2f} | {vals['f1']:<6.2f} | {vals['support']:<6}")
    print("-" * 55)
    print(f"Overall Accuracy:  {metrics['accuracy']:.2%}")
    print(f"Step Accuracy:     {metrics['step_accuracy']:.2%}")
    print(f"Macro F1:          {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:       {metrics['weighted_f1']:.4f}")
    print("=" * 55 + "\n")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"summary": metrics, "details": detailed_results}, f, ensure_ascii=False, indent=2)

    print(f" Результаты сохранены в: {output_path}")

if __name__ == "__main__":
    run_benchmark()