import json
from pathlib import Path

CATEGORIES = ("action_items", "decisions", "risks")


def load_samples(path: Path) -> list[dict]:
    """Load eval samples from a JSONL file (one JSON object per line)."""
    samples: list[dict] = []
    with Path(path).open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {e}") from e

            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{lineno}: expected a JSON object")
            if not isinstance(obj.get("id"), str):
                raise ValueError(f"{path}:{lineno}: missing or non-string 'id'")
            if not isinstance(obj.get("transcript"), str):
                raise ValueError(f"{path}:{lineno}: missing or non-string 'transcript'")
            expected = obj.get("expected")
            if not isinstance(expected, dict):
                raise ValueError(f"{path}:{lineno}: missing or non-object 'expected'")
            for cat in CATEGORIES:
                if not isinstance(expected.get(cat), list):
                    raise ValueError(
                        f"{path}:{lineno}: 'expected.{cat}' must be a list"
                    )

            samples.append(obj)
    return samples
