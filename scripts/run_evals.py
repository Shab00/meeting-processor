"""Offline extraction-quality eval for the meeting-processor agent.

Usage:
    python scripts/run_evals.py [--limit N] [--out PATH]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

# Allow `python scripts/run_evals.py` from the repo root to import app/ and evals/.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from evals.loader import CATEGORIES, load_samples  # noqa: E402
from evals.runner import run_evals  # noqa: E402

SAMPLES_PATH = REPO_ROOT / "evals" / "data" / "samples.jsonl"
DEFAULT_OUT = REPO_ROOT / "evals" / "artifacts" / "report.json"


def _sample_rows(report: dict) -> list[list[str]]:
    rows = []
    for r in report["results"]:
        row = [r["sample_id"]]
        for cat in CATEGORIES:
            m = r[cat]
            row.append(f"{m['f1']:.2f} ({m['tp']}/{m['fp']}/{m['fn']})")
        rows.append(row)
    for f in report["failed"]:
        rows.append([f["sample_id"], f["error"], "", ""])
    return rows


def _aggregate_rows(report: dict) -> list[list[str]]:
    micro = report["aggregate"]["micro"]
    rows = []
    for cat in CATEGORIES:
        m = micro[cat]
        rows.append([
            cat,
            f"{m['precision']:.2f}",
            f"{m['recall']:.2f}",
            f"{m['f1']:.2f}",
            str(m["tp"]),
            str(m["fp"]),
            str(m["fn"]),
            f"{m['hallucination_rate']:.2f}",
        ])
    return rows


SAMPLE_HEADER = ["Sample", "action_items F1 (TP/FP/FN)", "decisions F1 (TP/FP/FN)", "risks F1 (TP/FP/FN)"]
AGG_HEADER = ["Category", "Precision", "Recall", "F1", "TP", "FP", "FN", "Halluc"]


def _text_table(header: list[str], rows: list[list[str]]) -> str:
    widths = [max(len(str(c)) for c in col) for col in zip(header, *rows)]
    lines = ["  ".join(h.ljust(w) for h, w in zip(header, widths))]
    for row in rows:
        lines.append("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    return "\n".join(lines)


def _md_table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _markdown(report: dict) -> str:
    agg = report["aggregate"]
    parts = [
        "# Meeting-processor extraction eval",
        "",
        f"Samples scored: {agg['n_samples']} · failed: {len(report['failed'])}",
        "",
        "## Aggregate (micro-averaged)",
        "",
        _md_table(AGG_HEADER, _aggregate_rows(report)),
        "",
        "Macro F1 (mean of per-sample F1): "
        + ", ".join(f"{cat} {agg['macro'][cat]['f1']:.2f}" for cat in CATEGORIES),
        "",
        "## Per sample",
        "",
        _md_table(SAMPLE_HEADER, _sample_rows(report)),
        "",
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=None, help="only run the first N samples")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="JSON report path")
    args = parser.parse_args()

    samples = load_samples(SAMPLES_PATH)
    report = asyncio.run(run_evals(samples, limit=args.limit))

    print("Per-sample results")
    print(_text_table(SAMPLE_HEADER, _sample_rows(report)))
    print()
    print(f"Aggregate (micro-averaged over {report['aggregate']['n_samples']} samples)")
    print(_text_table(AGG_HEADER, _aggregate_rows(report)))

    out_json: Path = args.out
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2))
    out_md = out_json.with_suffix(".md")
    out_md.write_text(_markdown(report))
    print()
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")

    if report["failed"]:
        print(f"{len(report['failed'])} sample(s) failed to run", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
