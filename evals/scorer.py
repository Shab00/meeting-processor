from evals.loader import CATEGORIES
from evals.matcher import (
    action_item_matches,
    decision_matches,
    greedy_match,
    risk_matches,
)

MATCH_FNS = {
    "action_items": action_item_matches,
    "decisions": decision_matches,
    "risks": risk_matches,
}

# Structural fields compared per category; everything else (source_quote,
# made_by, severity) is ignored.
FIELDS = {
    "action_items": ("owner", "task", "due_date"),
    "decisions": ("description",),
    "risks": ("description",),
}


def _metrics(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    hallucination_rate = fp / (tp + fp) if (tp + fp) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "hallucination_rate": hallucination_rate,
    }


def _to_dicts(items, fields: tuple[str, ...]) -> list[dict]:
    out = []
    for item in items:
        d = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        out.append({f: d.get(f) for f in fields})
    return out


def score_sample(sample: dict, analysis) -> dict:
    """analysis is a MeetingAnalysis. Compare to sample['expected'].
    Return per-category metrics and predicted counts."""
    result: dict = {"sample_id": sample["id"]}
    for cat in CATEGORIES:
        expected = sample["expected"][cat]
        predicted = _to_dicts(getattr(analysis, cat), FIELDS[cat])
        tp, fn, fp = greedy_match(expected, predicted, MATCH_FNS[cat])
        metrics = _metrics(tp, fp, fn)
        metrics["n_expected"] = len(expected)
        metrics["n_predicted"] = len(predicted)
        metrics["predicted"] = predicted
        result[cat] = metrics
    return result


def aggregate(results: list[dict]) -> dict:
    """Micro-average across samples: sum TP/FP/FN per category, then compute
    precision/recall/F1 from the sums. Also compute macro-average (mean of
    per-sample F1). Return both, plus totals."""
    micro: dict = {}
    macro: dict = {}
    totals = {"tp": 0, "fp": 0, "fn": 0}

    for cat in CATEGORIES:
        tp = sum(r[cat]["tp"] for r in results)
        fp = sum(r[cat]["fp"] for r in results)
        fn = sum(r[cat]["fn"] for r in results)
        micro[cat] = _metrics(tp, fp, fn)
        f1s = [r[cat]["f1"] for r in results]
        macro[cat] = {"f1": sum(f1s) / len(f1s) if f1s else 0.0}
        totals["tp"] += tp
        totals["fp"] += fp
        totals["fn"] += fn

    overall = _metrics(totals["tp"], totals["fp"], totals["fn"])
    return {
        "n_samples": len(results),
        "micro": micro,
        "macro": macro,
        "overall": overall,
        "totals": totals,
    }
