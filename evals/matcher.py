import re
import string
from typing import Callable

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "by",
    "with", "at", "is", "are", "was", "were", "be", "been", "will", "would",
    "should", "can", "could", "do", "does", "did", "this", "that", "these",
    "those", "it", "its", "we", "our", "you", "your", "they", "their", "i",
    "my", "he", "she", "his", "her",
}

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def normalise(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace, strip."""
    text = (text or "").lower().translate(_PUNCT_TABLE)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> set[str]:
    return {t for t in normalise(text).split() if t not in STOPWORDS}


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    union = ta | tb
    if not union:
        return 0.0
    return len(ta & tb) / len(union)


def action_item_matches(expected: dict, predicted: dict) -> bool:
    owner_match = normalise(expected["owner"]) == normalise(predicted["owner"])
    task_match = jaccard(expected["task"], predicted["task"]) >= 0.6
    return owner_match and task_match


def decision_matches(expected: dict, predicted: dict) -> bool:
    return jaccard(expected["description"], predicted["description"]) >= 0.6


def risk_matches(expected: dict, predicted: dict) -> bool:
    return jaccard(expected["description"], predicted["description"]) >= 0.6


def greedy_match(
    expected: list[dict],
    predicted: list[dict],
    match_fn: Callable[[dict, dict], bool],
) -> tuple[int, int, int]:
    """Return (true_positives, false_negatives, false_positives).

    Each expected matches at most one predicted, and vice versa.
    Iterate expected in order; for each, find the first unmatched predicted
    that satisfies match_fn. Count TP. Remaining expected = FN.
    Remaining predicted = FP.
    """
    matched_pred = [False] * len(predicted)
    tp = 0
    for e in expected:
        for i, p in enumerate(predicted):
            if not matched_pred[i] and match_fn(e, p):
                matched_pred[i] = True
                tp += 1
                break
    fn = len(expected) - tp
    fp = len(predicted) - tp
    return tp, fn, fp
