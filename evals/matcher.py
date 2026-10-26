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
    """Symmetric token overlap: |A∩B| / |A∪B|.

    Penalises length mismatch. A short expected phrase and a long verbose
    predicted phrase score low even when the meaning is identical.
    """
    ta, tb = tokens(a), tokens(b)
    union = ta | tb
    if not union:
        return 0.0
    return len(ta & tb) / len(union)


def containment(a: str, b: str) -> float:
    """Asymmetric overlap: |A∩B| / min(|A|, |B|).

    Scores 1.0 when one token set is a subset of the other. This is the
    right shape for evaluating a verbose LLM paraphrase against a terse
    ground-truth label: the labels are short, the predictions are long,
    and the meaning lives in the shared core.
    """
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _match(a: str, b: str, threshold: float) -> bool:
    """Pass if either symmetric or asymmetric similarity clears threshold."""
    return max(jaccard(a, b), containment(a, b)) >= threshold


def action_item_matches(expected: dict, predicted: dict) -> bool:
    owner_match = normalise(expected["owner"]) == normalise(predicted["owner"])
    # Task threshold is 0.5 because tasks are short verbs+noun phrases where
    # synonym verbs ("fix" vs "handle") would otherwise drop Jaccard below 0.6
    # even though owner is exact and the noun object is identical.
    task_match = _match(expected["task"], predicted["task"], 0.5)
    return owner_match and task_match


def decision_matches(expected: dict, predicted: dict) -> bool:
    return _match(expected["description"], predicted["description"], 0.6)


def risk_matches(expected: dict, predicted: dict) -> bool:
    return _match(expected["description"], predicted["description"], 0.6)


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
